r"""
:mod:`cape.pyfun.case`: FUN3D case control module
==================================================

This module contains the important function :func:`case.run_fun3d`,
which actually runs ``nodet`` or ``nodet_mpi``, along with the utilities
that support it.

It also contains FUN3D-specific versions of some of the generic methods
from :mod:`cape.case`.  For instance the function :func:`GetCurrentIter`
determines how many FUN3D iterations have been run in the current
folder, which is obviously a solver-specific task.  It also contains the
function :func:`LinkPLT`, which creates links to fixed Tecplot file
names from the most recent output created by FUN3D.

All of the functions from :mod:`cape.case` are imported here.  Thus they
are available unless specifically overwritten by specific
:mod:`cape.pyfun` versions.

"""

# Standard library modules
import glob
import os
import re
import shutil
import sys

# Third-party modules
import numpy as np

# Local imports
from . import bin
from . import cmd
from .. import argread
from .. import text as textutils
from ..cfdx import case as cc
from ..cfdx import queue
from .options.runctlopts import RunControlOpts
from .namelist import Namelist


# Regular expression to find a line with an iteration
_regex_dict = {
    "time": "(?P<time>[1-9][0-9]*)",
    "iter": "(?P<iter>[1-9][0-9]*)",
}
# Combine them; different format for steady and time-accurate modes
REGEX_F3DOUT = re.compile(r"\s*%(time)s?\s+%(iter)s\s{2,}[-0-9]" % _regex_dict)

# Help message for CLI
HELP_RUN_FUN3D = r"""
``run_fun3d.py``: Run FUN3D for one phase
================================================

This script determines the appropriate phase to run for an individual
case (e.g. if a restart is appropriate, etc.), sets that case up, and
runs it.

:Call:

    .. code-block:: console

        $ run_fun3d.py [OPTIONS]
        $ python -m cape.pyfun run [OPTIONS]

:Options:

    -h, --help
        Display this help message and quit

:Versions:
    * 2014-10-02 ``@ddalle``: v1.0 (pycart)
    * 2015-10-19 ``@ddalle``: v1.0
    * 2021-10-01 ``@ddalle``: v2.0; part of :mod:`case`
"""

# Maximum number of calls to run_phase()
NSTART_MAX = 80


# Function to complete final setup and call the appropriate FUN3D commands
def run_fun3d():
    r"""Setup and run the appropriate FUN3D command

    :Call:
        >>> case.run_fun3d()
    :Versions:
        * 2015-10-19 ``@ddalle``: v1.0
        * 2016-04-05 ``@ddalle``: v1.1; add AFLR3 hook
    """
    # Process arguments
    a, kw = argread.readkeys(sys.argv)
    # Check for help argument.
    if kw.get('h') or kw.get('help'):
        # Display help and exit
        print(textutils.markdown(HELP_RUN_FUN3D))
        return cc.IERR_OK
    # Start RUNNING and timer (checks if already running)
    tic = cc.init_timer()
    # Get the run control settings
    rc = read_case_json()
    # Initialize FUN3D start counter
    nstart = 0
    # Loop until case complete, new job submitted, or timeout
    while nstart < NSTART_MAX:
        # Determine the run index
        j = GetPhaseNumber(rc)
        # Write the start time
        WriteStartTime(tic, rc, j)
        # Prepare files
        PrepareFiles(rc, j)
        # Prepare environment variables (other than OMP_NUM_THREADS)
        cc.prepare_env(rc, j)
        # Run the appropriate commands
        try:
            run_phase(rc, j)
        except Exception:
            # Failure
            cc.mark_failure("run_phase")
            # Stop running marker
            cc.mark_stopped()
            # Return code
            return cc.IERR_RUN_PHASE
        # Clean up files
        FinalizeFiles(rc, j)
        # Save time usage
        WriteUserTime(tic, rc, j)
        # Check for errors
        if not CheckSuccess(rc, j):
            # Failure from FUN3D numerics
            cc.mark_failure("nan_locations")
            # Stop running case
            cc.mark_stopped()
            # Return code
            return cc.IERR_NANS
        # Update start counter
        nstart += 1
        # Check for explicit exit
        if check_complete(rc):
            break
        # Submit new PBS/Slurm job if appropriate
        q = resubmit_case(rc, j)
        # If new job started, this one should stop
        if q:
            break
    # Remove the RUNNING file
    cc.mark_stopped()
    # Return code
    return cc.IERR_OK


# Run one phase appropriately
def run_phase(rc, i):
    r"""Run one phase using appropriate commands

    :Call:
        >>> run_phase(rc, i)
    :Inputs:
        *rc*: :class:`RunControlOpts`
            Options interface from ``case.json``
        *i*: :class:`int`
            Phase number
    :Versions:
        * 2016-04-13 ``@ddalle``: v1.0 (``RunPhase()``)
        * 2023-06-02 ``@ddalle``: v2.0
    """
    # Count number of times this phase has been run previously.
    nprev = len(glob.glob('run.%02i.*' % i))
    # Check for dual
    if rc.get_Dual():
        os.chdir('Flow')
    # Read namelist
    nml = GetNamelist(rc, i)
    # Get the project name
    fproj = GetProjectRootname(rc=rc, i=i, nml=nml)
    # Get the last iteration number
    n = GetCurrentIter()
    # Number of requested iters for the end of this phase
    nj = rc.get_PhaseIters(i)
    # Number of iterations to run this phase
    ni = rc.get_nIter(i)
    # Mesh generation and verification actions
    if i == 0 and n is None:
        # Run intersect and verify
        cc.CaseIntersect(rc, fproj, n)
        cc.CaseVerify(rc, fproj, n)
        # Create volume mesh if necessary
        cc.run_aflr3(rc, proj=fproj, fmt=nml.GetGridFormat(), n=n)
        # Check for mesh-only phase
        if nj is None or ni is None or ni <= 0 or nj < 0:
            # Name of next phase
            fproj_adapt = GetProjectRootname(rc, i=i+1, nml=nml)
            # AFLR3 output format
            fmt = nml.GetGridFormat()
            # Check for renamed file
            if fproj_adapt != fproj:
                # Copy mesh
                os.symlink(
                    '%s.%s' % (fproj, fmt),
                    '%s.%s' % (fproj_adapt, fmt))
            # Make sure *n* is not ``None``
            if n is None:
                n = 0
            # Exit appropriately
            if rc.get_Dual():
                os.chdir('..')
            # Create an output file to make phase number programs work
            open("run.%02i.%i" % (i, n), 'w').close()
            return
    # Prepare for restart if that's appropriate.
    SetRestartIter(rc)
    # Get *n* but ``0`` instead of ``None``
    if n is None:
        n0 = 0
    else:
        n0 = n
    # Check if the primal solution has already been run
    if nprev == 0 or n0 < nj:
        # Get the `nodet` or `nodet_mpi` command
        cmdi = cmd.nodet(rc, i=i)
        # Call the command.
        bin.callf(cmdi, f='fun3d.out')
        # Get new iteration number
        n1 = GetCurrentIter()
        # Check for lack of progress
        if n1 <= n0:
            raise SystemError("Running phase did not advance iteration count.")
    else:
        # No new iteratoins
        n1 = n
    # Go back up a folder if we're in the "Flow" folder
    if rc.get_Dual():
        os.chdir('..')
    # Check current iteration count.
    if (i >= rc.get_PhaseSequence(-1)) and (n0 >= rc.get_LastIter()):
        return
    # Check for adaptive solves
    if n1 < nj:
        return
    # Check for adjoint solver
    if rc.get_Dual() and rc.get_DualPhase(i):
        # Copy the correct namelist
        os.chdir('Flow')
        # Delete ``fun3d.nml`` if appropriate
        if os.path.isfile('fun3d.nml') or os.path.islink('fun3d.nml'):
            os.remove('fun3d.nml')
        # Copy the correct one into place
        os.symlink('fun3d.dual.%02i.nml' % i, 'fun3d.nml')
        # Enter the 'Adjoint/' folder
        os.chdir('..')
        os.chdir('Adjoint')
        # Create the command to calculate the adjoint
        cmdi = cmd.dual(rc, i=i, rad=False, adapt=False)
        # Run the adjoint analysis
        bin.callf(cmdi, f='dual.out')
        # Create the command to adapt
        cmdi = cmd.dual(rc, i=i, adapt=True)
        # Estimate error and adapt
        bin.callf(cmdi, f='dual.out')
        # Rename output file after completing that command
        os.rename('dual.out', 'dual.%02i.out' % i)
        # Return
        os.chdir('..')
    elif rc.get_Adaptive() and rc.get_AdaptPhase(i):
        # Check if this is a weird mixed case with Dual and Adaptive
        if rc.get_Dual():
            os.chdir('Flow')
        # Run the feature-based adaptive mesher
        cmdi = cmd.nodet(rc, adapt=True, i=i)
        # Make sure "restart_read" is set to .true.
        nml.SetRestart(True)
        nml.Write('fun3d.%02i.nml' % i)
        # Call the command.
        bin.callf(cmdi, f='adapt.out')
        # Rename output file after completing that command
        os.rename('adapt.out', 'adapt.%02i.out' % i)
        # Return home if appropriate
        if rc.get_Dual():
            os.chdir('..')


# Prepare the files of the case
def PrepareFiles(rc, i=None):
    r"""Prepare file names appropriate to run phase *i* of FUN3D

    :Call:
        >>> PrepareFiles(rc, i=None)
    :Inputs:
        *rc*: :class:`RunControlOpts`
            Options interface from ``case.json``
        *i*: :class:`int`
            Phase number
    :Versions:
        * 2016-04-14 ``@ddalle``: v1.0
    """
    # Get the phase number if necessary
    if i is None:
        # Get the phase number
        i = GetPhaseNumber(rc)
    # Check for dual phase
    if rc.get_Dual(): os.chdir('Flow')
    # Delete any input file (primary namelist)
    if os.path.isfile('fun3d.nml') or os.path.islink('fun3d.nml'):
        os.remove('fun3d.nml')
    # Create the correct namelist
    os.symlink('fun3d.%02i.nml' % i, 'fun3d.nml')
    # Delete any moving_body.input namelist link
    fmove = 'moving_body.input'
    if os.path.isfile(fmove) or os.path.islink(fmove):
        os.remove(fmove)
    # Target moving_body.[0-9][0-9].input file
    ftarg = 'moving_body.%02i.input' % i
    # Create the correct namelist
    if os.path.isfile(ftarg):
        os.symlink(ftarg, fmove)
    # Return to original folder
    if rc.get_Dual(): os.chdir('..')


# Function to call script or submit.
def StartCase():
    r"""Start a case by either submitting it or calling locally

    :Call:
        >>> case.StartCase()
    :Versions:
        * 2014-10-06 ``@ddalle``: v1.0
        * 2015-10-19 ``@ddalle``: Copied from :mod:`cape.pycart`
    """
    # Get the config.
    rc = read_case_json()
    # Determine the run index.
    i = GetPhaseNumber(rc)
    # Check qsub status.
    if rc.get_slurm(i):
        # Get the name of the PBS file
        fpbs = GetPBSScript(i)
        # Submit the Slurm case
        pbs = queue.psbatch(fpbs)
        return pbs
    elif rc.get_qsub(i):
        # Get the name of the PBS file.
        fpbs = GetPBSScript(i)
        # Submit the case.
        pbs = queue.pqsub(fpbs)
        return pbs
    else:
        # Simply run the case. Don't reset modules either.
        run_fun3d()


def check_complete(rc):
    r"""Check if case is complete as described

    :Call:
        >>> q = check_complete(rc)
    :Inputs:
        *rc*: :class:`RunControl`
            Options interface from ``case.json``
    :Outputs:
        *q*: ``True`` | ``False``
            Whether case has reached last phase w/ enough iters
    :Versions:
        * 2023-06-02 ``@ddalle``: v1.0
    """
    # Determine current phase
    j = GetPhaseNumber(rc)
    # Check if last phase
    if j < rc.get_PhaseSequence(-1):
        return False
    # Get restart iteration
    n = GetRestartIter()
    # Check iteration number
    if n is None:
        # No iterations complete
        return False
    elif n < rc.get_LastIter():
        # Not enough iterations complete
        return False
    else:
        # All criteria met
        return True


def resubmit_case(rc, j0):
    r"""Resubmit a case as a new job if appropriate

    :Call:
        >>> q = resubmit_case(rc, j0)
    :Inputs:
        *rc*: :class:`RunControl`
            Options interface from ``case.json``
        *j0*: :class:`int`
            Index of phase most recently run prior
            (may differ from :func:`get_phase` now)
    :Outputs:
        *q*: ``True`` | ``False``
            Whether or not a new job was submitted to queue
    :Versions:
        * 2022-01-20 ``@ddalle``: v1.0 (:mod:`cape.pykes.case`)
        * 2023-06-02 ``@ddalle``: v1.0
    """
    # Get *current* phase
    j1 = GetPhaseNumber(rc)
    # Get name of run script for next case
    fpbs = GetPBSScript(j1)
    # Call parent function
    return cc.resubmit_case(rc, fpbs, j0, j1)


# Check success
def CheckSuccess(rc=None, i=None):
    r"""Check for errors before continuing

    Currently the following checks are performed.

        * Check for NaN residual in the output file

    :Call:
        >>> CheckSuccess(rc=None, i=None)
    :Inputs:
        *rc*: :class:`RunControlOpts`
            Options interface from ``case.json``
        *i*: :class:`int`
            Phase number
    :Outputs:
        *q*: :class:`bool`
            Whether or not the case ran successfully
    :Versions:
        * 2016-04-18 ``@ddalle``: v1.0
        * 2023-06-02 ``@ddalle``: v1.1; return `bool` instead of raise
    """
    # Get phase number if necessary.
    if i is None:
        # Get locally.
        i = GetPhaseNumber(rc)
    # Get the last iteration number
    n = GetCurrentIter()
    # Don't use ``None`` for this
    if n is None:
        n = 0
    # Output file name
    fname = 'run.%02i.%i' % (i, n)
    # Check for the file
    if os.path.isfile(fname):
        # Get the last line from nodet output file
        line = bin.tail(fname)
        # Check if NaN is in there
        if 'NaN' in line:
            return False
    # Otherwise no errors detected
    return True


# Clean up immediately after running
def FinalizeFiles(rc, i=None):
    r"""Clean up files after running one cycle of phase *i*

    :Call:
        >>> FinalizeFiles(rc, i=None)
    :Inputs:
        *rc*: :class:`RunControlOpts`
            Options interface from ``case.json``
        *i*: :class:`int`
            Phase number
    :Versions:
        * 2016-04-14 ``@ddalle``: v1.0
    """
    # Get phase number if necessary.
    if i is None:
        # Get locally.
        i = GetPhaseNumber(rc)
    # Read namelist
    nml = GetNamelist(rc, i)
    # Get the project name
    fproj = GetProjectRootname(nml=nml)
    # Get the last iteration number
    n = GetCurrentIter()
    # Don't use ``None`` for this
    if n is None: n = 0
    # Check for dual folder setup
    if os.path.isdir('Flow'):
        # Enter the flow folder
        os.chdir('Flow')
        qdual = True
        # History gets moved to parent
        fhist = os.path.join('..', 'run.%02i.%i' % (i, n))
    else:
        # Single folder
        qdual = False
        # History remains in present folder
        fhist = 'run.%02i.%i' % (i, n)
    # Assuming that worked, move the temp output file.
    if os.path.isfile('fun3d.out'):
        # Move the file
        os.rename('fun3d.out', fhist)
    else:
        # Create an empty file
        os.system('touch %s' % fhist)
    # Rename the flow file, too.
    if rc.get_KeepRestarts(i):
        shutil.copy('%s.flow' % fproj, '%s.%i.flow' % (fproj, n))
    # Move back to parent folder if appropriate
    if qdual: os.chdir('..')


# Write start time
def WriteStartTime(tic, rc, i, fname="pyfun_start.dat"):
    r"""Write the start time in *tic*

    :Call:
        >>> WriteStartTime(tic, rc, i, fname="pyfun_start.dat")
    :Inputs:
        *tic*: :class:`datetime.datetime`
            Time to write into data file
        *rc*: :class:`RunControlOpts`
            Options interface
        *i*: :class:`int`
            Phase number
        *fname*: {``"pyfun_start.dat"``} | :class:`str`
            Name of file containing run start times
    :Versions:
        * 2016-08-31 ``@ddalle``: v1.0
    """
    # Call the function from :mod:`cape.case`
    cc.WriteStartTimeProg(tic, rc, i, fname, 'run_fun3d.py')


# Write time used
def WriteUserTime(tic, rc, i, fname="pyfun_time.dat"):
    r"""Write time usage since time *tic* to file

    :Call:
        >>> toc = WriteUserTime(tic, rc, i, fname="pyfun_time.dat")
    :Inputs:
        *tic*: :class:`datetime.datetime`
            Time from which timer will be measured
        *rc*: :class:`RunControlOpts`
            Options interface
        *i*: :class:`int`
            Phase number
        *fname*: :class:`str`
            Name of file containing CPU usage history
    :Outputs:
        *toc*: :class:`datetime.datetime`
            Time at which time delta was measured
    :Versions:
        * 2015-12-09 ``@ddalle``: v1.0
    """
    # Call the function from :mod:`cape.case`
    cc.WriteUserTimeProg(tic, rc, i, fname, 'run_fun3d.py')


# Function to determine which PBS script to call
def GetPBSScript(i=None):
    r"""Determine the file name of the PBS script to call

    This is a compatibility function for cases that do or do not have
    multiple PBS scripts in a single run directory

    :Call:
        >>> fpbs = case.GetPBSScript(i=None)
    :Inputs:
        *i*: :class:`int`
            Run index
    :Outputs:
        *fpbs*: :class:`str`
            Name of PBS script to call
    :Versions:
        * 2014-12-01 ``@ddalle``: v1.0
        * 2015-10-19 ``@ddalle``: FUN3D version
    """
    # Form the full file name, e.g. run_cart3d.00.pbs
    if i is not None:
        # Create the name.
        fpbs = 'run_fun3d.%02i.pbs' % i
        # Check for the file.
        if os.path.isfile(fpbs):
            # This is the preferred option if it exists.
            return fpbs
        else:
            # File not found; use basic file name
            return 'run_fun3d.pbs'
    else:
        # Do not search for numbered PBS script if *i* is None
        return 'run_fun3d.pbs'


# Function to chose the correct input to use from the sequence.
def GetPhaseNumber(rc):
    r"""Determine the phase number based on files in folder

    :Call:
        >>> i = case.GetPhaseNumber(rc)
    :Inputs:
        *rc*: :class:`RunControlOpts`
            Options interface for run control
    :Outputs:
        *i*: :class:`int`
            Most appropriate phase number for a restart
    :Versions:
        * 2014-10-02 ``@ddalle``: v1.0
        * 2015-10-19 ``@ddalle``: FUN3D version
    """
    # Get the run index.
    n = GetRestartIter()
    # Global options
    qdual = rc.get_Dual()
    qadpt = rc.get_Adaptive()
    # Loop through possible input numbers.
    for j in range(rc.get_nSeq()):
        # Get the actual run number
        i = rc.get_PhaseSequence(j)
        # Check for output files.
        if len(glob.glob('run.%02i.*' % i)) == 0:
            # This run has not been completed yet.
            return i
        # Check the iteration numbers
        if rc.get_PhaseIters(j) is None:
            # Don't check null phases
            pass
        elif n is None:
            # No iters yet
            return i
        elif n < rc.get_PhaseIters(j):
            # This case has been run, but hasn't reached the min iter cutoff
            return i
        # Check for dual
        if qdual and rc.get_DualPhase(i):
            # Check for the dual output file
            if not os.path.isfile(os.path.join(
                    'Adjoint', 'dual.%02i.out' % i)):
                return i
        # Check for dual
        if qadpt and rc.get_AdaptPhase(i):
            # Check for weird hybrid setting
            if qdual:
                # It's in the ``Flow/`` folder; other phases may be dual phases
                fadpt = os.path.join('Flow', 'dual.%02i.out' % i)
            else:
                # Purely adaptive; located in this folder
                fadpt = 'adapt.%02i.out' % i
            # Check for the dual output file
            qadpt = os.path.isfile(fadpt)
            # Check for subseqnent phase outputs
            qnext = len(glob.glob("run.%02i.*" % (i+1))) > 0
            if not (qadpt or qnext):
                return i
    # Case completed; just return the last value.
    return i


# Get the namelist
def GetNamelist(rc=None, i=None):
    r"""Read case namelist file

    :Call:
        >>> nml = case.GetNamelist(rc=None, i=None)
    :Inputs:
        *rc*: :class:`RunControlOpts`
            Run control options
        *i*: :class:`int`
            Phase number
    :Outputs:
        *nml*: :class:`cape.pyfun.namelist.Namelist`
            Namelist interface
    :Versions:
        * 2015-10-19 ``@ddalle``: v1.0
    """
    # Read ``case.json`` if necessary
    if rc is None:
        try:
            rc = read_case_json()
        except Exception:
            pass
    # Process phase number
    if i is None and rc is not None:
        # Default to most recent phase number
        i = GetPhaseNumber(rc)
    # Check for `Flow` folder
    if os.path.isdir('Flow'):
        # Enter the folder
        qdual = True
        os.chdir('Flow')
    else:
        # No `Flow/` folder
        qdual = False
    # Check for folder with no working ``case.json``
    if rc is None:
        # Check for simplest namelist file
        if os.path.isfile('fun3d.nml'):
            # Read the currently linked namelist.
            nml = Namelist('fun3d.nml')
        else:
            # Look for namelist files
            fglob = glob.glob('fun3d.??.nml')
            # Sort it
            fglob.sort()
            # Read one of them.
            nml = Namelist(fglob[-1])
        # Return home if appropriate
        if qdual: os.chdir('..')
        return nml
    # Get the specified namelist
    nml = Namelist('fun3d.%02i.nml' % i)
    # Exit `Flow/` folder if necessary
    if qdual: os.chdir('..')
    # Output
    return nml


# Get the project rootname
def GetProjectRootname(rc=None, i=None, nml=None):
    r"""Read namelist and return project namelist

    :Call:
        >>> rname = case.GetProjectRootname()
        >>> rname = case.GetProjectRootname(rc=None, i=None,
                        nml=None)
    :Inputs:
        *rc*: :class:`RunControlOpts`
            Run control options
        *i*: :class:`int`
            Phase number
        *nml*: :class:`cape.pyfun.namelist.Namelist`
            Namelist interface; overrides *rc* and *i* if used
    :Outputs:
        *rname*: :class:`str`
            Project rootname
    :Versions:
        * 2015-10-19 ``@ddalle``: v1.0
    """
    # Read a namelist.
    if nml is None: nml = GetNamelist(rc=rc, i=i)
    # Read the project root name
    return nml.GetRootname()


# Function to read the local settings file.
def read_case_json():
    r"""Read "RunControl" settings from ``case.json```

    :Call:
        >>> rc = case.read_case_json()
    :Outputs:
        *rc*: :class:`RunControlOpts`
            Options interface for run control settings
    :Versions:
        * 2014-10-02 ``@ddalle``: v1.0 (pycart)
        * 2015-10-19 ``@ddalle``: v1.0 (``ReadCaseJSON()``)
        * 2023-06-02 ``@ddalle``: v2.0 hooks to :mod:`cape.cfdx`
    """
    # Call generic version but w/ pyfun's RunControlOpts
    return cc.read_case_json(RunControlOpts)


# Get last line of 'history.dat'
def GetCurrentIter():
    r"""Get the most recent iteration number

    :Call:
        >>> n = case.GetHistoryIter()
    :Outputs:
        *n*: :class:`int` | ``None``
            Last iteration number
    :Versions:
        * 2015-10-19 ``@ddalle``: v1.0
        * 2016-04-28 ``@ddalle``: v1.1; ``Flow/`` folder
    """
    # Read the two sources
    nh, ns = GetHistoryIter()
    nr = GetRunningIter()
    # Process
    if nr in [0, None]:
        # No running iterations; check history
        return ns
    else:
        # Some iterations saved and some running
        return nh + nr


# Get the number of finished iterations
def GetHistoryIter():
    r"""Get the most recent iteration number for a history file

    :Call:
        >>> nh, n = case.GetHistoryIter()
    :Outputs:
        *nh*: :class:`int`
            Iterations from previous cases before Fun3D deleted history
        *n*: :class:`int` | ``None``
            Most recent iteration number
    :Versions:
        * 2015-10-20 ``@ddalle``: v1.0
        * 2016-04-28 ``@ddalle``: Accounting for ``Flow/`` folder
        * 2016-10-29 ``@ddalle``: Handling Fun3D's iteration reset
        * 2017-02-23 ``@ddalle``: Handling for adaptive
    """
    # Read JSON settings
    rc = read_case_json()
    # Get adaptive settings
    qdual = rc.get_Dual()
    qadpt = rc.get_Adaptive()
    # Check for flow folder
    if qdual: os.chdir("Flow")
    # Read the project rootname
    try:
        rname = GetProjectRootname(rc=rc)
    except Exception:
        # No iterations
        if qdual: os.chdir('..')
        return None, None
    # Assemble file name.
    fname = "%s_hist.dat" % rname
    # Check for "pyfun00", "pyfun01", etc.
    if qdual or qadpt:
        # Check for sequence of file names
        fnames = glob.glob(rname[:-2] + '??_hist.[0-9][0-9].dat')
        fnames.sort()
        # Single history file name(s)
        fhist = glob.glob("%s??_hist.dat" % rname[:-2])
        # Apppend the most recent one
        if len(fhist) > 0:
            # Get maximum file
            fnhist = max(fhist)
            # Check adaption numbers... don't use older adaption history
            if len(fnames) > 0:
                # Get adaption number on both files
                nr = len(rname) - 2
                na0 = int(fnames[-1][nr:nr+2])
                na1 = int(fnhist[nr:nr+2])
                # Don't use pyfun01_hist.dat to append pyfun02_hist.03.dat
                if na1 >= na0: fnames.append(fnhist)
            else:
                # No previous history; append
                fnames.append(fnhist)
    else:
        # Check for historical files
        fnames = glob.glob("%s_hist.[0-9][0-9].dat" % rname)
        fnames.sort()
        # Single history file name
        fnames.append("%s_hist.dat" % rname)
    # Loop through possible file(s)
    n = None
    nh = 0
    for fname in fnames:
        # Process the file
        ni = GetHistoryIterFile(fname)
        # Add to history
        if ni is not None:
            # Check if any iterations have been found
            if n is None:
                # First find
                n = ni
                # Check if this is a previous history
                if len(fname.split('.')) == 3:
                    # Also save as history
                    nh = ni
            elif len(fname.split('.')) == 3:
                # Add this history to previous history [restarted iter count]
                nh = n
                n += ni
            else:
                # New file for adaptive but not cumulative
                n = nh + ni
    # No history to read.
    if qdual: os.chdir('..')
    # Output
    return nh, n


# Get the number of iterations from a single iterative history file
def GetHistoryIterFile(fname):
    r"""Get the most recent iteration number from a history file

    :Call:
        >>> n = case.GetHistoryIterFile(fname)
    :Inputs:
        *fname*: {``"pyfun_hist.dat"``} | :class:`str`
            Name of file to read
    :Outputs:
        *n*: :class:`int` | ``None``
            Most recent iteration number
    :Versions:
        * 2016-05-04 ``@ddalle``: Extracted from :func:`GetHistoryIter`
    """
    # Check for the file.
    if not os.path.isfile(fname):
        return None
    # Check the file.
    try:
        # Tail the file
        txt = bin.tail(fname)
    except Exception:
        # Failure; return no-iteration result.
        return None
    # Get the iteration number.
    try:
        return int(txt.split()[0])
    except Exception:
        return None


# Get the last line (or two) from a running output file
def GetRunningIter():
    r"""Get the most recent iteration number for a running file

    :Call:
        >>> n = case.GetRunningIter()
    :Outputs:
        *n*: :class:`int` | ``None``
            Most recent iteration number
    :Versions:
        * 2015-10-19 ``@ddalle``: v1.0
        * 2016-04-28 ``@ddalle``: Now handles ``Flow/`` folder
    """
    # Check for the file.
    if os.path.isfile('fun3d.out'):
        # Use the current folder
        fflow = 'fun3d.out'
    elif os.path.isfile(os.path.join('Flow', 'fun3d.out')):
        # Use the ``Flow/`` folder
        fflow = os.path.join('Flow', 'fun3d.out')
    else:
        # No current file
        return None
    # Check for flag to ignore restart history
    lines = bin.grep('on_nohistorykept', fflow)
    # Check whether or not to add restart iterations
    if len(lines) < 2:
        # Get the restart iteration line
        try:
            # Search for particular text
            lines = bin.grep('the restart files contains', fflow)
            # Process iteration count from the RHS of the last such line
            nr = int(lines[0].split('=')[-1])
        except Exception:
            # No restart iterations
            nr = None
    else:
        # Do not use restart iterations
        nr = None
    # Length of chunk at end of line to check
    nchunk = 10
    # Maximum number of chunks to scan
    mchunk = 50
    # Loop until chunk found with iteration number
    for ichunk in range(mchunk):
        # Get (cumulative) size of chunk and previous chunk
        ia = ichunk * nchunk
        ib = ia + nchunk
        # Get the last few lines of :file:`fun3d.out`
        lines = bin.tail(fflow, ib).strip().split('\n')
        lines.reverse()
        # Initialize output
        n = None
        # Try each line
        for line in lines[ia:]:
            try:
                # Check for direct specification
                if 'current history iterations' in line:
                    # Direct specification
                    n = int(line.split()[-1])
                    nr = None
                    break
                # Use the iteration regular expression
                match = REGEX_F3DOUT.match(line)
                # Check for match
                if match:
                    # Get the iteration number from the line
                    n = int(match.group('iter'))
                    # Search completed
                    break
            except Exception:
                continue
        # Exit if valid line was found
        if n is not None:
            break
    # Output
    if n is None:
        return nr
    elif nr is None:
        return n
    else:
        return n + nr


# Function to get total iteration number
def GetRestartIter():
    r"""Get total iteration number of most recent flow file

    This function works by checking FUN3D output files for particular
    lines of text.  If the ``fun3d.out`` file exists, only that file is
    checked. Otherwise, all files matching ``run.[0-9]*.[0-9]*`` are
    checked.

    The lines in the FUN3D output file that report each new restart file
    have the following format.

    .. code-block:: none

        inserting previous and current history iterations 300 + 80 = 380

    :Call:
        >>> n = GetRestartIter()
    :Outputs:
        *n*: :class:`int`
            Index of most recent check file
    :Versions:
        * 2015-10-19 ``@ddalle``: v1.0
        * 2016-04-19 ``@ddalle``: Checks STDIO file for iteration number
        * 2020-01-15 ``@ddalle``: Proper glob sorting order
    """
    # List of saved run files
    frun_glob = glob.glob('run.[0-9]*.[0-9]*')
    # More exact pattern check
    frun_pattern = []
    # Loop through glob finds
    for fi in frun_glob:
        # Above doesn't guarantee exact pattern
        try:
            # Split into parts
            _, s_phase, s_iter = fi.split(".")
            # Compute phase and iteration
            int(s_phase)
            int(s_iter)
        except Exception:
            continue
        # Append to filterted list
        frun_pattern.append(fi)
    # Sort by iteration number
    frun = sorted(frun_pattern, key=lambda f: int(f.split(".")[2]))

    # List the output files
    if os.path.isfile('fun3d.out'):
        # Only use the current file
        fflow = frun + ['fun3d.out']
    elif os.path.isfile(os.path.join('Flow', 'fun3d.out')):
        # Use the current file from the ``Flow/`` folder
        fflow = frun + [os.path.join('Flow', 'fun3d.out')]
    else:
        # Use the run output files
        fflow = frun
    # Initialize iteration number until informed otherwise.
    n = 0
    # Cumulative restart iteration number
    n0 = 0
    # Loop through the matches.
    for fname in fflow:
        # Check for restart of iteration counter
        lines = bin.grep('on_nohistorykept', fname)
        if len(lines) > 1:
            # Reset iteration counter
            n0 = n
            n = 0
        # Get the output report lines
        lines = bin.grep('current history iterations', fname)
        # Be safe
        try:
            # Split up line
            V = lines[-2].split()
            # Attempt to get existing iterations
            try:
                # Format: "3000 + 2000 = 5000"
                i0 = int(V[-5])
            except Exception:
                # No restart... restart_read is 'off' or 'on_nohistorykept'
                i0 = 0
            # Get the last write iteration number
            i = int(V[-1])
            # Update iteration number
            if i0 < n:
                # Somewhere we missed an on_nohistorykept
                n0 = n
                n = i
            else:
                # Normal situation
                n = max(i, n)
        except Exception:
            pass
    # Output
    return n0 + n


# Function to set the most recent file as restart file.
def SetRestartIter(rc, n=None):
    r"""Set a given check file as the restart point

    :Call:
        >>> case.SetRestartIter(rc, n=None)
    :Inputs:
        *rc*: :class:`RunControlOpts`
            Run control options
        *n*: :class:`int`
            Restart iteration number, defaults to most recent available
    :Versions:
        * 2014-10-02 ``@ddalle``: v1.0
        * 2023-03-14 ``@ddalle``: v1.1; add WarmStart
    """
    # Check the input.
    if n is None:
        n = GetRestartIter()
    # Read the namelist.
    nml = GetNamelist(rc)
    # Set restart flag
    if n > 0:
        # Get the phase
        i = GetPhaseNumber(rc)
        # Check if this is a phase restart
        nohist = True
        if os.path.isfile('run.%02i.%i' % (i, n)):
            # Nominal restart
            nohist = False
        elif i == 0:
            # Not sure how we could still be in phase 0
            nohist = False
        else:
            # Check for preceding phases
            f1 = glob.glob('run.%02i.*' % (i-1))
            n1 = rc.get_PhaseIters(i-1)
            # Read the previous namelist
            if n is not None and n1 is not None and (n > n1):
                if (len(f1) > 0) and os.path.isfile("fun3d.out"):
                    # Current phase was already run, but run.{i}.{n}
                    # wasn't created
                    nml0 = GetNamelist(rc, i)
                else:
                    nml0 = GetNamelist(rc, i-1)
            else:
                # Read the previous phase
                nml0 = GetNamelist(rc, i-1)
            # Get 'time_accuracy' parameter
            ta0 = nml0.GetVar('nonlinear_solver_parameters', 'time_accuracy')
            ta1 = nml.GetVar('nonlinear_solver_parameters', 'time_accuracy')
            # Check for a match
            nohist = ta0 != ta1
            # If we are moving to a new mode, prevent Fun3D deleting history
            if nohist:
                CopyHist(nml0, i-1)
        # Set the restart flag on.
        nml.SetRestart(nohist=nohist)
    else:
        # Check for warm-start flag
        warmstart = PrepareWarmStart(rc, nml)
        # Set the restart flag on/off depending on warm-start config
        nml.SetRestart(warmstart)
    # Write the namelist.
    nml.Write()


# Check WarmStart settings
def PrepareWarmStart(rc, nml):
    r"""Process WarmStart settings and copy files if appropriate

    :Call:
        >>> warmstart = PrepareWarmStart(rc, nml)
    :Inputs:
        *rc*: :class:`RunControlOpts`
            RunControl options from ``case.json``
        *nml*: :class:`Fun3DNamelist`
            Namelist interface
    :Outputs:
        *warmstart*: ``True`` | ``False``
            Whether or not case is a valid warm-start
    :Versions:
        * 2023-03-14 ``@ddalle``: v1.0
    """
    # Check initial WarmStart setting
    if not rc.get_WarmStart(0):
        return False
    # Get folder
    fdir = rc.get_WarmStartFolder(0)
    # Check for an *fdir* input
    if fdir is not None:
        # Get conditions
        x = cc.ReadConditions()
        # Absolutize path to source folder
        srcdir = os.path.realpath(fdir % x)
        # Remember location
        workdir = os.getcwd()
        # Check if current folder
        return srcdir != workdir
    # Valid warm-start scenario
    return True


# Copy the histories
def CopyHist(nml, i):
    r"""Copy all force and moment histories along with residual history

    :Call:
        >>> CopyHist(nml, i)
    :Inputs:
        *nml*: :class:`cape.pyfun.namelist.Namelist`
            Fun3D namelist interface for phase *i*
        *i*: :class:`int`
            Phase number to use for storing histories
    :Versions:
        * 2016-10-28 ``@ddalle``: v1.0
    """
    # Project name
    proj = nml.GetRootname()
    # Get the list of FM files
    fmglob = glob.glob('%s_fm_*.dat' % proj)
    # Loop through FM files
    for f in fmglob:
        # Split words
        F = f.split('.')
        # Avoid re-copies
        if len(F) > 2: continue
        # Copy-to name
        fcopy = F[0] + ('.%02i.dat' % i)
        # Avoid overwrites
        if os.path.isfile(fcopy): continue
        # Copy the file
        os.rename(f, fcopy)
    # Copy the history file
    if os.path.isfile('%s_hist.dat' % proj):
        # Destination name
        fcopy = '%s_hist.%02i.dat' % (proj, i)
        # Avoid overwrites
        if not os.path.isfile(fcopy):
            # Copy the file
            os.rename('%s_hist.dat' % proj, fcopy)
    # Copy the history file
    if os.path.isfile('%s_subhist.dat' % proj):
        # Destination name
        fcopy = '%s_subhist.%02i.dat' % (proj, i)
        # Get time-accuracy option
        ta0 = nml.GetVar('nonlinear_solver_parameters', 'time_accuracy')
        # Avoid overwrites
        if not os.path.isfile(fcopy) and (ta0 != 'steady'):
            # Copy the file
            os.rename('%s_subhist.dat' % proj, fcopy)


# Function to determine newest triangulation file
def GetPltFile():
    r"""Get most recent boundary ``plt`` file and its associated
    iterations

    :Call:
        >>> fplt, n, i0, i1 = GetPltFile()
    :Outputs:
        *fplt*: :class:`str`
            Name of ``plt`` file
        *n*: :class:`int`
            Number of iterations included
        *i0*: :class:`int`
            First iteration in the averaging
        *i1*: :class:`int`
            Last iteration in the averaging
    :Versions:
        * 2016-12-20 ``@ddalle``: v1.0
    """
    # Read *rc* options to figure out iteration values
    rc = read_case_json()
    # Get current phase number
    j = GetPhaseNumber(rc)
    # Read the namelist to get prefix and iteration options
    nml = GetNamelist(rc, j)
    # =============
    # Best PLT File
    # =============
    # Prefix
    proj = GetProjectRootname(nml=nml)
    # Create glob to search for
    fglb = '%s_tec_boundary_timestep[1-9]*.plt' % proj
    # Check in working directory?
    if rc.get_Dual():
        # Look in the 'Flow/' folder
        fglb = os.path.join('Flow', fglb)
    # Get file
    fplt = GetFromGlob(fglb)
    # Check for nothing...
    if fplt is None:
        # Check if we can fall back to a previous project
        if glob.fnmatch.fnmatch(proj, '*[0-9][0-9]'):
            # Allow any project
            fglb = '%s[0-9][0-9]_tec_boundary_timestep[1-9]*.plt' % proj[:-2]
            # Try again
            fplt = GetFromGlob(fglb)
            # Check for second-try miss
            if fplt is None:
                return None, None, None, None
        else:
            # No file, global project name
            return None, None, None, None
    # Get the iteration number
    nplt = int(fplt.rstrip('.plt').split('timestep')[-1])
    # ============================
    # Actual Iterations after Runs
    # ============================
    # Glob of ``run.%02i.%i`` files
    fgrun = glob.glob('run.[0-9][0-9].[1-9]*')
    # Form dictionary of iterations
    nrun = []
    drun = {}
    # Loop through files
    for frun in fgrun:
        # Get iteration number
        ni = int(frun.split('.')[2])
        # Get phase number
        ji = int(frun.split('.')[1])
        # Save
        nrun.append(ni)
        drun[ni] = ji
    # Sort on iteration number
    nrun.sort()
    nrun = np.array(nrun)
    # Determine the last run that terminated before this PLT file was created
    krun = np.where(nplt > nrun)[0]
    # If no 'run.%02i.%i' before *nplt*, then use 0
    if len(krun) == 0:
        # Use current phase as reported
        nprev = 0
        nstrt = 1
        jstrt = j
    else:
        # Get the phase from the last run that finished before *nplt*
        kprev = krun[-1]
        nprev = nrun[kprev]
        jprev = drun[nprev]
        # Have we moved to the next phase?
        if nprev >= rc.get_PhaseIters(jprev):
            # We have *nplt* from the next phase
            mprev = rc.get_PhaseSequence().index(jprev)
            jstrt = rc.get_PhaseSequence(mprev+1)
        else:
            # Still running phase *jprev* to create *fplt*
            jstrt = jprev
        # First iteration included in PLT file
        nstrt = nprev + 1
    # Make sure we have the right namelist
    if j != jstrt:
        # Read the new namelist
        j = jstrt
        try:
            nml = GetNamelist(rc, j)
        except Exception:
            pass
    # ====================
    # Iteration Statistics
    # ====================
    # Check for averaging
    qavg = nml.GetVar('time_avg_params', 'itime_avg')
    # Number of iterations
    if qavg:
        # Time averaging included
        nStats = nplt - nprev
    else:
        # One iteration
        nStats = 1
        nstrt = nplt
    # ======
    # Output
    # ======
    return fplt, nStats, nstrt, nplt


# Get best file based on glob
def GetFromGlob(fglb, fname=None):
    r"""Find the most recently edited file matching a glob

    :Call:
        >>> fname = case.GetFromGlob(fglb, fname=None)
        >>> fname = case.GetFromGlob(fglbs, fname=None)
    :Inputs:
        *fglb*: :class:`str`
            Glob for targeted file names
        *fglbs*: :class:`list`\ [:class:`str`]
            Multiple glob file name patterns
        *fname*: {``None``} | :class:`str`
            Optional alternate file name to consider
    :Outputs:
        *fbest*: :class:`str`
            Name of file matching glob that was most recently modified
    :Versions:
        * 2016-12-19 ``@ddalle``: v1.0
        * 2023-02-03 ``@ddalle``: v1.1; add *fname* input
        * 2023-03-26 ``@ddalle``: v1.2; multiple *fglbs*
    """
    # Check for one or multiple globs
    if isinstance(fglb, (list, tuple)):
        # Combine list of globs
        fglob = []
        # Loop through multiples
        for fi in fglb:
            fglob.extend(glob.glob(fi))
    else:
        # List of files matching requested glob
        fglob = glob.glob(fglb)
    # Check for output file
    if fname is not None and os.path.isfile(fname):
        fglob.append(fname)
    # Check for empty glob
    if len(fglob) == 0:
        return
    # Get modification times
    t = [os.path.getmtime(f) for f in fglob]
    # Extract file with maximum index
    return fglob[t.index(max(t))]


# Link best file based on name and glob
def LinkFromGlob(fname, fglb):
    r"""Link the most recent file to a generic Tecplot file name

    :Call:
        >>> case.LinkFromGlob(fname, fglb)
        >>> case.LinkFromGlob(fname, fglbs)
    :Inputs:
        *fname*: :class:`str`
            Name of unmarked file, like ``Components.i.plt``
        *fglb*: :class:`str`
            Glob for marked file names
        *fglbs*: :class:`list`\ [:class:`str`]
            Multiple glob file name patterns
    :Versions:
        * 2016-10-24 ``@ddalle``: v1.0
        * 2023-03-26 ``@ddalle``: v1.1; multiple *fglbs*
    """
    # Check for already-existing regular file
    if os.path.isfile(fname) and not os.path.islink(fname):
        return
    # Extract file with maximum index
    fsrc = GetFromGlob(fglb, fname=fname)
    # Exit if no matches
    if fsrc is None:
        return
    # Remove the link if necessary
    if os.path.islink(fname):
        # Check if link matches
        if os.readlink(fname) == fsrc:
            # Nothing to do
            return
        else:
            # Remove existing link to different file
            os.remove(fname)
    # Create the link if possible
    if os.path.isfile(fsrc):
        os.symlink(fsrc, fname)


# Link best Tecplot files
def LinkPLT():
    r"""Link the most recent Tecplot files to fixed file names

    :Call:
        >>> case.LinkPLT()
    :Versions:
        * 2016-10-24 ``@ddalle``: v1.0
    """
    # Read the options
    rc = read_case_json()
    j = GetPhaseNumber(rc)
    # Need the namelist to figure out planes, etc.
    nml = GetNamelist(rc=rc, i=j)
    # Get the project root name
    proj = nml.GetVar('project', 'project_rootname')
    # Strip suffix
    if rc.get_Dual() or rc.get_Adaptive():
        # Strip adaptive section
        proj0 = proj[:-2]
        # Search for 'pyfun00', 'pyfun01', ...
        proj = proj0 + "??"
    else:
        # Use the full project name if no adaptations
        proj0 = proj
    # Get the list of output surfaces
    fsrf = []
    i = 1
    flbl = nml.GetVar('sampling_parameters', 'label', i)
    # Loop until there's no output surface name
    while flbl is not None:
        # Append
        fsrf.append(flbl)
        # Move to sampling output *i*
        i += 1
        # Get the name
        flbl = nml.GetVar('sampling_parameters', 'label', i)
    # Initialize file names
    fname = [
        '%s_tec_boundary' % proj0,
        '%s_volume' % proj0,
        '%s_volume' % proj0
    ]
    # Initialize globs
    fglob = [
        ['%s_tec_boundary_timestep*' % proj],
        ['%s_volume_timestep*' % proj],
        ['%s_volume' % proj]
    ]
    # Add special ones
    for fi in fsrf:
        fname.append('%s_%s' % (proj0, fi))
        fglob.append(
            ['%s_%s' % (proj, fi), '%s_%s_timestep*' % (proj, fi)])
    # Link the globs
    for i in range(len(fname)):
        # Loop through viz extensions
        for ext in (".tec", ".dat", ".plt", ".szplt"):
            # Append extensions to output and patterns
            fnamei = fname[i] + ext
            fglobi = [fj + ext for fj in fglob[i]]
            # Process the glob as well as possible
            LinkFromGlob(fnamei, fglobi)


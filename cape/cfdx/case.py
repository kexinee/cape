r"""
:mod:`cape.cfdx.case`: Case Control Module
==========================================
This module contains templates for interacting with and executing
individual cases. Since this is one of the most highly customized
modules of the CAPE system, there are few functions here, and the
functions that are present are mostly templates.

In general, the :mod:`case` module is used for actually running the CFD
solver (and any additional binaries that may be required as part of the
run process), and it contains other capabilities for renaming files and
determining the settings for a particular case. CAPE saves many settings
for the CFD solver and archiving in a file called ``case.json` within
each case folder, which allows for the settings of one case to diverge
from the other cases in the same run matrix.

Actual functionality is left to individual modules listed below.

    * :mod:`cape.pycart.case`
    * :mod:`cape.pyfun.case`
    * :mod:`cape.pyover.case`
"""

# Standard library modules
import os
import glob
import json
from datetime import datetime

# System-dependent standard library
if os.name == "nt":
    resource = None
else:
    import resource

# Local imports
from . import queue
from . import bin
from .options import RunControlOpts
from ..tri import Tri


# Constants:
# Name of file that marks a case as currently running
RUNNING_FILE = "RUNNING"
# Name of file marking a case as in a failure status
FAIL_FILE = "FAIL"
# Return codes
IERR_OK = 0
IERR_NANS = 32
IERR_RUN_PHASE = 128


# Function to intersect geometry if appropriate
def CaseIntersect(rc, proj='Components', n=0, fpre='run'):
    r"""Run ``intersect`` to combine geometries if appropriate

    This is a multistep process in order to preserve all the component
    IDs of the input triangulations. Normally ``intersect`` requires
    each intersecting component to have a single component ID, and each
    component must be a water-tight surface.

    Cape utilizes two input files, ``Components.c.tri``, which is the
    original triangulation file with intersections and the original
    component IDs, and ``Components.tri``, which maps each individual
    original ``tri`` file to a single component. The files involved are
    tabulated below.

    * ``Components.tri``: Intersecting components, each with own compID
    * ``Components.c.tri``: Intersecting triangulation, original compIDs
    * ``Components.o.tri``: Output of ``intersect``, only a few compIDs
    * ``Components.i.tri``: Original compIDs mapped to intersected tris

    More specifically, these files are ``"%s.i.tri" % proj``, etc.; the
    default project name is ``"Components"``.  This function also calls
    the Chimera Grid Tools program ``triged`` to remove unused nodes from
    the intersected triangulation and optionally remove small triangles.

    :Call:
        >>> CaseIntersect(rc, proj='Components', n=0, fpre='run')
    :Inputs:
        *rc*: :class:`RunControlOpts`
            Case options interface from ``case.json``
        *proj*: {``'Components'``} | :class:`str`
            Project root name
        *n*: :class:`int`
            Iteration number
        *fpre*: {``'run'``} | :class:`str`
            Standard output file name prefix
    :See also:
        * :class:`cape.tri.Tri`
        * :func:`cape.bin.intersect`
    :Versions:
        * 2015-09-07 ``@ddalle``: Split from :func:`run_flowCart`
        * 2016-04-05 ``@ddalle``: Generalized to :mod:`cape`
    """
    # Check for phase number
    j = GetPhaseNumber(rc, n, fpre=fpre)
    # Exit if not phase zero
    if j > 0:
        return
    # Check for intersect status.
    if not rc.get_intersect():
        return
    # Check for initial run
    if n:
        return
    # Triangulation file names
    ftri  = "%s.tri" % proj
    fftri = "%s.f.tri" % proj
    fotri = "%s.o.tri" % proj
    fctri = "%s.c.tri" % proj
    fatri = "%s.a.tri" % proj
    futri = "%s.u.tri" % proj
    fitri = "%s.i.tri" % proj
    # Check for triangulation file.
    if os.path.isfile(fitri):
        # Note this.
        print("File '%s' already exists; aborting intersect." % fitri)
        return
    # Set file names
    rc.set_intersect_i(ftri)
    rc.set_intersect_o(fotri)
    # Run intersect
    if not os.path.isfile(fotri):
        bin.intersect(opts=rc)
    # Read the original triangulation.
    tric = Tri(fctri)
    # Read the intersected triangulation.
    trii = Tri(fotri)
    # Read the pre-intersection triangulation.
    tri0 = Tri(ftri)
    # Map the Component IDs
    if os.path.isfile(fatri):
        # Just read the mapped file
        trii = Tri(fatri)
    elif os.path.isfile(futri):
        # Just read the mapped file w/o unused nodes
        trii = Tri(futri)
    else:
        # Perform the mapping
        trii.MapCompID(tric, tri0)
        # Add in far-field, sources, non-intersect comps
        if os.path.isfile(fftri):
            # Read the tri file
            trif = Tri(fftri)
            # Add it to the mapped triangulation
            trii.AddRawCompID(trif)
    # Intersect post-process options
    o_rm = rc.get_intersect_rm()
    o_triged = rc.get_intersect_triged()
    o_smalltri = rc.get_intersect_smalltri()
    # Check if we can use ``triged`` to remove unused triangles
    if o_triged:
        # Write the triangulation.
        trii.Write(fatri)
        # Remove unused nodes
        infix = "RemoveUnusedNodes"
        fi = open('triged.%s.i' % infix, 'w')
        # Write inputs to the file
        fi.write('%s\n' % fatri)
        fi.write('10\n')
        fi.write('%s\n' % futri)
        fi.write('1\n')
        fi.close()
        # Run triged to remove unused nodes
        print(" > triged < triged.%s.i > triged.%s.o" % (infix, infix))
        os.system("triged < triged.%s.i > triged.%s.o" % (infix, infix))
    else:
        # Trim unused trianlges (internal)
        trii.RemoveUnusedNodes(v=True)
        # Write trimmed triangulation
        trii.Write(futri)
    # Check if we should remove small triangles
    if o_rm and o_triged:
        # Input file to remove small tris
        infix = "RemoveSmallTris"
        fi = open('triged.%s.i' % infix, 'w')
        # Write inputs to file
        fi.write('%s\n' % futri)
        fi.write('19\n')
        fi.write('%f\n' % rc.get("SmallArea", o_smalltri))
        fi.write('%s\n' % fitri)
        fi.write('1\n')
        fi.close()
        # Run triged to remove small tris
        print(" > triged < triged.%s.i > triged.%s.o" % (infix, infix))
        os.system("triged < triged.%s.i > triged.%s.o" % (infix, infix))
    elif o_rm:
        # Remove small triangles (internally)
        trii.RemoveSmallTris(o_smalltri, v=True)
        # Write final triangulation file
        trii.Write(fitri)
    else:
        # Rename file
        os.rename(futri, fitri)


# Function to verify if requested
def CaseVerify(rc, proj='Components', n=0, fpre='run'):
    r"""Run ``verify`` to check triangulation if appropriate

    This function checks the validity of triangulation in file
    ``"%s.i.tri" % proj``.  It calls :func:`cape.bin.verify`.

    :Call:
        >>> CaseVerify(rc, proj='Components', n=0, fpre='run')
    :Inputs:
        *rc*: :class:`RunControlOpts`
            Case options interface from ``case.json``
        *proj*: {``'Components'``} | :class:`str`
            Project root name
        *n*: :class:`int`
            Iteration number
        *fpre*: {``'run'``} | :class:`str`
            Standard output file name prefix
    :Versions:
        * 2015-09-07 ``@ddalle``: v1.0; from :func:`run_flowCart`
        * 2016-04-05 ``@ddalle``: v1.1; generalize to :mod:`cape`
    """
    # Check for phase number
    j = GetPhaseNumber(rc, n, fpre=fpre)
    # Exit if not phase zero
    if j > 0:
        return
    # Check for verify
    if not rc.get_verify():
        return
    # Check for initial run
    if n:
        return
    # Set file name
    rc.set_verify_i('%s.i.tri' % proj)
    # Run it.
    bin.verify(opts=rc)


# Mesh generation
def run_aflr3(opts, proj='Components', fmt='lb8.ugrid', n=0):
    r"""Create volume mesh using ``aflr3``

    This function looks for several files to determine the most
    appropriate actions to take, replacing ``Components`` with the value
    from *proj* for each file name and ``lb8.ugrid`` with the value from
    *fmt*:

        * ``Components.i.tri``: Triangulation file
        * ``Components.surf``: AFLR3 surface file
        * ``Components.aflr3bc``: AFLR3 boundary conditions
        * ``Components.xml``: Surface component ID mapping file
        * ``Components.lb8.ugrid``: Output volume mesh
        * ``Components.FAIL.surf``: AFLR3 surface indicating failure

    If the volume grid file already exists, this function takes no
    action. If the ``surf`` file does not exist, the function attempts
    to create it by reading the ``tri``, ``xml``, and ``aflr3bc`` files
    using :class:`cape.tri.Tri`.  The function then calls
    :func:`cape.bin.aflr3` and finally checks for the ``FAIL`` file.

    :Call:
        >>> run_aflr3(opts, proj="Components", fmt='lb8.ugrid', n=0)
    :Inputs:
        *opts*: :class:`RunControlOpts`
            Options instance from ``case.json``
        *proj*: {``"Components"``} | :class:`str`
            Project root name
        *fmt*: {``"b8.ugrid"``} | :class:`str`
            AFLR3 volume mesh format
        *n*: :class:`int`
            Iteration number
    :Versions:
        * 2016-04-05 ``@ddalle``: v1.0 (``CaseAFLR3()``)
        * 2023-06-02 ``@ddalle``: v1.1; Clean and use ``run_aflr3_run)``
    """
    # Check for initial run
    if n:
        # Don't run AFLR3 if >0 iterations already complete
        return
    # Check for option to run AFLR3
    if not opts.get_aflr3_run(j=0):
        # AFLR3 not requested for this run
        return
    # File names
    ftri = '%s.i.tri' % proj
    fsurf = '%s.surf' % proj
    fbc = '%s.aflr3bc' % proj
    fxml = '%s.xml' % proj
    fvol = '%s.%s' % (proj, fmt)
    ffail = "%s.FAIL.surf" % proj
    # Exit if volume exists
    if os.path.isfile(fvol):
        return
    # Check for file availability
    if not os.path.isfile(fsurf):
        # Check for the triangulation to provide a nice error message if app.
        if not os.path.isfile(ftri):
            raise ValueError(
                "User has requested AFLR3 volume mesh.\n" +
                ("But found neither Cart3D tri file '%s' " % ftri) +
                ("nor AFLR3 surf file '%s'" % fsurf))
        # Read the triangulation
        if os.path.isfile(fxml):
            # Read with configuration
            tri = Tri(ftri, c=fxml)
        else:
            # Read without config
            tri = Tri(ftri)
        # Check for boundary condition flags
        if os.path.isfile(fbc):
            tri.ReadBCs_AFLR3(fbc)
        # Write the surface file
        tri.WriteSurf(fsurf)
    # Set file names
    opts.set_aflr3_i(fsurf)
    opts.set_aflr3_o(fvol)
    # Run AFLR3
    bin.aflr3(opts=opts)
    # Check for failure; aflr3 returns 0 status even on failure
    if os.path.isfile(ffail):
        # Remove RUNNING file
        mark_stopped()
        # Create failure file
        mark_failure("aflr3")
        # Error message
        raise RuntimeError(
            "Failure during AFLR3 run:\n" +
            ("File '%s' exists." % ffail))


# Function for the most recent available restart iteration
def GetRestartIter():
    r"""Get the restart iteration

    This is a placeholder function and is only called in error.

    :Call:
        >>> cape.case.GetRestartIter()
    :Raises:
        *RuntimeError*: :class:`Exception`
            Error regarding where this was called
    :Versions:
        * 2016-04-14 ``@ddalle``: v1.0
    """
    raise IOError("Called cape.case.GetRestartIter()")


# Function to call script or submit.
def StartCase():
    r"""Empty template for starting a case

    The function is empty but does not raise an error

    :Call:
        >>> cape.case.StartCase()
    :See also:
        * :func:`cape.pycart.case.StartCase`
        * :func:`cape.pyfun.case.StartCase`
        * :func:`cape.pyover.case.StartCase`
    :Versions:
        * 2015-09-27 ``@ddalle``: v1.0
        * 2023-06-02 ``@ddalle``: v2.0; empty
    """
    pass


# Function to delete job and remove running file.
def StopCase():
    r"""Stop a case by deleting PBS job and removing ``RUNNING`` file

    :Call:
        >>> case.StopCase()
    :Versions:
        * 2014-12-27 ``@ddalle``: v1.0
    """
    # Get the config.
    fc = ReadCaseJSON()
    # Get the job number.
    jobID = queue.pqjob()
    # Try to delete it.
    if fc.get_slurm(0):
        # Delete Slurm job
        queue.scancel(jobID)
    else:
        # Delete PBS job
        queue.qdel(jobID)
    # Delete RUNNING file if appropriate
    mark_stopped()


# Celete running file if approrpate
def mark_stopped():
    r"""Delete the ``RUNNING`` file if it exists

    :Call:
        >>> mark_stopped()
    :Versions:
        * 2023-06-02 ``@ddalle``: v1.0
    """
    # Check if file exists
    if os.path.isfile(RUNNING_FILE):
        # Delete it
        os.remove(RUNNING_FILE)


# Check if case is already running
def check_running():
    r"""Check if a case is already running, raise exception if so

    :Call:
        >>> check_running()
    :Versions:
        * 2023-06-02 ``@ddalle``: v1.0
    """
    # Check for RUNNING file
    if os.path.isfile(RUNNING_FILE):
        # Case already running
        raise IOError('Case already running!')


# Mark a cases as running
def mark_running():
    r"""Check if cases already running and create ``RUNNING`` otherwise

    :Call:
        >>> mark_running()
    :Versions:
        * 2023-06-02 ``@ddalle``: v1.0
    """
    # Check for RUNNING file
    check_running()
    # Create RUNNING file
    open(RUNNING_FILE, "w").close()


# General function to mark failures
def mark_failure(msg="no details"):
    r"""Mark the current folder in failure status using ``FAIL`` file

    :Call:
        >>> mark_failure(msg="no details")
    :Inputs:
        *msg*: ``{"no details"}`` | :class:`str`
            Error message for output file
    :Versions:
        * 2023-06-02 ``@ddalle``: v1.0
    """
    # Ensure new line
    txt = msg.rstrip("\n") + "\n"
    # Append message to failure file
    open(FAIL_FILE, "a+").write(txt)


# Function to read the local settings file.
def ReadCaseJSON(fjson='case.json'):
    r"""Read Cape settings for local case

    :Call:
        >>> rc = cape.case.ReadCaseJSON()
    :Inputs:
        *fjson*: {``"case.json"``} | :class:`str`
            Name of JSON settings file
    :Outputs:
        *rc*: :class:`RunControlOpts`
            Options interface for run control and command-line inputs
    :Versions:
        * 2014-10-02 ``@ddalle``: v1.0
        * 2023-06-02 ``@ddalle``: v2.0; one-line version
    """
    return RunControlOpts(fjson)


# Read variable from conditions file
def ReadConditions(k=None):
    r"""Read run matrix variable value in the current folder

    :Call:
        >>> conds = cape.case.ReadConditions()
        >>> v = cape.case.ReadConditions(k)
    :Inputs:
        *k*: {``None``} | :class:`str`
            Name of run matrix key
    :Outputs:
        *conds*: :class:`dict` [:class:`object`]
            Dictionary of run matrix conditions
        *v*: :class:`any`
            Run matrix conditions of key *k*
    :Versions:
        * 2017-03-28 ``@ddalle``: v1.0
        * 2023-06-02 ``@ddalle``: v2.0; different checks
    """
    # Check for file
    if not os.path.isfile("conditions.json"):
        return
    # Read the file
    with open('conditions.json', 'r') as fp:
        # Read the settings
        conds = json.load(fp)
    # Check for trajectory key
    if k is None:
        # Return full set
        return conds
    else:
        # Return the trajectory value
        return conds.get(k)


# Function to set the environment
def prepare_env(rc, i=0):
    r"""Set environment variables, alter resource limits (``ulimit``)

    This function relies on the system module :mod:`resource`.

    :Call:
        >>> case.prepare_env(rc, i=0)
    :Inputs:
        *rc*: :class:`RunControlOpts`
            Options interface for run control and command-line inputs
        *i*: :class:`int`
            Phase number
    :See also:
        * :func:`SetResourceLimit`
    :Versions:
        * 2015-11-10 ``@ddalle``: v1.0 (``PrepareEnvironment()``)
        * 2023-06-02 ``@ddalle``: v1.1; fix logic for appending
            - E.g. ``"PATH": "+$HOME/bin"``
            - This is designed to append to path
    """
    # Loop through environment variables
    for key in rc.get('Environ', {}):
        # Get the environment variable
        val = rc.get_Environ(key, i)
        # Check if it stars with "+"
        if val.startswith("+"):
            # Remove preceding '+' signes
            val = val.lstrip('+')
            # Check if it's present
            if key in os.environ:
                # Append to path
                os.environ[key] += (os.path.pathsep + val.lstrip('+'))
                continue
        # Set the environment variable from scratch
        os.environ[key] = val
    # Get ulimit parameters
    ulim = rc['ulimit']
    # Block size
    block = resource.getpagesize()
    # Set the stack size
    SetResourceLimit(resource.RLIMIT_STACK,   ulim, 's', i, 1024)
    SetResourceLimit(resource.RLIMIT_CORE,    ulim, 'c', i, block)
    SetResourceLimit(resource.RLIMIT_DATA,    ulim, 'd', i, 1024)
    SetResourceLimit(resource.RLIMIT_FSIZE,   ulim, 'f', i, block)
    SetResourceLimit(resource.RLIMIT_MEMLOCK, ulim, 'l', i, 1024)
    SetResourceLimit(resource.RLIMIT_NOFILE,  ulim, 'n', i, 1)
    SetResourceLimit(resource.RLIMIT_CPU,     ulim, 't', i, 1)
    SetResourceLimit(resource.RLIMIT_NPROC,   ulim, 'u', i, 1)


# Set resource limit
def SetResourceLimit(r, ulim, u, i=0, unit=1024):
    r"""Set resource limit for one variable

    :Call:
        >>> SetResourceLimit(r, ulim, u, i=0, unit=1024)
    :Inputs:
        *r*: :class:`int`
            Integer code of particular limit, from :mod:`resource`
        *ulim*: :class:`cape.options.ulimit.ulimit`
            System resource options interface
        *u*: :class:`str`
            Name of limit to set
        *i*: :class:`int`
            Phase number
        *unit*: :class:`int`
            Multiplier, usually for a kbyte
    :See also:
        * :mod:`cape.options.ulimit`
    :Versions:
        * 2016-03-13 ``@ddalle``: v1.0
        * 2021-10-21 ``@ddalle``: v1.1; check if Windows
    """
    # Check if the limit has been set
    if u not in ulim:
        return
    elif resource is None:
        # Running on Windows
        return
    # Get the value of the limit
    l = ulim.get_ulimit(u, i)
    # Check the type
    if isinstance(l, (int, float)) and (l > 0):
        # Set the value numerically
        try:
            resource.setrlimit(r, (unit*l, unit*l))
        except ValueError:
            pass
    else:
        # Set unlimited
        resource.setrlimit(r, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))


# Function to chose the correct input to use from the sequence.
def GetPhaseNumber(rc, n=None, fpre='run'):
    r"""Determine the phase number based on results available

    :Call:
        >>> j = GetPhaseNumber(rc, n=None, fpre='run')
    :Inputs:
        *rc*: :class:`RunControlOpts`
            Options interface for run control
        *n*: :class:`int`
            Iteration number
        *fpre*: {``"run"``} | :class:`str`
            Prefix for output files
    :Outputs:
        *j*: :class:`int`
            Most appropriate phase number for a restart
    :Versions:
        * 2014-10-02 ``@ddalle``: v1.0
        * 2015-10-19 ``@ddalle``: v1.1; FUN3D version
        * 2016-04-14 ``@ddalle``: v1.2; CAPE version
    """
    # Loop through possible input numbers.
    for i in range(rc.get_nSeq()):
        # Get the actual run number
        j = rc.get_PhaseSequence(i)
        # Check for output files
        if len(glob.glob('%s.%02i.*' % (fpre, j))) == 0:
            # This run has not been completed yet
            return j
        # Check the iteration number
        if n < rc.get_PhaseIters(i):
            # This case has been run, but hasn't reached the min iter cutoff
            return j
    # Case completed; just return the last value.
    return j


# Function to get most recent L1 residual
def GetCurrentIter():
    r"""Template function to report the most recent iteration

    :Call:
        >>> n = cape.case.GetCurrentIter()
    :Outputs:
        *n*: ``0``
            Most recent index, customized for each solver
    :Versions:
        * 2015-09-27 ``@ddalle``: v1.0
    """
    return 0


# Write time used
def WriteUserTimeProg(tic, rc, i, fname, prog):
    r"""Write time usage since time *tic* to file

    :Call:
        >>> toc = WriteUserTime(tic, rc, i, fname, prog)
    :Inputs:
        *tic*: :class:`datetime.datetime`
            Time from which timer will be measured
        *rc*: :class:`RunControlOpts`
            Options interface
        *i*: :class:`int`
            Phase number
        *fname*: :class:`str`
            Name of file containing CPU usage history
        *prog*: :class:`str`
            Name of program to write in history
    :Outputs:
        *toc*: :class:`datetime.datetime`
            Time at which time delta was measured
    :Versions:
        * 2015-12-09 ``@ddalle``: v1.0 (pycart)
        * 2015-12-22 ``@ddalle``: v1.0
    """
    # Check if the file exists
    if not os.path.isfile(fname):
        # Create it
        f = open(fname, 'w')
        # Write header line
        f.write("# TotalCPUHours, nProc, program, date, PBS job ID\n")
    else:
        # Append to the file
        f = open(fname, 'a')
    # Check for job ID
    if rc.get_qsub(i) or rc.get_slurm(i):
        try:
            # Try to read it and convert to integer
            jobID = open('jobID.dat').readline().split()[0]
        except Exception:
            jobID = ''
    else:
        # No job ID
        jobID = ''
    # Get the time.
    toc = datetime.now()
    # Time difference
    t = toc - tic
    # Number of processors
    nProc = rc.get_nProc(i)
    # Calculate CPU hours
    CPU = nProc * (t.days*24 + t.seconds/3600.0)
    # Format time
    t_text = toc.strftime('%Y-%m-%d %H:%M:%S %Z')
    # Write the data
    f.write('%8.2f, %4i, %-20s, %s, %s\n' % (CPU, nProc, prog, t_text, jobID))
    # Cleanup
    f.close()


# Write current time use
def WriteStartTimeProg(tic, rc, i, fname, prog):
    """Write the time to file at which a program or job started

    :Call:
        >>> WriteStartTimeProg(tic, rc, i, fname, prog)
    :Inputs:
        *tic*: :class:`datetime.datetime`
            Time from which timer will be measured
        *rc*: :class:`RunControlOpts`
            Options interface
        *i*: :class:`int`
            Phase number
        *fname*: :class:`str`
            Name of file containing CPU usage history
        *prog*: :class:`str`
            Name of program to write in history
    :Versions:
        * 2016-08-30 ``@ddalle``: v1.0
    """
    # Check if the file exists
    if not os.path.isfile(fname):
        # Create it.
        f = open(fname, 'w')
        # Write header line
        f.write("# nProc, program, date, PBS job ID\n")
    else:
        # Append to file
        f = open(fname, 'a')
    # Check for job ID
    if rc.get_qsub(i) or rc.get_slurm(i):
        try:
            # Try to read it and convert to integer
            jobID = open('jobID.dat').readline().split()[0]
        except Exception:
            jobID = ''
    else:
        # No job ID
        jobID = ''
    # Number of processors
    nProc = rc.get_nProc(i)
    # Write the data.
    f.write(
        '%4i, %-20s, %s, %s\n' % (
            nProc, prog, tic.strftime('%Y-%m-%d %H:%M:%S %Z'), jobID))
    # Cleanup
    f.close()


# Read most recent start time from file
def ReadStartTimeProg(fname):
    """Read the most recent start time to file

    :Call:
        >>> nProc, tic = ReadStartTimeProg(fname)
    :Inputs:
        *fname*: :class:`str`
            Name of file containing CPU usage history
    :Outputs:
        *nProc*: :class:`int`
            Number of cores
        *tic*: :class:`datetime.datetime`
            Time at which most recent run was started
    :Versions:
        * 2016-08-30 ``@ddalle``: v1.0
    """
    # Check for the file
    if not os.path.isfile(fname):
        # No time of start
        return None, None
    # Avoid failures
    try:
        # Read the last line and split on commas
        V = bin.tail(fname).split(',')
        # Get the number of processors
        nProc = int(V[0])
        # Split date and time
        dtxt, ttxt = V[2].strip().split()
        # Get year, month, day
        year, month, day = [int(v) for v in dtxt.split('-')]
        # Get hour, minute, second
        hour, minute, sec = [int(v) for v in ttxt.split(':')]
        # Construct date
        tic = datetime(year, month, day, hour, minute, sec)
        # Output
        return nProc, tic
    except Exception:
        # Fail softly
        return None, None


# Function to determine newest triangulation file
def GetTriqFile(proj='Components'):
    r"""Get most recent ``triq`` file and its associated iterations

    This is a template version with specific implementations for each
    solver. The :mod:`cape.cfdx` version simply returns the most recent
    ``triq`` file in the  folder with no iteration information.

    :Call:
        >>> ftriq, n, i0, i1 = GetTriqFile(proj='Components')
    :Inputs:
        *proj*: {``"Components"``} | :class:`str`
            File root name
    :Outputs:
        *ftriq*: :class:`str`
            Name of most recently modified ``triq`` file
        *n*: {``None``}
            Number of iterations included
        *i0*: {``None``}
            First iteration in the averaging
        *i1*: {``None``}
            Last iteration in the averaging
    :Versions:
        * 2016-12-19 ``@ddalle``: v1.0
    """
    # Get the glob of numbered files.
    fglob = glob.glob('*.triq')
    # Check it.
    if len(fglob) > 0:
        # Get modification times
        t = [os.path.getmtime(f) for f in fglob]
        # Extract file with maximum index
        ftriq = fglob[t.index(max(t))]
        # Output
        return ftriq, None, None, None
    else:
        # No TRIQ files
        return None, None, None, None


# Initialize running case
def init_timer():
    r"""Mark a case as ``RUNNING`` and initialize a timer

    :Call:
        >>> tic = init_timer()
    :Outputs:
        *tic*: :class:`datetime.datetime`
            Time at which case was started
    :Versions:
        * 2021-10-21 ``@ddalle``: v1.0; from :func:`run_fun3d`
    """
    # Touch (create) the running file, exception if already exists
    mark_running()
    # Start timer
    tic = datetime.now()
    # Output
    return tic


# Function to read the local settings file
def read_case_json(cls=RunControlOpts):
    r"""Read *RunControl* settings from ``case.json``

    :Call:
        >>> rc = read_case_json()
        >>> rc = read_case_json(cls)
    :Inputs:
        *cls*: {:mod:`RunControlOpts`} | :class:`type`
            Class to use for output file
    :Outputs:
        *rc*: *cls*
            Case run control settings
    :Versions:
        * 2021-10-21 ``@ddalle``: v1.0
    """
    # Check for file
    if not os.path.isfile("case.json"):
        # Use defaults
        return cls()
    # Read the file, fail if not present
    with open("case.json") as fp:
        # Read the settings.
        opts = json.load(fp)
    # Convert to a flowCart object.
    rc = cls(**opts)
    # Output
    return rc


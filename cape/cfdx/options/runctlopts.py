r"""
:mod:`cape.cfdx.options.rctlopts`: Primary case control options
==================================================================

This module provides a class :class:`RunControlOpts` that defines a CAPE
job's basic phasing and submittal settings. For example, it contains
settings for whether a case is submitted as a PBS job, Slurm job, or run
in the current shell.

It contains the critical options *PhaseSequence* and *PhaseIters*, which
define the number of times number of iterations for each phase for which
the CFD solver will be run.

This portion of the settings interface also includes command-line
options for the various executables that are used in the execution
sequence. It specifies command-line options to grid generation tools
like ``aflr3`` or other preprocessing tools like ``intersect``. The
solver-specific subclasses of :class:`RunControlOpts` also contain the
command-line options to solver commands such as ``flowCart`` for Cart3D.
"""

# Local imports
from .ulimitopts import ULimitOpts
from .aflr3opts import AFLR3Opts
from .archiveopts import ArchiveOpts
from .isectopts import IntersectOpts, VerifyOpts
from ...optdict import (
    BOOL_TYPES,
    INT_TYPES,
    WARNMODE_ERROR,
    OptionsDict)


# Environment class
class EnvironOpts(OptionsDict):
    r"""Class for environment variables

    :Call:
        >>> opts = EnvironOpts(**kw)
    :Inputs:
        *kw*: :class:`dict`
            Dictionary of environment variables
    :Outputs:
        *opts*: :class:`cape.options.runControl.Environ`
            System environment variable options interface
    :Versions:
        * 2015-11-10 ``@ddalle``: v1.0 (Environ)
        * 2022-10-28 ``@ddalle``: v2.0; OptionsDict
    """
    # Class attributes
    _opttypes = {
        "_default_": INT_TYPES + (str,),
    }

    # Get an environment variable by name
    def get_Environ(self, opt, j=0, i=None):
        r"""Get an environment variable setting by name

        :Call:
            >>> val = opts.get_Environ(opt, j=0)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *opt*: :class:`str`
                Name of the environment variable
            *i*: {``None``} | :class:`int`
                Case index
            *j*: {``0``} | ``None`` | :class:`int`
                Phase number
        :Outputs:
            *val*: :class:`str`
                Value to set the environment variable to
        :Versions:
            * 2015-11-10 ``@ddalle``: v1.0
            * 2022-10-29 ``@ddalle``: v2.0; OptionsDict methods
        """
        # Get value
        val = self.get_opt(opt, j, i=i, mode=WARNMODE_ERROR)
        # Return a string
        return str(val)

    # Set an environment variable by name
    def set_Environ(self, opt, val, j=None):
        r"""Set an environment variable setting by name

        :Call:
            >>> val = opts.get_Environ(opts, j=0)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *opt*: :class:`str`
                Name of the environment variable
            *val*: :class:`str`
                Value to set the environment variable to
            *j*: {``None``} | :class:`int`
                Phase index
        :Versions:
            * 2015-11-10 ``@ddalle``: v1.0
            * 2022-10-29 ``@ddalle``: v2.0; OptionsDict methods
        """
        self.set_opt(opt, val, j, mode=WARNMODE_ERROR)


# Class for iteration & mode control settings and command-line inputs
class RunControlOpts(OptionsDict):
    r"""Dictionary-based interface for generic code run control

    :Call:
        >>> opts = RunControlOpts(**kw)
    :Inputs:
        *kw*: :class:`dict`
            Dictionary of run control options
    :Outputs:
        *opts*: :class:`RunControlOpts`
            Basic control options interface
    :Versions:
        * 2014-12-01 ``@ddalle``: v1.0
    """
   # ================
   # Class attributes
   # ================
   # <
    # Accepted options
    _optlist = {
        "Archive",
        "Continue",
        "Environ",
        "JSONFile",
        "MPI",
        "PhaseSequence",
        "PhaseIters",
        "PostShellCmds",
        "PreMesh",
        "Resubmit",
        "RootDir",
        "Verbose",
        "WarmStart",
        "WarmStartFolder",
        "aflr3",
        "intersect",
        "mpicmd",
        "nIter",
        "nJob",
        "nProc",
        "qsub",
        "slurm",
        "ulimit",
        "verify",
    }

    # Option types
    _opttypes = {
        "Continue": BOOL_TYPES,
        "JSONFile": str,
        "MPI": BOOL_TYPES,
        "PreMesh": BOOL_TYPES,
        "PhaseIters": INT_TYPES,
        "PhaseSequence": INT_TYPES,
        "PostShellCmds": str,
        "Resubmit": BOOL_TYPES,
        "RootDir": str,
        "Verbose": BOOL_TYPES,
        "WarmStart": BOOL_TYPES,
        "mpicmd": str,
        "nIter": INT_TYPES,
        "nJob": INT_TYPES,
        "nProc": INT_TYPES,
        "qsub": BOOL_TYPES,
        "slurm": BOOL_TYPES,
    }

    # Aliases
    _optmap = {
        "CAPEFile": "JSONFile",
        "PostCmds": "PostShellCmds",
        "sbatch": "slurm",
        "nJob": "nJob",
    }

    # Allowed values
    _optvals = {
        "mpicmd": ("mpiexec", "mpirun"),
    }

    # Defaults
    _rc = {
        "Continue": True,
        "MPI": False,
        "PreMesh": False,
        "Resubmit": False,
        "Verbose": False,
        "WarmStart": False,
        "qsub": False,
        "slurm": False,
        "nJob": 0,
    }

    # List depth
    _optlistdepth = {
        "PostShellCmds": 1,
    }

    # Local parameter descriptions
    _rst_descriptions = {
        "Continue": "whether restarts of same phase can use same job",
        "JSONFile": "name of JSON file from which settings originated",
        "MPI": "whether or not to run MPI in phase",
        "PhaseIters": "check-point iterations for phase *j*",
        "PhaseSequence": "list of phase indices to run",
        "PostShellCmds": "list of commands to run after each cycle",
        "PreMesh": "whether or not to generate volume mesh before submitting",
        "RootDir": "(absolute) base folder from which CAPE settings were read",
        "Resubmit": "whether or not to submit new job at end of phase *j*",
        "WarmStart": "whether to warm start a case",
        "WarmStartFolder": "folder from which to get warm-start file",
        "Verbose": '"RunControl" verbosity flag',
        "mpicmd": "MPI executable name",
        "nIter": "number of iterations to run in phase *j*",
        "nJob": "number of jobs to run concurrently",
        "nProc": "number of cores/threads to use per case",
        "qsub": "whether or not to submit jobs with PBS",
        "slurm": "whether or not to submit jobs with Slurm",
    }

    # Sections
    _sec_cls = {
        "Archive": ArchiveOpts,
        "Environ": EnvironOpts,
        "aflr3": AFLR3Opts,
        "intersect": IntersectOpts,
        "ulimit": ULimitOpts,
        "verify": VerifyOpts,
    }
   # >

   # =======
   # General
   # =======
   # <
    # Get general RunControl option
    def get_RunControlOpt(self, opt: str, j=None, **kw):
        r"""Get a general option from the "RunControl" section

        :Call:
            >>> val = opts.get_RunControlOpt(opt, j=None, **kw)
        :Inputs:
            *opts*: :class:`Options`
                Options interface
            *opt*: :class:`str`
                Name of option to get or sample
            *j*: {``None``} | :class:`int`
                Phase index
        :Outputs:
            *val*: :class:`object`
                Value of ``opts[opt]``, sampled as appropriate
        :Versions:
            * 2023-07-17 ``@ddalle``: v1.0
        """
        return self.get_opt(opt, j, **kw)

    # Get general RunControl option
    def set_RunControlOpt(self, opt: str, val, j=None, **kw):
        r"""Get a general option from the "RunControl" section

        :Call:
            >>> opts.set_RunControlOpt(opt, val, j=None, **kw)
        :Inputs:
            *opts*: :class:`Options`
                Options interface
            *opt*: :class:`str`
                Name of option to get or sample
            *v*: :class:`object`
                Value to set in ``opts[opt]``
            *j*: {``None``} | :class:`int`
                Phase index
        :Versions:
            * 2023-07-17 ``@ddalle``: v1.0
        """
        return self.set_opt(opt, val, j, **kw)
   # >

   # =====
   # AFLR3
   # =====
   # <
    # Whether or not to use AFLR3
    def get_aflr3(self):
        r"""Return whether or not to run AFLR3 to create mesh

        :Call:
            >>> q = opts.get_aflr3()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *q*: ``True`` | {``False``}
                Whether or not there are nontrivial AFLR3 settings
        :Versions:
            * 2016-04-05 ``@ddalle``: v1.0
            * 2022-10-14 ``@ddalle``: v1.1; use :func:`bool`
        """
        # Initialize if necessary
        self.init_section(AFLR3Opts, "aflr3")
        # Get the value and type
        v = self.get('aflr3')
        # Get the flag and convert to True or False
        return bool(v.get('run'))
   # >

   # =========
   # intersect
   # =========
   # <
    # Whether or not to use intersect
    def get_intersect(self):
        r"""Return whether or not to run ``intersect`` on triangulations

        :Call:
            >>> q = opts.get_intersect()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *q*: ``True`` | {``False``}
                Whether or not to run ``intersect``
        :Versions:
            * 2016-04-05 ``@ddalle``: v1.0
            * 2022-10-23 ``@ddalle``: v1.1; use :func:`bool`
        """
        # Initialize if necessary
        self.init_section(IntersectOpts, "intersect")
        # Get the value and type
        v = self.get("intersect")
        # Get the flag and convert to True or False
        return bool(v.get('run'))
   # >

   # ======
   # verify
   # ======
   # <
    # Whether or not to use verify
    def get_verify(self):
        r"""Return whether or not to run ``verify`` on triangulations

        :Call:
            >>> q = opts.get_verify()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *q*: ``True`` | {``False``}
                Whether or not to run ``verify``
        :Versions:
            * 2016-04-05 ``@ddalle``: v1.0
            * 2022-10-23 ``@ddalle``: v1.1; use :func:`bool`
        """
        # Initialize if necessary
        self.init_section(VerifyOpts, "verify")
        # Get the value and type
        v = self.get("verify")
        # Get the flag and convert to True or False
        return bool(v.get('run'))
   # >

   # ===============
   # Local Functions
   # ===============
   # <
    # Number of phases
    def get_nSeq(self, i=None):
        r"""Return the number of phases in the sequence

        :Call:
            >>> nSeq = opts.get_nSeq(i=None)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *i*: {``None``} | :class:`int`
                Case index
        :Outputs:
            *nSeq*: :class:`int`
                Number of input sets in the sequence
        :Versions:
            * 2014-10-02 ``@ddalle``: v1.0
            * 2015-02-02 ``@ddalle``: v1.1; add *nPhase* override
            * 2022-10-23 ``@ddalle``: v2.0; ``OptionsDict``
            * 2022-10-28 ``@ddalle``: v2.1; add *i*
            * 2023-03-10 ``@ddalle``: v2.2; no scalar sequence check
        """
        # Get the phases for case *i*
        PhaseSeq = self.get_PhaseSequence(i=i)
        # Use index of last phase rather than length
        return max(PhaseSeq) + 1

    # Minimum required number of iterations
    def get_LastIter(self, i=None):
        r"""Return the minimum number of iterations for case to be done

        :Call:
            >>> nIter = opts.get_LastIter(i=None)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *i*: {``None``} | :class:`int`
                Case index
        :Outputs:
            *nIter*: :class:`int`
                Number of required iterations for case
        :Versions:
            * 2014-10-02 ``@ddalle``: v1.0
        """
        # Get last phase
        phase = self.get_PhaseSequence(j=-1, i=i)
        # Get cutoff for that phase
        return self.get_PhaseIters(j=phase, i=i)
   # >


# Create properties
RunControlOpts.add_properties(RunControlOpts._rst_descriptions)
# Upgrade subsections
RunControlOpts.promote_sections()

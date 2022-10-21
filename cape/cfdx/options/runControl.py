r"""
:mod:`cape.cfdx.options.runControl`: Primary case control options
==================================================================

This module provides a class to access (or set) options pertaining to the basic
execution of the code.  For example, it specifies how many iterations to run,
whether or not to use an MPI version of a solver, and whether or not to submit
the job to a PBS queue.

It also contains command-line options that are given to each binary that is
utilized for a a solver, and it also contains archiving options.  This entire
section is written to the file ``case.json`` within each run folder.
"""

# Ipmort options-specific utilities
from .util import rc0, odict, getel
from . import util
# Required submodules
from . import Archive
from . import ulimit
from . import aflr3opts
from . import intersect


# Environment class
class Environ(odict):
    r"""Class for environment variables
    
    :Call:
        >>> opts = Environ(**kw)
    :Inputs:
        *kw*: :class:`dict`
            Dictionary of environment variables
    :Outputs:
        *opts*: :class:`cape.options.runControl.Environ`
            System environment variable options interface
    :Versions:
        * 2015-11-10 ``@ddalle``: Version 1.0
    """
    
    # Get an environment variable by name
    def get_Environ(self, key, i=0):
        """Get an environment variable setting by name
        
        :Call:
            >>> val = opts.get_Environ(key, i=0)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *key*: :class:`str`
                Name of the environment variable
            *i*: :class:`int` or ``None``
                Phase number
        :Outputs:
            *val*: :class:`str`
                Value to set the environment variable to
        :Versions:
            * 2015-11-10 ``@ddalle``: Version 1.0
        """
        # Check for the key.
        if key not in self:
            raise KeyError(
                "Environment variable '%s' is not set in JSON file" % key)
        # Get the setting or list of settings
        V = self[key]
        # Select the value for run sequence *i*
        return str(getel(V, i))
        
    # Set an environment variable by name
    def set_Environ(self, key, val, i=None):
        r"""Set an environment variable setting by name
        
        :Call:
            >>> val = opts.get_Environ(key, i=0)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *key*: :class:`str`
                Name of the environment variable
            *val*: :class:`str`
                Value to set the environment variable to
            *i*: :class:`int` or ``None``
                Phase number
        :Versions:
            * 2015-11-10 ``@ddalle``: Version 1.0
        """
        # Initialize the key if necessary.
        self.setdefault(key, "")
        # Set the value by run sequence.
        self[key] = setel(self[key], str(val), i)
# class Environ


# Class for iteration & mode control settings and command-line inputs
class RunControl(odict):
    r"""Dictionary-based interface for generic code run control
    
    :Call:
        >>> opts = RunControl(**kw)
    :Inputs:
        *kw*: :class:`dict`
            Dictionary of run control options
    :Outputs:
        *opts*: :class:`cape.options.runControl.RunControl`
            Basic control options interface
    :Versions:
        * 2014-12-01 ``@ddalle``: Version 1.0
    """
    
    # Initialization method
    def __init__(self, fname=None, **kw):
        # Store the data in *this* instance
        for k in kw:
            self[k] = kw[k]
        # Upgrade important groups to their own classes.
        self._Environ()
        self._ulimit()
        self._Archive()
        self._aflr3()
        self._intersect()
        self._verify()
    
   # ===========
   # Environment
   # ===========
   # <
    # Environment variable interface
    def _Environ(self):
        """Initialize environment variables if necessary"""
        if 'Environ' not in self:
            # Empty/default
            self['Environ'] = Environ()
        elif type(self['Environ']).__name__ == 'dict':
            # Convert to special class
            self['Environ'] = Environ(**self['Environ'])
    
    # Get environment variable
    def get_Environ(self, key, i=0):
        self._Environ()
        return self['Environ'].get_Environ(key, i)
        
    # Set environment variable
    def set_Environ(self, key, val, i=None):
        self._Environ()
        self['Environ'].set_Environ(key, val, i)
        
    # Copy documentation
    for k in ['Environ']:
        # Get the documentation for the "get" and "set" functions
        eval('get_'+k).__doc__ = getattr(Environ,'get_'+k).__doc__
        eval('set_'+k).__doc__ = getattr(Environ,'set_'+k).__doc__
   # >

   # ===============
   # Resource Limits
   # ===============
   # <
   
    # Environment variable interface
    def _ulimit(self):
        """Initialize environment variables if necessary"""
        if 'ulimit' not in self:
            # Empty/default
            self['ulimit'] = ulimit.ulimit()
        elif type(self['ulimit']).__name__ == 'dict':
            # Convert to special class
            self['ulimit'] = ulimit.ulimit(**self['ulimit'])
    
    # Get resource limit variable
    def get_ulimit(self, u, i=0):
        self._ulimit()
        return self['ulimit'].get_ulimit(u, i)
        
    # Set resource limit variable
    def set_ulimit(self, u, l, i=None):
        self._ulimit()
        self['ulimit'].set_ulimit(u, l, i)
        
    # Stack size
    def get_ulimit_s(self, i=0):
        self._ulimit()
        return self['ulimit'].get_s(i)
        
    # Stack size
    def set_ulimit_s(self, s=rc0('ulimit_s'), i=0):
        self._ulimit()
        self['ulimit'].set_s(s, i)
        
    # Core file size
    def get_ulimit_c(self, i=0):
        self._ulimit()
        return self['ulimit'].get_c(i)
        
    # Core file size
    def set_ulimit_c(self, c, i=0):
        self._ulimit()
        self['ulimit'].set_c(c, i)
        
    # Data segment size
    def get_ulimit_d(self, i=0):
        self._ulimit()
        return self['ulimit'].get_d(i)
        
    # Data segment size
    def set_ulimit_d(self, d, i=0):
        self._ulimit()
        self['ulimit'].set_d(d, i)
        
    # Scheduling priority
    def get_ulimit_e(self, i=0):
        self._ulimit()
        return self['ulimit'].get_e(i)
        
    # Scheduling priority
    def set_ulimit_e(self, e, i=0):
        self._ulimit()
        self['ulimit'].set_e(e, i)
        
    # File size
    def get_ulimit_f(self, i=0):
        self._ulimit()
        return self['ulimit'].get_f(i)
        
    # File size
    def set_ulimit_f(self, f, i=0):
        self._ulimit()
        self['ulimit'].set_f(f, i)
        
    # Pending signals
    def get_ulimit_i(self, i=0):
        self._ulimit()
        return self['ulimit'].get_i(i)
        
    # Pending signals
    def set_ulimit_i(self, e, i=0):
        self._ulimit()
        self['ulimit'].set_i(e, i)
        
    # Max locked memory
    def get_ulimit_l(self, i=0):
        self._ulimit()
        return self['ulimit'].get_l(i)
        
    # Max locked memory
    def set_ulimit_l(self, l, i=0):
        self._ulimit()
        self['ulimit'].set_l(l, i)
        
    # Max memory
    def get_ulimit_m(self, i=0):
        self._ulimit()
        return self['ulimit'].get_m(i)
        
    # Max memory
    def set_ulimit_m(self, i=0):
        self._ulimit()
        self['ulimit'].set_m(i)
        
    # Open files
    def get_ulimit_n(self, i=0):
        self._ulimit()
        return self['ulimit'].get_n(i)
        
    # Open files
    def set_ulimit_n(self, n, i=0):
        self._ulimit()
        self['ulimit'].set_n(n, i)
        
    # Pipe size
    def get_ulimit_p(self, i=0):
        self._ulimit()
        return self['ulimit'].get_p(i)
        
    # Pipe size
    def set_ulimit_p(self, p, i=0):
        self._ulimit()
        self['ulimit'].set_p(p, i)
        
    # POSIX message queues
    def get_ulimit_q(self, i=0):
        self._ulimit()
        return self['ulimit'].get_q(i)
        
    # POSIX message queues
    def set_ulimit_q(self, q, i=0):
        self._ulimit()
        self['ulimit'].set_q(q, i)
        
    # Real-time priority
    def get_ulimit_r(self, i=0):
        self._ulimit()
        return self['ulimit'].get_r(i)
        
    # Real-time priority
    def set_ulimit_r(self, r, i=0):
        self._ulimit()
        self['ulimit'].set_r(r, i)
        
    # CPU time limit
    def get_ulimit_t(self, i=0):
        self._ulimit()
        return self['ulimit'].get_t(i)
        
    # CPU time limit
    def set_ulimit_t(self, t, i=0):
        self._ulimit()
        self['ulimit'].set_t(t, i)
        
    # Max user processes
    def get_ulimit_u(self, i=0):
        self._ulimit()
        return self['ulimit'].get_u(i)
        
    # Max user processes
    def set_ulimit_u(self, u, i=0):
        self._ulimit()
        self['ulimit'].set_u(u, i)
        
    # Virtual memory
    def get_ulimit_v(self, i=0):
        self._ulimit()
        return self['ulimit'].get_v(i)
        
    # Virtual memory
    def set_ulimit_v(self, v, i=0):
        self._ulimit()
        self['ulimit'].set_v(v, i)
        
    # File locks
    def get_ulimit_x(self, i=0):
        self._ulimit()
        return self['ulimit'].get_x(i)
        
    # File locks
    def set_ulimit_x(self, x, i=0):
        self._ulimit()
        self['ulimit'].set_x(x, i)
        
    # Copy documentation
    for k in ['ulimit']:
        # Get the documentation for the "get" and "set" functions
        eval('get_'+k).__doc__ = getattr(ulimit.ulimit,'get_'+k).__doc__
        eval('set_'+k).__doc__ = getattr(ulimit.ulimit,'set_'+k).__doc__
        
    # Copy documentation
    for k in [
        'c', 'd', 'e', 'f', 'i', 'l', 'm', 'n', 'p', 'q', 'r',
        's', 't', 'u', 'v', 'x'
    ]:
        # Get the documentation for the "get" and "set" functions
        eval('get_ulimit_'+k).__doc__ = getattr(ulimit.ulimit,'get_'+k).__doc__
        eval('set_ulimit_'+k).__doc__ = getattr(ulimit.ulimit,'set_'+k).__doc__
        
    # "Get" aliases
    get_stack_size           = get_ulimit_s
    get_core_file_size       = get_ulimit_c
    get_data_seg_limit       = get_ulimit_d
    get_scheduling_priority  = get_ulimit_e
    get_file_size            = get_ulimit_f
    get_pending_signal_limit = get_ulimit_i
    get_max_locked_memory    = get_ulimit_l
    get_max_memory_size      = get_ulimit_m
    get_open_file_limit      = get_ulimit_n
    get_pipe_size            = get_ulimit_p
    get_message_queues       = get_ulimit_q
    get_real_time_priority   = get_ulimit_r
    get_time_limit           = get_ulimit_t
    get_max_processes        = get_ulimit_u
    get_virtual_memory_limit = get_ulimit_v
    get_file_locks_limit     = get_ulimit_x
    
    # "Set" aliases
    set_stack_size           = set_ulimit_s
    set_core_file_size       = set_ulimit_c
    set_data_seg_limit       = set_ulimit_d
    set_scheduling_priority  = set_ulimit_e
    set_file_size            = set_ulimit_f
    set_pending_signal_limit = set_ulimit_i
    set_max_locked_memory    = set_ulimit_l
    set_max_memory_size      = set_ulimit_m
    set_open_file_limit      = set_ulimit_n
    set_pipe_size            = set_ulimit_p
    set_message_queues       = set_ulimit_q
    set_real_time_priority   = set_ulimit_r
    set_time_limit           = set_ulimit_t
    set_max_processes        = set_ulimit_u
    set_virtual_memory_limit = set_ulimit_v
    set_file_locks_limit     = set_ulimit_x
   # >
   
   # =====
   # AFLR3
   # =====
   # <
    # AFLR3 variable interface
    def _aflr3(self):
        r"""Initialize AFLR3 settings if necessary"""
        # Initialize section if necessary
        self.init_section(aflr3opts.AFLR3Opts, "aflr3")
            
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
            * 2016-04-05 ``@ddalle``: Version 1.0
            * 2022-10-14 ``@ddalle``: Version 1.1; use :func:`bool`
        """
        # Initialize if necessary
        self._aflr3()
        # Get the value and type
        v = self.get('aflr3')
        # Get the flag and convert to True or False
        return bool(v.get('run'))
   # >
    
   # =========
   # intersect
   # =========
   # <
    # ``itnersect`` variable interface
    def _intersect(self):
        """Initialize ``intersect`` settings if necessary"""
        # Get the value and type
        v = self.get('intersect')
        t = type(v).__name__
        # Check inputs
        if t == 'intersect':
            # Already initialized
            return
        elif v is None:
            # Empty/default
            self['intersect'] = intersect.intersect()
        elif t == 'dict':
            # Convert to special class
            self['intersect'] = intersect.intersect(**v)
        else:
            # Initialize
            self['intersect'] = intersect.intersect()
            # Set a flag
            if v:
                self['intersect']['run'] = True
            else:
                self['intersect']['run'] = False
            
    # Whether or not to use intersect
    def get_intersect(self):
        """Return whether or not to run ``intersect`` on triangulations
        
        :Call:
            >>> q = opts.get_intersect()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *q*: ``True`` | {``False``}
                Whether or not there are nontrivial ``intersect`` settings
        :Versions:
            * 2016-04-05 ``@ddalle``: Version 1.0
        """
        # Initialize if necessary
        self._intersect()
        # Get the value and type
        v = self.get('intersect')
        # Get the flag
        q = v.get('run')
        # Check.
        if q is None:
            # Check for nontrivial entries
            return len(v.keys()) > 0
        else:
            # Return the 'run' flag
            return q == True
    
    # Get intersect input file
    def get_intersect_i(self, j=0):
        self._intersect()
        return self['intersect'].get_intersect_i(j)
        
    # Set intersect input file
    def set_intersect_i(self, fname, j=None):
        self._intersect()
        self['intersect'].set_intersect_i(fname, j)
    
    # Get intersect output file
    def get_intersect_o(self, j=0):
        self._intersect()
        return self['intersect'].get_intersect_o(j)
        
    # Set intersect output file
    def set_intersect_o(self, fname, j=None):
        self._intersect()
        self['intersect'].set_intersect_o(fname, j)

    # get option to remove small tris
    def get_intersect_rm(self):
        self._intersect()
        return self['intersect'].get_intersect_rm()

    # Set option to remove small tris
    def set_intersect_rm(self, q=rc0('intersect_rm')):
        self._intersect()
        self['intersect'].set_intersect_rm(q)

    # get option to remove small tris
    def get_intersect_smalltri(self):
        self._intersect()
        return self['intersect'].get_intersect_smalltri()

    # set option for small triangles
    def set_intersect_smalltri(self, A=rc0('intersect_smalltri')):
        self._intersect()
        self['intersect'].set_intersect_smalltri(A)
        
    # Use triged to remove unused tris
    def get_intersect_triged(self):
        self._intersect()
        return self['intersect'].get_intersect_triged()
        
    # Use triged to remove unused tris
    def set_intersect_triged(self, q=rc0('intersect_triged')):
        self._intersect()
        self['intersect'].set_intersect_triged(q)
        
    # Copy documentation
    for k in [
        'intersect_i', 'intersect_o',
        'intersect_rm', 'intersect_smalltri', 'intersect_triged'
    ]:
        # Get the documentation for the "get" and "set" functions
        eval('get_'+k).__doc__ = getattr(intersect.intersect,'get_'+k).__doc__
        eval('set_'+k).__doc__ = getattr(intersect.intersect,'set_'+k).__doc__
   # >
   
   # ======
   # verify
   # ======
   # <
    # ``verify`` interface
    def _verify(self):
        """Initialize ``verify`` settings if necessary"""
        # Get the value and type
        v = self.get('verify')
        t = type(v).__name__
        # Check inputs
        if t == 'verify':
            # Already initialized
            return
        elif v is None:
            # Empty/default
            self['verify'] = intersect.verify()
        elif t == 'dict':
            # Convert to special class
            self['verify'] = intersect.verify(**v)
        else:
            # Initialize
            self['verify'] = intersect.verify()
            # Set a flag
            if v:
                self['verify']['run'] = True
            else:
                self['verify']['run'] = False
            
    # Whether or not to use verify
    def get_verify(self):
        """Return whether or not to run ``verify`` on triangulations
        
        :Call:
            >>> q = opts.get_verify()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *q*: ``True`` | {``False``}
                Whether or not there are nontrivial ``intersect`` settings
        :Versions:
            * 2016-04-05 ``@ddalle``: Version 1.0
        """
        # Initialize if necessary
        self._verify()
        # Get the value and type
        v = self.get('verify')
        # Get the flag
        q = v.get('run')
        # Check.
        if q is None:
            # Check for nontrivial entries
            return len(v.keys()) > 0
        else:
            # Return the 'run' flag
            return q == True
    
    # Get intersect input file
    def get_verify_i(self, j=0):
        self._verify()
        return self['verify'].get_verify_i(j)
        
    # Set intersect input file
    def set_verify_i(self, fname, j=0):
        self._verify()
        self['verify'].set_verify_i(fname, j)
        
    # Copy documentation
    for k in ['verify_i']:
        # Get the documentation for the "get" and "set" functions
        eval('get_'+k).__doc__ = getattr(intersect.verify,'get_'+k).__doc__
        eval('set_'+k).__doc__ = getattr(intersect.verify,'set_'+k).__doc__
   # >
   
   # =================
   # Folder management
   # =================
   # <
    # Initialization method for folder management optoins
    def _Archive(self):
        self.init_section(Archive.ArchiveOpts, "Archive")
   # >
    
   # =============== 
   # Local Functions
   # ===============
   # <
    # Number of iterations
    def get_nIter(self, i=None):
        """Return the number of iterations for run sequence *i*
        
        :Call:
            >>> nIter = opts.get_nIter(i=None)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *i*: :class:`int` or ``None``
                Run sequence index
        :Outputs:
            *nIter*: :class:`int` or :class:`list`\ [:class:`int`]
                Number of iterations to run
        :Versions:
            * 2015-10-20 ``@ddalle``: Version 1.0
        """
        return self.get_key('nIter', i)
        
    # Set number of iterations
    def set_nIter(self, nIter=rc0('nIter'), i=None):
        """Set the number of iterations for run sequence *i*
        
        :Call:
            >>> nIter = opts.get_nIter(i=None)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *i*: :class:`int` or ``None``
                Phase number
        :Outputs:
            *nIter*: :class:`int` or :class:`list`\ [:class:`int`]
                Number of iterations to run
        :Versions:
            * 2015-10-20 ``@ddalle``: Version 1.0
        """
        self.set_key('nIter', nIter, i)
    

    # Run input sequence
    def get_PhaseSequence(self, i=None):
        """Return the input sequence for `flowCart`
        
        :Call:
            >>> PhaseSeq = opts.get_PhaseSequence(i=None)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *i*: :class:`int` or ``None``
                Phase number
        :Outputs:
            *PhaseSeq*: :class:`int` or :class:`list`\ [:class:`int`]
                Sequence of input run index(es)
        :Versions:
            * 2014-10-02 ``@ddalle``: Version 1.0
            * 2015-11-27 ``@ddalle``: InputSeq -> PhaseSeq
        """
        return self.get_key('PhaseSequence', i)
        
    # Set run input sequence.
    def set_PhaseSequence(self, PhaseSeq=rc0('PhaseSequence'), i=None):
        """Set the input sequence for `flowCart`
        
        :Call:
            >>> opts.get_PhaseSequence(PhaseSeq, i=None)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *PhaseSeq*: :class:`int` or :class:`list`(:class:`int`)
                Sequence of input run index(es)
            *i*: :class:`int` or ``None``
                Phase number
        :Versions:
            * 2014-10-02 ``@ddalle``: Version 1.0
        """
        self.set_key('PhaseSequence', PhaseSeq, i)
        
    
    # Get minimum cumulative iteration count
    def get_PhaseIters(self, i=None):
        """
        Get the break points for run *i*.  Input *i* will be repeated until the
        cumulative iteration count is greater than or equal to *PhaseIters[i]*.
        
        :Call:
            >>> PhaseIters = opts.get_PhaseIters(i=None)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *i*: :class:`int` or ``None``
                Phase number
        :Outputs:
            *PhaseIters*: :class:`int` or :class:`list`(:class:`int`)
                Sequence of iteration break points
        :Versions:
            * 2014-10-02 ``@ddalle``: Version 1.0
        """
        return self.get_key('PhaseIters', i)
        
    # Set minimum cumulative iteration count
    def set_PhaseIters(self, PhaseIters, i=None):
        """
        Get the break points for run *i*.  Input *i* will be repeated until the
        cumulative iteration count is greater than or equal to *PhaseIters[i]*.
        
        :Call:
            >>> opts.get_PhaseIters(PhaseIters, i=None)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *i*: :class:`int` or ``None``
                Phase number
        :Outputs:
            *PhaseIters*: :class:`int` or :class:`list`(:class:`int`)
                Sequence of iteration break points
        :Versions:
            * 2014-10-02 ``@ddalle``: Version 1.0
        """
        self.set_key('PhaseIters', PhaseIters, i)
        
    
    # Number of phases
    def get_nSeq(self):
        """Return the number of input sets in the sequence
        
        :Call:
            >>> nSeq = opts.get_nSeq()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *nSeq*: :class:`int`
                Number of input sets in the sequence
        :Versions:
            * 2014-10-02 ``@ddalle``: Version 1.0
            * 2015-02-02 ``@ddalle``: Added *nPhase* override
        """
        # Check for number of phases
        nPhase = self.get('nPhase')
        # Output if specified
        if nPhase is not None: return nPhase
        # Get the input sequence.
        PhaseSeq = self.get_PhaseSequence()
        # Check if it's a list.
        if type(PhaseSeq).__name__ == "list":
            # Use the length.
            return max(PhaseSeq) + 1
        else:
            # Something is messed up.
            return 1
            
    # Minimum required number of iterations
    def get_LastIter(self):
        """Return the minimum number of iterations for case to be done
        
        :Call:
            >>> nIter = opts.get_LastIter()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *nIter*: :class:`int`
                Number of required iterations for case
        :Versions:
            * 2014-10-02 ``@ddalle``: Version 1.0
        """
        return self.get_PhaseIters(self.get_PhaseSequence(-1))
        
    # Get MPI status
    def get_MPI(self, i):
        """Return whether or not to use MPI version
        
        :Call:
            >>> MPI = opts.get_mpi(i=None)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *i*: :class:`int`
                Run sequence index
        :Outputs:
            *MPI*: :class:`bool`
                Whether or not to use MPI
        :Versions:
            * 2015-10-17 ``@ddalle``: Version 1.0
        """
        return self.get_key('MPI', i)
        
    # Set MPI status
    def set_MPI(self, MPI=rc0('MPI'), i=None):
        """Set whether or not to use MPI version
        
        :Call:
            >>> q = opts.get_mpi(i=None)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *i*: :class:`int`
                Run sequence index
        :Outputs:
            *MPI*: :class:`bool`
                Whether or not to use MPI
        :Versions:
            * 2015-10-17 ``@ddalle``: Version 1.0
        """
        self.set_key('MPI', MPI, i)
        
    # Get the number of threads to use
    def get_nProc(self, i=None):
        """Return the number of threads to use
        
        :Call:
            >>> nProc = opts.get_nProc(i=None)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *i*: :class:`int` or ``None``
                Phase number
        :Outputs:
            *nProc*: :class:`int` or :class:`list`(:class:`int`)
                Number of threads for `flowCart`
        :Versions:
            * 2014-08-02 ``@ddalle``: Version 1.0
            * 2014-10-02 ``@ddalle``: Switched to "nProc"
        """
        return self.get_key('nProc', i)
    
    # Set number of threads to use
    def set_nProc(self, nProc=rc0('nProc'), i=None):
        """Set the number of threads to use
        
        :Call:
            >>> opts.set_nProc(nProc, i)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *nProc*: :class:`int` or :class:`list`(:class:`int`)
                Number of threads for `flowCart`
            *i*: :class:`int` or ``None``
                Phase number
        :Versions:
            * 2014-08-02 ``@ddalle``: Version 1.0
            * 2014-10-02 ``@ddalle``: Switched to "nProc"
        """
        self.set_key('nProc', nProc, i)
        
    # Get the command name for "mpirun" or "mpiexec"
    def get_mpicmd(self, i=None):
        """Return either ``'mpirun'`` or ``'mpiexec``
        
        :Call:
            >>> mpicmd = opts.get_mpicmd(i=None)
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
            *i*: :class:`int` or ``None``
                Phase number
        :Outputs:
            *mpicmd*: :class:`str`
                System command to call MPI
        :Versions:
            * 2014-10-02 ``@ddalle``: Version 1.0
        """
        return self.get_key('mpicmd', i)
    
    # Set the command name for "mpirun" or "mpiexec"
    def set_mpicmd(self, mpicmd=rc0('mpicmd'), i=None):
        """Set minimum CFL number for `flowCart`
        
        :Call:
            >>> opts.set_mpicmd(mpicmd, i)
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
            *mpicmd*: :class:`str`
                System command to call MPI
            *i*: :class:`int` or ``None``
                Phase number
        :Versions:
            * 2014-10-02 ``@ddalle``: Version 1.0
        """
        self.set_key('mpicmd', mpicmd, i)
    
    # Get the submittable-job status
    def get_qsub(self, i=None):
        """Determine whether or not to submit jobs
        
        :Call:
            >>> qsub = opts.get_qsub(i=None)
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
            *i*: :class:`int` or ``None``
                Phase number
        :Outputs:
            *qsub*: :class:`bool` or :class:`list`(:class:`bool`)
                Whether or not to submit case to PBS
        :Versions:
            * 2014-10-05 ``@ddalle``: Version 1.0
        """
        return self.get_key('qsub', i)
    
    # Set the submittable-job status
    def set_qsub(self, qsub=rc0('qsub'), i=None):
        """Set jobs as submittable or nonsubmittable
        
        :Call:
            >>> opts.set_qsub(qsub, i)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *qsub*: :class:`bool` or :class:`list`(:class:`bool`)
                Whether or not to submit case to PBS
            *i*: :class:`int` or ``None``
                Phase number
        :Versions:
            * 2014-10-05 ``@ddalle``: Version 1.0
        """
        self.set_key('qsub', qsub, i)
    
    # Get the submittable-job status
    def get_sbatch(self, i=None):
        """Determine whether or not to submit jobs using SLURM
        
        :Call:
            >>> sbatch = opts.get_sbatch(i=None)
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
            *i*: :class:`int` or ``None``
                Phase number
        :Outputs:
            *sbatch*: :class:`bool` or :class:`list`(:class:`bool`)
                Whether or not to submit case to SLURM
        :Versions:
            * 2018-10-10 ``@ddalle``: Version 1.0
        """
        return self.get_key('sbatch', i)
    
    # Set the submittable-job status
    def set_sbatch(self, sbatch=rc0('sbatch'), i=None):
        """Set jobs as submittable or nonsubmittable via SLURM
        
        :Call:
            >>> opts.set_sbatch(sbatch, i)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *sbatch*: :class:`bool` or :class:`list`(:class:`bool`)
                Whether or not to submit case to SLURM
            *i*: :class:`int` or ``None``
                Phase number
        :Versions:
            * 2018-10-10 ``@ddalle``: Version 1.0
        """
        self.set_key('sbatch', sbatch, i)
        
    
    # Get the resubmittable-job status
    def get_Resubmit(self, i=None):
        """Determine whether or not a job should restart or resubmit itself
        
        :Call:
            >>> resub = opts.get_Resubmit(i=None)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *i*: :class:`int` or ``None``
                Phase number
        :Outputs:
            *resub*: :class:`bool` | :class:`list` (:class:`bool`)
                Whether or not to resubmit/restart a case
        :Versions:
            * 2014-10-05 ``@ddalle``: Version 1.0
        """
        return self.get_key('Resubmit', i)
    
    # Set the resubmittable-job status
    def set_Resubmit(self, resub=rc0('Resubmit'), i=None):
        """Set jobs as resubmittable or nonresubmittable
        
        :Call:
            >>> opts.set_Resubmit(resub, i)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *resub*: :class:`bool` or :class:`list`(:class:`bool`)
                Whether or not to resubmit/restart a case
            *i*: :class:`int` or ``None``
                Phase number
        :Versions:
            * 2014-10-05 ``@ddalle``: Version 1.0
        """
        self.set_key('Resubmit', resub, i)
        
    # Get the continuance status
    def get_Continue(self, i=None):
        """Determine if restarts of the same run input should be resubmitted
        
        :Call:
            >> cont = opts.get_Continue(i=None)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *i*: :class:`int` or ``None``
                Phase number
        :Outputs:
            *cont*: :class:`bool` | :class:`list` (:class:`bool`)
                Whether or not to continue restarts of same input sequence
                without resubmitting
        :Versions:
            * 2015-11-08 ``@ddalle``: Version 1.0
        """
        return self.get_key('Continue', i)
        
    # Set the continuance status
    def set_Continue(self, cont=rc0('Continue'), i=None):
        """Set the resubmit status for restarts of the same input sequence
        
        :Call:
            >> opts.set_Continue(, cont, i=None)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *i*: :class:`int` or ``None``
                Phase number
        :Outputs:
            *cont*: :class:`bool` | :class:`list` (:class:`bool`)
                Whether or not to continue restarts of same input sequence
                without resubmitting
        :Versions:
            * 2015-11-08 ``@ddalle``: Version 1.0
        """
        self.set_key('Continue', cont, i)
        
    # Whether or not to generate mesh before submitting
    def get_PreMesh(self, i=0):
        """Determine whether or not to generate volume mesh before submitting
        
        :Call:
            >>> preMesh = opts.get_PreMesh(i=0)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *i*: {``0``} | :class:`int`
                Phase number
        :Outputs:
            *preMesh*: :class:`bool`
                Whether or not to create mesh before submitting PBS job
        :Versions:
            * 2016-04-06 ``@ddalle``: Version 1.0
        """
        return self.get_key('PreMesh', i)
    
    # Set the pre-submit mesh generation option
    def set_PreMesh(self, preMesh=rc0('PreMesh'), i=None):
        """Set the setting regarding pre-submit mesh generation
        
        :Call:
            >>> opts.set_PreMesh(preMesh=False, i=None)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *preMesh*: :class:`bool`
                Whether or not to create mesh before submitting PBS job
            *i*: :class:`int` | ``None``
                Phase number
        :Outputs:
            * 2016-04-06 ``@ddalle``: Version 1.0
        """
        self.set_key('PreMesh', preMesh, i)
    
    # Get verbosity
    def get_Verbose(self, i=0):
        """Get the verbosity flag from the "RunControl" section
        
        :Call:
            >>> v = opts.get_Verbose(i=0)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *i*: {``0``} | :class:`int`
                Phase number
        :Outputs:
            *v*: ``True`` | {``False``}
                Verbosity
        :Versions:
            * 2017-03-12 ``@ddalle``: Version 1.0
        """
        return self.get_key("Verbose", i)
   # >


# Upgrade subsections
util.promote_subsec(aflr3opts.AFLR3Opts, "aflr3")
util.promote_subsec(Archive.ArchiveOpts, "Archive")

r"""
:mod:`cape.cfdx.options.databookopts`: Databook definition options
===================================================================

This module contains the basic interface that define the ``"DataBook"``
of a CAPE configuration, which controls which information from the CFD
runs are extracted and collected elsewhere.

The :class:`DataBookOpts` class defined here defines the list of
databook components in the option *Components*, and each component has
its own entry in the ``"DataBook"`` section. A component that has no
further definitions is usually interpreted as a force & moment
component (*Type* is ``"FM"``), but other databook component types can
also be used.

"""

# Standard library
import fnmatch

# Local imports
from ...optdict import OptionsDict, INT_TYPES
from .util import rc0, odict


# Class for data book
class DataBookOpts(OptionsDict):
    r"""Dictionary-based interface for DataBook specifications

    :Call:
        >>> opts = DataBookOpts(**kw)
    :Inputs:
        *kw*: :class:`dict`
            Dictionary of options
    :Outputs:
        *opts*: :class:`cape.cfdx.options.databookopts.DataBookOpts`
            Data book options interface
    :Versions:
        * 2014-12-20 ``@ddalle``: Version 1.0
    """
  # ================
  # Class Attributes
  # ================
  # <
    # Recognized options
    _optlist = {
        "Components",
        "nMin",
        "nStats",
    }

    # Aliases
    _optmap = {
        "NAvg": "nStats",
        "NFirst": "nFirst",
        "NMin": "nMin",
        "NStats": "nStats",
        "nAvg": "nStats",
        "nFirst": "nMin",
    }

    # Types
    _opttypes = {
        "Components": str,
        "nStats": INT_TYPES,
    }

    # Defaults
    _rc = {
        "nMin": 0,
        "nStats": 0,
    }

    # Descriptions
    _rst_descriptions = {
        "Components": "list of databook components",
        "nMin": "first iter to consider for use in databook [for a comp]",
        "nStats": "iterations to use in averaging window [for a comp]",
    }

    # Key defining additional *_xoptlist*
    _xoptkey = "Components"

    # Section map
    _sec_cls_opt = "Type"
    _sec_cls_optmap = {}
  # >

  # ======
  # Config
  # ======
  # <
    # Initialization method
    def __init__(self, fname=None, **kw):
        """Data book options initialization method

        :Versions:
            * 2014-12-21 ``@ddalle``: Version 1.0
        """
        # Store the data in *this* instance
        for k in kw:
            self[k] = kw[k]
        # Upgrade important groups to their own classes.
        self._DBTarget()

    # Initialization and confirmation for autoInputs options
    def _DBTarget(self):
        """Initialize data book target options if necessary"""
        # Check for missing entirely.
        if 'Targets' not in self:
            # Empty/default
            self['Targets'] = {}
            return None
        # Read the targets
        targs = self['Targets']
        # Check the type.
        if not isinstance(targs, dict):
            # Invalid type
            raise TypeError('Data book targets must be a dictionary')
        # Initialize final state.
        self['Targets'] = {}
        # Loop through targets
        for targ in targs:
            # Convert to special class.
            self['Targets'][targ] = DBTarget(**targs[targ])
  # >

  # =================
  # Global Components
  # =================
  # <
    # Get the targets for a specific component
    def get_CompTargets(self, comp):
        r"""Get the list of targets for a specific data book component

        :Call:
            >>> targs = opts.get_CompTargets(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of component
        :Outputs:
            *targs*: :class:`list`\ [:class:`str`]
                List of targets for that component
        :Versions:
            * 2014-12-21 ``@ddalle``: Version 1.0
        """
        # Get the component options.
        copts = self.get(comp, {})
        # Get the targets.
        targs = copts.get('Targets', {})
        # Make sure it's a dict.
        if type(targs).__name__ not in ['dict']:
            raise TypeError("Targets for component '%s' are not a dict" % comp)
        # Output
        return targs

    # Get list of point in a point sensor group
    def get_DBGroupPoints(self, name):
        r"""Get the list of points in a group

        For example, get the list of point sensors in a point sensor
        group

        :Call:
            >>> pts = opts.get_DBGroupPoints(name)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *name*: :class:`str`
                Name of data book group
        :Outputs:
            *pts*: :class:`list`\ [:class:`str`]
                List of points (by name) in the group
        :Versions:
            * 2015-12-04 ``@ddalle``: Version 1.0
            * 2016-02-17 ``@ddalle``: Version 1.1; generic version
        """
        # Check.
        if name not in self:
            raise KeyError("Data book group '%s' not found" % name)
        # Check for points.
        pts = self[name].get("Points", [name])
        # Check if it's a list.
        if type(pts).__name__ in ['list', 'ndarray']:
            # Return list as-is
            return pts
        else:
            # Singleton list
            return [pts]
  # >

  # =================
  # Common Properties
  # =================
  # <
    # Get the number of initial divisions
    def get_nStats(self, comp=None, **kw):
        r"""Get the iterations to use in averaging window [for a comp]

        :Call:
            >>> nStats = opts.get_nStats(comp=None, **kw)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: {``None``} | :class:`str`
                Name of specific databook component
        :Outputs:
            *nStats*: :class:`int`
                Number of iterations to be used for statistics
        :Versions:
            * 2014-12-20 ``@ddalle``: Version 1.0
        """
        # No phases
        kw["j"] = 0
        # Global data book setting
        db_stats = self.get_opt('nStats', **kw)
        # Process
        if comp is None:
            return db_stats
        else:
            # Return specific setting; default to global
            return self[comp].get('nStats', db_stats)

    # Get the earliest iteration to consider
    def get_nMin(self, comp=None, **kw):
        r"""Get first iter to consider for use in databook [for a comp]

        :Call:
            >>> nMin = opts.get_nMin(comp=None, **kw)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: {``None``} | :class:`str`
                Name of specific databook component
        :Outputs:
            *nMin*: :class:`int`
                Minimum iteration index to consider for statistics
        :Versions:
            * 2015-02-28 ``@ddalle``: Version 1.0
        """
        # No phases
        kw["j"] = 0
        # Check for a value
        db_nmin = self.get_opt("nMin", **kw)
        # Check inputs
        if comp is None:
            # Global setting
            nmin = db_nmin
        else:
            # Specific setting; default to global
            nmin = self[comp].get('nMin', db_nmin)
        # Output
        return nmin
        
    # Get the number of initial divisions
    def get_nMaxStats(self, comp=None):
        """Get the maximum number of iterations to be used for statistics
        
        :Call:
            >>> nMax = opts.get_nMaxStats()
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of specific data book to query
        :Outputs:
            *nMax*: :class:`int`
                Maximum number of iterations to be used for statistics
        :Versions:
            * 2014-12-20 ``@ddalle``: Version 1.0
        """
        # Read global option
        db_nMax = self.get_key('nMaxStats', rc0('db_max'))
        # Process request type
        if comp is None:
            # Global
            return db_nMax
        else:
            # Return specific setting; default to global
            return self[comp].get('nMaxStats', db_nMax)
        
    # Set the maximum number of initial mesh divisions
    def set_nMaxStats(self, nMax=rc0('db_max')):
        """Set the maximum number of iterations to be used for statistics
        
        :Call:
            >>> opts.set_nMaxStats(nMax)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *nMax*: :class:`int`
                Number of iterations to be used for statistics
        :Versions:
            * 2014-12-20 ``@ddalle``: Version 1.0
        """
        self['nMaxStats'] = nMax
        
    # Interval
    def get_dnStats(self, comp=None):
        """Get the increment in window sizes
        
        :Call:
            >>> dn = opts.get_dnStats(comp=None)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of specific data book to query
        :Outputs:
            *dn*: :class:`int`
                Increment in candidate window sizes
        :Versions:
            * 2017-09-29 ``@ddalle``: Version 1.0
        """
        # Read global option
        db_dn = self.get_key('dnStats', self.get_nStats(comp))
        # Process request type
        if comp is None:
            # Global
            return db_dn
        else:
            # Return specific setting; default to global
            return self[comp].get('dnStats', db_dn)
        
    # Set the maximum number of initial mesh divisions
    def set_dnStats(self, dn):
        """Set the increment in window sizes
        
        :Call:
            >>> opts.set_dnStats(dn)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *dn*: :class:`int`
                Increment in candidate window sizes
        :Versions:
            * 2017-09-29 ``@ddalle``: Version 1.0
        """
        self['nMaxStats'] = dn
        
    # Get a specific iteration to end statistics at
    def get_nLastStats(self, comp=None):
        """Get the iteration at which to end statistics
        
        :Call:
            >>> nLast = opts.get_nLastStats()
            >>> nLast = opts.get_nLastStats(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of specific data book to query
        :Outputs:
            *nLast*: :class:`int`
                Maximum iteration to use for statistics
        :Versions:
            * 2015-03-04 ``@ddalle``: Version 1.0
        """
        # Global option
        db_nLast = self.get('nLastStats')
        # Process request type
        if comp is None:
            # Global data book setting
            return db_nLast
        else:
            # Return specific setting
            return self[comp].get('nLastStats', db_nLast)
        
    # Set a specific iteration to end statistics at
    def set_nLastStats(self, nLast=None):
        """Get the iteration at which to end statistics
        
        :Call:
            >>> opts.get_nLastStats(nLast)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *nLast*: :class:`int`
                Maximum iteration to use for statistics
        :Versions:
            * 2015-03-04 ``@ddalle``: Version 1.0
        """
        self['nLastStats'] = nLast
        
    # Get the location
    def get_DataBookDir(self):
        """Get the folder that holds the data book
        
        :Call:
            >>> fdir = opts.get_DataBookDir()
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
        :Outputs:
            *fdir*: :class:`str`
                Relative path to data book folder
        :Versions:
            * 2014-12-20 ``@ddalle``: Version 1.0
        """
        return self.get('Folder', 'data')
        
    # Set the location
    def set_DataBookDir(self, fdir=rc0('db_dir')):
        """Set the folder that holds the data book
        
        :Call:
            >>> fdir = opts.get_DataBookDir()
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *fdir*: :class:`str`
                Relative path to data book folder
        :Versions:
            * 2014-12-20 ``@ddalle``: Version 1.0
        """
        self['Folder'] = fdir
        
    # Get the file delimiter
    def get_Delimiter(self):
        """Get the delimiter to use in files
        
        :Call:
            >>> delim = opts.get_Delimiter()
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
        :Outputs:
            *delim*: :class:`str`
                Delimiter to use in data book files
        :Versions:
            * 2014-12-21 ``@ddalle``: Version 1.0
        """
        return self.get('Delimiter', rc0('Delimiter'))
        
    # Set the file delimiter.
    def set_Delimiter(self, delim=rc0('Delimiter')):
        """Set the delimiter to use in files
        
        :Call:
            >>> opts.set_Delimiter(delim)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *delim*: :class:`str`
                Delimiter to use in data book files
        :Versions:
            * 2014-12-21 ``@ddalle``: Version 1.0
        """
        self['Delimiter'] = delim
        
    # Get the key on which to sort
    def get_SortKey(self):
        """Get the key to use for sorting the data book
        
        :Call:
            >>> key = opts.get_SortKey()
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
        :Outputs:
            *key*: :class:`str` | ``None`` | :class:`list`\ [:class:`str`]
                Name of key to sort with
        :Versions:
            * 2014-12-30 ``@ddalle``: Version 1.0
        """
        return self.get('Sort')
        
    # Set the key on which to sort
    def set_SortKey(self, key):
        """Set the key to use for sorting the data book
        
        :Call:
            >>> opts.set_SortKey(key)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *key*: :class:`str` | ``None`` | :class:`list`\ [:class:`str`]
                Name of key to sort with
        :Versions:
            * 2014-12-30 ``@ddalle``: Version 1.0
        """
        self['Sort'] = key
        
    # Get prefix
    def get_DataBookPrefix(self, comp):
        """Get the prefix to use for a data book component
        
        :Call:
            >>> fpre = opts.get_DataBookPrefix(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of component
        :Outputs:
            *fpre*: :class:`str`
                Name of prefix
        :Versions:
            * 2016-06-07 ``@ddalle``: Version 1.0
        """
        # Global data book setting
        db_pre = self.get('Prefix')
        # Get component options
        copts = self.get(comp, {})
        # Get the extension
        return copts.get("Prefix", db_pre)
        
    # Get extension
    def get_DataBookExtension(self, comp):
        """Get the file extension for a data book component
        
        :Call:
            >>> ext = opts.get_DataBookExtension(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of component
        :Outputs:
            *ext*: :class:`str`
                File extension
        :Versions:
            * 2016-06-07 ``@ddalle``: Version 1.0
        """
        # Global data book setting
        db_ext = self.get('Extension', "dlds")
        # Get component options
        copts = self.get(comp, {})
        # Get the extension
        return copts.get("Extension", db_ext)
  # >
  
  # ===========
  # Other Files
  # ===========
  # <
    # Get output format
    def get_DataBookOutputFormat(self, comp):
        """Get any output format option for a data book component
        
        :Call:
            >>> fmt = opts.get_DataBookOutputFormat(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Data book component name
        :Outputs:
            *fmt*: ``None`` | :class:`str`
                File format for additional output
        :Versions:
            * 2017-03-28 ``@ddalle``: Version 1.0
        """
        # Get the options for the component.
        copts = self.get(comp, {})
        # Get the global option
        fmt = self.get("OutputFormat")
        # Get the component-specific option
        fmt = copts.get("OutputFormat", fmt)
        # Output
        return fmt
        
    # Get output format
    def get_DataBookTriqFormat(self, comp):
        """Get endianness and single/double for ``triq`` files
        
        :Call:
            >>> fmt = opts.get_DataBookTriqFormat(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Data book component name
        :Outputs:
            *fmt*: ``ascii`` | {``lb4``} | ``b4`` | ``lb8`` | ``b8``
                File format for additional output
        :Versions:
            * 2017-03-28 ``@ddalle``: Version 1.0
        """
        # Get the options for the component.
        copts = self.get(comp, {})
        # Get the global option
        fmt = self.get("TriqFormat", "lb4")
        # Get the component-specific option
        fmt = copts.get("TriqFormat", fmt)
        # Output
        return fmt
  # >

  # =======
  # PyFunc
  # =======
  # <
    def get_DataBookFunction(self, comp):
        r"""Get function name for PyFunc component
        
        :Call:
            >>> funcname = opts.get_DataBookFunction(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Data book component name
        :Outputs:
            *funcname*: :class:`str`
                Name of function to use for this component
        :Versions:
            * 2022-04-13 ``@ddalle``: Version 1.0
        """
        # Get the options for the component.
        copts = self.get(comp, {})
        # Get the global option
        funcname = self.get("Function")
        # Get the component-specific option
        funcname = copts.get("Function", funcname)
        # Output
        return funcname
  # >
  
  # ======
  # TriqFM
  # ======
  # <
    # Get absolute tangent tolerance
    def get_DataBookAbsTol(self, comp):
        """Get absolute tangent tolerance, not affected by component scale
        
        :Call:
            >>> atol = opts.get_DataBookAbsTol(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Data book component name
        :Outputs:
            *atol*: :class:`float`
                Absolute tangential distance tolerance for TriqFM
        :Versions:
            * 2017-04-07 ``@ddalle``: Version 1.0
        """
        # Read options for compoonent
        copts = self.get(comp, {})
        # Get global option
        atol = self.get("AbsTol", rc0("atoldef"))
        # Get component-specific option
        return copts.get("AbsTol", copts.get("atol", atol))
    
    # Get relative tangent tolerance
    def get_DataBookRelTol(self, comp):
        """Get tangent tolerance relative to overall geometry scale
        
        :Call:
            >>> rtol = opts.get_DataBookRelTol(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Data book component name
        :Outputs:
            *rtol*: :class:`float`
                Tangential distance tolerance relative to total BBox
        :Versions:
            * 2017-04-07 ``@ddalle``: Version 1.0
        """
        # Read options for compoonent
        copts = self.get(comp, {})
        # Get global option
        rtol = self.get("RelTol", rc0("rtoldef"))
        # Get component-specific option
        return copts.get("RelTol", copts.get("rtol", rtol))
    
    # Get relative tangent tolerance
    def get_DataBookCompTol(self, comp):
        """Get tangent tolerance relative to component
        
        :Call:
            >>> rtol = opts.get_DataBookCompTol(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Data book component name
        :Outputs:
            *rtol*: :class:`float`
                Tangential distance tolerance relative to component BBox
        :Versions:
            * 2017-04-07 ``@ddalle``: Version 1.0
        """
        # Read options for compoonent
        copts = self.get(comp, {})
        # Get global option
        ctol = self.get("CompTol", rc0("ctoldef"))
        # Get component-specific option
        return copts.get("CompTol", copts.get("ctol", ctol))
        
    # Get absolute projection tolerance
    def get_DataBookAbsProjTol(self, comp):
        """Get absolute projection tolerance, not affected by component scale
        
        :Call:
            >>> antol = opts.get_DataBookAbsProjTol(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Data book component name
        :Outputs:
            *antol*: :class:`float`
                Absolute distance tolerance for TriqFM projection
        :Versions:
            * 2017-04-07 ``@ddalle``: Version 1.0
        """
        # Read options for compoonent
        copts = self.get(comp, {})
        # Get global option
        antol = self.get("ProjTol", self.get("AbsProjTol", rc0("antoldef")))
        # Get component-specific option
        return copts.get("ProjTol", copts.get("AbsProjTol", 
            copts.get("antol", antol)))
        
    # Get absolute projection tolerance
    def get_DataBookRelProjTol(self, comp):
        """Get projection tolerance relative to size of geometry
        
        :Call:
            >>> rntol = opts.get_DataBookRelProjTol(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Data book component name
        :Outputs:
            *rntol*: :class:`float`
                Projection distance tolerance relative to total BBox
        :Versions:
            * 2017-04-07 ``@ddalle``: Version 1.0
        """
        # Read options for compoonent
        copts = self.get(comp, {})
        # Get global option
        rntol = self.get("RelProjTol", rc0("rntoldef"))
        # Get component-specific option
        return copts.get("RelProjTol", copts.get("rntol", rntol))
        
    # Get component-relative projection tolerance
    def get_DataBookCompProjTol(self, comp):
        """Get projection tolerance relative to size of component
        
        :Call:
            >>> cntol = opts.get_DataBookCompProjTol(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Data book component name
        :Outputs:
            *cntol*: :class:`float`
                Projection distance tolerance relative to comp BBox
        :Versions:
            * 2017-04-07 ``@ddalle``: Version 1.0
        """
        # Read options for compoonent
        copts = self.get(comp, {})
        # Get global option
        cntol = self.get("CompProjTol", rc0("cntoldef"))
        # Get component-specific option
        return copts.get("CompProjTol", copts.get("cntol", cntol))
        
    # Get all tolerances
    def get_DataBookMapTriTol(self, comp):
        """Get dictionary of projection tolerances for :func:`tri.MapTriCompID`
        
        :Call:
            >>> tols = opts.get_DataBookMapTriTol(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Data book component name
        :Outputs:
            *tols*: :class:`dict`\ [:class:`float`]
                Dict of relative and absolute tolerances for CompID mapping
        :Versions:
            * 2017-04-07 ``@ddalle``: Version 1.0
        """
        # Get the options
        atol  = self.get_DataBookAbsTol(comp)
        rtol  = self.get_DataBookRelTol(comp)
        ctol  = self.get_DataBookCompTol(comp)
        antol = self.get_DataBookAbsProjTol(comp)
        rntol = self.get_DataBookRelProjTol(comp)
        cntol = self.get_DataBookCompProjTol(comp)
        # Initialize output
        tols = {}
        # Set each parameter
        if atol  is not None: tols["atol"]  = atol
        if rtol  is not None: tols["rtol"]  = rtol
        if ctol  is not None: tols["ctol"]  = ctol
        if antol is not None: tols["antol"] = antol
        if rntol is not None: tols["rntol"] = rntol
        if cntol is not None: tols["cntol"] = cntol
        # Output
        return tols
            
    # Get config file for raw grid/triangulation
    def get_DataBookConfigFile(self, comp):
        """Get config file for the original mesh or unmapped tri file
        
        :Call:
            >>> fcfg = opts.get_DataBookConfigFile(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Data book component name
        :Outputs:
            *fcfg*: :class:`str`
                Name of configuration file
        :Versions:
            * 2017-04-07 ``@ddalle``: Version 1.0
        """
        # Read options for compoonent
        copts = self.get(comp, {})
        # Get global option
        fcfg = self.get("ConfigFile")
        # Get component-specific option
        return copts.get("ConfigFile", fcfg)
        
    # Restrict analysis to this component
    def get_DataBookConfigCompID(self, comp):
        """Get config file for the original mesh or unmapped tri file
        
        :Call:
            >>> compID = opts.get_DataBookConfigCompID(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Data book component name
        :Outputs:
            *compID*: {``None``} | :class:`int` | :class:`str` | :class:`list`
                Component from pre-mapped tri file
        :Versions:
            * 2017-04-07 ``@ddalle``: Version 1.0
        """
        # Read options for compoonent
        copts = self.get(comp, {})
        # Get global option
        compID = self.get("ConfigCompID")
        # Get component-specific option
        return copts.get("ConfigCompID", compID)
  # >
  
  # =======
  # Targets
  # =======
  # <
    # Get the targets
    def get_DataBookTargets(self):
        """Get the list of targets to be used for the data book
        
        :Call:
            >>> targets = opts.get_DataBookTargets()
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
        :Outputs:
            *targets*: :class:`dict`\ [:class:`dict`]
                Dictionary of targets
        :Versions:
            * 2014-12-20 ``@ddalle``: Version 1.0
        """
        # Output
        return self.get('Targets', {})
        
    # Get a target by name
    def get_DataBookTargetByName(self, targ):
        """Get a data book target option set by the name of the target
        
        :Call:
            >>> topts = opts.get_DataBookTargetByName(targ)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *targ*: :class:`str`
                Name of the data book target
        :Outputs:
            * 2015-12-15 ``@ddalle``: Version 1.0
        """
        # Get the set of targets
        DBTs = self.get_DataBookTargets()
        # Check if it's present
        if targ not in DBTs:
            raise KeyError("There is no DBTarget called '%s'" % targ)
        # Output
        return DBTs[targ]
    
    # Get type for a given target
    def get_DataBookTargetType(self, targ):
        """Get the target data book type
        
        This can be either a generic target specified in a single file or a Cape
        data book that has the same description as the present data book
        
        :Call:
            >>> typ = opts.get_DataBookTargetType(targ)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *targ*: :class:`str`
                Name of the data book target
        :Outputs:
            *typ*: {``"generic"``} | ``"cape"``
                Target type, generic CSV file or duplicate data book
        :Versions:
            * 2016-06-27 ``@ddalle``: Version 1.0
        """
        # Get the set of targets
        DBTs = self.get_DataBookTargets()
        # Check if it's present
        if targ not in DBTs:
            raise KeyError("There is no DBTarget called '%s'" % targ)
        # Get the type
        return DBTs[targ].get('Type', 'generic')
        
    # Get data book target directory
    def get_DataBookTargetDir(self, targ):
        """Get the folder for a data book duplicate target
        
        :Call:
            >>> fdir = opts.get_DataBookTargetDir(targ)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *targ*: :class:`str`
                Name of the data book target
        :Outputs:
            *typ*: {``"generic"``} | ``"cape"``
                Target type, generic CSV file or duplicate data book
        :Versions:
            * 2016-06-27 ``@ddalle``: Version 1.0
        """
        # Get the set of targets
        DBTs = self.get_DataBookTargets()
        # Check if it's present
        if targ not in DBTs:
            raise KeyError("There is no DBTarget called '%s'" % targ)
        # Get the type
        return DBTs[targ].get('Folder', 'data')
  # >
  
  # ================
  # Component Config
  # ================
  # <
    # Get data book components by type
    def get_DataBookByType(self, typ):
        """Get the list of data book components with a given type
        
        :Call:
            >>> comps = opts.get_DataBookByType(typ)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *typ*: ``"Force"`` | ``"FM"`` | ``"LineLoad"`` | :class:`str`
                Data book type
        :Outputs:
            *comps*: :class:`list`\ [:class:`str`]
                List of data book components with ``"Type"`` matching *typ*
        :Versions:
            * 2016-06-07 ``@ddalle``: Version 1.0
        """
        # Initialize components
        comps = []
        # Get list of types
        for comp in self.get_DataBookComponents():
            # Check the type
            if typ == self.get_DataBookType(comp):
                # Append the component to the list
                comps.append(comp)
        # Output
        return comps
        
    # Get list of components matching a type and list of wild cards
    def get_DataBookByGlob(self, typ, comp=None):
        """Get list of components by type and list of wild cards
        
        :Call:
            >>> comps = opts.get_DataBookByGlob(typ, comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *typ*: FM | Force | Moment | LineLoad | TriqFM
                Data book type
            *comp*: {``None``} | :class:`str`
                List of component wild cards, separated by commas
        :Outputs:
            *comps*: :class:`str`
                All components meeting one or more wild cards
        :Versions:
            * 2017-04-25 ``@ddalle``: Version 1.0
        """
        # Check for list of types
        if type(typ).__name__ not in ['ndarray', 'list']:
            # Ensure list
            typ = [typ]
        # Get list of all components with matching type
        comps_all = []
        for t in typ:
            comps_all += self.get_DataBookByType(t)
        # Check for default option
        if comp in [True, None]:
            return comps_all
        # Initialize output
        comps = []
        # Ensure input is a list
        if type(comp).__name__ in ['list', 'ndarray']:
            comps_in = comp
        else:
            comps_in = [comp]
        # Initialize wild cards
        comps_wc = []
        # Split by comma
        for c in comps_in:
            comps_wc += c.split(",")
        # Loop through components to check if it matches
        for c in comps_all:
            # Loop through components
            for pat in comps_wc:
                # Check if it matches
                if fnmatch.fnmatch(c, pat):
                    # Add the component to the list
                    comps.append(c)
                    break
        # Output
        return comps
            
    # Get the data type of a specific component
    def get_DataBookType(self, comp):
        """Get the type of data book entry for one component
        
        :Call:
            >>> ctype = opts.get_DataBookType(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of component
        :Outputs:
            *ctype*: {Force} | Moment | FM | PointSensor | LineLoad
                Data book entry type
        :Versions:
            * 2015-12-14 ``@ddalle``: Version 1.0
        """
        # Get the component options.
        copts = self.get(comp, {})
        # Return the type
        return copts.get("Type", "FM")
        
    # Get list of components in a component
    def get_DataBookCompID(self, comp):
        """Get list of components in a data book component
        
        :Call:
            >>> compID = opts.get_DataBookCompID(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of data book component/field
        :Outputs:
            *compID*: :class:`str` | :class:`int` | :class:`list`
                Component or list of components to which this DB applies
        :Versions:
            * 2016-06-07 ``@ddalle``: Version 1.0
        """
        # Get the options for that component
        copts = self.get(comp, {})
        # Get the componetns
        return copts.get('CompID', comp)
        
    # Get the coefficients for a specific component
    def get_DataBookCoeffs(self, comp):
        """Get the list of data book coefficients for a specific component
        
        :Call:
            >>> coeffs = opts.get_DataBookCoeffs(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of component
        :Outputs:
            *coeffs*: :class:`list`\ [:class:`str`]
                List of coefficients for that component
        :Versions:
            * 2014-12-21 ``@ddalle``: Version 1.0
        """
        # Get the component options.
        copts = self.get(comp, {})
        # Check for manually-specified coefficients
        coeffs = copts.get("Cols", self.get("Coefficients", []))
        # Check the type.
        if not isinstance(coeffs, list):
            raise TypeError(
                "Coefficients for component '%s' must be a list." % comp)
        # Exit if that exists.
        if len(coeffs) > 0:
            return coeffs
        # Check the type.
        ctype = self.get_DataBookType(comp)
        # Default coefficients
        if ctype in ["Force", "force"]:
            # Force only, body-frame
            coeffs = ["CA", "CY", "CN"]
        elif ctype in ["Moment", "moment"]:
            # Moment only, body-frame
            coeffs = ["CLL", "CLM", "CLN"]
        elif ctype in ["DataFM", "FM", "full", "Full"]:
            # Force and moment
            coeffs = ["CA", "CY", "CN", "CLL", "CLM", "CLN"]
        elif ctype in ["TriqFM"]:
            # Extracted force and moment
            coeffs = [
                "CA",  "CY",  "CN", 
                "CAv", "CYv", "CNv",
                "Cp_min", "Cp_max",
                "Ax", "Ay", "Az"
            ]
        elif ctype in ["PointSensor", "TriqPoint"]:
            # Default to list of points for a point sensor
            coeffs = ["x", "y", "z", "cp"]
        # Output
        return coeffs
        
    # Get coefficients for a specific component/coeff
    def get_DataBookCoeffStats(self, comp, coeff):
        """Get the list of statistical properties for a specific coefficient
        
        :Call:
            >>> sts = opts.get_DataBookCoeffStats(comp, coeff)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of data book component
            *coeff*: :class:`str`
                Name of data book coefficient, e.g. "CA", "CY", etc.
        :Outputs:
            *sts*: :class:`list` (mu | std | min | max | err)
                List of statistical properties for this coefficient
        :Versions:
            * 2016-03-15 ``@ddalle``: Version 1.0
        """
        # Get the component options
        copts = self.get(comp, {})
        # Get the coefficient
        sts = copts.get(coeff)
        # Get type
        typ = self.get_DataBookType(comp)
        # Process default if necessary
        if sts is not None:
            # Non-default; check the type
            if type(sts).__name__ not in ['list', 'ndarray']:
                raise TypeError(
                    "List of statistical properties must be a list")
            # Output
            return sts
        # Data book type
        typ = self.get_DataBookType(comp)
        # Check data book type
        if typ in ["TriqFM", "TriqPoint", "PointSensor"]:
            # No iterative history
            return ['mu']
        # Others; iterative history available
        if coeff in ['x', 'y', 'z', 'X', 'Y', 'Z']:
            # Coordinates
            return ['mu']
        elif coeff in ['CA', 'CY', 'CN', 'CLL', 'CLM', 'CLN']:
            # Body-frame force/moment
            return ['mu', 'min', 'max', 'std', 'err']
        elif coeff in ['CL', 'CN', 'CS']:
            # Stability-frame force/moment
            return ['mu', 'min', 'max', 'std', 'err']
        elif typ in ["PyFunc"]:
            return ["mu"]
        else:
            # Default for most states
            return ['mu', 'std', 'min', 'max']
        
    # Get additional float columns
    def get_DataBookFloatCols(self, comp):
        """Get additional numeric columns for component (other than coeffs)
        
        :Call:
            >>> fcols = opts.get_DataBookFloatCols(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of data book component
        :Outputs:
            *fcols*: :class:`list`\ [:class:`str`]
                List of additional float columns
        :Versions:
            * 2016-03-15 ``@ddalle``: Version 1.0
        """
        # Get the component options
        copts = self.get(comp, {})
        # Get data book default
        fcols_db = self.get("FloatCols")
        # Get float columns option
        fcols = copts.get("FloatCols")
        # Check for default
        if fcols is not None:
            # Manual option
            return fcols
        elif fcols_db is not None:
            # Data book option
            return fcols_db
        else:
            # Global default
            return []
            
    # Get integer columns
    def get_DataBookIntCols(self, comp):
        """Get integer columns for component
        
        :Call:
            >>> fcols = opts.get_DataBookFloatCols(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of data book component
        :Outputs:
            *fcols*: :class:`list`\ [:class:`str`]
                List of additional float columns
        :Versions:
            * 2016-03-15 ``@ddalle``: Version 1.0
        """
        # Get the component options
        copts = self.get(comp, {})
        # Get type
        ctyp = self.get_DataBookType(comp)
        # Get data book default
        icols_db = self.get("IntCols")
        # Get float columns option
        icols = copts.get("IntCols")
        # Check for default
        if icols is not None:
            # Manual option
            return icols
        elif icols_db is not None:
            # Data book option
            return icols_db
        elif ctyp in ["TriqPoint", "PointSensor", "PyFunc"]:
            # Limited default
            return ['nIter']
        else:
            # Global default
            return ['nIter', 'nStats']
        
    # Get full list of columns for a specific component
    def get_DataBookCols(self, comp):
        """Get the full list of data book columns for a specific component
        
        This includes the list of coefficients, e.g. ``['CA', 'CY', 'CN']``;
        statistics such as ``'CA_min'`` if *nStats* is greater than 0; and
        targets such as ``'CA_t'`` if there is a target for *CA*.
        
        :Call:
            >>> cols = opts.get_DataBookCols(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of component
        :Outputs:
            *cols*: :class:`list`\ [:class:`str`]
                List of coefficients and other columns for that coefficient
        :Versions:
            * 2014-12-21 ``@ddalle``: Version 1.0
        """
        # Data columns (from CFD)
        dcols = self.get_DataBookDataCols(comp)
        # Output
        return dcols
        
    # Get full list of data columns for a specific component
    def get_DataBookDataCols(self, comp):
        """Get the list of data book columns for a specific component
        
        This includes the list of coefficients, e.g. ``['CA', 'CY', 'CN']``;
        statistics such as ``'CA_min'`` if *nStats* is greater than 0.
        
        :Call:
            >>> cols = opts.get_DataBookDataCols(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of component
        :Outputs:
            *cols*: :class:`list`\ [:class:`str`]
                List of coefficients and other columns for that coefficient
        :Versions:
            * 2014-12-21 ``@ddalle``: Version 1.0
            * 2022-04-08 ``@ddalle``: Version 2.0; cooeff-spec suffixes
        """
        # Get the list of coefficients.
        coeffs = self.get_DataBookCoeffs(comp)
        # Initialize output
        cols = [] + coeffs
        # Get the number of iterations used for statistics
        nStats = self.get_nStats()
        # Process statistical columns.
        if nStats > 0:
            # Loop through columns.
            for coeff in coeffs:
                # Get stat cols for this coeff
                scols = self.get_DataBookCoeffStats(comp, coeff)
                # Don't double-count the mean
                if "mu" in scols:
                    scols.remove("mu")
                # Append all statistical columns.
                cols += [coeff + "_" + suf for suf in scols]
        # Output.
        return cols
        
    # Get list of target data columns for a specific component
    def get_DataBookTargetCols(self, comp):
        """Get the list of data book target columns for a specific component
        
        :Call:
            >>> cols = opts.get_DataBookDataCols(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of component
        :Outputs:
            *cols*: :class:`list`\ [:class:`str`]
                List of coefficient target values
        :Versions:
            * 2014-12-21 ``@ddalle``: Version 1.0
        """
        # Initialize output
        cols = []
        # Process targets.
        targs = self.get_CompTargets(comp)
        # Loop through the targets.
        for c in targs:
            # Append target column
            cols.append(c+'_t')
        # Output
        return cols
  # >
  
  
  # =============
  # Point Sensors
  # =============
  # <
    # Get data book subcomponents
    def get_DataBookPoints(self, comp):
        """Get the data book subcomponent for one target
        
        For example, for "PointSensor" targets will return the list of points
        
        :Call:
            >>> pts = opts.get_DataBookPoints(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of data book component
        :Outputs:
            *pts*: :class:`list`\ [:class:`str`]
                List of subcomponents
        :Versions:
            * 2015-12-14 ``@ddalle``: Version 1.0
        """
        # Get component
        copts = self.get(comp, {})
        # Get the type
        ctype = copts.get("Type", "Force")
        # Check the type
        if ctype in ["PointSensor", "TriqPoint"]:
            # Check the point
            return copts.get("Points", [])
        else:
            # Otherwise, no subcomponents
            return []
  # >
  
  # ======================
  # Iterative Force/Moment
  # ======================
  # <
        
    # Get the transformations for a specific component
    def get_DataBookTransformations(self, comp):
        """
        Get the transformations required to transform a component's data book
        into the body frame of that component.
        
        :Call:
            >>> tlist = opts.get_DataBookTransformations(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of component
        :Outputs:
            *tlist*: :class:`list`\ [:class:`dict`]
                List of targets for that component
        :Versions:
            * 2014-12-22 ``@ddalle``: Version 1.0
        """
        # Get the options for the component.
        copts = self.get(comp, {})
        # Get the value specified, defaulting to an empty list.
        tlist = copts.get('Transformations', [])
        # Make sure it's a list.
        if type(tlist).__name__ not in ['list', 'ndarray']:
            # Probably a single transformation; put it in a list
            tlist = [tlist]
        # Output
        return tlist
        
    # Get the tri file to use for mapping
    def get_DataBookMapTri(self, comp):
        """
        Get the name of a triangulation file to use for remapping ``triq``
        triangles to extract a component not defined in the ``triq`` file
        
        :Call:
            >>> ftri = opts.get_DataBookMapTri(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of component file
        :Outputs:
            *ftri*: {``None``} | :class:`str`
                Name of tri file relative to root directory
        :Versions:
            * 2017-03-05 ``@ddalle``: Version 1.0
        """
        # Get the options for the component
        copts = self.get(comp, {})
        # Global option
        ftri = self.get("MapTri")
        # Get the component-specific option
        ftri = copts.get("MapTri", ftri)
        # Output
        return ftri
        
    # Get the Config.xml file to use for mapping
    def get_DataBookMapConfig(self, comp):
        """
        Get the GMP XML file for mapping component IDs to names or interpreting
        the component names of a remapping TRI file
        
        :Call:
            >>> fcfg = opts.get_DataBookMapConfig(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of component file
        :Outputs:
            *fcfg*: {``None``} | :class:`str`
                Name of config XML or JSON file, if any
        :Versions:
            * 2017-03-05 ``@ddalle``: Version 1.0
        """
        # Get the options for the component
        copts = self.get(comp, {})
        # Global option
        fcfg = self.get("MapConfig")
        # Get the component-specific option
        fcfg = copts.get("MapConfig", fcfg)
        # Output
        return fcfg
        
    # Get the list of patches
    def get_DataBookPatches(self, comp):
        """
        Get list of patches for a databook component, usually for ``TriqFM``
        
        :Call:
            >>> fpatches = opts.get_DataBookPatches(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of component file
        :Outputs:
            *fpatches*: :class:`list`\ [:class:`str`]
                List of names of patches, if any
        :Versions:
            * 2017-03-28 ``@ddalle``: Version 1.0
        """
        # Get the options for the component
        copts = self.get(comp, {})
        # Get list of patches
        return copts.get("Patches", [])
    
  # >
      
  # ===========
  # Line Loads
  # ===========
  # <
    # Get the number of cuts
    def get_DataBook_nCut(self, comp):
        """Get the number of cuts to make for a sectional load group
        
        :Call:
            >>> nCut = opts.get_DataBook_nCut(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of line load group
        :Outputs:
            *nCut*: :class:`int`
                Number of cuts to include in line loads
        :Versions:
            * 2015-09-15 ``@ddalle``: Version 1.0
        """
        # Global data book setting
        db_nCut = self.get('nCut', rc0("db_nCut"))
        # Get component options
        copts = self.get(comp, {})
        # Get the extension
        return copts.get("nCut", db_nCut)
        
    # Get momentum setting
    def get_DataBookMomentum(self, comp):
        """Get 'Momentum' flag for a data book component
        
        :Call:
            >>> qm = opts.get_DataBookMomentum(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of component
        :Outputs:
            *qm*: ``True`` | {``False``}
                Whether or not to include momentum
        :Versions:
            * 2016-06-07 ``@ddalle``: Version 1.0
        """
        # Global data book setting
        db_qm = self.get("Momentum", False)
        # Get component options
        copts = self.get(comp, {})
        # Get the local setting
        return copts.get("Momentum", db_qm)
        
    # Get guage pressure setting
    def get_DataBookGauge(self, comp):
        """Get 'Gauge' flag for a data book component
        
        :Call:
            >>> qg = opts.get_DataBookGauge(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of component
        :Outputs:
            *qg*: {``True``} | ``False``
                Option to use gauge forces (freestream pressure as reference)
        :Versions:
            * 2017-03-29 ``@ddalle``: Version 1.0
        """
        # Global data book setting
        db_qg = self.get("Gauge", True)
        # Get component options
        copts = self.get(comp, {})
        # Get the local setting
        return copts.get("Gauge", db_qg)
        
    # Get trim setting
    def get_DataBookTrim(self, comp):
        """Get 'Trim' flag for a data book component
        
        :Call:
            >>> iTrim = opts.get_DataBookTrim(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of component
        :Outputs:
            *iTrim*: ``0`` | {``1``}
                Trim setting; no output if ``None``
        :Versions:
            * 2016-06-07 ``@ddalle``: Version 1.0
        """
        # Global data book setting
        db_trim = self.get("Trim", 1)
        # Get component options
        copts = self.get(comp, {})
        # Get the local setting
        return copts.get("Trim", db_trim)
        
    # Get line load type
    def get_DataBookSectionType(self, comp):
        """Get line load section type
        
        :Call:
            >>> typ = opts.get_DataBookSectionType(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str`
                Name of component
        :Outputs:
            *typ*: {``"dlds"``} | ``"slds"`` | ``"clds"`` | :class:`str`
                Value of the ``"SectionType"`` option
        :Versions:
            * 2016-06-09 ``@ddalle``: Version 1.0
        """
        # Global data book setting
        db_o = self.get("SectionType", 'dlds')
        # Get component options
        copts = self.get(comp, {})
        # Get the local setting
        c_o = copts.get("SectionType", db_o).lower()
        # Convert if necessary
        if c_o == 'sectional':
            # Sectional
            return 'slds'
        elif c_o == 'cumulative':
            # Cumulative
            return 'clds'
        elif c_o == 'derivative':
            # Derivative
            return 'dlds'
        else:
            # Don't mess with the option
            return c_o
  # >
  
  # ==============================
  # Plotting (Possibly Deprecated)
  # ==============================
  # <
    # List of components to plot
    def get_PlotComponents(self):
        """Return the list of components to plot
        
        :Call:
            >>> comps = opts.get_PlotComponents()
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
        :Outputs:
            *comps*: :class:`list`\ [:class:`str` | :class:`int`]
                List of components (names or numbers) to plot
        :Versions:
            * 2014-11-22 ``@ddalle``: Version 1.0
        """
        # Get the value from the dictionary.
        comps = self.get('PlotComponents', ['entire'])
        # Make sure it's a list.
        if type(comps).__name__ not in ['list']:
            comps = [comps]
        # Check contents.
        for comp in comps:
            if (type(comp).__name__ not in ['str', 'int', 'unicode']):
                raise IOError("Component '%s' is not a str or int." % comp)
        # Output
        return comps
        
    # Set run input sequence.
    def set_PlotComponents(self, comps):
        """Set the list of components to plot
        
        :Call:
            >>> opts.set_PlotComponents(comps)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comps*: :class:`list`\ [:class:`str` | :class:`int`]
                List of components (names or numbers) to plot
        :Versions:
            * 2014-11-22 ``@ddalle``: Version 1.0
        """
        # Make sure it's a list.
        if type(comps).__name__ not in ['list']:
            comps = [comps]
        # Check contents.
        for comp in comps:
            if (type(comp).__name__ not in ['str', 'int', 'unicode']):
                raise IOError("Component '%s' is not a str or int." % comp)
        # Set the value.
        self.set_key('PlotComponents', comps)
        
    # Function to add to the list of components.
    def add_PlotComponents(self, comps):
        """Add to the list of components to plot
        
        :Call:
            >>> opts.add_PlotComponents(comps)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comps*: :class:`list`\ [:class:`str` | :class:`int`]
                List of components (names or numbers) to plot
        :Versions:
            * 2014-11-23 ``@ddalle``: Version 1.0
        """
        # Get the current list.
        comps_cur = self.get('Components', [])
        # Make sure it's a list.
        if type(comps_cur).__name__ not in ['list']:
            comps_cur = [comps_cur]
        # Check the type of the input.
        try:
            # Try it as a list first.
            comps_cur += comps
        except Exception:
            # Append it as a string/int.
            comps_cur.append(comps)
        # Set the value.
        self['Components'] = comps_cur
        
        
    # Function to get the coefficients to plot.
    def get_PlotCoeffs(self, comp=None):
        """Return the list of plot coefficients for a component
        
        This applies the default from the "Plot" section of the options, but
        this is superseded by specific exceptions.
        
        :Call:
            >>> coeffs = opts.get_PlotCoeffs(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str` or :class:`int`
                Name of component to plot
        :Outputs:
            *coeffs*: :class:`list`\ [:class:`str`]
                List of coefficients to plot
        :Versions:
            * 2014-11-22 ``@ddalle``: Version 1.0
        """
        # Get the value from the dictionary.
        coeffs = self.get('Coefficients', ['CA', 'CY', 'CN', 'L1'])
        # Check for a specific coefficient.
        if comp in self:
            # List from specific coefficient supersedes.
            coeffs = self[comp].get('Coefficients', coeffs)
        # Make sure it's a list.
        if type(coeffs).__name__ not in ['list']:
            coeffs = [coeffs]
        # Check contents.
        for coeff in coeffs:
            if coeff not in ['CA', 'CY', 'CN', 'CLL', 'CLM', 'CLN', 'L1',
                    'CAhist', 'CYhist', 'CNhist',
                    'CLLhist', 'CLMhist', 'CLNhist']:
                raise IOError("Coefficient '%s' not recognized." % coeff)
        # Output
        return coeffs
        
        
    # Function to get the number of iterations
    def get_nPlotIter(self, comp=None):
        """Return the number of iterations to plot for a component
        
        If there are fewer than *nPlot* iterations in the current history, all
        iterations will be plotted.
        
        :Call:
            >>> nPlot = opts.get_nPlotIter(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str` or :class:`int`
                Name of component to plot
        :Outputs:
            *nPlot*: :class:`int`
                Number of iterations to plot (maximum)
        :Versions:
            * 2014-11-23 ``@ddalle``: Version 1.0
        """
        # Get the default.
        nPlot = self.get('nPlot')
        # Check for specific component.
        if comp in self:
            # Value supersedes
            nPlot = self[comp].get('nPlot', nPlot)
        # Output
        return nPlot
        
    # Function to get the last iteration to plot
    def get_nPlotLast(self, comp=None):
        """Return the last iteration to plot
        
        :Call:
            >>> nLast = opts.get_nPlotLast(comp)
        :Inptus:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str` or :class:`int`
                Name of component to plot
        :Outputs:
            *nLast*: :class:`int`
                Last iteration to plot for coefficient plots
        :Versions:
            * 2015-03-04 ``@ddalle``: Version 1.0
        """
        # Get the default.
        nLast = self.get('nLast')
        # Check for specific component.
        if comp in self:
            # Value supersedes
            nLast = self[comp].get('nLast', nLast)
        # Output
        return nLast
        
    # Function to get the first iteration to plot
    def get_nPlotFirst(self, comp=None):
        """Return the first iteration to plot in coefficient plots
        
        :Call:
            >>> nFirst = opts.get_nPlotFirst(comp)
        :Inptus:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str` or :class:`int`
                Name of component to plot
        :Outputs:
            *nFirst*: :class:`int`
                First iteration to plot for coefficient plots
        :Versions:
            * 2015-03-04 ``@ddalle``: Version 1.0
        """
        # Get the default.
        nFirst = self.get('nFirst')
        # Check for specific component.
        if comp in self:
            # Value supersedes
            nFirst = self[comp].get('nFirst', nFirst)
        # Output
        return nFirst
        
    # Function to get the number of iterations for averaging
    def get_nAverage(self, comp=None):
        """Return the number of iterations to use for averaging
        
        If there are fewer than *nAvg* iterations in the current history, all
        iterations will be plotted.
        
        :Call:
            >>> nAvg = opts.get_nAverage()
            >>> nAvg = opts.get_nAverage(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str` or :class:`int`
                Name of component to plot
        :Outputs:
            *nAvg*: :class:`int`
                Number of iterations to use for averaging
        :Versions:
            * 2014-11-23 ``@ddalle``: Version 1.0
        """
        # Get the default.
        nAvg = self.get('nAverage', rc0('nAvg'))
        # Check for specific component to supersede.
        if comp in self:
            nAvg = self[comp].get('nAverage', nAvg)
        # Output
        return nAvg
        
    # Function to get the number of rows of plots
    def get_nPlotRows(self, comp=None):
        """Return the number of rows to use in plots
        
        :Call:
            >>> nRow = opts.get_nPlotRows()
            >>> nRow = opts.get_nPlotRows(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str` or :class:`int`
                Name of component to plot
        :Outputs:
            *nRow*: :class:`int`
                Number of rows of plots
        :Versions:
            * 2014-11-23 ``@ddalle``: Version 1.0
        """
        # Get the default.
        nRow = self.get('nRow', rc0('nRow'))
        # Check for specific component to supersede
        if comp in self:
            nRow = self[comp].get('nRow', nRow)
        # Output
        return nRow
        
    # Function to get the number of columns of plots
    def get_nPlotCols(self, comp=None):
        """Return the number of columns to use in plots
        
        :Call:
            >>> nCol = opts.get_nPlotCols()
            >>> nCol = opts.get_nPlotCols(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str` or :class:`int`
                Name of component to plot
        :Outputs:
            *nCol*: :class:`int`
                Number of columns of plots
        :Versions:
            * 2014-11-23 ``@ddalle``: Version 1.0
        """
        # Get the default.
        nCol = self.get('nCol', rc0('nCol'))
        # Check for specific component to supersede
        if comp in self:
            nCol = self[comp].get('nCol', nCol)
        # Output            
        return nCol
        
    # Function to get the number of columns of plots
    def get_PlotRestriction(self, comp=None):
        """Return the number of columns to use in plots
        
        :Call:
            >>> sTag = opts.get_nPlotRestriction()
            >>> sTag = opts.get_nPlotRestriction(comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str` or :class:`int`
                Name of component to plot
        :Outputs:
            *sTag*: :
                Number of columns of plots
        :Versions:
            * 2014-11-23 ``@ddalle``: Version 1.0
        """
        # Get the default.
        sTag = self.get('Restriction', '')
        # Check for specific component to supersede
        if comp in self:
            sTag = self[comp].get('Restriction', sTag)
        # Output
        return sTag
        
    # Function to get the delta for a given comp and coeff
    def get_PlotDelta(self, coeff, comp=None):
        """
        Get the fixed-width interval to plot above and below the mean for a
        specific component and coefficient
        
        :Call:
            >>> dC = opts.get_PlotDelta(coeff, comp)
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
            *comp*: :class:`str` or :class:`int`
                Name of component to plot
            *coeff*: :class:`str`
                Name of coefficient 
        :Outputs:
            *dC*: :class:`float` or ``None``
                Offset to plot from mean with dotted line
        :Versions:
            * 2014-11-23 ``@ddalle``: Version 1.0
        """
        # Check for recognized coefficient
        if coeff not in ['CA','CY','CN','CLL','CLM','CLN']:
            # Null output
            return None
        # Check for a hard default
        dC = self.get('d'+coeff, rc0('dC'))
        # Get the list of Deltas
        Deltas = self.get('Deltas', {})
        # Process the correct universal value.
        dC = Deltas.get(coeff, dC)
        # Check for component-specific information
        if comp not in self: return dC
        # Check for hard value for the component.
        dC = self[comp].get('d'+coeff, dC)
        # Check for dictionary
        Deltas = self[comp].get('Deltas', {})
        # Get the value from that dictionary.
        dC = Deltas.get(coeff, dC)
        # Output
        return dC
                
    # Plot figure width
    def get_PlotFigWidth(self):
        """Get the figure width for plot
        
        :Call:
            >>> w = opts.get_PlotFigWidth()
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
        :Outputs:
            *w*: :class:`float`
                Figure width
        :Versions:
            * 2015-03-09 ``@ddalle``: Version 1.0
        """
        # Get the width.
        return self.get('FigWidth', rc0('FigWidth'))
                
    # Plot figure height
    def get_PlotFigHeight(self):
        """Get the figure height for plot
        
        :Call:
            >>> h = opts.get_PlotFigHeight()
        :Inputs:
            *opts*: :class:`cape.cfdx.options.Options`
                Options interface
        :Outputs:
            *h*: :class:`float`
                Figure height
        :Versions:
            * 2015-03-09 ``@ddalle``: Version 1.0
        """
        # Get the width.
        return self.get('FigHeight', rc0('FigHeight'))
  # >
# class DataBook        
            
            
# Class for target data
class DBTarget(odict):
    """Dictionary-based interface for data book targets
    
    :Call:
        >>> opts = DBTarget(**kw)
    :Inputs:
        *kw*: :class:`dict`
            Dictionary of PBS options
    :Outputs:
        *opts*: :class:`cape.options.DataBook.DBTarget`
            Data book target options interface
    :Versions:
        * 2014-12-01 ``@ddalle``: Version 1.0
    """
    
    # Get the maximum number of refinements
    def get_TargetName(self):
        """Get the name/identifier for a given data book target
        
        :Call:
            >>> Name = opts.get_TargetName()
        :Inputs:
            *opts*: :class:`cape.options.DataBook.DBTarget`
                Options interface
        :Outputs:
            *Name*: :class:`str`
                Identifier for the target
        :Versions:
            * 2014-08-03 ``@ddalle``: Version 1.0
        """
        return self.get('Name', 'Target')
        
    # Get the label
    def get_TargetLabel(self):
        """Get the name/identifier for a given data book target
        
        :Call:
            >>> lbl = opts.get_TargetLabel()
        :Inputs:
            *opts*: :class:`cape.options.DataBook.DBTarget`
                Options interface
        :Outputs:
            *lbl*: :class:`str`
                Label for the data book target to be used in plots and reports 
        :Versions:
            * 2015-06-04 ``@ddalle``: Version 1.0
        """
        # Default to target identifier
        return self.get('Label', self.get_TargetName())
        
    # Get the components that this target describes
    def get_TargetComponents(self):
        """Get the list of components described by this component
        
        Returning ``None`` is a flag to use all components from the data book.
        
        :Call:
            >>> comps = opts.get_TargetComponents()
        :Inputs:
            *opts*: :class:`cape.options.DataBook.DBTarget`
                Options interface
        :Outputs:
            *comps*: :class:`list`\ [:class:`str`]
                List of components (``None`` if not specified)
        :Versions:
            * 2015-06-03 ``@ddalle``: Version 1.0
        """
        # Get the list
        comps = self.get('Components')
        # Check type.
        if type(comps).__name__ in ['str', 'unicode']:
            # String: make it a list.
            return [comps]
        else:
            # List, ``None``, or nonsense
            return comps
        
    # Get the file name
    def get_TargetFile(self):
        """Get the file name for the target
        
        :Call:
            >>> fname = opts.get_TargetFile()
        :Inputs:
            *opts*: :class:`cape.options.DataBook.DBTarget`
                Options interface
        :Outputs:
            *fname*: :class:`str`
                Name of the file
        :Versions:
            * 2014-12-20 ``@ddalle``: Version 1.0
        """
        return self.get('File', 'Target.dat')
        
    # Get the directory name
    def get_TargetDir(self):
        """Get the directory for the duplicate target data book
        
        :Call:
            >>> fdir = opts.get_TargetDir()
        :Inputs:
            *opts*: :class:`cape.options.DataBook.DBTarget`
                Options interface
        :Outputs:
            *fdir*: :class:`str`
                Name of the directory (relative to root directory)
        :Versions:
            * 2016-06-27 ``@ddalle``: Version 1.0
        """
        return self.get('Folder', 'data')
        
    # Get the target type
    def get_TargetType(self):
        """Get the target type for a target data book
        
        :Call:
            >>> typ = opts.get_TargetType()
        :Inputs:
            *opts*: :class:`cape.otpions.DataBook.DBTarget`
                Options interface
        :Outputs:
            *typ*: {``"generic"``} | ``"cape"``
                Target type, generic CSV file or duplicate data book
        :Versions:
            * 2016-06-27 ``@ddalle``: Version 1.0
        """
        return self.get('Type', 'generic')
        
    # Get tolerance
    def get_Tol(self, xk):
        """Get the tolerance for a particular trajectory key
        
        :Call:
            >>> tol = opts.get_Tol(xk)
        :Inputs:
            *opts*: :class:`cape.options.DataBook.DBTarget`
                Options interface
            *xk*: :class:`str`
                Name of trajectory key
        :Outputs:
            *tol*: :class:`float`
                Tolerance to consider as matching value for a trajectory key
        :Versions:
            * 2015-12-16 ``@ddalle``: Version 1.0
        """
        # Get tolerance option set
        tolopts = self.get("Tolerances", {})
        # Get the option specific to this key
        return tolopts.get(xk, None)
        
    # Get the delimiter
    def get_Delimiter(self):
        """Get the delimiter for a target file
        
        :Call:
            >>> delim = opts.get_Delimiter()
        :Inputs:
            *opts*: :class:`cape.options.DataBook.DBTarget`
                Options interface
        :Outputs:
            *delim*: :class:`str`
                Delimiter text
        :Versions:
            * 2014-12-21 ``@ddalle``: Version 1.0
        """
        return self.get('Delimiter', rc0('Delimiter'))
        
    # Get the comment character.
    def get_CommentChar(self):
        """Get the character to used to mark comments
        
        :Call:
            >>> comchar = opts.get_CommentChar()
        :Inputs:
            *opts*: :class:`cape.options.DataBook.DBTarget`
                Options interface
        :Outputs:
            *comchar*: :class:`str`
                Comment character (may be multiple characters)
        :Versions:
            * 2014-12-21 ``@ddalle``: Version 1.0
        """
        return self.get('Comment', '#')
    
    # Get trajectory conversion
    def get_RunMatrix(self):
        """Get the trajectory translations
        
        :Call:
            >>> traj = opts.get_RunMatrix()
        :Inputs:
            *opts*: :class:`cape.options.DataBook.DBTarget`
                Options interface
        :Outputs:
            *comchar*: :class:`str`
                Comment character (may be multiple characters)
        :Versions:
            * 2014-12-21 ``@ddalle``: Version 1.0
        """
        return self.get('RunMatrix', {})    
# class DBTarget


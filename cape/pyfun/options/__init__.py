r"""
:mod:`cape.pyfun.options`: FUN3D options interface module
==========================================================

This module provides the options interface for :mod:`cape.pyfun`. Many
settings are inherited from :mod:`cape.cfdx.options`, and there are
some additional options specific to FUN3D for pyfun.

:See also:
    * :mod:`cape.cfdx.options`

"""

# Local imports
from . import util
from .runctlopts import RunControlOpts
from .databookopts import DataBookOpts
from .meshopts import MeshOpts
from .configopts import ConfigOpts
from .functionalopts import FunctionalOpts
from .fun3dnmlopts import (
    Fun3DNmlOpts,
    DualFun3DNmlOpts,
    MovingBodyFun3DNmlOpts)
from ...cfdx import options


# Class definition
class Options(options.Options):
    r"""Options interface for :mod:`cape.pyfun`

    :Call:
        >>> opts = Options(fname=None, **kw)
    :Inputs:
        *fname*: :class:`str`
            File to be read as a JSON file with comments
        *kw*: :class:`dict`
            Dictionary to be transformed into :class:`pyCart.options.Options`
    :Versions:
        * 2014-07-28 ``@ddalle``: Version 1.0
    """
   # ================
   # Class attributes
   # ================
   # <
    # Additional attributes
    __slots__ = ()

    # Additional options
    _optlist = {
        "DualFun3D",
        "Fun3D",
        "Fun3DNamelist",
        "Functional",
        "MovingBodyInput",
        "NamelistFunction",
        "RubberDataFile",
    }

    # Aliases
    _optmap = {
        "Namelist": "Fun3DNamelist",
        "RubberData": "RubberDataFile",
    }

    # Known option types
    _opttypes = {
        "Fun3DNamelist": str,
        "NamelistFunction": str,
        "RubberDataFile": str,
    }

    # Option default list depth
    _optlistdepth = {
        "NamelistFunction": 1,
    }

    # Defaults
    _rc = {
        "Fun3DNamelist": "fun3d.nml",
        "RubberDataFile": "rubber.data",
    }

    # Descriptions for methods
    _rst_descriptions = {
        "Fun3DNamelist": "template ``fun3d.nml`` file",
        "RubberDataFile": "template ``rubber.data`` file",
    }

    # New or replaced sections
    _sec_cls = {
        "Config": ConfigOpts,
        "DataBook": DataBookOpts,
        "DualFun3D": DualFun3DNmlOpts,
        "Fun3D": Fun3DNmlOpts,
        "Functional": FunctionalOpts,
        "Mesh": MeshOpts,
        "MovingBodyInput": MovingBodyFun3DNmlOpts,
        "Report": options.ReportOpts,
        "RunControl": RunControlOpts,
    }
   # >

   # =============
   # Configuration
   # =============
   # <
    # Initialization hook
    def init_post(self):
        r"""Initialization hook for :class:`Options`

        :Call:
            >>> opts.init_post()
        :Inputs:
            *opts*: :class:`Options`
                Options interface
        :Versions:
            * 2022-10-23 ``@ddalle``: Version 1.0
        """
        # Read the defaults
        defs = util.getPyFunDefaults()
        # Apply the defaults
        self = util.applyDefaults(self, defs)
        # Add extra folders to path.
        self.AddPythonPath()
   # >


# Add properties
Options.add_properties(
    (
        "Fun3DNamelist",
    ))
# Add methods from subsections
Options.promote_sections()

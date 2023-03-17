"""
:mod:`cape.pyfun.options.Mesh`: FUN3D Meshing Options
======================================================

This module provides options for surface and  volume meshes in FUN3D.  This
consists of three parts, although the second or third option (but never both)
may be optional depending of the configuration 

    * Provides the name of the FUN3D ``.mapbc`` file using the option 
      *BCFile*.  This specifies the FUN3D boundary condition for each surface
      component
      
    * Specifies the name of a volume mesh, *MeshFile* (which can also be grown
      from the surface using AFLR3)
      
    * Specifies a surface triangulation either for creating a volume mesh with
      AFLR3 and/or providing a surface for thrust BC definitions
  
The FUN3D version also provides options for *Faux* and *Freeze* (or point to an
external one) in combination with mesh adaptation.

:See Also:
    * :mod:`cape.cfdx.options.Mesh`
    * :mod:`cape.cfdx.options.aflr3`
    * :mod:`cape.pyfun.options.runControl`
    * :mod:`cape.pyfun.options.Config`
"""

# Import options-specific utilities
from .util import rc0, odict
# Import Cape template
import cape.cfdx.options.Mesh


# Class for FUN3D mesh settings
class Mesh(cape.cfdx.options.Mesh):
    """Dictionary-based interface for FUN3D meshing options"""
        
    # Get the surface BC map
    def get_MapBCFile(self, i=None):
        """Return the name of the boundary condition map file
        
        :Call:
            >>> fname = opts.get_MapBCFile(i=None)
        :Inputs:
            *opts*: :class:`pyFun.options.Options`
                Options interface
            *i*: :class:`int`
                Phase index
        :Outputs:
            *fname*: :class:`str`
                Boundary condition file name
        :Versions:
            * 2016-03-29 ``@ddalle``: First version
        """
        return self.get_key('BCFile', i)
        
    # Get the "faux_input" file
    def get_FauxFile(self, i=None):
        """Get the ``faux_input`` file if specified
        
        This reads the ``"Mesh"`` > ``"FauxFile"`` option
        
        :Call:
            >>> fname = opts.get_FauxFile(i=None)
        :Inputs:
            *opts*: :class:`pyFun.options.Options`
                Options interface
            *i*: {``None``} | :class:`int`
                Phase number
        :Outputs:
            *fname*: ``None`` | :class:`str`
                Faux geometry file
        :Versions:
            * 2017-02-23 ``@ddalle``: First version
        """
        return self.get_key("FauxFile", i)
        
    # Get the "freeze" input file
    def get_FreezeFile(self, i=None):
        """Get the file that lists component IDs to freeze during adaptation
        
        This reads the ``"Mesh"`` > ``"FreezeFile"`` option
        
        :Call:
            >>> fname = opts.get_FreezeFile(i=None)
        :Inputs:
            *opts*: :class:`pyFun.options.Options`
                Options interface
            *i*: {``None``} | :class:`int`
                Phase number
        :Outputs:
            *fname*: ``None`` | :class:`str`
                Faux geometry file
        :Versions:
            * 2017-02-23 ``@ddalle``: First version
        """
        return self.get_key("FreezeFile", i)
    
    # Get list of components to freeze
    def get_FreezeComponents(self):
        """Get the list of components to freeze during adaptation
        
        This reads the ``"Mesh"`` > ``"FreezeComponents"`` option
        
        :Call:
            >>> comps  = opts.get_FreezeComponents()
        :Inputs:
            *opts*: :class:`pyFun.options.Options`
                Options interface
        :Outputs:
            *comps*: :class:`list` (:class:`int` | :class:`str`)
                List of face numbers or face names (using ``mapbc`` lookup)
        :Versions:
            * 2017-02-23 ``@ddalle``: First version
        """
        return self.get("FreezeComponents", [])
        
    # Get faux geometry for a component
    def get_Faux(self, comp=None):
        """Get the geometry information for ``faux_input`` for a component
        
        :Call:
            >>> faux = opts.get_Faux(comp=None)
        :Inputs:
            *opts*: :class:`pyFun.options.Options`
                Options interface
            *comp*: {``None``} | :class:`str`
                Name or number of component to process (all if ``None``)
        :Outputs:
            *faux*: :class:`dict` (:class:`float` | :class:`list`)
                ``faux_input`` plane definition(s)
        :Versions:
            * 2017-02-23 ``@ddalle``: First version
        """
        # Get full dictionary of faux geometry
        faux = self.get("Faux", {})
        # Check if seeking a single component
        if comp is None:
            # Return full set of instructions
            return faux
        else:
            # Return component instructions
            return faux[comp]
# class Mesh


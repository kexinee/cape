"""
:mod:`cape.pyus.runmatrix`: US3D run matrix module 
==================================================

This module handles classes and methods that are specific to the list of run
cases (i.e., the "trajectory").  It is defined in the ``"RunMatrix"`` section
of the master JSON file (e.g. :file:`pyUS.json`), and is usually read from a
modified comma-separated or space-separated text file.

The primary FUN3D state variables are Mach number, angle of attack, and
sidelsip.  To this it is common practice to add a ``"config"`` variable (which
sets the name of the group folder) and a ``"Label"`` which can be used to give
an extension to the name of a case.  A run matrix using only these variables
could be defined as follows.

    .. code-block:: javascript
    
        "RunMatrix": {
            "Keys": ["mach", "alpha", "beta", "q", "T", "config", "Label"],
            "File": "inputs/matrix.csv"
        }
        
Then the matrix file :file:`inputs/matrix.csv` could have contents such as the
following.

    .. code-block:: none
    
        # mach, alpha, beta, q, T, config, Label 
        0.8, 0.0, 0.0, 480.00, 425.7, ascent,
        1.2, 2.0, 0.0, 550.00, 425.7, ascent, a

Then the following example API commands could be used to show the case names.
In this case *fun3d* is the interface to a FUN3D run configuration read from
a JSON file, and *fun3d.x* is the run matrix.

    .. code-block:: pycon
    
        >>> import cape.pyus
        >>> cntl = pyUS.Cntl("pyUS.json")
        >>> cntl.x.GetFullFolderNames()
        ['ascent/m0.8a0.0b0.0', 'ascent/m1.2a2.0b0.0_maxq']
        
For this module, there are no methods that are particular to FUN3D.  All
functionality is inherited from :class:`cape.runmatrix.RunMatrix`.

:See Also:
    * :mod:`cape.runmatrix`
    * :mod:`cape.pyus.fun3d`
"""

# Import the cape module.
from .. import runmatrix


# RunMatrix class
class RunMatrix(runmatrix.RunMatrix):
    r"""Interface to US3D run matrix
    
    :Call:
        >>> x = runmatrix.RunMatrix(**traj)
        >>> x = runmatrix.RunMatrix(File=fname, Keys=keys)
    :Inputs:
        *traj*: :class:`dict`
            Dictionary of options from ``fun3d.Options["RunMatrix"]``
    :Keyword arguments:
        *File*: :class:`str`
            Name of file to read, defaults to ``'RunMatrix.dat'``
        *Keys*: :class:`list` of :class:`str` items
            List of variable names, defaults to ``['Mach','alpha','beta']``
        *Prefix*: :class:`str`
            Prefix to be used for each case folder name
        *GroupPrefix*: :class:`str`
            Prefix to be used for each grid folder name
        *GroupMesh*: :class:`bool`
            Whether or not cases in same group can share volume grids
        *Definitions*: :class:`dict`
            Dictionary of definitions for each key
    :Outputs:
        *x*: :class:`pyUS.runmatrix.RunMatrix`
            Instance of the trajectory class
    :Data members:
        *x.nCase*: :class:`int`
            Number of cases in the trajectory
        *x.prefix*: :class:`str`
            Prefix to be used in folder names for each case in trajectory
        *x.GroupPrefix*: :class:`str`
            Prefix to be used for each grid folder name
        *x.cols*: :class:`list`, *dtype=str*
            List of variable names used
        *x.text*: :class:`dict`, *dtype=list*
            Lists of variable values taken from trajectory file
        *x.Mach*: :class:`numpy.ndarray`, *dtype=float*
            Vector of Mach numbers in trajectory
        *x[key]*: :class:`numpy.ndarray`, *dtype=float*
            Vector of values of each variable specified in *x.cols*
    :Versions:
        2014-05-28 ``@ddalle``: First version
        2014-06-05 ``@ddalle``: Generalized for user-defined keys
    """
    pass


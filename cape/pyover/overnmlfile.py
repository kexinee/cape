r"""
:mod:`cape.pyover.overnmlfile`: OVERFLOW namelist module
==============================================================

This is a module built off of the :mod:`cape.filecntl.FileCntl` module
customized for manipulating Fortran namelists and customized for the
OVERFLOW input file ``overflow.inp``. Such files are split into sections
which are called "namelists." Each name list has syntax similar to the
following.

    .. code-block:: none

        $FLOINP
            FSMACH = 4.0,
            ALPHA = 1.0,
            BETA = 0.0,
            $END

The main feature of this module is methods to set specific properties of a
namelist file, for example the Mach number or CFL number.

See also:

    * :mod:`cape.nmlfile`
    * :mod:`cape.pyover.cntl`
    * :func:`cape.pyover.cntl.Cntl.PrepareNamelist`
    * :func:`cape.pyover.cntl.Cntl.ReadNamelist`

"""

# Standard library
import os

# Third-party
import numpy as np

# Local imports
from ..filecntl import namelist2


# Function to compare boundary indices
def gti(a, b):
    r"""Altered greater-than test for Fortran array indices

    Negative indices are always considered to be greater than positive
    ones, and negative indices closer to zero are the largest. The
    general pattern is ``1 < 2 < 20 < -20 < -1``, and ``-1`` is the
    maximum possible value.

    :Call:
        >>> q = gti(a, b)
    :Inputs:
        *a*: :class:`int` | :class:`float`
            First test value
        *b*: :class:`int` | :class:`float`
            Second test value
    :Outputs:
        *q*: ``True`` | ``False``
            Whether or not *a* > *b*
    :Versions:
        * 2016-12-30 ``@ddalle``: v1.0
    """
    # Check signs
    if a*b > 0:
        # Both negative of both positive; use normal test
        return a > b
    elif a < 0:
        # *a* is negative and *b* is positive
        return True
    elif b < 0:
        # *b* is negative and *a* is positive
        return False
    else:
        # Can't process ``0``
        raise ValueError("Index of ``0`` is not valid for Fortran")


# Function to compare boundary indices
def gteqi(a, b):
    r"""Altered greater-than-or-equal-to test for Fortran array indices

    Negative indices are always considered to be greater than positive
    ones, and negative indices closer to zero are the largest. The
    general pattern is ``1 < 2 < 20 < -20 < -1``, and ``-1`` is the
    maximum possible value.

    :Call:
        >>> q = gteqi(a, b)
    :Inputs:
        *a*: :class:`int` | :class:`float`
            First test value
        *b*: :class:`int` | :class:`float`
            Second test value
    :Outputs:
        *q*: ``True`` | ``False``
            Whether or not *a* > *b*
    :Versions:
        * 2016-12-30 ``@ddalle``: v1.0
    """
    # Check if the two values are equal
    if a == b:
        # Equal
        return True
    else:
        # Go to altered gt test
        return gti(a, b)


# Function to compare boundary indices
def lti(a, b):
    r"""Altered less-than test for Fortran array indices

    Negative indices are always considered to be greater than positive
    ones, and negative indices closer to zero are the largest. The
    general pattern is ``1 < 2 < 20 < -20 < -1``, and ``-1`` is the
    maximum possible value.

    :Call:
        >>> q = lti(a, b)
    :Inputs:
        *a*: :class:`int` | :class:`float`
            First test value
        *b*: :class:`int` | :class:`float`
            Second test value
    :Outputs:
        *q*: ``True`` | ``False``
            Whether or not *a* > *b*
    :Versions:
        * 2016-12-30 ``@ddalle``: v1.0
    """
    # Check signs
    if a*b > 0:
        # Both negative of both positive; use normal test
        return a < b
    elif a < 0:
        # *a* is negative and *b* is positive
        return False
    elif b < 0:
        # *b* is negative and *a* is positive
        return True
    else:
        # Can't process ``0``
        raise ValueError("Index of ``0`` is not valid for Fortran")


# Function to compare boundary indices
def lteqi(a, b):
    r"""Altered less-than-or-equal-to test for Fortran array indices

    Negative indices are always considered to be greater than positive
    ones, and negative indices closer to zero are the largest. The
    general pattern is ``1 < 2 < 20 < -20 < -1``, and ``-1`` is the
    maximum possible value.

    :Call:
        >>> q = lteqi(a, b)
    :Inputs:
        *a*: :class:`int` | :class:`float`
            First test value
        *b*: :class:`int` | :class:`float`
            Second test value
    :Outputs:
        *q*: ``True`` | ``False``
            Whether or not *a* > *b*
    :Versions:
        * 2016-12-30 ``@ddalle``: v1.0
    """
    # Check if the two values are equal
    if a == b:
        # Equal
        return True
    else:
        # Go to altered gt test
        return lti(a, b)


# Altered maximum function
def maxi(a, b):
    r"""Altered maximum function for array indices

    Negative indices are always considered to be greater than positive
    ones, and negative indices closer to zero are the largest. The
    general pattern is ``1 < 2 < 20 < -20 < -1``, and ``-1`` is the
    maximum possible value.

    :Call:
        >>> c = maxi(a, b)
    :Inputs:
        *a*: :class:`int` | :class:`float`
            First test value
        *b*: :class:`int` | :class:`float`
            Second test value
    :Outputs:
        *c*: :class:`int` | :class:`float`
            Either *a* or *b* depending on which is greater
    :Versions:
        * 2016-12-30 ``@ddalle``: v1.0
    """
    # Test a,b
    if gti(a, b):
        return a
    else:
        return b


# Altered minimum function
def mini(a, b):
    """Altered minimum function for array indices

    Negative indices are always considered to be greater than positive
    ones, and negative indices closer to zero are the largest. The
    general pattern is ``1 < 2 < 20 < -20 < -1``, and ``-1`` is the
    maximum possible value.

    :Call:
        >>> c = maxi(a, b)
    :Inputs:
        *a*: :class:`int` | :class:`float`
            First test value
        *b*: :class:`int` | :class:`float`
            Second test value
    :Outputs:
        *c*: :class:`int` | :class:`float`
            Either *a* or *b* depending on which is greater
    :Versions:
        * 2016-12-30 ``@ddalle``: v1.0
    """
    # Use altered test
    if lti(a, b):
        return a
    else:
        return b


# Base this class off of the main file control class.
class OverNamelist(namelist2.Namelist2):
    r""" File control class for ``over.namelist``

    :Call:
        >>> nml = OverNamelist(fname="over.namelist")
    :Inputs:
        *fname*: {``"over.namelist"``} | :class:`str`
            Name of namelist file to read
    :Outputs:
        *nml*: :class:`OverNamelist`
            Interface to OVERFLOW input namelist
    :Version:
        * 2016-01-31 ``@ddalle``: v1.0
    """
    # Initialization method (not based off of FileCntl)
    def __init__(self, fname="over.namelist"):
        r"""Initialization method"""
        # Check for file
        if not os.path.isfile(fname):
            raise ValueError("No file '%s' to read" % fname)
        # Read the file.
        self.Read(fname)
        # Save the file name.
        self.fname = fname
        # Split into sections.
        self.UpdateNamelist()
        # Get grid names
        self.GetGridNames()

    # Function to get list of grid names
    def GetGridNames(self):
        r"""Get the list of grid names in an OVERFLOW namelist

        :Call:
            >>> nml.GetGridNames()
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
        :Versions:
            * 2016-01-31 ``@ddalle``: v1.0
        """
        # Get list indices of the 'GRDNAM' lists
        I = self.GetGroupByName('GRDNAM', None)
        # Save the names as an array (for easier searching)
        self.GridNames = [self.GetKeyFromGroupIndex(i, 'NAME') for i in I]
        # Save the indices of those lists
        self.iGrid = I

    # Get grid number
    def GetGridNumberByName(self, grdnam):
        r"""Get the number of a grid from its name

        :Call:
            >>> i = nml.GetGridNumberByName(grdnam)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *grdnam*: :class:`str`
                Name of the grid
        :Outputs:
            *i*: :class:`int`
                Grid number
        :Versions:
            * 2016-01-31 ``@ddalle``: v1.0
        """
        # Check for integer
        if type(grdnam).__name__.startswith('int'):
            return grdnam
        # Check if the grid is present
        if grdnam not in self.GridNames:
            raise KeyError("No grid named '%s' was found" % grdnam)
        # Return the index
        return self.GridNames.index(grdnam)

    # Get grid number (alias)
    GetGridNumber = GetGridNumberByName

    # Write SPLITMQ.I file
    def WriteSplitmqI(self, fname="splitmq.i", **kw):
        r"""Write a ``splitmq.i`` file to extract surface and second layer

        :Call:
            >>> nml.WriteSplitmqI(fname="splitmq.i", **kw)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *fname*: {``"splitmq.i"``} | :class:`str`
                Name of ``splitmq`` input file to write
            *qin*, *i*: {``"q.p3d"``} | :class:`str`
                Name of the input OVERFLOW solution file
            *qout*, *o*: {``"q.save"``} | :class:`str`
                Name of output OVERFLOW file for second line of "splitmq.i"
            *wall*: {``True``} | ``False``
                Only include walls if ``True``; else include thrust BCs
        :Versions:
            * 2016-12-30 ``@ddalle``: v1.0
        """
        # Open the output file
        f = open(fname, 'w')
        # Get input and output solution file names
        qin  = kw.get('qin',  kw.get('i', "q.p3d"))
        qout = kw.get('qout', kw.get('o', "q.save"))
        # Write header
        f.write('%s\n' % qin)
        f.write('%s\n' % qout)
        # Valid boundary condition types
        wtyp = range(1, 10)
        # Check for other surface BCs such as thrust BCs
        if kw.get('wall') is False:
            wtyp += [42, 153]
        # Loop through grids
        gn = 0
        for grid in self.GridNames:
            # Increase grid number
            gn += 1
            # Get boundary conditions and directions
            ibtyp = self.GetKeyFromGrid(grid, 'BCINP', 'IBTYP')
            ibdir = self.GetKeyFromGrid(grid, 'BCINP', 'IBDIR')
            # Check for off-body grid
            if ibtyp is None:
                # Off-body grid
                continue
            elif type(ibtyp).__name__ == "int":
                # Integer; create list
                ibtyp = [ibtyp]
                ibdir = [ibdir]
            # Check for other non-boundary grid
            J = np.intersect1d(ibtyp, wtyp)
            # If no walls, skip this grid
            if len(J) == 0: continue
            # Get range of indices
            jbcs = self.GetKeyFromGrid(grid, 'BCINP', 'JBCS')
            jbce = self.GetKeyFromGrid(grid, 'BCINP', 'JBCE')
            kbcs = self.GetKeyFromGrid(grid, 'BCINP', 'KBCS')
            kbce = self.GetKeyFromGrid(grid, 'BCINP', 'KBCE')
            lbcs = self.GetKeyFromGrid(grid, 'BCINP', 'LBCS')
            lbce = self.GetKeyFromGrid(grid, 'BCINP', 'LBCE')
            # Enlist
            if type(jbcs).__name__ == "int":
                jbcs, jbce = [jbcs], [jbce]
                kbcs, kbce = [kbcs], [kbce]
                lbcs, lbce = [lbcs], [lbce]
            # Loop through the three directions
            for k in [1, 2, 3]:
                # Initialize range
                ja, jb = -1, 1
                ka, kb = -1, 1
                la, lb = -1, 1
                # Loop through boundary conditions, looking only for walls
                for i in range(len(ibtyp)):
                    # Check for valid BC type
                    if ibtyp[i] not in wtyp: continue
                    # Check direction
                    if ibdir[i] != k: continue
                    # Compare boundaries
                    ja, jb = mini(ja, jbcs[i]), maxi(jb, jbce[i])
                    ka, kb = mini(ka, kbcs[i]), maxi(kb, kbce[i])
                    la, lb = mini(la, lbcs[i]), maxi(lb, lbce[i])
                # Check for valid range
                if (k == 3) and lteqi(ja, jb) and lteqi(ka, kb):
                    # Write L=1,2
                    la, lb = 1, 2
                elif (k == 1) and lteqi(ka, kb) and lteqi(la, lb):
                    # Write J=1,2
                    ja, jb = 1, 2
                elif (k == 2) and lteqi(la, lb) and lteqi(ja, jb):
                    # Write k=1,2
                    ka, kb = 1, 2
                else:
                    continue
                # Write the range
                f.write("%5i," % gn)
                f.write("%9i,%6i,%6i," % (ja, jb, 1))
                f.write("%9i,%6i,%6i," % (ka, kb, 1))
                f.write("%9i,%6i,%6i," % (la, lb, 1))
                f.write("\n")
        # Close the file
        f.close()

    # Apply dictionary of options to a grid
    def ApplyDictToGrid(self, grdnam, opts):
        r"""Apply a dictionary of settings to a grid

        :Call:
            >>> nml.ApplyDictToGrid(grdnam, opts)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *grdnam*: :class:`str` | :class:`int`
                Grid name or index
            *opts*: :class:`dict`
                Dictionary of options to apply
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
        """
        # Get the indices of the requested grid's groups
        jbeg, jend = self.GetGroupIndexByGridName(grdnam)
        # Get the list of group names
        grps = [self.Groups[j].lower() for j in range(jbeg, jend)]
        # Loop through the major keys
        for grp in opts:
            # Use lower-case group name for Fortran consistency
            grpl = grp.lower()
            # Find the group index
            if grpl in grps:
                # Get the group index (global)
                jgrp = jbeg + grps.index(grpl)
            else:
                # Insert the group
                self.InsertGroup(jend, grp)
                jgrp = jend
                # Update info
                jend += 1
            # Loop through the keys
            for k in opts[grp]:
                # Set the value.
                self.SetKeyInGroupIndex(jgrp, k, opts[grp][k])

    # Apply a dictionary of options to all grids
    def ApplyDictToALL(self, opts):
        r"""Apply a dictionary of settings to all grids

        :Call:
            >>> nml.ApplyDictToALL(opts)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *opts*: :class:`dict`
                Dictionary of options to apply
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
        """
        # Loop through groups
        for igrd in range(len(self.GridNames)):
            # Apply settings to individual grid
            self.ApplyDictToGrid(igrd, opts)

    # Get a quantity from a grid (with fallthrough)
    def GetKeyFromGrid(self, grdnam, grp, key, i=None):
        r"""Get the value of a key for a grid with a specific name

        This function uses fall-through, so if a setting is not
        explicitly defined for grid *grdnam*, it will check the
        preceding grid, and the grid before that, etc.

        :Call:
            >>> val = nml.GetKeyFromGrid(grdnam, grp, key, i=None)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *grdnam*: :class:`str`
                Name of the grid
            *grp*: :class:`str`
                Name of the namelist group of key to query
            *key*: :class:`str`
                Name of the key to query
            *i*: {``None``} | ``':'`` | :class:`int`
                Index to use in the namelist, e.g. "BCPAR(*i*)"
        :Outputs:
            *val*: :class:`str` | :class:`int` | :class:`float` | :class:`bool`
                Value from the namelist
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
            * 2016-08-29 ``@ddalle``: Added namelist indices
        """
        # Use lower case for Fortran consistency
        grpl = grp.lower()
        # Get the indices of the requested grid
        jbeg, jend = self.GetGroupIndexByGridName(grdnam)
        # Get the list of group names
        grps = [self.Groups[j].lower() for j in range(jbeg, jend)]
        # Check if the group is in the requested grid definition
        if grpl in grps:
            # Group explicitly in *grdnam* defn
            jgrp = jbeg + grps.index(grpl)
        else:
            # Get the groups for grid 0 (i.e. first grid)
            jbeg, jend = self.GetGroupIndexByGridName(0)
            grps = [self.Groups[j].lower() for j in range(jbeg, jend)]
            # If not in grid 0, this is not a valid request
            if grpl not in grps:
                raise KeyError("No group named '%s' in grid definitions" % grp)
            # Otherwise, loop backwards until we find it (fallthrough)
            igrid = self.GetGridNumberByName(grdnam)
            # Loop until found
            while igrid > 0:
                # Move backwards a grid
                igrid -= 1
                # Get the groups for that grid
                jbeg, jend = self.GetGroupIndexByGridName(igrid)
                grps = [self.Groups[j].lower() for j in range(jbeg, jend)]
                # Test for a match
                if grpl in grps:
                    # Use this group index; discontinue search
                    jgrp = jbeg + grps.index(grpl)
                    break
        # Get the key from this group.
        return self.GetKeyFromGroupIndex(jgrp, key, i=i)

    # Set a quantity for a specific grid
    def SetKeyForGrid(self, grdnam, grp, key, val, i=None):
        r"""Set the value of a key for a grid with a specific name

        :Call:
            >>> nml.SetKeyForGrid(grdnam, grp, key, val, i=None)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *grdnam*: :class:`str` | :class:`int`
                Name or number of the grid
            *grp*: :class:`str`
                Name of the namelist group
            *key*: :class:`str`
                Name of the key to set
            *val*: :class:`str` | :class:`float` | :class:`bool` | ...
                Value to set the key to
            *i*: {``None``} | ``':'`` | :class:`int`
                Index to use in the namelist, e.g. "BCPAR(*i*)"
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
            * 2016-08-29 ``@ddalle``: Added namelist indices
        """
        # Use lower-case group name for Fortran consistency
        grpl = grp.lower()
        # Get the indices of the requested grid's groups
        jbeg, jend = self.GetGroupIndexByGridName(grdnam)
        # Get the list of group names
        grps = [self.Groups[j].lower() for j in range(jbeg, jend)]
        # Check if the group is in the requested grid
        if grpl in grps:
            # Get the overall index of the requested group
            jgrp = jbeg + grps.index(grpl)
        else:
            # Insert a new group at the end of this grid definition
            self.InsertGroup(jend, grp)
            # Use the new group
            jgrp = jend
        # Set the key in that group
        self.SetKeyInGroupIndex(jgrp, key, val, i)

    # Get list of lists in a grid
    def GetGroupNamesByGridName(self, grdnam):
        r"""Get the list names in a grid definition

        :Call:
            >>> grps = nml.GetGroupNamesByGridName(grdnam)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *grdnam*: :class:`str`
                Name of the grid
        :Outputs:
            *grps*: :class:`list`\ [:class:`str`]
                List of group names in the grid *grdnam* definition
        :Versions:
            * 2016-01-31 ``@ddalle``: v1.0
        """
        # Get the start and end indices
        jbeg, jend = self.GetGroupIndexByGridName(grdnam)
        # Return the corresponding list
        return [self.Groups[j] for j in range(jbeg, jend)]

    # Get start and end of list indices in a grid
    def GetGroupIndexByGridName(self, grdnam):
        r"""Get the indices of the first and last list in a grid by name

        :Call:
            >>> jbeg, jend = nml.GetGroupIndexByGridName(grdnam)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *grdnam*: :class:`str`
                Name of the grid
        :Outputs:
            *jbeg*: :class:`int`
                Index of first list in the grid definition
            *jend*: :class:`int`
                Index of last list in the grid definition
        :Versions:
            * 2016-01-31 ``@ddalle``: v1.0
        """
        # Get the grid number
        grdnum = self.GetGridNumberByName(grdnam)
        # Get the list index of this grid's start
        jbeg = self.iGrid[grdnum]
        # Number of grids
        nGrid = len(self.GridNames)
        # Get the list index of the last list in this grid
        if grdnum >= nGrid-1:
            # Use the last list
            jend = len(self.Groups)
        else:
            # Use the list before the start of the next grid
            jend = self.iGrid[grdnum+1]
        # Output
        return jbeg, jend

    # Get FLOINP value
    def GetFLOINP(self, key):
        r"""Return value of key from the $FLOINP group

        :Call:
            >>> val = nml.GetFLOINP(key)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *key*: :class:`str`
                Name of field to query
        :Outputs:
            *val*: :class:`float` | :class:`list`
                Value of field *key* in group ``"FLOINP"``
        :Versions:
            * 2016-02-01 ``@ddalle``
        """
        return self.GetKeyInGroupName('FLOINP', key)

    # Set FLOINP value
    def SetFLOINP(self, key, val):
        r"""Set the value of key in the $FLOINP group

        :Call:
            >>> nml.SetFLOINP(key, val)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *key*: :class:`str`
                Name of field to query
            *val*: :class:`float` | :class:`list`
                Value of field *key* in group ``"FLOINP"``
        :Versions:
            * 2016-02-01 ``@ddalle``
        """
        self.SetKeyInGroupName('FLOINP', key, val)

    # Get GLOBAL value
    def GetGLOBAL(self, key):
        r"""Return value of key from the $GLOBAL group

        :Call:
            >>> val = nml.GetGLOBAL(key)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *key*: :class:`str`
                Name of field to query
        :Outputs:
            *val*: :class:`int` | :class:`bool` | :class:`list`
                Value of field *key* in group ``"GLOBAL"``
        :Versions:
            * 2016-02-01 ``@ddalle``
        """
        return self.GetKeyInGroupName('GLOBAL', key)

    # Set GLOBAL value
    def SetGLOBAL(self, key, val):
        r"""Set value of key from the $GLOBAL group

        :Call:
            >>> nml.GetGLOBAL(key, val)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *key*: :class:`str`
                Name of field to query
            *val*: :class:`int` | :class:`bool` | :class:`list`
                Value of field *key* in group ``"GLOBAL"``
        :Versions:
            * 2016-02-01 ``@ddalle``
        """
        self.SetKeyInGroupName('GLOBAL', key, val)

    # Function set the Mach number.
    def SetMach(self, mach):
        r"""Set the freestream Mach number

        :Call:
            >>> nml.SetMach(mach)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *mach*: :class:`float`
                Mach number
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
        """
        # Replace the line or add it if necessary.
        self.SetKeyInGroupName('FLOINP', 'FSMACH', mach)

    # Function to get the current Mach number.
    def GetMach(self):
        r"""Find the current Mach number

        :Call:
            >>> mach = nml.GetMach()
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
        :Outputs:
            *M*: :class:`float` (or :class:`str`)
                Mach number specified in :file:`input.cntl`
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
        """
        # Get the value.
        return self.GetKeyFromGroupName('FLOINP', 'FSMACH')

    # Function to set the angle of attack
    def SetAlpha(self, alpha):
        r"""Set the angle of attack

        :Call:
            >>> nml.SetAlpha(alpha)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *alpha*: :class:`float`
                Angle of attack
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
        """
        # Replace the line or add it if necessary.
        self.SetKeyInGroupName('FLOINP', 'ALPHA', alpha)

    # Get the angle of attack
    def GetAlpha(self):
        r"""Return the angle of attack

        :Call:
            >>> alpha = nml.GetAlpha()
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
        :Outputs:
            *alpha*: :class:`float`
                Angle of attack
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
        """
        # Get the value
        return self.GetKeyFromGroupName('FLOINP', 'ALPHA')

    # Function to set the sideslip angle
    def SetBeta(self, beta):
        r"""Set the sideslip angle

        :Call:
            >>> nml.SetBeta(beta)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *beta*: :class:`float`
                Sideslip angle
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
        """
        # Replace the line or add it if necessary.
        self.SetKeyInGroupName('FLOINP', 'BETA', beta)

    # Get the slideslip angle
    def GetBeta(self):
        r"""Get the sideslip angle

        :Call:
            >>> beta = nml.GetBeta()
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
        :Outputs:
            *beta*: :class:`float`
                Sideslip angle
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
        """
        return self.GetKeyFromGroupName('FLOINP', 'BETA')

    # Set the temperature
    def SetTemperature(self, T):
        r"""Set the freestream temperature

        :Call:
            >>> nml.SetTemperature(T)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *T*: :class:`float`
                Freestream temperature
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
        """
        self.SetKeyInGroupName('FLOINP', 'TINF', T)

    # Get the temperature
    def GetTemperature(self):
        r"""Get the freestream temperature

        :Call:
            >>> T = nml.GetTemperature()
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
        :Outputs:
            *T*: :class:`float`
                Freestream temperature
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
        """
        return self.GetKeyInGroupName('FLOINP', 'TINF')

    # Set the Reynolds number
    def SetReynoldsNumber(self, Re):
        r"""Set the Reynolds number per unit length

        :Call:
            >>> nml.SetReynoldsNumber(Re)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *Re*: :class:`float`
                Reynolds number per unit length
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
        """
        self.SetKeyInGroupName('FLOINP', 'REY', Re)

    # Get the Reynolds number
    def GetReynoldsNumber(self):
        r"""Get the Reynolds number per unit length

        :Call:
            >>> Re = nml.GetReynoldsNumber()
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
        :Outputs:
            *Re*: :class:`float`
                Reynolds number per unit length
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
        """
        return self.GetKeyInGroupName('FLOINP', 'REY')

    # Set the number of iterations
    def SetnIter(self, nIter):
        r"""Set the number of iterations

        :Call:
            >>> nml.SetnIter(nIter)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *nIter*: :class:`int`
                Number of iterations to run
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
        """
        self.SetKeyInGroupName('GLOBAL', 'NSTEPS', nIter)

    # Get the number of iterations
    def GetnIter(self):
        r"""Get the number of iterations

        :Call:
            >>> nIter = nml.GetnIter()
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
        :Outputs:
            *nIter*: :class:`int`
                Number of iterations to run
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
        """
        return self.GetKeyInGroupName('GLOBAL', 'NSTEPS')

    # Set the restart setting
    def SetRestart(self, q=True):
        r"""Set or unset restart flag

        :Call:
            >>> nml.SetRestart(q=True)
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
            *q*: :class:`bool`
                Whether or not to run as a restart
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
        """
        self.SetKeyInGroupName('GLOBAL', 'RESTRT', q)

    # Get the restart setting
    def GetRestart(self):
        r"""Get the current restart flag

        :Call:
            >>> q = nml.GetRestart()
        :Inputs:
            *nml*: :class:`OverNamelist`
                Interface to OVERFLOW input namelist
        :Outputs:
            *q*: :class:`bool`
                Whether or not to run as a restart
        :Versions:
            * 2016-02-01 ``@ddalle``: v1.0
        """
        return self.GetKeyInGroupName('GLOBAL', 'RESTRT')


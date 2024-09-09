r"""
This is a module built off of the :mod:`cape.filecntl.FileCntl` module
customized for manipulating Fortran namelists.  Such files are split
into sections which are called "name lists."  Each name list has syntax
similar to the following.

    .. code-block:: none

        $FLOINP
            FSMACH = 4.0,
            ALPHA = 1.0,
            BETA = 0.0,
            $END

and this module is designed to recognize such sections.  The main
feature of this module is methods to set specific properties of a
namelist file, for example the Mach number or CFL number.

The difference between this module and
:class:`cape.filecntl.namelist.Namelist` is that this module can support
multiple namelists with the same title.  This is particularly important
for Overflow, which has ``GRDNAM``, ``BCINP``, and other sections
defined for each structured grid.  These modules should be combined as
the differing namelist syntaxes are actually part of one file
convention.

This function provides a class
:class:`cape.filecntl.namelist2.Namelist2` that can both read and set
values in the namelist.  The key functions are

    * :func:`Namelist2.GetKeyFromGroupName`
    * :func:`Namelist2.GetKeyFromGroupIndex`
    * :func:`Namelist2.SetKeyInGroupName`
    * :func:`Namelist2.SetKeyInGroupIndex`

The conversion from namelist text to Python is handled by
:func:`Namelist2.ConvertToText`, and the reverse is handled by
:func:`Namelist2.ConvertToVal`. Conversions cannot quite be performed
just by the Python functions :func:`print` and :func:`eval` because
delimiters are not used in the same fashion. Some of the conversions are
tabulated below.

    +----------------------+------------------------+
    | Namelist             | Python                 |
    +======================+========================+
    | ``val = "text"``     | ``val = "text"``       |
    +----------------------+------------------------+
    | ``val = 'text'``     | ``val = 'text'``       |
    +----------------------+------------------------+
    | ``val = 3``          | ``val = 3``            |
    +----------------------+------------------------+
    | ``val = 3.1``        | ``val = 3.1``          |
    +----------------------+------------------------+
    | ``val = .false.``    | ``val = False``        |
    +----------------------+------------------------+
    | ``val = .true.``     | ``val = True``         |
    +----------------------+------------------------+
    | ``val = .f.``        | ``val = False``        |
    +----------------------+------------------------+
    | ``val = .t.``        | ``val = True``         |
    +----------------------+------------------------+
    | ``val = 10.0 20.0``  | ``val = [10.0, 20.0]`` |
    +----------------------+------------------------+
    | ``val = 1, 100``     | ``val = [1, 100]``     |
    +----------------------+------------------------+
    | ``val(1) = 1.2``     | ``val = [1.2, 1.5]``   |
    +----------------------+------------------------+
    | ``val(2) = 1.5``     |                        |
    +----------------------+------------------------+
    | ``val = _mach_``     | ``val = "_mach_"``     |
    +----------------------+------------------------+

In most cases, the :class:`Namelist` will try to interpret invalid values for
any namelist entry as a string with missing quotes.  The reason for this is
that users often create template namelist with entries like ``_mach_`` that can
be safely replaced with appropriate values using ``sed`` commands or something
similar.

See also:

    * :mod:`cape.filecntl.namelist`
    * :mod:`cape.pyfun.namelist`
    * :mod:`cape.pyover.overNamelist`
    * :func:`pyFun.casecntl.GetNamelist`
    * :func:`cape.pyfun.cntl.Cntl.ReadNamelist`
    * :func:`cape.pyover.cntl.Cntl.ReadNamelist`

"""

# Standard library modules


# Third-party modules
import numpy as np

# Local modules
from .filecntl import FileCntl


# Subclass off of the file control class
class Namelist2(FileCntl):
    r"""File control class for Fortran namelists with duplicate sections

    :Call:
        >>> nml = Namelist2()
        >>> nml = Namelist2(fname)
    :Inputs:
        *fname*: :class:`str`
            Name of namelist file to read, defaults to ``'overflow.inp'``
    :Outputs:
        *nml*: :class:`cape.filecntl.namelist2.Namelist2`
            Namelist file control instance
        *nml.ibeg*: :class:`np.ndarray`\ [:class:`int`]
            Indices of lines starting each namelist/section
        *nml.iend*: :class:`np.ndarray`\ [:class:`int`]
            Indices of lines ending each namelist/section
        *nml.Groups*: :class:`np.ndarray`\ [:class:`str`]
            List of namelist/section/group titles
    :Versions:
        * 2016-02-01 ``@ddalle``: Version 1.0
    """
    # Initialization method
    def __init__(self, fname="overflow.inp"):
        r"""Initialization method

        :Versions:
            * 2016-01-29 ``@ddalle``: Version 1.0
        """
        # Read the file.
        self.Read(fname)
        # Save the file name
        self.fname = fname
        # Get the lists of indices of each namelist
        self.UpdateNamelist()

    # Function to update the namelists
    def UpdateNamelist(self):
        r"""Update the line indices for each namelist

        :Call:
            >>> nml.UpdateNamelist()
        :Inputs:
            *nml*: :class:`cape.filecntl.namelist2.Namelist2`
                Interface to namelist with repeated lists
        :Versions:
            * 2016-01-29 ``@ddalle``: Version 1.0
        """
        # Find the lines that start the lists
        I0 = np.array(self.GetIndexSearch(r'\s*[&$]'), dtype=int)
        # Find the lines that end with '/'
        J0 = np.array(self.GetIndexSearch(r'.*/\s*$'), dtype=int)
        # Of those, find those that are comments
        J1 = np.array(self.GetIndexSearch(r'\s*!.*/\s*$'), dtype=int)
        # These are the namelist end lines using '/'
        J = np.setdiff1d(J0, J1)
        # Get start and end keywords to each line
        grpnm = np.array([self.lines[i].split()[0][1:] for i in I0])
        kwbeg = np.array([self.lines[i].split()[0][1:].lower() for i in I0])
        kwend = np.array([self.lines[i].split()[-1][1:].lower() for i in I0])
        # Save the start indices
        self.ibeg = I0[kwbeg != "end"]
        # Save the end indices
        self.iend = np.sort(np.hstack((I0[kwend == "end"], J)))
        # Save the names
        self.Groups = grpnm[kwbeg != "end"]

    # Apply a whole bunch of options
    def ApplyDict(self, opts):
        r"""Apply a whole dictionary of settings to the namelist

        :Call:
            >>> nml.ApplyDict(opts)
        :Inputs:
            *nml*: :class:`cape.filecntl.namelist2.Namelist2`
                Old-style namelist inerface
            *opts*: :class:`dict`
                Dictionary of namelist options
        :Versions:
            * 2016-02-01 ``@ddalle``: Version 1.0
        """
        # Loop through major keys.
        for grp in opts.keys():
            # Check for illegal name to specify which index to use
            if "&" in grp:
                try:
                    # Split into two parts
                    ggrp, igrp = grp.split("&")
                    # Convert to integer
                    igrp = int(igrp)-1
                except Exception:
                    # Some sort of error
                    raise ValueError("Illegal namelist group '%s'" % grp)
            else:
                # Assume first grip
                ggrp = grp
                igrp = 0
            # Check it it's an existing group
            if ggrp not in self.Groups:
                # Initialize the section.
                self.InsertGroup(0, ggrp)
            # Loop through the keys in this subnamelist/section
            for k in opts[grp].keys():
                # Set the value.
                self.SetKeyInGroupName(ggrp, k, opts[grp][k], igrp=igrp)

    # Add a group
    def InsertGroup(self, igrp, grp):
        r"""Insert a group as group number *igrp*

        :Call:
            >>> nml.InsertGroup(igrp, grp)
        :Inputs:
            *nml*: :class:`cape.filecntl.namelist2.Namelist2`
                Interface to namelist with repeated lists
            *igrp*: :class:`int`
                Index of location at which to insert group
            *grp*: :class:`str`
                Name of the group to insert
        :Versions:
            * 2016-02-01 ``@ddalle``: Version 1.0
        """
        # Test for "append"
        if igrp >= len(self.ibeg) or igrp == -1:
            # Making a new group
            ibeg = self.iend[-1]+1
            iend = self.iend[-1]
        else:
            # Get the index of the group that we insert before
            ibeg = self.ibeg[igrp]
            iend = self.iend[igrp]
        # Query the current starting character
        gchar = self.lines[ibeg].lstrip()[0]
        # Check end line type
        if self.lines[iend].rstrip().endswith('/'):
            # Ends with a '/' line
            lend = "     /\n"
        else:
            # Ends with an $END or &END
            lend = "     %sEND\n" % gchar
        # Insert the lines in reverse order
        self.lines.insert(ibeg, lend)
        self.lines.insert(ibeg, " %s%s\n" % (gchar, grp))
        # Update the namelist info
        self.UpdateNamelist()

    # Find a list by name (and index if repeated)
    def GetGroupByName(self, grp, igrp=0):
        r"""Get index of group with a specific name

        :Call:
            >>> i = nml.GetGroupByName(grp, igrp=0)
        :Inputs:
            *nml*: :class:`cape.name.ist2.Namelist2`
                Interface to namelist with repeated lists
            *grp*: :class:`str`
                Name of namelist group
            *igrp*: {``0``} | :class:`int`
                If multiple matches, return match number *igrp*
        :Outputs:
            *i*: :class:`int` | :class:`np.ndarray`\ [:class:`int`]
                Group index of requested match
        :Versions:
            * 2016-01-31 ``@ddalle``: Version 1.0
        """
        # Search based on lower-case names
        grps = np.array([gi.lower() for gi in self.Groups])
        # Find the all indices that match
        I0 = np.where(grps == grp.lower())[0]
        # Process output
        if igrp is None:
            # Return all matches
            return I0
        elif len(I0) == 0:
            # No match
            return KeyError(
                "Namelist '%s' has no list '%s'"
                % (self.fname, grp))
        elif len(I0) < igrp:
            # Not enough matches
            return ValueError(
                "Namelist '%s' has fewer than %i lists named '%s'"
                % (self.fname, igrp, grp))
        else:
            # Return the requested match
            return I0[igrp]

    # Turn a namelist into a dict
    def ReadGroupIndex(self, igrp):
        r"""Read group *igrp* and return a dictionary

        The output is a :class:`dict` such as the following

            ``{'FSMACH': '0.8', 'ALPHA': '2.0'}``

        If a parameter has an index specification, such as ``"PAR(2) = 1.0"``,
        the dictionary will have the following format for such keys.

            ``{'PAR': {2: 1.0}}``

        :Call:
            >>> d = nml.ReadGroupIndex(igrp)
        :Inputs:
            *nml*: :class:`cape.filecntl.namelist2.Namelist2`
                Interface to namelist with repeated lists
            *igrp*: :class:`int`
                Group index to read
        :Outputs:
            *d*: :class:`dict`\ [:class:`str`]
                Raw (uncoverted) values of the dict
        :Versions:
            * 2016-01-29 ``@ddalle``: Version 1.0
        """
        # Initialize the dictionary
        d = {}
        # Get index of starting line
        ibeg = self.ibeg[igrp]
        # Get index of end line
        if igrp == len(self.ibeg):
            # Use the last line
            iend = len(self.lines)+1
        else:
            # Use the line before the start of the next line
            iend = self.ibeg[igrp+1]
        # Get the lines
        lines = [line.strip() for line in self.lines[ibeg:iend]]
        # Process the first line to catch keys in the opening line
        vals = lines[0].split()
        # Check for multiple entries
        if len(vals) > 1:
            # Read the additional values
            line = ' '.join(vals[1:])
            # Process it
            di = self.ReadKeysFromLine(line)
            # Append the keys.
            for k in di: d[k] = di[k]
        # Loop through the lines.
        for line in lines[1:]:
            # Process the line
            di = self.ReadKeysFromLine(line)
            # Check for end
            if di == -1: break
            # Append the keys.
            for k in di: d[k] = di[k]
        # Output
        return d

    # Search for a specific key in a numbered section
    def GetKeyFromGroupIndex(self, igrp, key, i=None):
        """Get the value of a key from a specific section

        :Call:
            >>> v = nml.GetKeyFromGroupIndex(igrp, key, i=i)
        :Inputs:
            *nml*: :class:`cape.filecntl.namelist2.Namelist2`
                Interface to namelist with repeated lists
            *key*: :class:`str`
                Name of the key to search for
            *i*: {``None``} | ``":"`` | :class:`int`
                Index to use in the namelist, e.g. "BCPAR(*i*)"
        :Outputs:
            *v*: :class:`str` | :class:`int` | :class:`float` | :class:`list`
                Evaluated value of the text for this key
        :Versions:
            * 2016-01-29 ``@ddalle``: Version 1.0
            * 2016-08-29 ``@ddalle``: Added parameter index
        """
        # Get index of starting line
        ibeg = self.ibeg[igrp]
        # Get index of end line
        if igrp == len(self.ibeg):
            # Use the last line
            iend = len(self.lines)+1
        else:
            # Use the line before the start of the next line
            iend = self.ibeg[igrp+1]
        # Initialize the boolean indicator of a match
        q = False
        # Loop through the lines
        for line in self.lines[ibeg:iend]:
            # Try to read the key from the line
            q, v = self.GetKeyFromLine(line, key, i=i)
            # Break if we found it.
            if q: break
        # Output
        return v

    # Search for a specific key by name
    def GetKeyFromGroupName(self, grp, key, igrp=0, i=None):
        """Get the value of a key from a section by group name

        :Call:
            >>> v = nml.GetKeyFromGroupName(grp, key, igrp=0, i=None)
        :Inputs:
            *nml*: :class:`cape.filecntl.namelist2.Namelist2`
                Old-style Fortran namelist interface
            *grp*: :class:`str`
                Group name to search for
            *key*: :class:`str`
                Name of key to search for
            *igrp*: :class:`int`
                If multiple sections have same name, use match number *igrp*
            *i*: {``None``} | ``":"`` | :class:`int`
                Index to use in the namelist, e.g. "BCPAR(*i*)"
        :Outputs:
            *v*: :class:`any`
                Converted value
        :Versions:
            * 2016-01-31 ``@ddalle``: Version 1.0
            * 2016-08-29 ``@ddalle``: Added parameter index
        """
        # Find matches
        j = self.GetGroupByName(grp, igrp)
        # Get the key from that list
        return self.GetKeyFromGroupIndex(j, key, i=i)

    # Function to process a single line
    def ReadKeysFromLine(self, line):
        r"""Read zero or more keys from a single text line

        :Call:
            >>> d = nml.ReadKeysFromLine(line)
        :Inputs:
            *nml*: :class:`cape.filecntl.namelist2.Namelist2`
                Interface to namelist with repeated lists
            *line*: :class:`str`
                One line from a namelist file
        :Outputs:
            *d*: :class:`dict`\ [:class:`str`]
                Unconverted values of each key
        :Versions:
            * 2016-01-29 ``@ddalle``: Version 1.0
        """
        # Initialize dictionary
        d = {}
        # Initialize remaining text
        txt = line.strip()
        # Loop until line is over
        while txt != '':
            # Read the keys
            txt, key, val, i = self.PopLine(txt)
            # Check for relevant key
            if key is not None:
                # Check for index
                if i is None:
                    # Set the value of the dictionary.
                    d[key] = val
                else:
                    # Set the value for that parameter
                    d.setdefault(key, {})
                    d[key][i] = val
        # Output
        return d

    # Try to read a key from a line
    def GetKeyFromLine(self, line, key, i=None):
        """Read the value of a key from a line

        :Call:
            >>> q, val = nml.GetKeyFromLine(line, key, i=None)
        :Inputs:
            *nml*: :class:`cape.filecntl.namelist2.Namelist2`
                Interface to namelist with repeated lists
            *line*: :class:`str`
                A line of text that may or may not contain the value of *key*
            *key*: :class:`str`
                Name of key
            *i*: {``None``} | ``":"`` | :class:`int`
                Index to use in the namelist, e.g. "BCPAR(*i*)"
        :Outputs:
            *q*: :class:`bool`
                Whether or not the key was found in the line
            *val*: :class:`str` | :class:`float` | :class:`int` | :class:`bool`
                Value of the key, if found
        :Versions:
            * 2016-01-29 ``@ddalle``: Version 1.0
            * 2016-01-30 ``@ddalle``: Case-insensitive
            * 2016-08-29 ``@ddalle``: Added index capability
        """
        # Check for the line
        if key.lower() not in line.lower():
            # Key not read in this text
            return False, None
        # Initialize text remaining.
        tend = line
        while tend != "":
            # Read the first key in the remaining text.
            try:
                tend, ki, vi, ii = self.PopLine(tend)
            except Exception as e:
                raise ValueError(
                    ("Failure reading line or partial line:\n") +
                    ("  '%s'\n" % tend) +
                    ("Original error:\n") +
                    ("  '%s'" % e.message))
            # Check for a match.
            if ki.lower() == key.lower() and ii == i:
                # Use the value from this key.
                return True, self.ConvertToVal(vi)
        # If this point is reached, the key name is hiding in a comment or str
        return False, None

    # Set a key
    def SetKeyInGroupName(self, grp, key, val, igrp=0, i=None):
        """Set the value of a key from a group by name

        :Call:
            >>> nml.SetKeyInGroupName(grp, key, val, igrp=0, i=None)
        :Inputs:
            *nml*: :class:`cape.filecntl.namelist2.Namelist2`
                Old-style Fortran namelist interface
            *grp*: :class:`str`
                Group name to search for
            *key*: :class:`str`
                Name of key to search for
            *val*: :class:`any`
                Converted value
            *igrp*: :class:`int`
                If multiple sections have same name, use match number *igrp*
            *i*: {``None``} | ``":"`` | :class:`int`
                Index to use in the namelist, e.g. "BCPAR(*i*)"
        :Versions:
            * 2015-01-31 ``@ddalle``: Version 1.0
            * 2016-08-29 ``@ddalle``: Added index capability
        """
        # Find matches
        j = self.GetGroupByName(grp, igrp)
        # Get the key from that list
        return self.SetKeyInGroupIndex(j, key, val, i=i)

    # Set a key
    def SetKeyInGroupIndex(self, igrp, key, val, i=None):
        r"""Set the value of a key in a group by index

        If the key is not set in the present text, add it as a new line.
        The contents of the file control's text (in *nml.lines*) will be
        edited, and the list indices will be updated if a line is added.

        :Call:
            >>> nml.SetKeyInGroupIndex(igrp, key, val, i=None)
        :Inputs:
            *nml*: :class:`cape.filecntl.namelist2.Namelist2`
                File control instance for old-style Fortran namelist
            *igrp*: :class:`int`
                Index of namelist to edit
            *key*: :class:`str`
                Name of key to alter or set
            *val*: :class:`any`
                Value to use for *key*
            *i*: {``None``} | ``":"`` | :class:`int`
                Index to use in the namelist, e.g. "BCPAR(*i*)"
        :Versions:
            * 2015-01-30 ``@ddalle``: Version 1.0
            * 2016-08-29 ``@ddalle``: Added index capability
        """
        # Get index of starting and end lines
        ibeg = self.ibeg[igrp]
        iend = self.iend[igrp]
        # Initialize the boolean indicator of a match in existing text
        q = False
        # Loop through the lines
        for j in range(ibeg, iend):
            # Get the line.
            line = self.lines[j]
            # Try to set the key in this line
            q, line = self.SetKeyInLine(line, key, val, i=i)
            # Check for match.
            if q:
                # Set this line in the FC's text and exit
                self.lines[j] = line
                return
        # If no match found, nothing to delete
        if val is None:
            return
        # If no match found in existing text, add a line.
        if i is None:
            # No index
            line = '     %s = %s,\n' % (key, self.ConvertToText(val))
        else:
            # Specify line with an index
            line = '     %s(%s) = %s,\n' % (key, i, self.ConvertToText(val))
        # Insert the line.
        self.lines = self.lines[:iend] + [line] + self.lines[iend:]
        # Update the namelist indices.
        self.ibeg[igrp+1:] += 1
        self.iend[igrp:]   += 1

    # Set a key
    def SetKeyInLine(self, line, key, val, i=None):
        """Set the value of a key in a line if the key is already in the line

        :Call:
            >>> q, line = nml.SetKeyInLine(line, key, val, i=None)
        :Inputs:
            *nml*: :class:`cape.filecntl.namelist2.Namelist2`
                Interface to namelist with repeated lists
            *line*: :class:`str`
                A line of text that may or may not contain the value of *key*
            *key*: :class:`str`
                Name of key
            *val*: :class:`str` | :class:`float` | :class:`int` | :class:`bool`
                Value of the key, if found
            *i*: {``None``} | ``":"`` | :class:`int`
                Index to use in the namelist, e.g. "BCPAR(*i*)"
        :Outputs:
            *q*: :class:`bool`
                Whether or not the key was found in the line
            *line*: :class:`str`
                New version of the line with *key* reset to *val*
        :Versions:
            * 2016-01-29 ``@ddalle``: Version 1.0
            * 2016-08-29 ``@ddalle``: Added index capability
        """
        # Check if the key is present in the line of the text.
        if key not in line:
            return False, line
        # Initialize prior and remaining text
        tbeg = ""
        tend = line
        # Loop through keys in this line
        while True:
            # Read the first key in the remaining line.
            try:
                txt, ki, vi, ii = self.PopLine(tend)
            except Exception as e:
                raise ValueError(
                    ("Failure reading line or partial line:\n") +
                    ("  '%s'\n" % tend) +
                    ("Original error:\n") +
                    ("  '%s'" % e.message))
            # Check if the line is empty.
            if ki is None:
                # No match in this line.
                return False, line
            # Check if the key matches the target.
            if ki.lower() == key.lower() and ii == i:
                # Match found; exit and remember remaining text
                tbeg += tend[:tend.index(ki)]
                tend = txt
                break
            # Check if the line is empty.
            if txt == "":
                # No match in this line.
                return False, line
            # Otherwise, append to the prefix text and keep looking.
            tbeg += tend[:tend.index(txt)]
            # Update the text remaining
            tend = txt
        # If the value is ``None``, delete the entry.
        if val is None:
            # Use the beginning and remaining text Only
            line = "%s%s\n" % (tbeg, tend.lstrip())
        else:
            # Convert value to text
            sval = self.ConvertToText(val)
            # Check for index
            if i is None:
                # No index
                line = "%s%s = %s,%s\n" % (tbeg, key, sval, tend)
            else:
                # Set an index as well
                line = "%s%s(%s) = %s,%s\n" % (tbeg, key, i, sval, tend)
        return True, line

    # Pop line
    def PopLine(self, line):
        r"""Read the left-most key from line and return rest of line

        :Call:
            >>> txt, key, val, i = nml.PopLine(line)
        :Inputs:
            *nml*: :class:`cape.filecntl.namelist2.Namelist2`
                Interface to namelist with repeated lists
            *line*: :class:`str`
                One line of namelist text
        :Outputs:
            *txt*: :class:`str`
                Remaining text in *line* after first key has been read
            *key*: :class:`str`
                Name of first key read from *line*
            *val*: ``None`` | :class:`str`
                Raw (unconverted) value of *key*
            *i*: {``None``} | ``':"`` | :class:`int`
                Vector index if specified
        :Versions:
            * 2016-01-29 ``@ddalle``: Version 1.0
            * 2016-08-29 ``@ddalle``: Version 1.1
                - Add indices, e.g. BCPAR(2)
        """
        # Strip line
        txt = line.strip()
        # Check for comment
        if txt.startswith('!'):
            return '', None, None, None
        # Check for start of namelist
        if txt and txt[0] in ["$", "&"]:
            # Get the stuff.
            V = line.split()
            # Check for remaining stuff to process.
            if len(V) > 1:
                # Process the rest of the line
                txt = ' '.join(V[1:])
            else:
                # Nothing else in the line
                txt = ''
        # Check for empty key
        if txt == "":
            return txt, None, None, None
        # Split on the equals signs
        vals = txt.split("=")
        # Remaining text
        txt = '='.join(vals[1:])
        # Get the name of the key.
        key = vals[0].strip()
        # Attempt to split for index
        K = key.split('(')
        # Check for successful split
        if len(K) > 1:
            # Split by key and index
            key = K[0]
            # Template: "PAR(3) =" or "PAR(:) ="
            i = K[1].rstrip(')')
            # Check for ':'
            if i != ':': i = int(i)
        else:
            # No index
            i = None
        # Deal with quotes or no quotes
        if len(vals) == 1:
            # No value, last key in the line
            txt = ''
            val = None
        elif len(vals) == 2:
            # Last value in the line
            txt = ''
            val = vals[1].rstrip(',').strip()
            # Check for trivial value
            if val == "": val = None
        elif txt.startswith('"'):
            # Check for a second quote
            if '"' not in txt[1:]:
                # Unterminated string
                raise ValueError(
                    "Namelist line '%s' could not be interpreted" % line)
            # Find it
            iq = txt[1:].index('"') + 1
            # Split of at this point
            val = txt[1:iq]
            # Remaining text (?)
            if len(txt) > iq+1:
                txt = txt[iq+1:]
            else:
                txt = ''
        elif txt.startswith("'"):
            # Check for a second quote
            if "'" not in txt[1:]:
                # Unterminated string
                raise ValueError(
                    "Namelist line '%s' could not be interpreted" % line)
            # Find it
            iq = txt[1:].index("'") + 1
            # Split of at this point
            val = txt[1:iq]
            # Remaining text (?)
            if len(txt) > iq+1:
                txt = txt[iq+1:]
            else:
                txt = ''
        else:
            # Read until just before the next '='
            subvals = vals[1].split(',')
            # Rejoin but without name of next key
            val = ','.join(subvals[:-1])
            # Remaining text
            txt = subvals[-1] + '=' + '='.join(vals[2:])
        # Ouptut
        return txt, key, val, i

    # Conversion
    def ConvertToVal(self, val):
        r"""Convert text to Python based on a series of rules

        :Call:
            >>> v = nml.ConvertToVal(val)
        :Inputs:
            *nml*: :class:`cape.filecntl.namelist.Namelist`
                File control instance for :file:`fun3d.nml`
            *val*: :class:`str` | :class:`unicode`
                Text of the value from file
        :Outputs:
            *v*: ``str`` | ``int`` | ``float`` | ``bool`` | ``list``
                Evaluated value of the text
        :Versions:
            * 2015-10-16 ``@ddalle``: Version 1.0
            * 2016-01-29 ``@ddalle``: Added boolean shortcuts, ``.T.``
        """
        # Check inputs.
        if type(val).__name__ not in ['str', 'unicode']:
            # Not a string; return as is.
            return val
        # Split to parts
        V = val.split(',')
        # Check the value.
        try:
            # Check the value.
            if ('"' in val) or ("'" in val):
                # It's a string.  Remove the quotes.
                return eval(val)
            elif val.lower() in [".false.", ".f."]:
                # Boolean
                return False
            elif val.lower() in [".true.", ".t."]:
                # Boolean
                return True
            elif len(V) == 0:
                # Nothing here.
                return None
            elif len(V) == 1:
                # Convert to float/integer
                return eval(val)
            else:
                # List
                return [eval(v) for v in V]
        except Exception:
            # Give it back, whatever it was.
            return val

    # Conversion to text
    def ConvertToText(self, v):
        """Convert a scalar value to text to write in the namelist file

        :Call:
            >>> val = nml.ConvertToText(v)
        :Inputs:
            *nml*: :class:`cape.filecntl.namelist2.Namelist2`
                File control instance for old-style Fortran namelist
            *v*: :class:`str` | :class:`int` | :class:`float` | :class:`list`
                Evaluated value of the text
        :Outputs:
            *val*: :class:`str` | :class:`unicode`
                Text of the value from file
        :Versions:
            * 2015-10-16 ``@ddalle``: Version 1.0
        """
        # Get the type
        t = type(v).__name__
        # Form the output line.
        if t in ['str', 'unicode']:
            # Force quotes
            return "'%s'" % v
        elif t in ['bool'] and v:
            # Boolean
            return ".T."
        elif t in ['bool']:
            # Boolean
            return ".F."
        elif type(v).__name__ in ['list', 'ndarray']:
            # List (convert to string first)
            V = [str(vi) for vi in v]
            return ", ".join(V)
        else:
            # Use the built-in string converter
            return str(v)


# class Namelist2


#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:mod:`cape.pyus.inputInp`: US3D primary input file interface
===============================================================

This is a module built off of the :mod:`cape.filecntl.FileCntl` module
customized for manipulating US3D input files.  Such files are split into
"blocks" with a syntax such as the following:

    .. code-block:: none

        [CFD_SOLVER]
        !-----------------------------------------------------------------------
        !   nstop      ires     nplot     iconr      impl      kmax    kmaxo
            30000         0       300       0         21        10       4
        !
        !   ivisc      ivib     ichem      itrb     ibase   idiss_g
              11          2         1         0         0       1
        !
        !   ivmod     ikmod     idmod       ikv      icfl     dtfix
                3      -999         3        11         1     0.0d0
        !
        !  iorder      iuem      ikve       kbl      iman
                2         3        11        80       100
        !
        !   npfac     npvol
               0         0
        !
        !     cfl      epsj      wdis
             1.1d0      0.3     0.001d+0
        !-----------------------------------------------------------------------
        [/CFD_SOLVER]

This module is designed to recognize such sections.  The main feature of the
module is methods to set specific properties of an input file according to
certain named blocks.  Most of the parameters occur in ordered sections without
labels, and so therefore the contents are quite solver-specific.

"""

# Standard library
import re

# Standard third-party modules
import numpy as np

# Base file control class
from ..filecntl.namelist import Namelist
from .. import convert


# Base this class off of the main file control class
class InputInp(Namelist):
    r"""Input file class for US3D primary input files

    This class is derived from the :class:`cape.filecntl.FileCntl`
    class, so all methods applicable to that class can also be used for
    instances of this class.

    :Call:
        >>> inpt = InputInp()
        >>> inpt = InputInp(fname)
    :Inputs:
        *fname*: :class:`str`
            Name of namelist file to read, defaults to ``'input.inp'``
    :Outputs:
        *inp*: :class:`cape.pyus.inputinpfile.InputInp`
            Namelist file control instance
        *inp.Sections*: :class:`dict` (:class:`list`\ [:class:`str`])
            Dictionary of sections containing contents of each namelist
        *inp.SectionNames*: :class:`list`\ [:class:`str`]
            List of section names
    :Version:
        * 2019-06-06 ``@ddalle``: First version
    """
  # --- Hard-Coded Orders ---
    # Parameter names in [CFD_SOLVER] block
    CFD_SOLVER_keys = [
        ["nstop",  "ires",  "nplot",  "iconr", "impl",   "kmax",   "kmaxo"],
        ["ivisc",  "ivib",  "ichem",  "itrb",  "ibase",  "idiss_g"],
        ["ivmod",  "ikmod", "idmod",  "ikv",   "icfl",   "dtfix"],
        ["iorder", "iuem",  "ikve",   "kbl",   "iman"],
        ["npfac",  "npvol"],
        ["cfl",    "epsj",  "wdis"]
    ]
    # Parameter names in [TAILOR] block
    TAILOR_keys = [
        ["igtm", "igtt", "sens"],
        ["ngts", "ngtp", "igti"]
    ]
    # Current values of BCs table
    BCNames = []
    BCTable = {}
    # Mass fractions
    BC_Y = {}
    # Direction cosines
    BC_cos = {}
    # Number of lines in the BC Table
    BCTable_rows = 0
    
  # --- Config ---
    # Initialization method (not based off of FileCntl)
    def __init__(self, fname="input.inp"):
        """Initialization method"""
        # Read the file.
        self.Read(fname)
        # Save the file name.
        self.fname = fname
        # Split into sections.
        self.SplitToBlocks(reg="\[/?([\w_]+)\]", endreg="\[/([\w_]+)\]")
        
    
  # --- Conversions ---
    # Conversion to text
    def ConvertToText(self, v, exp="d", fmt="%s"):
        """Convert a value to text to write in the namelist file
        
        :Call:
            >>> val = inp.ConvertToText(v)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *v*: :class:`str` | :class:`int` | :class:`float` | :class:`list`
                Evaluated value of the text
            *exp*: {``"d"``} | ``"e"`` | ``"E"`` | ``"D"``
                Character to use for exponential notation
            *fmt*: {``"%s"``} | :class:`str`
                C-style format string
        :Outputs:
            *val*: :class:`str` | :class:`unicode`
                Text of the value from file
        :Versions:
            * 2015-10-16 ``@ddalle``: First version
        """
        # Get the type
        t = type(v).__name__
        # Form the output line.
        if t in ['str', 'unicode']:
            # Force quotes
            return '"%s"' % v
        elif t in ['bool'] and v:
            # Boolean
            return ".true."
        elif t in ['bool']:
            # Boolean
            return ".false."
        elif t in ['list', 'ndarray', "tuple"]:
            # List (convert to string first)
            V = [str(vi) for vi in v]
            return " ".join(V)
        elif isinstance(v, float):
            # Use the built-in string converter
            txt = fmt % v
            # Check for integer format
            if ("e" in txt) and ("." not in txt):
                # Redo with forced decimal
                txt = "%.1e" % v
            # Replace "e" with "d", or whatever character
            txt = txt.replace("e", exp)
            # Output
            return txt
        else:
            # Use the built-in string converter
            return str(v)
            
  # --- Sections ---
    # Add a section
    def AddSection(self, sec):
        """Add a section to the ``input.inp`` interface
        
        :Call:
            >>> inp.AddSection(sec)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Versions:
            * 2016-04-22 ``@ddalle``: First version
            * 2019-06-06 ``@ddalle``: Lightly modified from Namelist
        """
        # Escape if already present
        if sec in self.SectionNames:
            return
        # Append the section
        self.SectionNames.append(sec)
        # Add the lines
        self.Section[sec] = [
            '[%s]\n' % sec,
            '[/%s]\n' % sec,
        ]
            
  # --- Data ---
    # Convert a single line of text to values
    def ConvertLineToList(self, line, **kw):
        """Convert a line of space-separated values into parts
        
        :Call:
            >>> header, vals, LV, LS = inp.ConvertLineToList(line, **kw)
        :Inputs:
            *line*: :class:`str`
                Line of text with space-separated values
            *indent*: {``0``} | :class:`int` >= 0
                Number of characters to ignore at beginning of line
        :Outputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *header*: :class:`str`
                First *indent* characters of *line*
            *vals*: :class:`list`\ [:class:`str`]
                List of non-whitespace groups
            *LV*: :class:`list`\ [:class:`int`]
                Lengths of strings in *vals*
            *LS*: :class:`list`\ [:class:`int`]
                Lengths of whitespace groups between values
        :Versions:
            * 2019-06-05 ``@ddalle``: First version
        """
        # Number of spaces in tab
        indent = kw.get("indent", 0)
        # Save tab
        header = line[:indent]
        # Split the remaining portions by white space
        groups = re.findall("\s+[^\s]+", line[indent:])
        # Get non-whitespace groups and lengths of whitespace sections
        tags = [(t.lstrip(), len(t) - len(t.lstrip())) for t in groups]
        # Split columns into values and whitespace lengths
        vals = [t[0] for t in tags]
        lens_sep = [t[1] for t in tags]
        # Get lengths of values
        lens_val = [len(t) for t in vals]
        # Output
        return header, vals, lens_val, lens_sep
        
    # Set one value within a line of text
    def SetLineValueSequential(self, line, i, val, **kw):
        """Set a value in a line that assumes space-separated values
        
        :Call:
            >>> txt = inp.SetLineValueSequential(line, i, val, **kw)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *line*: :class:`str`
                Line of text in space-separated format
            *i*: :class:`int` >= 0
                Index of entry to change/set
            *val*: :class:`any`
                Value to print to entry *i* of modified *line*
            *align*: ``"left"`` | ``"center"`` | {``"right"``}
                Alignment option; determines output spacing
            *delimiter*, *delim*, *sep*: {``"    "`` } | :class:`str`
                Separator when *line* has less than *i* entries
            *delim_len*: {``len(delim)``} | :class:`int` > 0
                Number of spaces to use in default delimiter
            *vdef*: {``"_"``} | :class:`str`
                Default value if line needs additional entries
        :Outputs:
            *txt*: :class:`str`
                Modified *line* with entry *i* set to printed version of *val*
        :See also:
            * :func:`cape.pyus.inputinpfile.InputInp.ConvertToText`
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
       # --- Options ---
        # Alignment option
        align = kw.pop("align", "right")
        # Number of spaces in header
        indent = kw.pop("indent", 0)
        # Default separator
        delim = kw.pop("delimiter", kw.pop("delim", kw.pop("sep", "    ")))
        # Number of spaces in delimiter
        LD = kw.pop("delim_len", len(delim))
        # Default value
        vdef = kw.pop("vdef", kw.pop("val_def", "_"))
       # --- Inputs ---
        # Convert to string
        txt = self.ConvertToText(val, **kw)
        # Length of value
        L = len(txt)
       # --- Pad Lists ---
        # Split up line
        header, vals, LV, LS = self.ConvertLineToList(line, indent=indent)
        # Number of values found
        nval = len(vals)
        # Check length
        if i >= nval:
            # Number of additional values needed
            jval = i - nval + 1
            # Append empty values
            vals = vals + ([vdef] * jval)
            # Expand length lists
            LV = LV + ([len(vdef)] * jval)
            LS = LS + ([LD] * jval)
       # --- Text Updates ---
        # Updated length
        nval = len(vals)
        # Save new value
        vals[i] = txt
        # Update spaces, checking alignment option
        if align == "right":
            # Available string lengths
            L_avail = LS[i] + LV[i]
            # Check if we will overfill the slot
            LS[i] = max(1, L_avail - L)
        elif align == "center":
            # Check for end entry
            if i == nval:
                # Only spaces to the left (so far)
                L1 = LS[i]
                L2 = L1
            else:
                # Spaces on both sides
                L1 = LS[i]
                L2 = LS[i+1]
            # Length of current value
            L0 = LV[i]
            # Total available length
            L_avail = L1 + L0 + L2
            # Spaces left over
            L_ws = max(1, L_avail - L)
            # Calculate space on the left (attempt to keep L/R ratios)
            LS[i] = (L_ws * L1) // (L1 + L2)
            # Space on the right is whatever is left
            if i < nval:
                LS[i+1] = max(1, L_avail - L - LS[i])
        elif align == "right":
            # Check for end entry
            if i < nval:
                # Available string length
                L_avail = LS[i+1] + LV[i] - 1
                # Update space on the right, checking for overfills
                LS[i] = max(1, L_avail - L)
        else:
            raise ValueError(
                ("Alignment option '%s' unknown; " % align) +
                ("options are 'left', 'center', 'right'"))
       # --- Update ---
        # Convert gaps to spaces
        txt_ws = [" "*t for t in LS] 
        # Make a list of spaces followed by values
        txts = [txt_ws[i] + vals[i] for i in range(nval)]
        # Recreate the entire line
        line = header + "".join(txts) + "\n"
        # Output
        return line
        
    # Set a value in a space-separated table section
    def SetSectionTableValue(self, sec, row, col, val, **kw):
        """Set one value in a table-like space-separated section
        
        :Call:
            >>> inp.SetSectionTableValue(sec, row, col, val, **kw)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *row*: :class:`int` >= 0
                Index of non-comment line in section
            *col*: :class:`int` >= 0
                Index of entry in line of text to change/set
            *val*: :class:`any`
                Value to print to entry *i* of modified line
            *comment*: {``"!"``} | :class:`str`
                Character denoting start of comment line
            *skiprows*: {``0``} | :class:`int` >= 0
                Number of non-comment rows to not count towards *row*
            *align*: ``"left"`` | ``"center"`` | {``"right"``}
                Alignment option; determines output spacing
            *delimiter*, *delim*, *sep*: {``"    "`` } | :class:`str`
                Separator when *line* has less than *i* entries
            *delim_len*: {``len(delim)``} | :class:`int` > 0
                Number of spaces to use in default delimiter
            *vdef*: {``"_"``} | :class:`str`
                Default value if line needs additional entries
        :See also:
            * :func:`cape.pyus.inputinpfile.InputInp.SetLineValueSequential`
            * :func:`cape.pyus.inputinpfile.InputInp.ConvertToText`
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        # Get comment character
        comment = kw.pop("comment", kw.pop("comment_char", "!"))
        # Number of non-comment rows to skip
        skiprows = kw.pop("skiprows", 0)
        # Overall row number
        jrow = row + skiprows
        # Counter for number of lines found
        n = 0
        # Check if section is present
        if sec not in self.Section:
            # Add the section
            self.AddSection(sec)
        # Start with line *i0* and loop
        for (i, line) in enumerate(self.Section[sec][1:-1]):
            # Skip if comment
            if line.lstrip().startswith(comment):
                continue
            # Otherwise, increment counter
            n += 1
            # Otherwise, check count
            if n > jrow:
                break
        # Check if we actually found enough non-comment rows
        for j in range(n, jrow + 1):
            # Use blank line
            line = "\n"
            # Append to section (before EOS marker)
            self.Section[sec].insert(-1, line)
            # Update section line counter
            i += 1
        # We skipped section title row
        i += 1
        # Process line
        txt = self.SetLineValueSequential(line, col, val, **kw)
        # Save updated row
        self.Section[sec][i] = txt

    # Get a value from a space-separated table section
    def GetSectionTableValue(self, sec, row, col, vdef=None, **kw):
        r"""Get one value in a table-like space-separated section

        :Call:
            >>> inp.GetSectionTableValue(sec, row, col, val, **kw)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *row*: :class:`int` >= 0
                Index of non-comment line in section
            *col*: :class:`int` >= 0
                Index of entry in line of text to change/set
            *vdef*: {``None``} | :class:`any`
                Default value if line needs additional entries
            *comment*: {``"!"``} | :class:`str`
                Character denoting start of comment line
            *skiprows*: {``0``} | :class:`int` >= 0
                Number of non-comment rows to not count towards *row*
        :Outputs:
            *val*: {*vdef*} | :class:`any`
                Converted value if found; else *vdef*
        :See also:
            * :func:`cape.filecntl.namelist.Namelist.ConvertToVal`
            * :func:`cape.pyus.inputinpfile.InputInp.SetSectionTableValue`
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        # Get comment character
        comment = kw.pop("comment", kw.pop("comment_char", "!"))
        # Number of non-comment rows to skip
        skiprows = kw.pop("skiprows", 0)
        # Overall row number
        jrow = row + skiprows
        # Counter for number of lines found
        n = 0
        # Check if section is present
        if sec not in self.Section:
            return vdef
        # Start with line *i0* and loop
        for (i, line) in enumerate(self.Section[sec][1:-1]):
            # Skip if comment
            if line.lstrip().startswith(comment):
                continue
            # Otherwise, increment counter
            n += 1
            # Otherwise, check count
            if n > jrow:
                break
        # Check if we actually found enough non-comment rows
        if n < jrow:
            return vdef
        # Number of spaces in header
        indent = kw.pop("indent", 0)
        # Split row into values
        vals = line[indent:].split()
        # Check if line has enough values
        if col >= len(vals):
            return vdef
        # Otherwise, convert value
        return self.ConvertToVal(vals[col])
        
    # Get a value from a space-separated table section
    def GetSectionTable(self, sec, **kw):
        """Get entire contents in a table-like space-separated section
        
        :Call:
            >>> table = inp.GetSectionTable(sec, **kw)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *comment*: {``"!"``} | :class:`str`
                Character denoting start of comment line
            *skiprows*: {``0``} | :class:`int` >= 0
                Number of non-comment rows to not count towards *row*
        :Outputs:
            *table*: :class:`list`
                List of values in each row
        :See also:
            * :func:`cape.filecntl.namelist.Namelist.ConvertToVal`
            * :func:`cape.pyus.inputinpfile.InputInp.GetSectionTableValue`
        :Versions:
            * 2019-06-19 ``@ddalle``: First version
        """
        # Get comment character
        comment = kw.pop("comment", kw.pop("comment_char", "!"))
        # Number of non-comment rows to skip
        skiprows = kw.pop("skiprows", 0)
        maxrows  = kw.pop("maxrows", None)
        # Number of spaces in header
        indent = kw.pop("indent", 0)
        # Initialize table
        table = []
        # Counter for number of lines found
        n = 0
        # Check if section is present
        if sec not in self.Section:
            return table
        # Start with line *i0* and loop
        for (i, line) in enumerate(self.Section[sec][1:-1]):
            # Otherwise, check count
            if maxrows and i >= maxrows:
                break
            # Skip if comment
            if line.lstrip().startswith(comment):
                continue
            # Read the line; split into list
            grps = line[indent:].split()
            # Convert to Python values
            vals = [self.ConvertToVal(g) for g in grps]
            # Append to table
            table.append(vals)
        # Output
        return table
        
    # Get a value from a space-separated table section
    def GetSectionTableLines(self, sec, **kw):
        """Get indices of lines in a table-like space-separated section
        
        :Call:
            >>> I = inp.GetSectionTableLines(sec, **kw)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *comment*: {``"!"``} | :class:`str`
                Character denoting start of comment line
            *skiprows*: {``0``} | :class:`int` >= 0
                Number of non-comment rows to not count towards *row*
        :Outputs:
            *I*: :class:`list`\ [:class:`int`]
                List of values in each row
        :See also:
            * :func:`cape.filecntl.namelist.Namelist.ConvertToVal`
            * :func:`cape.pyus.inputinpfile.InputInp.GetSectionTableValue`
        :Versions:
            * 2019-06-19 ``@ddalle``: First version
        """
        # Get comment character
        comment = kw.pop("comment", kw.pop("comment_char", "!"))
        # Number of non-comment rows to skip
        skiprows = kw.pop("skiprows", 0)
        maxrows  = kw.pop("maxrows", None)
        # Initialize line numbers
        I = []
        # Check if section is present
        if sec not in self.Section:
            return I
        # Start with line *i0* and loop
        for (i, line) in enumerate(self.Section[sec][1:-1]):
            # Otherwise, check count
            if maxrows and i >= maxrows:
                break
            # Skip if comment
            if line.lstrip().startswith(comment):
                continue
            # Count this line
            I.append(i)
        # Output
        return I
        
    # Set an entire section table
    def SetSectionTable(self, sec, table, **kw):
        """Set entire contents in a table-like space-separated section
        
        :Call:
            >>> inp.SetSectionTable(sec, table, **kw)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *table*: :class:`list`
                List of values in each row
            *comment*: {``"!"``} | :class:`str`
                Character denoting start of comment line
            *skiprows*: {``0``} | :class:`int` >= 0
                Number of non-comment rows to not count towards *row*
        :Versions:
            * 2019-06-19 ``@ddalle``: First version
        """
        # Create section if necessary
        if sec not in self.Section:
            self.AddSection(sec)
        # Get current non-comment line indices
        I = self.GetSectionTableLines(sec, **kw)
        # Get handle to lines of section
        lines = self.Section[sec]
        # Delete all those lines
        if len(I) > 0:
            # Delete existing lines
            for i in I[::-1]:
                lines.pop(i+1)
            # Get first line
            i0 = I[0] + 1
        else:
            # Insert at beginning of section
            i0 = 1
        # Loop through table in reverse order
        for V in table[::-1]:
            # Convert list entry to text
            line = self.ConvertToText(V) + "\n"
            # Insert the line
            self.Section[sec].insert(i0, line)

  # --- Specific Settings ---
   # [general]
    # Get a generic parameter
    def GetVar(self, sec, key):
        """Get value of *key* from section *sec* of ``input.inp``

        :Call:
            >>> val = inp.GetVar(sec, key)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *key*: :class:`str`
                Name of parameter
        :Outputs:
            *val*: :class:`int` | :class:`float` | ``None``
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-27 ``@ddalle``: First version
        """
        # Check which section
        if sec == "CFD_SOLVER":
            # Tabled list
            return self.get_CFDSOLVER_key(key)
        elif sec == "CFD_SOLVER_OPTS":
            # Namelist
            return self.get_CFDSOLVEROPTS_key(key)
        elif sec == "CFD_BCS":
            # Boundary condition section, check key
            raise NotImplementedError(
                "Interface to CFD_BCS section of input.inp has " +
                "not been generalized.")
        elif sec == "MANAGE":
            # Manage section
            if key in ["flag"]:
                # Get the flag
                return self.get_MANAGE_flag()
            elif key in ["table"]:
                # Get the entire table
                return self.get_MANAGE_table()
            elif key in ["schedule"]:
                # Get the other rows in the table
                return self.get_MANAGE_schedule()
            else:
                # Unknown
                raise ValueError(
                    ("Unknown input.inp parameter '%s' " % key) +
                    ("from MANAGE section"))
        elif sec == "TAILOR":
            # Tabled list
            return self.get_TAILOR_key(key)
        else:
            # What section is this?
            raise ValueError("Unknown input.inp section '%s'" % sec)
   # [/general]

   # [CFD_SOLVER]
    # Generic parameter (get)
    def get_CFDSOLVER_key(self, key):
        """Get value of parameter *key* from ``CFD_SOLVER`` section
        
        :Call:
            >>> val = inp.get_CFDSOLVER_key(key)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *key*: :class:`str`
                Name of parameter
        :Outputs:
            *val*: :class:`int` | :class:`float` | ``None``
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        # Initialize column index
        col = None
        # Loop through rows
        for (i, row) in enumerate(self.CFD_SOLVER_keys):
            # Check if *k* is in row
            if key in row:
                # Get index
                col = row.index(key)
                # Stop searching
                break
        # If not found, raise exception
        if col is None:
            raise KeyError("CFD_SOLVER parameter '%s' not known" % k)
        # Otherwise, return the value
        return self.GetSectionTableValue("CFD_SOLVER", i, col)
    
    # Generic parameter (set)
    def set_CFDSOLVER_key(self, key, val):
        """Get value of parameter *key* from ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_key(key, val)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *key*: :class:`str`
                Name of parameter
            *val*: :class:`int` | :class:`float` | ``None``
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        # Initialize column index
        col = None
        # Loop through rows
        for (i, row) in enumerate(self.CFD_SOLVER_keys):
            # Check if *k* is in row
            if key in row:
                # Get index
                col = row.index(key)
                # Stop searching
                break
        # If not found, raise exception
        if col is None:
            raise KeyError("CFD_SOLVER parameter '%s' not known" % key)
        # Otherwise, return the value
        return self.SetSectionTableValue("CFD_SOLVER", i, col, val)
        
    # Hard-coded methods
    def get_CFDSOLVER_nstop(self):
        """Get *nstop* from ``CFD_SOLVER`` section
        
        :Call:
            >>> nstop = inp.get_CFDSOLVER_nstop()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *nstop*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 0, 0)
        
    def set_CFDSOLVER_nstop(self, nstop):
        """Set *nstop* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_nstop(nstop)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *nstop*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 0, 0, nstop)
    
    def get_CFDSOLVER_ires(self):
        """Get *ires* from ``CFD_SOLVER`` section
        
        :Call:
            >>> ires = inp.get_CFDSOLVER_ires()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *ires*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 0, 1)
        
    def set_CFDSOLVER_ires(self, ires):
        """Set *ires* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_nstop(nstop)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *ires*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 0, 1, ires)
    
    def get_CFDSOLVER_nplot(self):
        """Get *nplot* from ``CFD_SOLVER`` section
        
        :Call:
            >>> nplot = inp.get_CFDSOLVER_nplot()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *nplot*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 0, 2)
        
    def set_CFDSOLVER_nplot(self, nplot):
        """Set *nplot* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_nstop(nstop)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *nplot*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 0, 2, nplot)
    
    def get_CFDSOLVER_iconr(self):
        """Get *iconr* from ``CFD_SOLVER`` section
        
        :Call:
            >>> iconr = inp.get_CFDSOLVER_iconr()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *iconr*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 0, 3)
        
    def set_CFDSOLVER_iconr(self, iconr):
        """Set *nplot* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_iconr(iconr)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *iconr*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 0, 3, iconr)
    
    def get_CFDSOLVER_impl(self):
        """Get *impl* from ``CFD_SOLVER`` section
        
        :Call:
            >>> impl = inp.get_CFDSOLVER_impl()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *impl*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 0, 4)
        
    def set_CFDSOLVER_impl(self, impl):
        """Set *impl* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_impl(impl)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *impl*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 0, 4, impl)
    
    def get_CFDSOLVER_kmax(self):
        """Get *kmax* from ``CFD_SOLVER`` section
        
        :Call:
            >>> kmax = inp.get_CFDSOLVER_kmax()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *kmax*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 0, 5)
        
    def set_CFDSOLVER_kmax(self, nplot):
        """Set *kmax* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_kmax(kmax)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *kmax*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 0, 5, kmax)
    
    def get_CFDSOLVER_kmaxo(self):
        """Get *kmaxo* from ``CFD_SOLVER`` section
        
        :Call:
            >>> kmaxo = inp.get_CFDSOLVER_kmaxo()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *kmaxo*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 0, 6)
        
    def set_CFDSOLVER_kmaxo(self, nplot):
        """Set *kmaxo* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_kmaxo(kmaxo)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *kmaxo*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 0, 6, ires)
    
    def get_CFDSOLVER_ivisc(self):
        """Get *ivisc* from ``CFD_SOLVER`` section
        
        :Call:
            >>> ivisc = inp.get_CFDSOLVER_ivisc()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *ivisc*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 1, 0)
        
    def set_CFDSOLVER_ivisc(self, ivisc):
        """Set *ivisc* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_(ivisc)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *ivisc*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 1, 0, ivisc)
    
    def get_CFDSOLVER_ivib(self):
        """Get *ivib* from ``CFD_SOLVER`` section
        
        :Call:
            >>> ivib = inp.get_CFDSOLVER_ivib()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *ivib*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 1, 1)
        
    def set_CFDSOLVER_ivib(self, nplot):
        """Set *ivib* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_ivib(ivib)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *ivib*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 1, 1, ivib)
    
    def get_CFDSOLVER_ichem(self):
        """Get *ichem* from ``CFD_SOLVER`` section
        
        :Call:
            >>> ichem = inp.get_CFDSOLVER_ichem()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *ichem*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 1, 2)
        
    def set_CFDSOLVER_ichem(self, nplot):
        """Set *ichem* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_ichem(ichem)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *ichem*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 1, 2, ichem)
    
    def get_CFDSOLVER_itrb(self):
        """Get *itrb* from ``CFD_SOLVER`` section
        
        :Call:
            >>> itrb = inp.get_CFDSOLVER_itrb()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *itrb*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 1, 3)
        
    def set_CFDSOLVER_itrb(self, itrb):
        """Set *itrb* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_itrb(itrb)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *itrb*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 1, 3, itrb)
    
    def get_CFDSOLVER_ibase(self):
        """Get *ibase* from ``CFD_SOLVER`` section
        
        :Call:
            >>> ibase = inp.get_CFDSOLVER_ibase()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *ibase*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 1, 4)
        
    def set_CFDSOLVER_ibase(self, ibase):
        """Set *ibase* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_ibase(ibase)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *ibase*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 1, 4, ibase)
    
    def get_CFDSOLVER_idiss_g(self):
        """Get *idiss_g* from ``CFD_SOLVER`` section
        
        :Call:
            >>> idiss_g = inp.get_CFDSOLVER_idiss_g()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *idiss_g*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 1, 5)
        
    def set_CFDSOLVER_idiss_g(self, nplot):
        """Set *idiss_g* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_idiss_g(idiss_g)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *idiss_g*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 1, 5, idiss_g)
    
    def get_CFDSOLVER_ivmod(self):
        """Get *ivmod* from ``CFD_SOLVER`` section
        
        :Call:
            >>> ivmod = inp.get_CFDSOLVER_ivmod()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *ivmod*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 2, 0)
        
    def set_CFDSOLVER_ivmod(self, ivmod):
        """Set *ivmod* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_ivmod(ivmod)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *ivmod*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 2, 0, ivmod)
    
    def get_CFDSOLVER_ikmod(self):
        """Get *ikmod* from ``CFD_SOLVER`` section
        
        :Call:
            >>> ikmod = inp.get_CFDSOLVER_ikmod()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *ikmod*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 2, 1)
        
    def set_CFDSOLVER_ikmod(self, ikmod):
        """Set *ikmod* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_(ikmod)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *ikmod*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 2, 1, ikmod)
    
    def get_CFDSOLVER_idmod(self):
        """Get *idmod* from ``CFD_SOLVER`` section
        
        :Call:
            >>> idmod = inp.get_CFDSOLVER_idmod()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *idmod*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 2, 2)
        
    def set_CFDSOLVER_idmod(self, idmod):
        """Set *idmod* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_idmod(idmod)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *idmod*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 2, 2, idmod)
    
    def get_CFDSOLVER_ikv(self):
        """Get *ikv* from ``CFD_SOLVER`` section
        
        :Call:
            >>> ikv = inp.get_CFDSOLVER_ikv()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *ikv*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 2, 3)
        
    def set_CFDSOLVER_ikv(self, ikv):
        """Set *ikv* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_ikv(ikv)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *ikv*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 2, 3, ikv)
    
    def get_CFDSOLVER_icfl(self):
        """Get *icfl* from ``CFD_SOLVER`` section
        
        :Call:
            >>> icfl = inp.get_CFDSOLVER_icfl()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *icfl*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 2, 4)
        
    def set_CFDSOLVER_icfl(self, icfl):
        """Set *icfl* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_icfl(icfl)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *icfl*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 2, 4, icfl)
    
    def get_CFDSOLVER_dtfix(self):
        """Get *dtfix* from ``CFD_SOLVER`` section
        
        :Call:
            >>> dtfix = inp.get_CFDSOLVER_dtfix()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *dtfix*: :class:`float`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 2, 5)
        
    def set_CFDSOLVER_dtfix(self, dtfix):
        """Set *dtfix* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_dtfix(dtfix)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *dtfix*: :class:`float`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 2, 5, dtfix)
    
    def get_CFDSOLVER_iorder(self):
        """Get *iorder* from ``CFD_SOLVER`` section
        
        :Call:
            >>> iorder = inp.get_CFDSOLVER_iorder()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *iorder*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 3, 0)
        
    def set_CFDSOLVER_iorder(self, iorder):
        """Set *iorder* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_iorder(iorder)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *iorder*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 3, 0, iorder)
    
    def get_CFDSOLVER_iuem(self):
        """Get *iuem* from ``CFD_SOLVER`` section
        
        :Call:
            >>> iuem = inp.get_CFDSOLVER_iuem()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *iuem*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 3, 1)
        
    def set_CFDSOLVER_iuem(self, iuem):
        """Set *iuem* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_iuem(iuem)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *iuem*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 3, 1, iuem)
    
    def get_CFDSOLVER_ikve(self):
        """Get *nplot* from ``CFD_SOLVER`` section
        
        :Call:
            >>> ikve = inp.get_CFDSOLVER_ikve()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *ikve*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 3, 2)
        
    def set_CFDSOLVER_ikve(self, ikve):
        """Set *ikve* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_ikve(ikve)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *ikve*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 3, 2, ikve)
    
    def get_CFDSOLVER_kbl(self):
        """Get *kbl* from ``CFD_SOLVER`` section
        
        :Call:
            >>> kbl = inp.get_CFDSOLVER_kbl()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *kbl*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 3, 3)
        
    def set_CFDSOLVER_kbl(self, kbl):
        """Set *kbl* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_kbl(kbl)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *kbl*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 3, 3, kbl)
    
    def get_CFDSOLVER_iman(self):
        """Get *iman* from ``CFD_SOLVER`` section
        
        :Call:
            >>> iman = inp.get_CFDSOLVER_iman()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *iman*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 3, 4)
        
    def set_CFDSOLVER_iman(self, iman):
        """Set *iman* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_iman(iman)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *iman*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 3, 4, iman)
    
    def get_CFDSOLVER_npfac(self):
        """Get *npfac* from ``CFD_SOLVER`` section
        
        :Call:
            >>> npfac = inp.get_CFDSOLVER_npfac()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *npfac*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 4, 0)
        
    def set_CFDSOLVER_npfac(self, npfac):
        """Set *npfac* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_npfac(npfac)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *npfac*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 4, 0, npfac)
    
    def get_CFDSOLVER_npvol(self):
        """Get *npvol* from ``CFD_SOLVER`` section
        
        :Call:
            >>> npvol = inp.get_CFDSOLVER_npvol()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *npvol*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 4, 1)
        
    def set_CFDSOLVER_npvol(self, npvol):
        """Set *npvol* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_npvol(npvol)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *npvol*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 4, 1, npvol)
    
    def get_CFDSOLVER_cfl(self):
        """Get *cfl* from ``CFD_SOLVER`` section
        
        :Call:
            >>> cfl = inp.get_CFDSOLVER_cfl()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *cfl*: :class:`float`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 5, 0)
        
    def set_CFDSOLVER_cfl(self, cfl):
        """Set *cfl* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_cfl(cfl)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *cfl*: :class:`float`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 5, 0, cfl)
    
    def get_CFDSOLVER_epsj(self):
        """Get *epsj* from ``CFD_SOLVER`` section
        
        :Call:
            >>> epsj = inp.get_CFDSOLVER_epsj()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *epsj*: :class:`float`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 5, 1)
        
    def set_CFDSOLVER_epsj(self, epsj):
        """Set *epsj* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_epsj(epsj)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *epsj*: :class:`float`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 5, 1, epsj)
    
    def get_CFDSOLVER_wdis(self):
        """Get *wdis* from ``CFD_SOLVER`` section
        
        :Call:
            >>> wdis = inp.get_CFDSOLVER_wdis()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *wdis*: :class:`float`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("CFD_SOLVER", 5, 2)
        
    def set_CFDSOLVER_wdis(self, wdis):
        """Set *wdis* in ``CFD_SOLVER`` section
        
        :Call:
            >>> inp.set_CFDSOLVER_wdis(wdis)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *wdis*: :class:`float`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("CFD_SOLVER", 5, 2, wdis)
   # [/CFD_SOLVER]
   
   # [CFD_SOLVER_OPTS]
    # Generic parameter (get)
    def get_CFDSOLVEROPTS_key(self, key):
        """Get parameter *key* from ``CFD_SOLVER_OPTS`` section
        
        :Call:
            >>> val = inp.get_CFDSOLVEROPTS_key(key)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *key*: :class:`str`
                Name of parameter
        :Outputs:
            *val*: :class:`int` | :class:`float` | ``None``
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        # Output
        return self.GetVar("CFD_SOLVER_OPTS", key)

    # Generic parameter (set)
    def set_CFDSOLVEROPTS_key(self, key, val):
        """Get parameter *key* from ``CFD_SOLVER_OPTS`` section
        
        :Call:
            >>> val = inp.get_CFDSOLVEROPTS_key(key)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *key*: :class:`str`
                Name of parameter
            *val*: :class:`int` | :class:`float` | ``None``
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        # Output
        return self.SetVar("CFD_SOLVER_OPTS", key, val, tab="")
   # [/CFD_SOLVER_OPTS]
   
   # [CFD_BCS]
    # Read BCs table
    def ReadBCs(self):
        r"""Read boundary condition table
        
        :Call:
            >>> BCs = inp.ReadBCs()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *BCs*: :class:`dict`
                Dictionary of *zone*, *bcn*, *igrow*, *name*, and
                *params* for each boundary condition
        :Attributes:
            *inp.BCNames*: :class:`list`\ [:class:`str`]
                List of boundary condition names
            *inp.BCTable*: *BCs*
                Boundary condition properties
            *inp.BCTable_rows*: :class:`int`
                Number of rows in the BC table section
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        # Name of section
        sec = "CFD_BCS"
        # Check if section is present
        if sec not in self.Section:
            # Don't update tables
            return self.BCTable
        # Initialize properties
        BCTable = {}
        BCNames = []
        BCRows = {}
        BC_Y = {}
        BC_cos = {}
        # Number of zones found
        nzone = 0
        # Loop through rows
        for (i, line) in enumerate(self.Section[sec][1:-1]):
            # Check if line is a comment
            if line.lstrip().startswith("!"):
                # Comment
                continue
            elif line.strip() == "":
                # Empty line
                continue
            # Check if table is over
            if line.strip() == "done":
                # End of table
                self.BCTable_rows = i + 1
                break
            # Otherwise, process the line
            V = line.strip().split()
            # Check line length
            if len(V) < 4:
                raise ValueError(
                    "Boundary condition %i has only %i/%i required columns"
                    % (nzone+1, len(V), 4))
            # Get name
            name = V[3].strip('"').strip("'")
            # Append to list
            BCNames.append(name)
            # Save required parameters
            BCTable[name] = {
                "row":    i + 1,
                "zone":   self.ConvertToVal(V[0]),
                "bcn":    self.ConvertToVal(V[1]),
                "igrow":  self.ConvertToVal(V[2]),
                "params": " ".join(V[4:]),
            }
        # Loop through remaining rows
        # Save values
        self.BCTable = BCTable
        self.BCNames = BCNames
        # Output
        return BCTable

    # Read mass fractions
    def GetBCMassFraction(self, name, i=None):
        r"""Get boundary condition mass fraction(s) for specified BC
        
        :Call:
            >>> Y = inp.GetBCMassFraction(name)
            >>> y = inp.GetBCMassFraction(name, i)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *name*: :class:`str`
                Name of boundary condition zone
            *i*: {``None``} | :class:`int` >= 0
                Species index
        :Outputs:
            *y*: :class:`float` | ``None``
                Mass fraction of species *i*
            *Y*: :class:`list`\ [:class:`float`]
                List of species mass fractions
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        # Name of section
        sec = "CFD_BCS"
        # Check if section is present
        if sec not in self.Section:
            # Nothing to search
            return
        # Regular expression to search for
        regex = "^\s*['\"]%s['\"]" % name
        # Use section searcher for lines starting with whitespace plus name
        lines = self.GetLineInSectionSearch(sec, regex, 1)
        # Check for a match
        if len(lines) < 1:
            return
        # Separate line into space-separated values
        txts = lines[0].split()[1:]
        # Evaluate each entry
        vals = [self.ConvertToVal(txt) for txt in txts]
        # Check for index
        if i is None:
            # Return entire
            return vals
        elif i < len(vals):
            # Return indexed value
            return vals[i]
            
    # Set mass fraction
    def SetBCMassFraction(self, name, Y, i=None):
        """Set list of boundary condition mass fraction(s)
        
        
        :Call:
            >>> inp.SetBCMassFraction(name, Y)
            >>> inp.SetBCMassFraction(name, y, i)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *name*: :class:`str`
                Name of boundary condition zone
            *y*: :class:`float` | ``None``
                Mass fraction of species *i*
            *Y*: :class:`list`\ [:class:`float`]
                List of species mass fractions
            *i*: {``None``} | :class:`int` >= 0
                Species index
        :Versions:
            * 2019-06-19 ``@ddalle``: First version
        """
        # Check if setting list or one species
        if i is not None:
            # Get existing values
            Y0 = self.GetBCMassFraction(name)
            # Append if necessary
            for j in range(len(Y0), i):
                Y0.append(0.0)
            # Set value
            Y0[i] = Y
            # Transfer variables
            Y = Y0
        # Convert to text
        Ytxt = self.ConvertToText(Y)
        # Relevant section name
        sec = "CFD_BCS"
        # Regular expression to search for
        regex = "^\s*['\"]%s['\"]" % name
        # Use section searcher for lines starting with whitespace plus name
        lines = self.GetLineInSectionSearch(sec, regex, 1)
        # Check for a match
        if len(lines) < 1:
            # No existing line; use default of two leading spaces
            line0 = '  "%s"' % name
        else:
            # Replace the *first* line
            line0 = lines[0]
        # Copy previous number of spaces
        indent = re.match("\s*", line0).group()
        # Create output line
        line = indent + ('"%s"  ' % name) + Ytxt + "\n"
        # Set the line
        self.ReplaceOrAddLineToSectionStartsWith(sec, line0, line)
        
    # Get direction cosines
    def GetBCDirectionCosines(self, name="inflow", i=None):
        """Get direction cosine(s) for specified BC
        
        :Call:
            >>> U = inp.GetBCDirectionCosines(name="inflow")
            >>> u = inp.GetBCDirectionCosines(name="inflow", i)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *name*: {``"inflow"``} | :class:`str`
                Name of boundary condition zone
            *i*: {``None``} | :class:`int` >= 0 <= *i* < 3
                Axis index
        :Outputs:
            *u*: :class:`float` | ``None``
                Direction cosine for BC *name*, index *i*
            *U*: :class:`list`\ [:class:`float`] (size=3)
                Unit vector of direction cosine
        :Versions:
            * 2019-06-19 ``@ddalle``: First version
        """
        # Name of section
        sec = "CFD_BCS"
        # Check if section is present
        if sec not in self.Section:
            # Nothing to search
            return
        # Regular expression to search for
        regex = "^\s*['\"]%s['\"]" % name
        # Use section searcher for lines starting with whitespace plus name
        lines = self.GetLineInSectionSearch(sec, regex, 2)
        # Check for a match
        if len(lines) < 2:
            return
        # Separate line into space-separated values
        txts = lines[1].split()[1:]
        # Evaluate each entry
        vals = [self.ConvertToVal(txt) for txt in txts]
        # Check for index
        if i is None:
            # Return entire
            return vals
        elif i < len(vals):
            # Return indexed value
            return vals[i]
            
    # Set direction cosines
    def SetBCDirectionCosines(self, U, name="inflow", i=None):
        """Set direction cosine(s) for specified BC
        
        :Call:
            >>> inp.GetBCDirectionCosines(U, name="inflow")
            >>> inp.GetBCDirectionCosines(u, name="inflow", i=None)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *u*: :class:`float` | ``None``
                Direction cosine for BC *name*, index *i*
            *U*: :class:`list`\ [:class:`float`] (size=3)
                Unit vector of direction cosine
            *name*: {``"inflow"``} | :class:`str`
                Name of boundary condition zone
            *i*: {``None``} | :class:`int` >= 0 <= *i* < 3
                Axis index
        :Versions:
            * 2019-06-19 ``@ddalle``: First version
        """
        # Check if setting list or one species
        if i is not None:
            # Get existing values
            U0 = self.GetBCDirectionCosines(name)
            # Append if necessary
            for j in range(len(U0), i):
                U0.append(0.0)
            # Set value
            U0[i] = U
            # Transfer variables
            U = U0
        # Convert to text
        Utxt = self.ConvertToText(U)
        # Relevant section name
        sec = "CFD_BCS"
        # Regular expression to search for
        regex = "^\s*['\"]%s['\"]" % name
        # Use section searcher for lines starting with whitespace plus name
        lines = self.GetLineInSectionSearch(sec, regex, 2)
        # Check for a match
        if len(lines) < 2:
            # No existing line; use default of two leading spaces
            line0 = '  "%s" NEW' % name
        else:
            # Replace the *second* line
            line0 = lines[1]
        # Copy previous number of spaces
        indent = re.match("\s*", line0).group()
        # Create output line
        line = indent + ('"%s"  ' % name) + Utxt + "\n"
        # Set the line
        self.ReplaceOrAddLineToSectionStartsWith(sec, line0, line)
   # [/CFD_BCS]

   # [CFD_BCS/param]
    # Set BC parameter
    def SetBCParam(self, name, param, i=None):
        r"""Set BC "params" for specified BC

        :Call:
            >>> inp.SetBCParam(name, param, i=None)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *name*: :class:`str`
                Name of boundary condition zone
            *param*: :class:`str` | :class:`float` | :class:`list`
                Parameter or array of parameters to set
            *i*: {``None``} | :class:`int` >= 0
                Parameter index
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        # Process the BCs
        bcs = self.ReadBCs()
        # Check if BC is present
        if name not in bcs:
            raise KeyError("No BC named '%s'" % name)
        # Get the row
        row = bcs[name].get("row")
        # Make sure that worked
        if row is None:
            raise ValueError(
                "Could not determine line number for BC '%s'" % name)
        # Get the line
        line0 = self.Section["CFD_BCS"][row]
        # Set it
        if i is None:
            # Check for array
            if isinstance(param, (list, np.ndarray)):
                # Copy line
                line = line0
                # Loop through entries
                for (j, v) in enumerate(param):
                    # Set parameter
                    line = self.SetLineValueSequential(line, j+4, v)
            else:
                # Set entire parameter to this value
                line = self.SetLineValueSequential(line, 4, param)
        else:
            # Set indexed value
            line = self.SetLineValueSequential(line0, i + 4, param)
        # Save the new line
        self.ReplaceLineInSectionStartsWith("CFD_BCS", line0, line)

    # Get parameter
    def GetBCParam(self, name, i=None):
        r"""Get value of BC parameter by index

        :Call:
            >>> param = inp.GetBCParam(name, i=None)
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *name*: :class:`str`
                Name of boundary condition zone
            *i*: {``None``} | :class:`int` >= 0
                Parameter index
        :Param:
            *param*: :class:`str` | :class:`float` | :class:`list`
                Parameter or list of parameters to set
        :Versions:
            * 2020-04-27 ``@ddalle``: First version
        """
        # Get BC table
        bcs = self.ReadBCs()
        # Check if BC is present
        if name not in bcs:
            return
        # Get "params" key
        params = bcs[name].get("params")
        # Check if no parameters
        if params is None:
            return
        # Convert params
        if i is None:
            # Return entire parameter set
            return self.ConvertToVal(params)
        else:
            # Split params
            txts = params.split()
            # Ensure there are enough
            if i >= len(txts):
                # Not enough parameters
                return
            else:
                # Convert value
                return self.ConverToVal(txts[i])

    # Set density
    def SetDensity(self, v, name="inflow"):
        r"""Set density on inflow boundary condition

        :Call:
            >>> inp.SetDensity(v, name="inflow")
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *v*: :class:`float` | :class:`str`
                Value of freestream density to set
            *name*: {``"inflow"``} | :class:`str`
                Name of boundary condition zone
        :Versions:
            * 2020-04-27 ``@ddalle``: First version
        """
        # Set first *param* for BC
        self.SetBCParam(name, v, i=0)

    # Set freestream temperature
    def SetTemperature(self, v, name="inflow"):
        r"""Set static temperature on inflow boundary condition

        :Call:
            >>> inp.SetTemperature(v, name="inflow")
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *v*: :class:`float` | :class:`str`
                Value of freestream static temperature
            *name*: {``"inflow"``} | :class:`str`
                Name of boundary condition zone
        :Versions:
            * 2020-04-28 ``@ddalle``: First version
        """
        # Set second *param* for BC
        self.SetBCParam(name, v, i=1)

    # Set freestream temperature
    def SetVibTemp(self, v, name="inflow"):
        r"""Set vibrational temperature on inflow boundary condition

        :Call:
            >>> inp.SetVibTemp(v, name="inflow")
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *v*: :class:`float` | :class:`str`
                Value of freestream vibrational temperature
            *name*: {``"inflow"``} | :class:`str`
                Name of boundary condition zone
        :Versions:
            * 2020-04-28 ``@ddalle``: First version
        """
        # Set third *param* for BC
        self.SetBCParam(name, v, i=2)

    # Set freestream velocity
    def SetVelocity(self, v, name="inflow"):
        r"""Set vibrational temperature on inflow boundary condition

        :Call:
            >>> inp.SetVibTemp(v, name="inflow")
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *v*: :class:`float` | :class:`str`
                Value of freestream vibrational temperature
            *name*: {``"inflow"``} | :class:`str`
                Name of boundary condition zone
        :Versions:
            * 2020-04-28 ``@ddalle``: First version
        """
        # Set fourth *param* for BC
        self.SetBCParam(name, v, i=3)

    # Set wall temperature
    def SetTWall(self, v, name="wall"):
        r"""Set wall temperature on one BC

        :Call:
            >>> inp.SetTWall(v, name="wall")
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *v*: :class:`float` | :class:`str`
                Value of wall temperature
            *name*: {``"wall"``} | :class:`str`
                Name of boundary condition zone
        :Versions:
            * 2020-04-28 ``@ddalle``: First version
        """
        # Set second *param* for BC
        self.SetBCParam(name, v, i=1)

    # Set wall temperature mode
    def SetIWall(self, v, name="wall"):
        r"""Set wall temperature mode on one BC

        :Call:
            >>> inp.SetIWall(v, name="wall")
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *v*: :class:`int` | :class:`str`
                Mode for wall temperature BC
            *name*: {``"wall"``} | :class:`str`
                Name of boundary condition zone
        :Versions:
            * 2020-04-28 ``@ddalle``: First version
        """
        # Convert floats to int
        if isinstance(v, float):
            v = int(v)
        # Set first *param* for BC
        self.SetBCParam(name, v, i=0)
   # [/CFD_BCS/param]

   # [CFD_BCS/table]
    # Set BC table
    def SetBCTableParam(self, name, v, i):
        r"""Set BC table parameter

        :Call:
            >>> inp.SetBCTableParam(name, v, i)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *name*: :class:`str`
                Name of boundary condition zone
            *v*: :class:`str` | :class:`int`
                Parameter or string 
            *i*: :class:`int` >= 0
                Table column index
        :Versions:
            * 2020-04-28 ``@ddalle``: First version
        """
        # Check inputs
        if isinstance(v, (list, np.ndarray)):
            raise TypeError("Cannot set list in BC table")
        elif i < 0:
            raise ValueError("Cannot use negative BC table column index")
        elif i > 2:
            raise ValueError("Cannot set BC table beyond column 3")
        # Process the BCs
        bcs = self.ReadBCs()
        # Check if BC is present
        if name not in self.bcs:
            raise KeyError("No BC named '%s'" % name)
        # Get the row
        row = bcs[name].get("row")
        # Make sure that worked
        if row is None:
            raise ValueError(
                "Could not determine line number for BC '%s'" % name)
        # Get the line
        line0 = self.Section["CFD_BCS"][row]
        # Set indexed value
        line = self.SetLineValueSequential(line0, i, v)
        # Save the new line
        self.ReplaceLineInSectionStartsWith("CFD_BCS", line0, line)

    # Set zone
    def SetBCZone(self, name, zone):
        r"""Set *zone* for a BC by name

        :Call:
            >>> inp.SetBCZone(name, zone)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *name*: :class:`str`
                Name of boundary condition zone
            *zone*: :class:`str` | :class:`int`
                Zone number
        :Versions:
            * 2020-04-28 ``@ddalle``: First version
        """
        # Set first column
        self.SetBCTableParam(name, zone, 0)

    # Set *bcn*
    def SetBCNum(self, name, bcn):
        r"""Set *bcn* for a BC by name

        :Call:
            >>> inp.SetBCNum(name, bcn)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *name*: :class:`str`
                Name of boundary condition zone
            *bcn*: :class:`str` | :class:`int`
                Boundary condition number
        :Versions:
            * 2020-04-28 ``@ddalle``: First version
        """
        # Set second column
        self.SetBCTableParam(name, bcn, 1)

    # Set *igrow*
    def SetBCIGrow(self, name, igrow):
        r"""Set *igrow* for a BC by name

        :Call:
            >>> inp.SetBCIGrow(name, igrow)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *name*: :class:`str`
                Name of boundary condition zone
            *igrow*: :class:`str` | :class:`int`
                BC growth parameter
        :Versions:
            * 2020-04-28 ``@ddalle``: First version
        """
        # Set third column
        self.SetBCTableParam(name, igrow, 2)

    # Set *igrow*
    def SetIGrow(self, igrow, name="wall"):
        r"""Set *igrow* for a BC by name

        :Call:
            >>> inp.SetBCIGrow(name, igrow)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *igrow*: :class:`str` | :class:`int`
                BC growth parameter
            *name*: {``"wall"``} | :class:`str`
                Name of boundary condition zone
        :Versions:
            * 2020-04-28 ``@ddalle``: First version
        """
        # Set third column
        self.SetBCIGrow(name, igrow)
   # [/CFD_BCS/table]
   
   # [CFD_BCS/angles]
    # Get angle of attack
    def GetAlpha(self, name="inflow"):
        r"""Get angle of attack for specified BC
        
        :Call:
            >>> alpha = inp.GetAlpha(name="inflow")
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *name*: {``"inflow"``} | :class:`str`
                Name of boundary condition zone
        :Outputs:
            *alpha*: :class:`float`
                Angle of attack [deg] (``0.0`` if not specified)
        :Versions:
            * 2019-06-19 ``@ddalle``: First version
        """
        # Get direction cosines
        U = self.GetBCDirectionCosines(name)
        # Check validity
        if len(U) != 3:
            # Invalid length
            return 0.0
        elif any([not isinstance(u, (int, float)) for u in U]):
            # At least one non-float
            return 0.0
        # Unpack values
        u, v, w = U
        # Calculate length
        V = np.sqrt(u*u + v*v + w*w)
        # Check zero length
        if V <= 1e-6:
            return 0.0
        # Otherwise, convert to values
        alpha, beta = convert.DirectionCosines2AlphaBeta(u, v, w)
        # Return angle of attack
        return alpha
        
    # Get angle of sideslip
    def GetBeta(self, name="inflow"):
        """Get angle of sideslip for specified BC
        
        :Call:
            >>> beta = inp.GetBeta(name="inflow")
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *name*: {``"inflow"``} | :class:`str`
                Name of boundary condition zone
        :Outputs:
            *beta*: :class:`float`
                Angle of sideslip [deg] (``0.0`` if not specified)
        :Versions:
            * 2019-06-19 ``@ddalle``: First version
        """
        # Get direction cosines
        U = self.GetBCDirectionCosines(name)
        # Check validity
        if len(U) != 3:
            # Invalid length
            return 0.0
        elif any([not isinstance(u, (int, float)) for u in U]):
            # At least one non-float
            return 0.0
        # Unpack values
        u, v, w = U
        # Calculate length
        V = np.sqrt(u*u + v*v + w*w)
        # Check zero length
        if V <= 1e-6:
            return 0.0
        # Otherwise, convert to angles
        alpha, beta = convert.DirectionCosines2AlphaBeta(u, v, w)
        # Return angle of sideslip
        return beta
        
    # Set angle of attack
    def SetAlpha(self, alpha, name="inflow"):
        """Set angle of attack for specified BC
        
        :Call:
            >>> inp.SetAlpha(alpha, name="inflow")
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *name*: {``"inflow"``} | :class:`str`
                Name of boundary condition zone
            *alpha*: :class:`float`
                Angle of attack [deg] (``0.0`` if not specified)
        :Versions:
            * 2019-06-19 ``@ddalle``: First version
        """
        # Get sideslip angle
        beta = self.GetBeta(name=name)
        # Calculate direction cosines
        U = convert.AlphaBeta2DirectionCosines(alpha, beta)
        # Set those direction cosines
        self.SetBCDirectionCosines(U, name=name)
        
    # Set angle of sideslip
    def SetBeta(self, beta, name="inflow"):
        """Set angle of sideslip for specified BC
        
        :Call:
            >>> inp.SetBeta(beta, name="inflow")
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *name*: {``"inflow"``} | :class:`str`
                Name of boundary condition zone
            *beta*: :class:`float`
                Angle of sideslip [deg] (``0.0`` if not specified)
        :Versions:
            * 2019-06-19 ``@ddalle``: First version
        """
        # Get angle of attack
        alpha = self.GetAlpha(name=name)
        # Calculate direction cosines
        U = convert.AlphaBeta2DirectionCosines(alpha, beta)
        # Set those direction cosines
        self.SetBCDirectionCosines(U, name=name)
   # [/CFD_BCS/angles]
   
   # [MANAGE]
    # Get first entry
    def get_MANAGE_flag(self):
        """Get flag from *MANAGE* section, first table entry
        
        :Call:
            >>> flag = inp.get_MANAGE_table()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *flag*: :class:`int` >= 0
                Flag for what action for US3D to take
        :Versions:
            * 2019-06-19 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("MANAGE", 0, 0)
        
    # Get manage section table
    def get_MANAGE_schedule(self):
        """Get CFL schedule from *MANAGE* section
        
        :Call:
            >>> table = inp.get_MANAGE_schedule()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *table*: :class:`list`
                List of values in each row
        :Versions:
            * 2019-06-19 ``@ddalle``: First version
        """
        # Get the entire table
        table = self.get_MANAGE_table()
        # Skip first entry
        return table[1:]
        
    # Get manage section table
    def get_MANAGE_table(self):
        """Get entire table of *MANAGE* CFL schedule
        
        :Call:
            >>> table = inp.get_MANAGE_table()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *table*: :class:`list`
                List of values in each row
        :Versions:
            * 2019-06-19 ``@ddalle``: First version
        """
        return self.GetSectionTable("MANAGE")

    # Set manage section table
    def set_MANAGE_table(self, table):
        """Set entire table of *MANAGE* CFL schedule
        
        :Call:
            >>> inp.set_MANAGE_table(table)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *table*: :class:`list`
                List of values in each row
        :Versions:
            * 2019-06-19 ``@ddalle``: First version
        """
        self.SetSectionTable("MANAGE", table)
   # [/MANAGE]
   
   # [TAILOR]
    # Generic parameter (get)
    def get_TAILOR_key(self, key):
        """Get value of parameter *key* from ``TAILOR`` section
        
        :Call:
            >>> val = inp.get_TAILOR_key(key)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *key*: :class:`str`
                Name of parameter
        :Outputs:
            *val*: :class:`int` | :class:`float` | ``None``
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        # Initialize column index
        col = None
        # Loop through rows
        for (i, row) in enumerate(self.TAILOR_keys):
            # Check if *k* is in row
            if key in row:
                # Get index
                col = row.index(key)
                # Stop searching
                break
        # If not found, raise exception
        if col is None:
            # Use namelist
            return self.GetVar("TAILOR", key)
        # Otherwise, return the value
        return self.GetSectionTableValue("TAILOR", i, col)
    
    # Generic parameter (set)
    def set_TAILOR_key(self, key, val):
        """Get value of parameter *key* from ``TAILOR`` section
        
        :Call:
            >>> inp.set_TAILOR_key(key, val)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *key*: :class:`str`
                Name of parameter
            *val*: :class:`int` | :class:`float` | ``None``
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        # Initialize column index
        col = None
        # Loop through rows
        for (i, row) in enumerate(self.TAILOR_keys):
            # Check if *k* is in row
            if key in row:
                # Get index
                col = row.index(key)
                # Stop searching
                break
        # If not found, use namelist interface
        if col is None:
            # Use namelist interface
            self.SetVar("TAILOR", key, val, tab="")
        # Otherwise, return the value
        return self.SetSectionTableValue("TAILOR", i, col, val)
        
    # Hard-coded methods
    def get_TAILOR_igtm(self):
        """Get *igtm* from ``TAILOR`` section
        
        :Call:
            >>> igtm = inp.get_TAILOR_igtm()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *igtm*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("TAILOR", 0, 0)
        
    def set_TAILOR_igtm(self, igtm):
        """Set *igtm* in ``TAILOR`` section
        
        :Call:
            >>> inp.set_TAILOR_igtm(igtm)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *igtm*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("TAILOR", 0, 0, igtm)
        
    def get_TAILOR_igtt(self):
        """Get *igtt* from ``TAILOR`` section
        
        :Call:
            >>> igtt = inp.get_TAILOR_igtt()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *igtt*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("TAILOR", 0, 1)
        
    def set_TAILOR_igtt(self, igtt):
        """Set *igtm* in ``TAILOR`` section
        
        :Call:
            >>> inp.set_TAILOR_igtm(igtm)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *igtt*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("TAILOR", 0, 1, igtt)
        
    def get_TAILOR_sens(self):
        """Get *sens* from ``TAILOR`` section
        
        :Call:
            >>> sens = inp.get_TAILOR_sens()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *sens*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("TAILOR", 0, 2)
        
    def set_TAILOR_sens(self, sens):
        """Set *sens* in ``TAILOR`` section
        
        :Call:
            >>> inp.set_TAILOR_sens(sens)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *sens*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("TAILOR", 0, 2, sens)
        
    def get_TAILOR_ngts(self):
        """Get *ngts* from ``TAILOR`` section
        
        :Call:
            >>> ngts = inp.get_TAILOR_sens()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *ngts*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("TAILOR", 1, 0)
        
    def set_TAILOR_ngts(self, ngts):
        """Set *ngts* in ``TAILOR`` section
        
        :Call:
            >>> inp.set_TAILOR_ngts(ngts)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *ngts*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("TAILOR", 1, 0, ngts)
        
    def get_TAILOR_ngtp(self):
        """Get *ngtp* from ``TAILOR`` section
        
        :Call:
            >>> ngtp = inp.get_TAILOR_ngtp()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *ngtp*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("TAILOR", 1, 1)
        
    def set_TAILOR_ngtp(self, ngtp):
        """Set *ngtp* in ``TAILOR`` section
        
        :Call:
            >>> inp.set_TAILOR_ngtp(ngtp)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *ngtp*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("TAILOR", 1, 1, ngtp)
        
    def get_TAILOR_igti(self):
        """Get *igti* from ``TAILOR`` section
        
        :Call:
            >>> igti = inp.get_TAILOR_igti()
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
        :Outputs:
            *igti*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.GetSectionTableValue("TAILOR", 1, 2)
        
    def set_TAILOR_igti(self, igti):
        """Set *igti* in ``TAILOR`` section
        
        :Call:
            >>> inp.set_TAILOR_igti(igti)
        :Inputs:
            *inp*: :class:`cape.pyus.inputinpfile.InputInp`
                Namelist file control instance
            *igti*: :class:`int`
                Value in ``input.inp`` file
        :Versions:
            * 2019-06-06 ``@ddalle``: First version
        """
        return self.SetSectionTableValue("TAILOR", 1, 2, igti)
   # [/TAILOR]
# class InputInp

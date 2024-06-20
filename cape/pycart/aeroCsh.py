r"""
:mod:`cape.pycart.aeroCsh`: Cart3D ``aero.csh`` interface
=========================================================

This is a module built off of the :mod:`cape.filecntl` module customized for
manipulating ``aero.csh`` files.  Such files are actually C shell scripts
copied into each run directory that operate adaptive runs of Cart3D.  The
primary action of the :class:`AeroCsh` is to set the values of
several variables within the script.

Because this is a C shell script, the :func:`pyCart.aeroCsh.AeroCsh.Write`
method creates an executable script.

Parameters that are set in the header section of ``aero.csh`` include
inputs to ``cubes``, ``mgPrep``, ``flowCart``, and ``adjointCart``.  This is in
addition to the overall mesh adaptation parameters set in
:mod:`cape.pycart.options.runControl.Adaptation`.

:See Also:
    * :mod:`cape.filecntl`
    * :mod:`cape.pycart.cntl`
"""

# Import the base file control class.
from ..filecntl.filecntl import FileCntl


# Base this class off of the main file control class.
class AeroCsh(FileCntl):
    r"""File control class for ``aero.csh`` files

    This class is derived from :class:`cape.filecntl.filecntl.FileCntl`.

    :Call:
        >>> AC = AeroCsh()
        >>> AC = AeroCsh(fname="aero.csh")
    :Inputs:
        *fname*: :class:`str`
            Name of CNTL file to read, defaults to ``'aero.csh'``
    """
    __slots__ = (
        "binaryIO_bool",
        "y_is_spanwise_bool",
    )

    # Initialization method (not based off of FileCntl)
    def __init__(self, fname="aero.csh"):
        r"""Initialization method"""
        # Read the file
        self.Read(fname)
        # Save the file name
        self.fname = fname
        # Determine types for *binaryIO* and *y_is_spanwise*
        self._parse_vartypes()

    # Determine special types and save in slots
    def _parse_vartypes(self):
        r"""Check which types we use for two variables

        :Call:
            >>> AC._parse_vartypes()
        :Versions:
            * 2023-06-05 ``@ddalle``: v1.0
        """
        # Get current values
        yspan = self.GetVar("y_is_spanwise")
        binio = self.GetVar("binaryIO")
        # Check values
        self.y_is_spanwise_bool = (yspan in ("0", "1"))
        self.binaryIO_bool = (binio in ("0", "1"))

    # Method to write the file.
    def Write(self, fname=None):
        r"""Write *FC.lines* to text file

        :Call:
            >>> AC.Write()
            >>> AC.Write(fname)
        :Inputs:
            *AC*: :class:`AeroCsh`
                File control instance, defaults to *FC.fname*
            *fname*: :class:`str`
                Name of file to write to
        :Versions:
            * 2014-06-08 ``@ddalle``: v1.0
        """
        # Use the FileCntl.WriteEx method instead of FileCntl.Write
        self.WriteEx(fname=fname)

    # Prepare case
    def Prepare(self, opts, j=0):
        r"""Prepare all the key parameters of an ``aero.csh`` file

        :Call:
            >>> AC.Prepare(opts, j)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *opts*: :class:`pyCart.options.Options`
                Options interface
            *j*: :class:`int`
                Run sequence index
        :Versions:
            * 2015-11-09 ``@ddalle``: v1.0 (prev in ``pycart.cntl``)
        """
        # Process global options
        self.SetErrorTolerance(opts.get_etol(j))
        self.SetCFL(opts.get_cfl(j))
        self.SetCFLMin(opts.get_cflmin(j))
        self.SetnIter(opts.get_it_fc(j))
        self.SetnIterAdjoint(opts.get_it_ad(j))
        self.SetnAdapt(opts.get_n_adapt_cycles(j))
        self.SetnRefinements(opts.get_maxR(j))
        self.SetFlowCartMG(opts.get_mg_fc(j))
        self.SetAdjointCartMG(opts.get_mg_ad(j))
        self.SetFMG(opts.get_fmg(j))
        self.SetPMG(opts.get_pmg(j))
        self.SetTM(opts.get_tm(j))
        self.SetAdjFirstOrder(opts.get_adj_first_order(j))
        self.SetLimiter(opts.get_limiter(j))
        self.SetYIsSpanwise(opts.get_y_is_spanwise(j))
        self.SetABuffer(opts.get_abuff(j))
        self.SetFinalMeshXRef(opts.get_final_mesh_xref(j))
        self.SetBinaryIO(opts.get_binaryIO(j))
        # Initial mesh inputs; may not be used.
        self.SetCubesA(opts.get_cubes_a(0))
        self.SetCubesB(opts.get_cubes_b(0))
        self.SetMaxR(opts.get_maxR(0))
        self.SetPreSpec(True)
        # Process the adaptation-specific lists.
        self.SetAPC(opts.get_apc())
        self.SetMeshGrowth(opts.get_mesh_growth())
        self.SetnIterList(opts.get_ws_it())

    # Get value of a generic variable
    def GetVar(self, name):
        r"""Get generic ``aero.csh`` variable value

        :Call:
            >>> val = AC.GetVar(name)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *name*: :class:`str`
                Name of variable as identified in 'aero.csh'
        :Outputs:
            *val*: :class:`str`
                Text of value from file
        :Versions:
            * 2023-06-05 ``@ddalle``: v1.0
        """
        # Line regular expression: "set XXXX" but with white spaces
        reg = r'^\s*set\s+' + str(name) + r'\s*='
        # Find containing line
        lines = self.GetLineSearch(reg, 1)
        # Check for a match
        if len(lines) == 0:
            return
        # Parse (guaranteed '=' in line due to regex)
        txt = lines[0].split('=', 1)[1].strip()
        # Strip comments
        txt = txt.split('#', 1)[0].strip()
        # Remove quotes
        return txt.strip('\'"')

    # Function to set generic values, since they have the same format.
    def SetVar(self, name, val, f=False):
        r"""Set generic ``aero.csh`` variable value

        :Call:
            >>> AC.SetVar(name, val)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *name*: :class:`str`
                Name of variable as identified in 'aero.csh'
            *val*: *any*, converted using :func:`str`
                Value to which variable is set in final script
        :Versions:
            * 2014-06-10 ``@ddalle``: v1.0
        """
        # Line regular expression: "set XXXX" but with white spaces
        reg = r'^\s*set\s+' + str(name) + r'\s*[=\n]'
        # Convert *val* to string.
        val = str(val)
        # Form the output line.
        if val == '':
            # Empty line, used to turn a flag off.
            line = 'set %s \n' % name
        elif f:
            # Force character to be written as a float!
            line = 'set %s = %.20f\n' % (name, float(val))
        else:
            # Set a value.
            line = 'set %s = %s\n' % (name, val)
        # Replace the line; prepend it if missing
        self.ReplaceOrAddLineSearch(reg, line)

    # Function to set the functional error tolerance
    def SetErrorTolerance(self, etol):
        r"""Set error tolerance in ``aero.csh`` file

        :Call:
            >>> AC.SetErrorTolerance(etol)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *etol*: :class:`float`
                Number to set the function error tolerance to
        :Versions:
            * 2014-06-10 ``@ddalle``: v1.0
        """
        self.SetVar('etol', etol, True)

    # Function to set the number of refinements
    def SetnRefinements(self, maxR):
        r"""Set number of refinements for 'cubes' in 'aero.csh' file

        :Call:
            >>> AC.SetnRefinements(maxR)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *maxR*: :class:`int`
                Maximum number of refinements for `cubes`
        :Versions:
            * 2014-06-10 ``@ddalle``: v1.0
        """
        self.SetVar('maxR', maxR)

    # Set the maximum number of cells
    def SetMaxnCells(self, max_nCells):
        r"""Set the maximum number of cells for the mesh

        :Call:
            >>> AC.SetMaxnCells(max_nCells)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *max_nCells*: :class:`int`
                Maximum number of cells allowed in mesh
        :Versions:
            * 2014-06-10 ``@ddalle``: v1.0
        """
        self.SetVar('max_nCells', max_nCells)

    # Number of adaptation cycles.
    def SetnAdapt(self, n_adapt_cycles):
        r"""Set the number of adaptation cycles

        :Call:
            >>> AC.SetnAdapt(n_adapt_cycles)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *n_adapt_cycles*: :class:`int`
                Number of adaptation cycles
        :Versions:
            * 2014-06-10 ``@ddalle``: v1.0
        """
        self.SetVar('n_adapt_cycles', n_adapt_cycles)

    # Number of flowCart iterations on initial mesh
    def SetnIter(self, it_fc):
        r"""Set the *initial* number of flowCart iterations

        :Call:
            >>> AC.SetnIter(it_fc)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *it_fc*: :class:`int`
                Number of flowCart iters on initial mesh
        :Versions:
            * 2014-06-10 ``@ddalle``: v1.0
        """
        self.SetVar('it_fc', it_fc)

    # Number of flowCart iterations on subsequent meshes
    def SetnIterList(self, ws_it):
        r"""Set the number of flowCart iterations on new mesh

        :Call:
            >>> AC.SetnIterList(ws_it)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *ws_it*: :class:`int`
                Number of `flowCart` iters on subsequent meshes
        :Effects:
            Writes a line of the form ``'set ws_it = ( 50 50 50 )'``
        :Versions:
            * 2014-06-10 ``@ddalle``: v1.0
        """
        # Number of values specified
        n_ws = len(ws_it)
        # Initialize the string.
        line = '('
        # Loop through values.
        for n in ws_it:
            # Add a space and the number
            line += ' %s' % n
        # Write at least 12 entries.
        if n_ws < 12:
            # Repeat the last value until there are 12 entries.
            line += (' %s' % n)*(12-n_ws)
        # Finish the line.
        line += ' )'
        # Replace it.
        self.SetVar('ws_it', line)

    # Number of adjointCart iterations
    def SetnIterAdjoint(self, it_ad):
        r"""Set the number of adjointCart iterations

        :Call:
            >>> AC.SetnIter(it_ad)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *it_ad*: :class:`int`
                Number of `adjointCart` iters
        :Versions:
            * 2014-06-10 ``@ddalle``: v1.0
        """
        self.SetVar('it_ad', it_ad)

    # Set CFL number
    def SetCFL(self, cfl):
        r"""Set the CFL number

        :Call:
            >>> AC.SetCFL(cfl)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *cfl*: :class:`float`
                CFL number
        :Versions:
            * 2014-06-10 ``@ddalle``: v1.0
        """
        self.SetVar('cfl', cfl)

    # Set min CFL number
    def SetCFLMin(self, cflmin):
        r"""Set the minimum CFL number, which ``aero.csh`` uses as backup

        :Call:
            >>> AC.SetCFLMin(cflmin)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *cfl*: :class:`float`
                CFL number
        :Versions:
            * 2014-10-03 ``@ddalle``: v1.0
        """
        self.SetVar('cflmin', cflmin)

    # Set limiter type number
    def SetLimiter(self, limiter):
        r"""Set the limiter for `flowCart`

        :Call:
            >>> AC.SetLimiter(limiter)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *limiter*: :class:`int`
                Limiter, 2 or 5
        :Versions:
            * 2014-10-13 ``@ddalle``: v1.0
        """
        self.SetVar('limiter', int(limiter))

    # Set the number of multigrid levels
    def SetnMultiGrid(self, mg_fc):
        r"""Set the number of multigrid levels for both solvers

        :Call:
            >>> AC.SetnMultiGrid(mg_fc)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *mg_fc*: :class:`int`
                Number of multigrid levels, applied to flowCart and adjointCart
        :Versions:
            * 2014-06-10 ``@ddalle``: v1.0
        """
        # Set both variables.
        self.SetVar('mg_fc', mg_fc)
        self.SetVar('mg_ad', mg_fc)

    # Set the number of multigrid levels
    def SetFlowCartMG(self, mg_fc):
        r"""Set the number of multigrid levels for `flowCart`

        :Call:
            >>> AC.SetFlowCartMG(mg_fc)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *mg_fc*: :class:`int`
                Number of `flowCart` multigrid levels
        :Versions:
            * 2014-11-20 ``@ddalle``: v1.0
        """
        self.SetVar('mg_fc', mg_fc)

    # Set the number of multigrid levels
    def SetAdjointCartMG(self, mg_ad):
        r"""Set the number of multigrid levels for `adjointCart`

        :Call:
            >>> AC.SetAdjointCartMG(mg_ad)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *mg_ad*: :class:`int`
                Number of `adjointCart` multigrid levels
        :Versions:
            * 2014-11-20 ``@ddalle``: v1.0
        """
        self.SetVar('mg_ad', mg_ad)

    # Turn on or off buffer limiting.
    def SetBuffLim(self, buffLim):
        r"""Turn on or off buffer limiting to smear shocks

        :Call:
            >>> AC.SetBuffLim(buffLim)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *buffLim*: :class:`bool`
                Whether or not to use the ``-buffLim`` flag
        :Versions:
            * 2014-12-19 ``@ddalle``: v1.0
        """
        # Check input.
        if buffLim:
            # Turn flag on.
            self.SetVar('buffLim', '-buffLim')
        else:
            # Turn flag off
            self.SetVar('buffLim', '')

    # Turn on or off cut-cell first-order option
    def SetTM(self, tm):
        r"""Turn on or off option to use first-order cut cells

        :Call:
            >>> AC.SetTM(tm)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *tm*: :class:`bool` or :class:`int`
                Use first-order cut cells (*tm=0*) or not (*tm=1*)
        :Versions:
            * 2014-12-19 ``@ddalle``: v1.0
        """
        # Check inputs.
        if tm:
            # Second-order cut cells
            self.SetVar('tm', 1)
        else:
            # First-order cut cells
            self.SetVar('tm', 0)

    # Set the binary I/O setting
    def SetBinaryIO(self, binaryIO):
        r"""Set whether or not to write binary Tecplot files

        :Call:
            >>> AC.SetBinaryIO(binaryIO)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *binaryIO*: :class:`bool`
                Whether or not to write binary Tecplot files
        :Versions:
            * 2014-11-19 ``@ddalle``: v1.0
            * 2023-06-05 ``@ddalle``: v2.0; two output formats
        """
        # Determine outputs
        if self.binaryIO_bool:
            # Use 0 and 1
            vals = (0, 1)
        else:
            # Use flag or no flag
            vals = ("", "-binaryIO")
        # Convert boolean to index
        i = 1 if binaryIO else 0
        # Get value
        val = vals[i]
        # Set
        self.SetVar("binaryIO", val)

    # Set the mesh growth factor list
    def SetMeshGrowth(self, mesh_growth):
        r"""Set the list of mesh growth factors

        :Call:
            >>> AC.SetMeshGrowth(mesh_growth)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *mesh_growth*: *array_like*
                Vector of mesh growth parameters
        :Versions:
            * 2014-06-10 ``@ddalle``: v1.0
        """
        # Number of values specified
        n_ws = len(mesh_growth)
        # Initialize the string.
        line = '('
        # Loop through values.
        for n in mesh_growth:
            # Add a space and the number
            line += ' %s' % float(n)
        # Write at least 12 entries.
        if n_ws < 12:
            # Repeat the last value until there are 12 entries.
            line += (' %s' % float(n))*(12-n_ws)
        # Finish the line.
        line += ' )'
        # Replace it.
        self.SetVar('mesh_growth', line)

    # Set the mesh growth method
    def SetAPC(self, apc):
        r"""Set the list of mesh growth factors

        :Call:
            >>> AC.SetAPC(apc)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *apc*: *array_like*
                Vector of ``'p'`` and ``'a'``
        :Versions:
            * 2014-10-13 ``@ddalle``: v1.0
        """
        # Number of values specified
        n_ws = len(apc)
        # Initialize the string.
        line = '('
        # Loop through values.
        for c in apc:
            # Add a space and the number
            line += (" " + c)
        # Write at least 12 entries.
        if n_ws < 12:
            # Repeat the last value until there are 12 entries.
            line += (" "+c)*(12-n_ws)
        # Finish the line.
        line += ' )'
        # Replace it.
        self.SetVar('apc', line)

    # Set y_is_spanwise on or off.
    def SetYIsSpanwise(self, y_is_spanwise):
        r"""Turn on or off *y_is_spanwise* flag

        :Call:
            >>> AC.SetYIsSpanwise(y_is_spanwise)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *y_is_spanwise*: :class:`bool`
                Whether or not to use *y*-axis as spanwise axis
        :Versions:
            * 2014-11-11 ``@ddalle``: v1.0
            * 2023-06-05 ``@ddalle``: v2.0; two output formats
        """
        # Determine outputs
        if self.y_is_spanwise_bool:
            # Use 0 and 1
            vals = (0, 1)
        else:
            # Use flag or no flag
            vals = ("", "-y_is_spanwise")
        # Convert boolean to index
        i = 1 if y_is_spanwise else 0
        # Get value
        val = vals[i]
        # Set
        self.SetVar("y_is_spanwise", val)

    # Set full multigrid on or off
    def SetFMG(self, fmg):
        r"""Turn on or off ``-no_fmg`` flag

        :Call:
            >>> AC.SetFMG(fmg)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *fmg*: :class:`bool`
                Whether or not to use full multigrid
        :Versions:
            * 2014-11-13 ``@ddalle``: v1.0
            * 2024-06-20 ``@ddalle``: v2.0; two output formats
        """
        # Determine outputs
        if self.y_is_spanwise_bool:
            # Use 0 and 1
            vals = (0, 1)
        else:
            # Use flag or no flag
            vals = ("", "-fmg")
        # Convert boolean to index
        i = 1 if fmg else 0
        # Get value
        val = vals[i]
        # Modify the line to its appropriate value.
        self.SetVar('fmg', val)

    # Set poly multigrid on or off
    def SetPMG(self, pmg):
        r"""Turn on or off ``-pmg`` flag

        :Call:
            >>> AC.SetPMG(pmg)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *pmg*: :class:`bool`
                Whether or not to use poly multigrid
        :Versions:
            * 2014-11-13 ``@ddalle``: v1.0
            * 2024-06-20 ``@ddalle``: v2.0; two output formats
        """
        # Determine outputs
        if self.y_is_spanwise_bool:
            # Use 0 and 1
            vals = (0, 1)
        else:
            # Use flag or no flag
            vals = ("", "-pmg")
        # Convert boolean to index
        i = 1 if pmg else 0
        # Get value
        val = vals[i]
        # Modify the line to its appropriate value.
        self.SetVar('pmg', val)

    # Setting to run adjointCart first-order
    def SetAdjFirstOrder(self, adj):
        r"""Set flag to run `adjointCart` first-order

        :Call:
            >>> AC.SetAdjFirstOrder(adj)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *adj*: :class:`bool`
                Whether or not to run `adjointCart` first-order
        :Versions:
            * 2014-11-20 ``@ddalle``: v1.0
        """
        # Check value.
        if adj:
            # Turn the pmg flag on
            val = 1
        else:
            # No PMG flag
            val = 0
        # Modify the line to its appropriate value.
        self.SetVar('adj_first_order', val)

    # Function to set the number of buffers
    def SetABuffer(self, buf):
        r"""Set the number of buffer layers when refining a cell

        :Call:
            >>> AC.SetABuffer(buf)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *buf*: :class:`int`
                Number of buffer layers
        :Versions:
            * 2014-11-14 ``@ddalle``: v1.0
        """
        # Set this value (integer)
        self.SetVar('buf', buf)

    # Function to set number of additional adaptations on final error map
    def SetFinalMeshXRef(self, xref):
        r"""Set the number of additional adaptations on final error map

        :Call:
            >>> AC.SetFinalMeshXRef(xref)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *xref*: :class:`int`
                Number of additional adaptations
        :Versions:
            * 2014-11-14 ``@ddalle``: v1.0
        """
        # Make sure this is an integer.
        if not xref:
            xref = 0
        # Set this value (integer)
        self.SetVar('final_mesh_xref', xref)

    # Function to set `cubes` angle criterion
    def SetCubesA(self, a):
        r"""Set the angle criterion for `cubes`

        :Call:
            >>> AC.SetCubesA(a)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *a*: :class:`float`
                Angle criterion for `cubes`
        :Versions:
            * 2014-12-04 ``@ddalle``: v1.0
        """
        self.SetVar('cubes_a', a)

    # Function to set `cubes` number of buffer layers
    def SetCubesB(self, b):
        r"""Set number of buffer layers for `cubes`

        :Call:
            >>> AC.SetCubesB(b)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *b*: :class:`int`
                Number of buffer layers for `cubes`
        :Versions:
            * 2014-12-04 ``@ddalle``: v1.0
        """
        self.SetVar('cubes_b', b)

    # Function to set maximum number of revisions
    def SetMaxR(self, maxR):
        r"""Set the maximum number of refinements for `cubes`

        :Call:
            >>> AC.SetMaxR(maxR)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *maxR*: :class:`int`
                Maximum number of refinements for `cubes`
        :Versions:
            * 2014-12-04 ``@ddalle``: v1.0
        """
        self.SetVar('maxR', maxR)

    # Function to turn on (or off) preSpec for cubes
    def SetPreSpec(self, pre=True):
        r"""Turn on or off :file:`preSpec.c3d.cntl`

        :Call:
            >>> AC.SetPreSpec(pre=True)
        :Inputs:
            *AC*: :class:`AeroCsh`
                Instance of the ``aero.csh`` manipulation class
            *pre*: :class:`bool`
                Whether or not to use prespecified regions
        :Versions:
            * 2014-12-04 ``@ddalle``: v1.0
        """
        # Check input
        if pre:
            # On: set preSpec to 1
            self.SetVar('use_preSpec', 1)
        else:
            # Off: set preSpec to 0
            self.SetVar('use_preSpec', 0)


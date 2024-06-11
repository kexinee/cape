r"""
:mod:`cape.pyover.util`: Utilities for ``pyover``
==================================================

This module imports the generic utilities using

    .. code-block:: python

        from cape.util import *

It also stores the absolute path to the folder containing the
:mod:`cape.pyover` module as the variable *pyOverFolder*.

:See also:
    * :mod:`cape.util`
"""

# Import everything from cape.util
from ..util import *


# pyCart base folder
pyOverFolder = os.path.split(os.path.abspath(__file__))[0]



#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard library
import json
import os
import sys

# Standard library partial imports
from setuptools import Extension, setup

# Python version infor
PY_MAJOR_VERSION = sys.version_info.major
PY_MINOR_VERSION = sys.version_info.minor

# Version-dependent imports
if PY_MAJOR_VERSION == 2:
    # Standard library modules
    from ConfigParser import SafeConfigParser
    # Change name
    ConfigParser = SafeConfigParser
else:
    # Standard library modules
    from configparser import ConfigParser

# Config file
fcfg = "config%i.cfg" % PY_MAJOR_VERSION


# Path to this file
fdir = os.path.dirname(os.path.realpath(__file__))
fcape = os.path.join(fdir, "cape")

# Get a get/set type object
config = ConfigParser()
# Read the configuration options
config.read(os.path.join(fcape, fcfg))

# C compiler flags
cflags = config.get("compiler", "extra_cflags").split()

# Linker options
ldflags = config.get("compiler", "extra_ldflags").split()

# Extra include directories
include_dirs = config.get("compiler", "extra_include_dirs").split()

# Extensions JSON file
extjson = os.path.join(fcape, "extensions.json")
# Read extension settings
extopts = json.load(open(extjson))

# Initialize extensions
exts = []
# Loop through specified extensions
for (ext, opts) in extopts.items():
    # Get sources
    extsources = [str(src) for src in opts["sources"]]
    # Create extension
    _ext = Extension(
        str(ext) + str(PY_MAJOR_VERSION),
        include_dirs=include_dirs,
        extra_compile_args=cflags,
        extra_link_args=ldflags,
        sources=extsources)
    # Add to list
    exts.append(_ext)

# Compile and link
setup(
    name="cape",
    packages=[
        "cape",
        "cape.attdb",
        "cape.attdb.ftypes",
        "cape.cfdx",
        "cape.cfdx.options",
        "cape.filecntl",
        "cape.optdict",
        "cape.pycart",
        "cape.pycart.options",
        "cape.pyfun",
        "cape.pyfun.options",
        "cape.pyover",
        "cape.pyover.options",
        "cape.tnakit",
        "cape.tnakit.plot_mpl",
        "cape.tnakit.textutils"
    ],
    install_requires=[
        "defusedxml",
        "numpy>=1.4.1",
        "matplotlib>=2",
        "scipy",
        "vendorize",
        "xlrd%i" % PY_MAJOR_VERSION,
        "xlsxwriter"
    ],
    package_data={
        "cape": [
            "templates/paraview/*",
            "templates/tecplot/*"
        ],
        "cape.cfdx": ["templates/*"],
        "cape.cfdx.options": ["*.json"],
        "cape.pycart": ["templates/*"],
        "cape.pycart.options": ["*.json"],
        "cape.pyfun": ["templates/*"],
        "cape.pyfun.options": ["*.json"],
        "cape.pyover": ["templates/*"],
        "cape.pyover.options": ["*.json"],
    },
    scripts=[
        "bin/run_flowCart.py",
        "bin/run_fun3d.py",
        "bin/run_overflow.py"
    ],
    entry_points={
        "console_scripts": [
            "pycart=cape.pycart.cli:main",
            "pyfun=cape.pyfun.cli:main",
            "pyover=cape.pyover.cli:main",
            "dkit=cape.attdb.cli:main",
            "dkit-quickstart=cape.attdb.quickstart:main",
            "dkit-vendorize=cape.attdb.vendorutils:main",
            "dkit-writedb=cape.attdb.writedb:main",
            "cape-writell=cape.writell:main",
            "cape-step2crv=cape.tricli:main_step2crv",
            "cape-steptri2crv=cape.tricli:main_steptri2crv",
            "cape-uh3d2tri=cape.tricli:main_uh3d2tri",
            "cape-tri2uh3d=cape.tricli:main_tri2uh3d",
            "cape-tri2plt=cape.tricli:main_tri2plt",
            "cape-tri2surf=cape.tricli:main_tri2surf",
            "pyfun-plt2triq=cape.pyfun.tricli:main_plt2triq",
        ],
    },
    version="1.1.0-prelim4",
    description="CAPE computational aerosciences package",
    ext_modules=exts)

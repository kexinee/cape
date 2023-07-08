#!/bin/bash

# Package name
PKG="cape"

# Run tests
python3 -m pytest \
    test/902_pyfun \
    --pdb \
    --junitxml=test/junit.xml \
    --cov=$PKG \
    --cov-report html:test/htmlcov

# Save result
IERR=$?

# Create sphinx docs of results
#python3 -m testutils write-rst

# Return pytest's status
exit $IERR


r"""
This is a module for tarring and untarring folders automatically in combination
with changing directory into and out of the folder.  This function works in
combination primarily with the :class:`cape.cfdx.report.Report` class when the
``"Report"`` > ``"Archive"`` option is set to ``True``.

The primary functions and their actions are:

    * :func:`chdir_up`: Leave a folder, archive it, and delete the folder
        * Starting from folder called ``thisdir/``
        * ``cd ..``
        * ``tar -uf thisdir.tar thisdir``
        * ``rm -r thisdir/``

    * :func:`chdir_in`: Go into a folder that may be archived
        * ``tar -xf thisdir.tar``
        * ``cd thisdir/``

"""

# Standard library
import os
import glob
import shutil
import tarfile


# Simple function to untar a folder
def untar(ftar):
    r"""Untar an archive

    :Call:
        >>> ierr = tar.untar(ftar)
    :Inputs:
        *ftar*: :class:`str`
            Name of the archive to untar
    :Outputs:
        *ierr*: :class:`int`
            Exit code from the `tar` command
    :Versions:
        * 2015-03-07 ``@ddalle``: v1.0
    """
    # Open tar object
    tar = tarfile.open(ftar, "r")
    # Extract all files
    tar.extractall()
    # Close object
    tar.close()


# Function to tar a folder
def tar(ftar, *a):
    r"""Untar an archive

    :Call:
        >>> tar.tar(ftar, fdir, *a)
    :Inputs:
        *ftar*: :class:`str`
            Name of the archive
        *fdir*: :class:`str`
            Name of the folder to archive, for example
        *a*: :class:`list` (:class:`str`)
            Additional arguments are also passed to the tar command
    :Versions:
        * 2015-03-07 ``@ddalle``: v1.0
        * 2019-11-07 ``@ddalle``: v1.1; use :mod:`tarfile`
    """
    # Check if file exists
    if os.path.isfile(ftar):
        # Append to existing
        tar = tarfile.open(ftar, "a")
    else:
        # Create new
        tar = tarfile.open(ftar, "w")
    # Expand list of files
    fglob = []
    # Loop through files
    for ai in a:
        # Loop through matches
        for aj in glob.glob(ai):
            # Check if already in glob
            if aj in fglob:
                continue
            # Otherwise add it to archive
            tar.add(aj)
            # Add it to list
            fglob.append(aj)
    # Close the archive
    tar.close()


# Function to leave a folder and archive it.
def chdir_up():
    r"""Leave a folder, archive it, and delete the folder

    :Call:
        >>> tar.chdir_up()
    :Versions:
        * 2015-03-07 ``@ddalle``: v1.0
    """
    # Get the current folder
    fpwd = os.path.split(os.getcwd())[-1]
    # Go up
    os.chdir('..')
    # Name of the file
    ftar = fpwd + '.tar'
    # Update or create the archive
    tar(ftar, fpwd)
    # Delete the folder
    shutil.rmtree(fpwd)


# Function to go into a folder that might be archived.
def chdir_in(fdir: str):
    r"""Go into a folder that may be archived

    :Call:
        >>> tar.chdir_in(fdir)
    :Inputs:
        *fdir*: :class:`str`
            Name of folder
    :Versions:
        * 2015-03-07 ``@ddalle``: v1.0
    """
    # Name of the archive.
    ftar = fdir + '.tar'
    # Check for the archive.
    if os.path.isfile(ftar):
        # Check for the folder.
        if os.path.isdir(fdir):
            # Check the dates.
            if os.path.getmtime(fdir) < os.path.getmtime(ftar):
                # Folder needs updating
                untar(ftar)
        else:
            # No folder
            untar(ftar)
    # Go into the folder
    os.chdir(fdir)


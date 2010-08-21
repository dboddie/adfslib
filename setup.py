#! /usr/bin/env python

from distutils.core import setup
import sys

try:

    import cmdsyntax

except ImportError:

    print "Information:"
    print
    print "The cmdsyntax module is not installed. The ADF2INF.py utility"
    print "will use getopt for its argument handling. You can install"
    print "cmdsyntax later if you want."
    print
    print "See http://www.boddie.org.uk/david/Projects/Python/CMDSyntax"
    print "for details of how to obtain the cmdsyntax module."


import ADFSlib

setup(
    name="ADFSlib",
    description="ADFS disk image reader and utility",
    author="David Boddie",
    author_email="david@boddie.org.uk",
    url="http://www.boddie.org.uk/david/Projects/Python/ADFSlib",
    version=ADFSlib.__version__,
    py_modules=["ADFSlib"],
    scripts=["ADF2INF.py"]
    )

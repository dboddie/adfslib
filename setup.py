#! /usr/bin/env python

from distutils.core import setup
import sys

try:

    import cmdsyntax

except ImportError:

    print "Apologies:"
    print
    print "You need the cmdsyntax module to be able to use this tool."
    print "See http://www.boddie.org.uk/david/Projects/Python/CMDSyntax"
    print "for details."
    sys.exit()

setup(
    name="ADFSlib",
    description="ADFS disk image reader and utility",
    author="David Boddie",
    author_email="david@boddie.org.uk",
    url="http://www.boddie.org.uk/david/Projects/Python/ADF2INF",
    version="0.31c",
    py_modules=["ADFSlib"]
    scripts=["ADF2INF"]
    )

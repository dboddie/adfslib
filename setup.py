#! /usr/bin/env python

from distutils.core import setup
import sys

try:

    import cmdsyntax

except ImportError:

    print "Apologies:"
    print
    print "You need the cmdsyntax module to be able to use the ADF2INF.py"
    print "utility. You can still install the ADFSlib module if you want."
    print
    print "See http://www.boddie.org.uk/david/Projects/Python/CMDSyntax"
    print "for details of how to obtain the cmdsyntax module."
    print
    q = raw_input(
        "Do you wish to continue installing the ADFSlib module? [yes]/no:"
        )
    
    if q != "yes" and q != "":
    
        sys.exit()


setup(
    name="ADFSlib",
    description="ADFS disk image reader and utility",
    author="David Boddie",
    author_email="david@boddie.org.uk",
    url="http://www.boddie.org.uk/david/Projects/Python/ADF2INF",
    version="0.31c",
    py_modules=["ADFSlib"],
    scripts=["ADF2INF.py"]
    )

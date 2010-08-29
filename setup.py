#! /usr/bin/env python

"""
Copyright (c) 2010, David Boddie

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

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

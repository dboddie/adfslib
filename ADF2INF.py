#! /usr/bin/env python
"""
Name        : ADF2INF.py
Author      : David Boddie
Created     : Wed 18th October 2000
Updated     : Tue 15th April 2003
Purpose     : Convert ADFS disc images (ADF) to INF files
WWW         : http://david.boddie.org.uk/Projects/Python/ADFSlib

License:

Copyright (c) 2000-2003, David Boddie

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""


import os, sys
import ADFSlib

try:

    import cmdsyntax
    use_getopt = 0

except ImportError:

    import getopt
    use_getopt = 1


__version__ = "0.32c (Tue 15th April 2003)"


def read_cmdsyntax_input(argv, syntax):

    syntax_obj = cmdsyntax.Syntax(syntax)
    
    matches, failed = syntax_obj.get_args(argv[1:], return_failed = 1)
    
    if len(matches) != 1 and cmdsyntax.use_GUI() != None:
    
        form = cmdsyntax.Form("ADF2INF", syntax_obj, failed[0])
        
        matches = form.get_args()
    
    # Take the first match, if possible.
    if len(matches) > 0:
    
        match = matches[0]
    
    else:
    
        match = None
    
    return match


def read_getopt_input(argv):

    opts, args = getopt.getopt(argv[1:], "ldts:v")

    match = {}
    
    opt_dict = {"-l": "list", "-d": "directory", "-t": "file-types", "-s": "separator",
                "-v": "verify"}
    arg_list = ["ADF file", "destination path"]
    
    # Read the options specified.
    
    for opt, value in opts:
    
        if opt_dict.has_key(opt):
        
            match[opt_dict[opt]] = value or '1'
        
        else:
        
            return None
    
    # Read the remaining arguments: there should be two of these.
    
    if match.has_key("list") and len(args) != 1:
    
        return None
    
    elif not match.has_key("list") and len(args) != 2:
    
        return None
    
    else:
    
        i = 0
        for arg in args:
        
            match[arg_list[i]] = arg
            i = i + 1
    
    if match == {}: match = None
    
    return match


if __name__ == "__main__":
    
    if use_getopt == 0:
    
        syntax = """
        \r(
        \r    (-l | --list) [-t | --file-types] <ADF file>
        \r) |
        \r(
        \r    [-d | --create-directory]
        \r    [(-t | --file-types) [(-s separator) | --separator=character]]
        \r    <ADF file> <destination path>
        \r) |
        \r(
        \r    (-v | --verify) <ADF file>
        \r)
        """
        
        match = read_cmdsyntax_input(sys.argv, syntax)
    
    else:
    
        syntax = "[-l] [-d] [-t] [-s separator] [-v]" + \
                 "<ADF file> <destination path>"
        match = read_getopt_input(sys.argv)
    
    if match == {} or match is None:
    
        print "Syntax: ADF2INF.py " + syntax
        print
        print 'ADF2INF version ' + __version__
        print
        print 'Take the files stored in the directory given and store them as files with'
        print 'corresponding INF files.'
        print
        print 'If the -l flag is specified then the catalogue of the disc will be printed.'
        print
        print "The -d flag specifies that a directory should be created using the disc's"
        print 'name into which the contents of the disc will be written.'
        print
        print "The -t flag causes the load and execution addresses of files to be"
        print "interpreted as filetype information for files created on RISC OS."
        print "A separator used to append a suffix onto the file is optional and"
        print "defaults to the standard period character. e.g. myfile.fff"
        print
        print "The -v flag causes the disc image to be checked for simple defects and"
        print "determines whether there are files and directories which cannot be"
        print "correctly located by this tool, whether due to a corrupted disc image"
        print "or a bug in the image decoding techniques used."
        print
        sys.exit()
    
    
    # Determine whether the file is to be listed
    
    listing = match.has_key("l") or match.has_key("list")
    use_name = match.has_key("d") or match.has_key("create-directory")
    filetypes = match.has_key("t") or match.has_key("file-types")
    use_separator = match.has_key("s") or match.has_key("separator")
    verify = match.has_key("v") or match.has_key("verify")
    
    adf_file = match["ADF file"]
    
    out_path = match.get("destination path", None)
    
    separator = match.get("separator", ",")
    
    if sys.platform == 'RISCOS':
        suffix = '/'
    else:
        suffix = '.'
    
    if filetypes == 0 or (filetypes != 0 and use_separator == 0):

        # Use the standard suffix separator for the current platform if
        # none is specified.    
        separator = suffix
    
    
    # Try to open the ADFS disc image file.
    
    try:
        adf = open(adf_file, "rb")
    except IOError:
        print "Couldn't open the ADF file: %s" % adf_file
        print
        sys.exit()
    
    
    if verify == 0:
    
        # Create an ADFSdisc instance using this file.
        adfsdisc = ADFSlib.ADFSdisc(adf)
    
    else:
    
        # Verifying
        
        print "Verifying..."
        print
        
        # Create an ADFSdisc instance using this file.
        adfsdisc = ADFSlib.ADFSdisc(adf, verify = 1)
        
        adfsdisc.print_log()
        
        # Exit
        sys.exit()
    
    
    if listing != 0:
    
        # Print catalogue
        print 'Contents of', adfsdisc.disc_name,':'
        print
    
        adfsdisc.print_catalogue(
            adfsdisc.files, adfsdisc.root_name, filetypes, separator
            )
    
        # Exit
        sys.exit()
    
    
    # Make sure that the disc is put in a directory corresponding to the disc
    # name where applicable.
    
    if use_name != 0:
    
        # Place the output files on this new path.
        out_path = os.path.join(out_path, adfsdisc.disc_name)
    
    # Extract the files
    adfsdisc.extract_files(out_path, adfsdisc.files, filetypes, separator)
    
    # Exit
    sys.exit()

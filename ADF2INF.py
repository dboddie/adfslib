#! /usr/bin/env python
"""
    Name        : ADF2INF.py
    Author      : David Boddie
    Created     : Wed 18th October 2000
    Updated     : Mon 24th March 2003
    Purpose     : Convert ADFS disc images (ADF) to INF files
    WWW         : http://david.boddie.org.uk/Projects/Emulation/T2Tools
"""


import os, string, sys
import ADFSlib, cmdsyntax


__version__ = "0.31c (Wed 26th March 2003)"


if __name__ == "__main__":
    
    syntax = """
    (
        (-l | --list) [-t | --file-types] <ADF file>
    ) |
    (
        [-d | --create-directory]
        [(-t | --file-types) [(-s separator) | --separator=character]]
        <ADF file> <destination path>
    )"""
    
    version = __version__
    
    syntax_obj = cmdsyntax.Syntax(syntax)
    
    matches = syntax_obj.get_args(sys.argv[1:])
    
    if matches == [] and cmdsyntax.use_GUI() != None:
    
        form = cmdsyntax.Form("ADF2INF", syntax_obj)
        
        matches = [form.get_args()]
    
    # Take the first match.
    match = matches[0]
    
    if match == {} or match is None:
    
        print "Syntax: ADF2INF.py "+syntax
        print
        print 'ADF2INF version '+version
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
        sys.exit()
    
    
    # Determine whether the file is to be listed
    
    
    listing = match.has_key("l") or match.has_key("list")
    use_name = match.has_key("d") or match.has_key("create-directory")
    filetypes = match.has_key("t") or match.has_key("file-types")
    use_separator = match.has_key("s") or match.has_key("separator")
    
    adf_file = match["ADF file"]
    
    if listing == 0:
    
        out_path = match["destination path"]
    
    if use_separator != 0:
    
        separator = match["separator"]
    
    if sys.platform == 'RISCOS':
        suffix = '/'
    else:
        suffix = '.'
    
    if filetypes != 0 and use_separator == 0:
    
        separator = suffix
    
    
    # Disc properties
    
    
    try:
        adf = open(adf_file, "rb")
    except IOError:
        print "Couldn't open the ADF file, %s" % adf_file
        print
        sys.exit()
    
    
    # Create an ADFSdisc instance using this file.
    adfsdisc = ADFSlib.ADFSdisc(adf)
    
    # Print catalogue
    if listing != 0:
    
        print 'Contents of', adfsdisc.disc_name,':'
        print
    
        adfsdisc.print_catalogue(adfsdisc.files, adfsdisc.root_name)
    
        # Exit
        sys.exit()
    
    
    # Attempt to create a directory using the output path in case the user
    # wants to put the disc inside a directory to be sure that the disc won't
    # overwrite files.
    
    try:
        os.mkdir(out_path)
        print 'Created directory: %s' % out_path
    except OSError:
        print "Couldn't create directory: %s" % out_path
        sys.exit()
    
    # Make sure that the disc is put in a directory corresponding to the disc
    # name where applicable.
    
    if use_name != 0 and adfsdisc.disc_name != '$':
    
        new_path = adfsdisc.create_directory(out_path, adfsdisc.disc_name)
        
        if new_path != "":
        
            print 'Created directory: %s' % new_path
            
            # Place the output files on this new path.
            out_path = new_path
        
        else:
        
            print "Couldn't create directory: %s" % self.disc_name
    
    # Extract the files
    adfsdisc.extract_files(out_path, adfsdisc.files)
    
    # Exit
    sys.exit()

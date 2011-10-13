#!/usr/bin/env python

import ADFSlib
import glob, os, sys

if __name__ == "__main__":

    if len(sys.argv) < 2:
    
        sys.stderr.write("Usage: %s <ADFS disc image> ...\n" % sys.argv[0])
        sys.exit(1)
    
    paths = sys.argv[1:]
    
    for path in paths:
    
        if os.path.isfile(path):
        
            try:
                d = ADFSlib.ADFSdisc(open(path))
                print path, d.disc_format()
            except ADFSlib.ADFS_exception:
                sys.stderr.write("Unrecognised file: %s\n" % path)
    
    sys.exit()

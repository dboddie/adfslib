#! /usr/bin/env python
"""
ADFSlib.py

A library for reading ADFS disc images.

Copyright (c) 2003, David Boddie

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

__author__ = "David Boddie <david@boddie.org.uk>"
__date__ = "Mon 21st July 2003"
__version__ = "0.21"


import os, string


INFORM = 0
WARNING = 1
ERROR = 2


class ADFS_exception(Exception):

    pass


class ADFSdisc:

    def __init__(self, adf, verify = 0):
    
        # Log problems if the verify flag is set.
        self.verify = verify
        self.verify_log = []
        
        # Check the properties using the length of the file
        adf.seek(0,2)
        length = adf.tell()
        adf.seek(0,0)
        
        if length == 163840:
            self.ntracks = 40
            self.nsectors = 16
            self.sector_size = 256
            interleave = 0
            self.disc_type = 'adf'
        
        #if string.lower(adf_file[-4:])==(suffix+"adf"):
        elif length == 327680:
            self.ntracks = 80
            self.nsectors = 16
            self.sector_size = 256
            interleave = 0
            self.disc_type = 'adf'
        
        #elif string.lower(adf_file[-4:])==(suffix+"adl"):
        elif length == 655360:
            self.ntracks = 160
            self.nsectors = 16        # per track
            self.sector_size = 256    # in bytes
            interleave = 0 # 1
            self.disc_type = 'adl'
        
        elif length == 819200:
        
            self.ntracks = 80
            self.nsectors = 10
            self.sector_size = 1024
            interleave = 0
            
            format = self.identify_format(adf)
            
            if format == 'D':
            
                self.disc_type = 'adD'
            
            elif format == 'E':
            
                self.disc_type = 'adE'
            
            else:
                raise ADFS_exception, \
                    'Please supply a .adf, .adl or .adD file.'
        
        elif length == 1638400:
        
            self.ntracks = 80
            self.nsectors = 20
            self.sector_size = 1024
            interleave = 0
            self.disc_type = 'adEbig'
        
        else:
            raise ADFS_exception, 'Please supply a .adf, .adl or .adD file.'
        
        # Read tracks
        self.sectors = self.read_tracks(adf, interleave)
        
        # Close the ADF file
        adf.close()
        
        #open('dump', 'wb').write(self.sectors)
        #sys.exit()
        
        # Set the default disc name.
        self.disc_name = 'Untitled'
        
        # Read the files on the disc.
        
        if self.disc_type == 'adD':
        
            # Find the root directory name and all the files and directories
            # contained within it
            self.root_name, self.files = self.read_old_catalogue(0x400)
        
        elif self.disc_type == 'adE':
        
            # Read the disc name and map
            self.disc_name = self.safe(self.read_disc_info(), with_space = 1)
            
            # Find the root directory name and all the files and directories
            # contained within it
            self.root_name, self.files = self.read_new_catalogue(0x800)
        
        elif self.disc_type == 'adEbig':
        
            # Read the disc name and map
            self.disc_name = self.safe(self.read_disc_info(), with_space = 1)
            
            # Find the root directory name and all the files and directories
            # contained within it
            self.root_name, self.files = self.read_new_catalogue(0xc8800)
        
        else:
        
            # Find the root directory name and all the files and directories
            # contained within it
            self.root_name, self.files = self.read_old_catalogue(2*self.sector_size)
    
    
    def str2num(self, size, s):
    
        i = 0
        n = 0
        while i < size:
        
            n = n | (ord(s[i]) << (i*8))
            i = i + 1
        
        return n
    
    
    def binary(self, size, n):
    
        new = ""
        while (n != 0) & (size > 0):
        
            if (n & 1)==1:
                new = "1" + new
            else:
                new = "0" + new
            
            n = n >> 1
            size = size - 1
        
        if size > 0:
            new = ("0"*size) + new
        
        return new
    
    
    def identify_format(self, adf):
    
        # Look for a valid disc record when determining whether the disc
        # image represents an 800K D or E format floppy disc. First, the
        # disc image needs to be read.
        
        # Read all the data in the image. This will be overwritten
        # when the image is read properly.
        self.sectors = adf.read()
        
        # This will be done again for E format and later discs.
        
        record = self.read_disc_record(4)
        
        # Define a checklist of criteria to satisfy.
        checklist = \
        {
            "Length field matches image length": 0,
            "Expected sector size (1024 bytes)": 0,
            "Expected density (double)": 0,
            "Root directory at location given": 0
        }
        
        # Check the disc image length.
        
        # Seek to the end of the disc image.
        adf.seek(0, 2)
        
        #print hex(record["disc size"]), hex(adf.tell())
        
        if record["disc size"] == adf.tell():
        
            # The record (if is exists) does not provide a consistent value
            # for the length of the image file.
            checklist["Length field matches image length"] = 1
        
        
        # Check the sector size of the disc.
        
        #print hex(record["sector size"])
        
        if record["sector size"] == 1024:
        
            # These should be equal if the disc record is valid.
            checklist["Expected sector size (1024 bytes)"] = 1
        
        
        # Check the density of the disc.
        
        #print record["density"]
        
        if record["density"] == "double":
        
            # This should be a double density disc if the disc record is valid.
            checklist["Expected density (double)"] = 1
        
        
        # Check the data at the root directory location.
        #print hex(record["root dir"])
        
        adf.seek((record["root dir"] * record["sector size"]) + 1, 0)
        word = adf.read(4)
        
        if word == "Hugo" or word == "Nick":
        
            # A valid directory identifier was found.
            checklist["Root directory at location given"] = 1
        
        
        if self.verify:
        
            self.verify_log.append(
                (INFORM, "Checklist for E format discs:")
                )
            
            for key, value in checklist.items():
            
                self.verify_log.append(
                    (INFORM, "%s: %s" % (key, ["no", "yes"][value]))
                    )
        
        # If all the tests pass then the disc is an E format disc.
        if reduce(lambda a, b: a + b, checklist.values(), 0) == \
            len(checklist.keys()):
        
            if self.verify: self.verify_log.append((INFORM, "E format disc"))
            return "E"
        
        # Since there may not be a valid disc record for earlier discs
        # then anything other than full marks can be interpreted as
        # an indication that the disc is a D format disc. However, we
        # can perform a final test to check this.
        
        # Simple test for D and E formats: look for Hugo at 0x401 for D format
        # and Nick at 0x801 for E format
        adf.seek(0x401)
        word1 = adf.read(4)
        adf.seek(0x801)
        word2 = adf.read(4)
        adf.seek(0)
        
        if word1 == 'Hugo':
        
            if self.verify:
            
                self.verify_log.append(
                    ( INFORM,
                      "Found directory in typical place for the root " + \
                      "directory of a D format disc." )
                    )
            
            return 'D'
        
        elif word2 == 'Nick':
        
            if self.verify:
            
                self.verify_log.append(
                    ( INFORM,
                      "Found directory in typical place for the root " + \
                      "directory of an E format disc." )
                    )
            
            return 'E'
        
        else:
        
            if self.verify:
            
                self.verify_log.append(
                    ( ERROR,
                      "Failed to find any information which would help " + \
                      "determine the disc format." )
                    )
            
            return '?'
    
    
    def read_disc_record(self, offset):
    
        # Total sectors per track (sectors * heads)
        log2_sector_size = ord(self.sectors[offset])
        # Sectors per track
        nsectors = ord(self.sectors[offset + 1])
        # Heads per track
        heads = ord(self.sectors[offset + 2])
        
        density = ord(self.sectors[offset+3])
        
        if density == 1:
        
            density = 'single'        # Single density disc
            sector_size = 256
        
        elif density == 2:
        
            density = 'double'        # Double density disc
            sector_size = 512
        
        elif density == 3:
        
            density = 'quad'        # Quad density disc
            sector_size = 1024
        
        else:
        
            density = 'unknown'
        
        # Length of ID fields in the disc map
        idlen = self.str2num(1, self.sectors[offset + 4])
        # Number of bytes per map bit.
        bytes_per_bit = 2 ** self.str2num(1, self.sectors[offset + 5])
        # LowSector
        # StartUp
        # LinkBits
        # BitSize (size of ID field?)
        bit_size = self.str2num(1, self.sectors[offset + 6 : offset + 7])
        #print "Bit size: %s" % hex(bit_size)
        # RASkew
        # BootOpt
        # Zones
        zones = ord(self.sectors[offset + 9])
        # ZoneSpare
        # RootDir
        root = self.str2num(3, self.sectors[offset + 13 : offset + 16]) # was 15
        # Identify
        # SequenceSides
        # DoubleStep
        # DiscSize
        disc_size = self.str2num(4, self.sectors[offset + 16 : offset + 20])
        # DiscId
        disc_id   = self.str2num(2, self.sectors[offset + 20 : offset + 22])
        # DiscName
        disc_name = string.strip(self.sectors[offset + 22 : offset + 32])
        
        return {'sectors': nsectors, 'log2 sector size': log2_sector_size,
            'sector size': 2**log2_sector_size, 'heads': heads,
            'density': density,
            'disc size': disc_size, 'disc ID': disc_id,
            'disc name': disc_name, 'zones': zones, 'root dir': root }
    
    
    def read_disc_info(self):
    
        checksum = ord(self.sectors[0])
        first_free = self.str2num(2, self.sectors[1:3])
        
        if self.disc_type == 'adE':
        
            self.record = self.read_disc_record(4)
            
            self.sector_size = self.record["sector size"]
            
            self.map_header = 0
            self.map_start, self.map_end = 0x40, 0x400
            self.free_space = self.read_free_space(
                self.map_header, self.map_start, self.map_end
                )
            self.disc_map = self.read_new_map(
                self.map_header, self.map_start, self.map_end
                )
            
            return self.record['disc name'] #, map
        
        if self.disc_type == 'adEbig':
        
            self.record = self.read_disc_record(0xc6804)
            
            self.sector_size = self.record["sector size"]
            
            self.map_header = 0xc6800
            self.map_start, self.map_end = 0xc6840, 0xc7800
            self.free_space = self.read_free_space(
                self.map_header, self.map_start, self.map_end
                )
            self.disc_map = self.read_new_map(
                self.map_header, self.map_start, self.map_end
                )
            
            return self.record['disc name'] #, map
        
        else:
            return 'Unknown'
    
    #    zone_size = 819200 / record['zones']
    #    ids_per_zone = zone_size /
    
    def read_new_map(self, header, begin, end):
    
        disc_map = {}
        
        a = begin
        
        current_piece = None
        current_start = 0
        
        next_zone = header + self.sector_size
        
        # Copy the free space map.
        free_space = self.free_space[:]
        
        while a < end:
        
            # The next entry to be read will occur one byte after this one
            # unless one of the following checks override this behaviour.
            next = a + 1
            
            if (a % self.sector_size) < 4:
            
                # In a zone header. Not the first zone header as this
                # was already skipped when we started reading.
                next = a + 4 - (a % self.sector_size)
                
                # Set the next zone offset.
                next_zone = next_zone + self.sector_size
                
                # Reset the current piece and starting offset.
                current_piece = None
                current_start = 0
            
            elif free_space != [] and a >= free_space[0][0]:
            
                # In the next free space entry. Go to the entry following
                # it and discard this free space entry.
                next = free_space[0][1]
                
                free_space.pop(0)
                
                # Reset the current piece and starting offset.
                current_piece = None
                current_start = 0
            
            elif current_piece is None and (next_zone - a) >= 2:
            
                # If there is enough space left in this zone to allow
                # further fragments then read the next two bytes.
                value = self.str2num(2, self.sectors[a:a+2])
                
                entry = value & 0x7fff
                
                # See ADFS/EAddrs.htm document for restriction on
                # the disc address and hence the file number.
                # i.e.the top bit of the file number cannot be set.
                
                #if entry == 1:
                #
                #    # File number 1 (defect)
                #    next = a + 2
                #
                if entry >= 1:
                
                    # Defects (1), files or directories (greater than 1)
                    next = a + 2
                    
                    # Define a new entry.
                    #print "Begin:", hex(entry), hex(a)
                    
                    if not disc_map.has_key(entry):
                    
                        # Create a new map entry if none exists.
                        disc_map[entry] = []
                    
                    if (value & 0x8000) == 0:
                    
                        # Record the file number and start of this fragment.
                        current_piece = entry
                        current_start = a
                    
                    else:
                    
                        # For an immediately terminated fragment, add the
                        # extents of the block to the list of pieces found
                        # and implicitly finish reading this fragment
                        # (current_piece remains None).
                        
                        start_addr = self.find_address_from_map(
                            a, begin, entry
                            )
                        end_addr = self.find_address_from_map(
                            next, begin, entry
                            )
                        
                        if [start_addr, end_addr] not in disc_map[entry]:
                        
                            disc_map[entry].append( [start_addr, end_addr] )
                
                else:
                
                    # Search for a valid file number.
                    # Should probably stop looking in this zone.
                    next = a + 1
            
            elif current_piece is not None:
            
                # In a piece being read.
                
                value = ord(self.sectors[a])
                
                if value == 0:
                
                    # Still in the block.
                    next = a + 1
                
                elif value == 0x80:
                
                    # At the end of the block.
                    next = a + 1
                    
                    # For relevant entries add the block to the list of
                    # pieces found.
                    start_addr = self.find_address_from_map(
                        current_start, begin, current_piece
                        )
                    end_addr = self.find_address_from_map(
                        next, begin, current_piece
                        )
                    
                    if [start_addr, end_addr] not in disc_map[current_piece]:
                    
                        disc_map[current_piece].append(
                            [ start_addr, end_addr]
                            )
                    
                    # Look for a new fragment.
                    current_piece = None
                
                else:
                
                    # The byte found was unexpected - backtrack to the
                    # byte after the start of this block and try again.
                    print "Backtrack from %s to %s" % (hex(a), hex(current_start+1))
                    
                    next = current_start + 1
                    current_piece = None
            
            # Move to the next relevant byte.
            a = next
        
        #for k, v in disc_map.items():
        #
        #    print hex(k), map(lambda x: map(hex, x), v)
        
        return disc_map
    
    def read_free_space(self, header, begin, end):
    
        free_space = []
        
        a = header
        
        while a < end:
        
            # The next zone starts a sector after this one.
            next_zone = a + self.sector_size
            
            a = a + 1
            
            # Start by reading the offset in bits from the start of the header
            # of the first item of free space in the map.
            offset = self.str2num(2, self.sectors[a:a+2])
            
            # The top bit is apparently always set, so mask it off and convert
            # the result into bytes. * Not sure if this is the case for
            # entries in the map. *
            next = ((offset & 0x7fff) >> 3)
            
            if next == 0:
            
                # No more free space in this zone. Look at the free
                # space field in the next zone.
                a = next_zone
                continue
            
            # Update the offset to point to the free space in this zone.
            a = a + next
            
            while a < next_zone:
            
                # Read the offset to the next free fragment in this zone.
                offset = self.str2num(2, self.sectors[a:a+2])
                
                # Convert this to a byte offset.
                next = ((offset & 0x7fff) >> 3)
                
                # Find the end of the free space.
                b = a + 1
                
                while b < next_zone:
                
                    c = b + 1
                    
                    value = self.str2num(1, self.sectors[b])
                    
                    if (value & 0x80) != 0:
                    
                        break
                    
                    b = c
                
                # Record the offset into the map of this item of free space
                # and the offset of the byte after it ends.
                free_space.append( (a, c) )
                
                if next == 0:
                
                    break
                
                # Move to the next free space entry.
                a = a + next
            
            # Whether we are at the end of the zone or not, move to the
            # beginning of the next zone.
            a = next_zone
        
        #print map(lambda x: (hex(x[0]), hex(x[1])), free_space)
        
        # Return the free space list.
        return free_space
    
    def find_address_from_map(self, addr, begin, entry):
    
        if self.disc_type == 'adE':
        
            address = ((addr - begin) * self.sector_size)
        
        elif self.disc_type == 'adEbig':
        
            upper = (entry & 0x7f00) >> 8
            
            if upper > 1:
                upper = upper - 1
            if upper > 3:
                upper = 3
            
            address = ((addr - begin) - (upper * 0xc8)) * 0x200
        
        return address
    
    def find_in_new_map(self, file_no):
    
        try:
        
            return self.disc_map[file_no]
        
        except KeyError:
        
            return []
    
    def read_tracks(self, f, inter):
    
        t = ""
        
        f.seek(0, 0)
        
        if inter==0:
            try:
                for i in range(0, self.ntracks):
                
                    t = t + f.read(self.nsectors * self.sector_size)
            
            except IOError:
                print 'Less than %i tracks found.' % self.ntracks
                f.close()
                raise ADFS_exception, \
                    'Less than %i tracks found.' % self.ntracks
        
        else:
        
            # Tracks are interleaved (0 80 1 81 2 82 ... 79 159) so rearrange
            # them into the form (0 1 2 3 ... 159)
            
            try:
            
                for i in range(0, self.ntracks):
                
                    if i < (self.ntracks >> 1):
                        f.seek(i*2*self.nsectors*self.sector_size, 0)
                        t = t + f.read(self.nsectors*self.sector_size)
                    else:
                        j = i - (self.ntracks >> 1)
                        f.seek(((j*2)+1)*self.nsectors*self.sector_size, 0)
                        t = t + f.read(self.nsectors*self.sector_size)
            
            except IOError:
            
                print 'Less than %i tracks found.' % self.ntracks
                f.close()
                raise ADFS_exception, \
                    'Less than %i tracks found.' % self.ntracks
        
        return t
    
    
    def read_sectors(self, adf):
    
        s = []
        try:
        
            for i in range(0, self.ntracks):
            
                for j in range(0, self.nsectors):
                
                    s.append(adf.read(self.sector_size))
        
        except IOError:
        
            print 'Less than %i tracks x %i sectors found.' % \
                (self.ntracks, self.nsectors)
            adf.close()
            raise ADFS_exception, \
                'Less than %i tracks x %i sectors found.' % \
                (self.ntracks, self.nsectors)
        
        return s
    
    
    def safe(self, s, with_space = 0):
    
        new = ""
        if with_space == 1:
            lower = 31
        else:
            lower = 32
        
        for i in s:
        
            if ord(i) <= lower:
                break
            
            if ord(i) >= 128:
                c = ord(i)^128
                if c > 32:
                    new = new + chr(c)
            else:
                new = new + i
        
        return new
    
    
    def read_freespace(self):
    
        # Currently unused
            
        base = 0
    
        free = []
        p = 0
        while self.sectors[base+p] != 0:
    
            free.append(self.str2num(3, self.sectors[base+p:base_p+3]))
    
        name = self.sectors[self.sector_size-9:self.sector_size-4]
    
        disc_size = self.str2num(
            3, self.sectors[self.sector_size-4:self.sector_size-1]
            )
    
        checksum0 = self.str2num(1, self.sectors[self.sector_size-1])
    
        base = self.sector_size
    
        p = 0
        while self.sectors[base+p] != 0:
    
            free.append(self.str2num(3, self.sectors[base+p:base_p+3]))
    
        name = name + \
            self.sectors[base+self.sector_size-10:base+self.sector_size-5]
    
        disc_id = self.str2num(
            2, self.sectors[base+self.sector_size-5:base+self.sector_size-3]
            )
    
        boot = self.str2num(1, self.sectors[base+self.sector_size-3])
    
        checksum1 = self.str2num(1, self.sectors[base+self.sector_size-1])
    
    
    def read_old_catalogue(self, base):
    
        head = base
    #    base = sector_size*2
        p = 0
        
        dir_seq = self.sectors[head + p]
        dir_start = self.sectors[head+p+1:head+p+5]
        if dir_start != 'Hugo':
        
            if self.verify:
            
                self.verify_log.append(
                    (WARNING, 'Not a directory: %x' % head)
                    )
            
            return "", []
        
        p = p + 5
        
        files = []
        
        while ord(self.sectors[head+p]) != 0:
        
            old_name = self.sectors[head+p:head+p+10]
            top_set = 0
            counter = 1
            for i in old_name:
                if (ord(i) & 128) != 0:
                    top_set = counter
                counter = counter + 1
            
            name = self.safe(self.sectors[head+p:head+p+10])
            
            load = self.str2num(4, self.sectors[head+p+10:head+p+14])
            exe = self.str2num(4, self.sectors[head+p+14:head+p+18])
            length = self.str2num(4, self.sectors[head+p+18:head+p+22])
            
            if self.disc_type == 'adD':
                inddiscadd = 256 * self.str2num(
                    3, self.sectors[head+p+22:head+p+25]
                    )
            else:
                inddiscadd = self.sector_size * self.str2num(
                    3, self.sectors[head+p+22:head+p+25]
                    )
            
            olddirobseq = self.str2num(1, self.sectors[head+p+25])
            
            #print string.expandtabs(
            #   "%s\t%s\t%s\t%s" % (
            #       name, "("+self.binary(8, olddirobseq)+")",
            #       "("+self.binary(8, load)+")",
            #       "("+self.binary(8, exe)+")"
            #   ) )
            #print string.expandtabs(
            #   "%s\t%02x\t%08x\t%08x" % (
            #       name, olddirobseq, load, exe
            #   ) )
            
            if self.disc_type == 'adD':
            
                # Old format 800K discs.
                #if olddirobseq == 0xc:
                if (olddirobseq & 0x8) == 0x8:
                
                    # A directory has been found.
                    lower_dir_name, lower_files = \
                        self.read_old_catalogue(inddiscadd)
                        
                    files.append([name, lower_files])
                
                else:
                
                    # A file has been found.
                    files.append(
                        [ name, self.sectors[inddiscadd:inddiscadd+length],
                          load, exe, length ]
                        )
            
            else:
            
                # Old format < 800K discs.
                # [Needs more accurate check for directories.]
                if (load == 0 and exe == 0 and top_set > 2) or \
                    (top_set > 0 and length == (self.sector_size * 5)):
                
                    # A directory has been found.
                    lower_dir_name, lower_files = \
                        self.read_old_catalogue(inddiscadd)
                    
                    files.append([name, lower_files])
                
                else:
                
                    # A file has been found.
                    files.append(
                        [ name, self.sectors[inddiscadd:inddiscadd+length],
                          load, exe, length ]
                        )
            
            p = p + 26
        
        
        # Go to tail of directory structure (0x200 -- 0x700)
        
        if self.disc_type == 'adD':
            tail = head + self.sector_size    # 1024 bytes
        else:
            tail = head + (self.sector_size*4)    # 1024 bytes
        
        dir_end = self.sectors[tail+self.sector_size-5:tail+self.sector_size-1]
        if dir_end != 'Hugo':
        
            if self.verify:
            
                self.verify_log.append(
                    ( WARNING,
                      'Discrepancy in directory structure: [%x, %x] ' % \
                      ( head, tail ) )
                    )
                        
            return '', files
        
        # Read the directory name, its parent and any title given.
        if self.disc_type == 'adD':
        
            dir_name = self.safe(
                self.sectors[tail+self.sector_size-16:tail+self.sector_size-6]
                )
            
            parent = 256*self.str2num(
                3,
                self.sectors[tail+self.sector_size-38:tail+self.sector_size-35]
                )
            
            dir_title = \
                self.sectors[tail+self.sector_size-35:tail+self.sector_size-16]
        else:
        
            dir_name = self.safe(
                self.sectors[tail+self.sector_size-52:tail+self.sector_size-42]
                )
            
            parent = self.sector_size*self.str2num(
                3,
                self.sectors[tail+self.sector_size-42:tail+self.sector_size-39]
                )
            
            dir_title = self.safe(
                self.sectors[tail+self.sector_size-39:tail+self.sector_size-20]
                )
        
        if parent == head:
        
            # Use the directory title as the disc name.
            
            # Note that the title may contain spaces.
            self.disc_name = self.safe(dir_title, with_space = 1)
        
        #print "Directory title", dir_title
        #print "Directory name ", dir_name
        
        endseq = self.sectors[tail+self.sector_size-6]
        if endseq != dir_seq:
        
            if self.verify:
            
                self.verify_log.append(
                    ( WARNING,
                      'Broken directory: %s at [%x, %x]' % \
                      (dir_title, head, tail) )
                    )
            
            return dir_name, files
        
        return dir_name, files
    
    
    def read_new_address(self, s):
    
        # From the three character string passed, determine the address on the
        # disc.
        value = self.str2num(3, s)
        
        # This is a SIN (System Internal Number)
        # The bottom 8 bits are the sector offset + 1
        offset = value & 0xff
        if offset != 0:
            address = (offset - 1) * self.sector_size
        else:
            address = 0
        
        # The top 16 bits are the file number
        file_no = value >> 8
        
        #print "File number:", hex(file_no)
        #self.verify_log.append("File number: %s" % hex(file_no))
        
        # The pieces of the object are returned as a list of pairs of
        # addresses.
        #pieces = self.find_in_new_map(self.map_start, self.map_end, file_no)
        pieces = self.find_in_new_map(file_no)
        
        #print map(lambda x: map(hex, x), pieces)
        
        if pieces == []:
        
            return -1
        
        # Ensure that the first piece of data is read from the appropriate
        # point in the relevant sector.
        
        pieces[0][0] = pieces[0][0] + address
        
        return pieces
    
    
    def read_new_catalogue(self, base):
    
        head = base
        p = 0
        
        #print "Head:", hex(head)
        
        dir_seq = self.sectors[head + p]
        dir_start = self.sectors[head+p+1:head+p+5]
        if dir_start != 'Nick':
        
            if self.verify:
            
                self.verify_log.append(
                    (WARNING, 'Not a directory: %s' % hex(head))
                    )
                #print 'Not a directory: %s' % hex(head)
            
            return '', []
        
        p = p + 5
        
        files = []
        
        while ord(self.sectors[head+p]) != 0:
        
            old_name = self.sectors[head+p:head+p+10]
            top_set = 0
            counter = 1
            for i in old_name:
                if (ord(i) & 128) != 0:
                    top_set = counter
                counter = counter + 1
            
            name = self.safe(self.sectors[head+p:head+p+10])
            
            #print hex(head+p), name
            
            load = self.str2num(4, self.sectors[head+p+10:head+p+14])
            exe = self.str2num(4, self.sectors[head+p+14:head+p+18])
            length = self.str2num(4, self.sectors[head+p+18:head+p+22])
            
            #print hex(ord(self.sectors[head+p+22])), \
            #        hex(ord(self.sectors[head+p+23])), \
            #        hex(ord(self.sectors[head+p+24]))
            
            inddiscadd = self.read_new_address(
                self.sectors[head+p+22:head+p+25]
                )
            newdiratts = self.str2num(1, self.sectors[head+p+25])
            
            if inddiscadd == -1:
            
                if (newdiratts & 0x8) != 0:
                
                    if self.verify:
                    
                        self.verify_log.append(
                            (WARNING, "Couldn't find directory: %s" % name)
                            )
                        self.verify_log.append(
                            (WARNING, "    at: %x" % (head+p+22))
                            )
                        self.verify_log.append( (
                            WARNING, "    file details: %x" % \
                            self.str2num(3, self.sectors[head+p+22:head+p+25])
                            ) )
                        self.verify_log.append(
                            (WARNING, "    atts: %x" % newdiratts)
                            )
                
                elif length != 0:
                
                    if self.verify:
                    
                        self.verify_log.append(
                            (WARNING, "Couldn't find file: %s" % name)
                            )
                        self.verify_log.append(
                            (WARNING, "    at: %x" % (head+p+22))
                            )
                        self.verify_log.append( (
                            WARNING,
                            "    file details: %x" % \
                            self.str2num(3, self.sectors[head+p+22:head+p+25])
                            ) )
                        self.verify_log.append(
                            (WARNING, "    atts: %x" % newdiratts)
                            )
                
                else:
                
                    # Store a zero length file. This appears to be the
                    # standard behaviour for storing empty files.
                    files.append([name, "", load, exe, length])
                    
                    #print hex(head+p), hex(head+p+22)
            
            else:
            
                if (newdiratts & 0x8) != 0:
                
                    #print '%s -> %s' % (name, hex(inddiscadd))
                    
                    # Remember that inddiscadd will be a sequence of
                    # pairs of addresses.
                    
                    #print
                    #print hex(head+p+22),
                    #print name, hex(load), hex(exe), hex(length)
                    #print hex(ord(self.sectors[head+p+22])), \
                    #        hex(ord(self.sectors[head+p+23])), \
                    #        hex(ord(self.sectors[head+p+24]))
                    #print "addrs:", map(lambda x: map(hex, x), inddiscadd),
                    #print "atts:", hex(newdiratts)
                    
                    for start, end in inddiscadd:
                    
                        #print hex(start), hex(end), "-->"
                        
                        # Try to interpret the data at the referenced address
                        # as a directory.
                        
                        lower_dir_name, lower_files = \
                            self.read_new_catalogue(start)
                        
                        # Store the directory name and file found therein.
                        files.append([name, lower_files])
                
                else:
                
                    # Remember that inddiscadd will be a sequence of
                    # pairs of addresses.
                    
                    file = ""
                    remaining = length
                    
                    #print hex(head+p+22), name
                    #print "addrs:", map(lambda x: map(hex, x), inddiscadd),
                    #print "atts:", hex(newdiratts)
                    
                    for start, end in inddiscadd:
                    
                        amount = min(remaining, end - start)
                        file = file + self.sectors[start : (start + amount)]
                        remaining = remaining - amount
                    
                    files.append([name, file, load, exe, length])
            
            p = p + 26
        
        
        # Go to tail of directory structure (0x800 -- 0xc00)
        
        tail = head + self.sector_size
        
        dir_end = self.sectors[tail+self.sector_size-5:tail+self.sector_size-1]
        
        if dir_end != 'Nick':
        
            if self.verify:
            
                self.verify_log.append(
                    ( WARNING,
                      'Discrepancy in directory structure: [%x, %x]' % \
                      ( head, tail ) )
                    )
            
            return '', files
        
        dir_name = self.safe(
            self.sectors[tail+self.sector_size-16:tail+self.sector_size-6]
            )
        
        #parent = self.read_new_address(
        #    self.sectors[tail+self.sector_size-38:tail+self.sector_size-35], dir = 1
        #    )
        #print "This directory:", hex(head), "Parent:", hex(parent)
        
        parent = \
            self.sectors[tail+self.sector_size-38:tail+self.sector_size-35]
        
        #256*self.str2num(
        #   3, self.sectors[tail+self.sector_size-38:tail+self.sector_size-35]
        #)
        
        dir_title = \
            self.sectors[tail+self.sector_size-35:tail+self.sector_size-16]
        
        if head == 0x800 and self.disc_type == 'adE':
            dir_name = '$'
        if head == 0xc8800 and self.disc_type == 'adEbig':
            dir_name = '$'
        
        endseq = self.sectors[tail+self.sector_size-6]
        if endseq != dir_seq:
        
            if self.verify:
            
                self.verify_log.append(
                    ( WARNING,
                      'Broken directory: %s at [%x, %x]' % \
                      (dir_title, head, tail) )
                    )
            
            return dir_name, files
        
        #print '<--'
        #print
        
        return dir_name, files
    
    
    def read_leafname(self, path):
    
        pos = string.rfind(path, os.sep)
        if pos != -1:
            return path[pos+1:]
        else:
            return path
    
    
    def print_catalogue(self, files = None, path = "$", filetypes = 0,
                        separator = ","):
    
        if files is None:
        
            files = self.files
        
        if files == []:
        
            print path, "(empty)"
        
        for i in files:
    
            name = i[0]
            if type(i[1]) != type([]):
            
                load, exec_addr, length = i[2], i[3], i[4]
                
                if filetypes == 0:
                
                    # Load and execution addresses treated as valid.
                    print string.expandtabs(
                        "%s.%s\t%X\t%X\t%X" % (
                            path, name, load, exec_addr, length
                            ), 16
                        )
                
                else:
                
                    # Load address treated as a filetype.
                    print string.expandtabs(
                        "%s.%s\t%X\t%X" % (
                            path, name, ((load >> 8) & 0xfff), length
                            ), 16
                        )
            
            else:
            
                self.print_catalogue(i[1], path + "." + name, filetypes)
    
    
    def convert_name(self, old_name, convert_dict):
    
        # Use the conversion dictionary to convert any forbidden
        # characters to accepted local substitutes.
        name = ""
        
        for c in old_name:
        
            if c in convert_dict.keys():
            
                name = name + convert_dict[c]
            
            else:
            
                name = name + c
        
        if self.verify and old_name != name:
        
            self.verify_log.append(
                ( WARNING,
                  "Changed %s to %s" % (old_name, name) )
                )
        
        return name
    
    def extract_old_files(self, l, path, filetypes = 0, separator = ",",
                          convert_dict = {}):
    
        new_path = self.create_directory(path)
        
        if new_path != "":
        
            path = new_path
        
        else:
        
            return
        
        for i in l:
        
            old_name = i[0]
            
            name = self.convert_name(old_name, convert_dict)
            
            if type(i[1]) != type([]):
            
                # A file.
                load, exec_addr, length = i[2], i[3], i[4]
                
                if filetypes == 0:
                
                    # Load and execution addresses assumed to be valid.
                    
                    # Create the INF file
                    out_file = os.path.join(path, name)
                    inf_file = os.path.join(path, name) + separator + "inf"
                    
                    try:
                        out = open(out_file, "wb")
                        out.write(i[1])
                        out.close()
                    except IOError:
                        print "Couldn't open the file: %s" % out_file
                    
                    try:
                        inf = open(inf_file, "w")
                        load, exec_addr, length = i[2], i[3], i[4]
                        inf.write( "$.%s\t%X\t%X\t%X" % \
                                   ( name, load, exec_addr, length ) )
                        inf.close()
                    except IOError:
                        print "Couldn't open the file: %s" % inf_file
                
                else:
                
                    # Interpret the load address as a filetype.
                    out_file = os.path.join(path, name) + separator + "%x" % \
                               ((load >> 8) & 0xfff)
                    
                    try:
                        out = open(out_file, "wb")
                        out.write(i[1])
                        out.close()
                    except IOError:
                        print "Couldn't open the file: %s" % out_file
            else:
            
                new_path = os.path.join(path, name)
                
                self.extract_old_files(
                    i[1], new_path, filetypes, separator, convert_dict
                    )
    
    
    def extract_new_files(self, l, path, filetypes = 0, separator = ",",
                          convert_dict = {}):
    
        new_path = self.create_directory(path)
        
        if new_path != "":
        
            path = new_path
        
        else:
        
            return
        
        for i in l:
        
            old_name = i[0]
            
            # Use the conversion dictionary to convert any forbidden
            # characters to accepted local substitutes.
            name = self.convert_name(old_name, convert_dict)
            
            if type(i[1]) != type([]):
            
                # A file.
                load, exec_addr, length = i[2], i[3], i[4]
                
                if filetypes == 0:
                
                    # Load and execution addresses assumed to be valid.
                    
                    # Create the INF file
                    out_file = path + os.sep + name
                    inf_file = path + os.sep + name + separator + "inf"
                    
                    try:
                        out = open(out_file, "wb")
                        out.write(i[1])
                        out.close()
                    except IOError:
                        print "Couldn't open the file: %s" % out_file
                    
                    try:
                        inf = open(inf_file, "w")
                        load, exec_addr, length = i[2], i[3], i[4]
                        inf.write( "$.%s\t%X\t%X\t%X" % \
                                   ( name, load, exec_addr, length ) )
                        inf.close()
                    except IOError:
                        print "Couldn't open the file: %s" % inf_file
                else:
                
                    # Interpret the load address as a filetype.
                    out_file = path + os.sep + name + separator + "%x" % \
                               ((load >> 8) & 0xfff)
                    
                    try:
                        out = open(out_file, "wb")
                        out.write(i[1])
                        out.close()
                    except IOError:
                        print "Couldn't open the file: %s" % out_file
            else:
            
                new_path = os.path.join(path, name)
                
                self.extract_new_files(
                    i[1], new_path, filetypes, separator, convert_dict
                    )
    
    
    def extract_files(self, out_path, files = None, filetypes = 0,
                      separator = ",", convert_dict = {}):
    
        if files is None:
        
            files = self.files
        
        if self.disc_type == 'adD':
        
            self.extract_old_files(
                files, out_path, filetypes, separator, convert_dict
                )
        
        elif self.disc_type == 'adE':
        
            self.extract_new_files(
                files, out_path, filetypes, separator, convert_dict
                )
        
        elif self.disc_type == 'adEbig':
        
            self.extract_new_files(
                files, out_path, filetypes, separator, convert_dict
                )
        
        else:
        
            self.extract_old_files(
                files, out_path, filetypes, separator, convert_dict
                )
    
    def create_directory(self, path, name = None):
    
        elements = []
        
        while not os.path.exists(path) and path != "":
        
            path, file = os.path.split(path)
            
            elements.insert(0, file)
        
        if path != "":
        
            elements.insert(0, path)
        
        if name is not None:
        
            elements.append(name)
        
        # Remove any empty list elements or those containing a $ character.
        elements = filter(lambda x: x != '' and x != "$", elements)
        
        try:
        
            built = ""
            
            for element in elements:
            
                built = os.path.join(built, element)
                
                if not os.path.exists(built):
                
                    # This element of the directory does not exist.
                    # Create a directory here.
                    os.mkdir(built)
                    print 'Created directory:', built
                
                elif not os.path.isdir(built):
                
                    # This element of the directory already exists
                    # but is not a directory.
                    print 'A file exists which prevents a ' + \
                        'directory from being created: %s' % built
                    
                    return ""
        
        except OSError:
        
            print 'Directory could not be created: %s' % \
                string.join(elements, os.sep)
            
            return ""
        
        # Success
        return built
    
    def plural(self, msg, values, words):
    
        """message = plural(self, msg, values, words)
        
        Return a message which takes into account the plural form of
        words in the original message, assuming that the appropriate
        form for negative numbers of items is the same as that for
        more than one item.
        
        values is a list of numeric values referenced in the message.
        words is a list of sequences of words to substitute into the
        message. This takes the form
        
            [ word_to_use_for_zero_items,
              word_to_use_for_one_item,
              word_to_use_for_two_or_more_items ]
        
        The length of the values and words lists must be equal.
        """
        
        substitutions = []
        
        for i in range(0, len(values)):
        
            n = values[i]
            
            # Each number must be mapped to a value in the range [0, 2].
            if n > 1: n = 2
            elif n < 0: n = 2
            
            substitutions.append(values[i])
            substitutions.append(words[i][n])
        
        return msg % tuple(substitutions)
    
    def print_log(self, verbose = 0):
    
        """print_log(self, verbose = 0)
        \r
        \rPrint the disc verification log. Any purely informational messages
        \rare only printed is verbose is set to 1.
        """
        
        if hasattr(self, "disc_map") and self.disc_map.has_key(1):
        
            print self.plural(
                "%i mapped %s found.", [len(self.disc_map[1])],
                [("defects", "defect", "defects")]
                )
        
        # Count the information, warning and error messages in the log.
        informs = reduce(lambda a, b: a + (b[0] == INFORM), self.verify_log, 0)
        warnings = reduce(
            lambda a, b: a + (b[0] == WARNING), self.verify_log, 0
            )
        errors = reduce(lambda a, b: a + (b[0] == ERROR), self.verify_log, 0)
        
        if (warnings + errors) == 0:
        
            print "All objects located."
            if not verbose: return
        
        if self.verify_log != []:
        
            print
        
        for msgtype, line in self.verify_log:
        
            print line


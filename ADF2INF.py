#! /usr/bin/env python
"""
    Name        : ADF2INF.py
    Author      : David Boddie
    Created     : Wed 18th October 2000
    Updated     : Mon 24th March 2003
    Purpose     : Convert ADFS disc images (ADF) to INF files
    WWW         : http://david.boddie.org.uk/Projects/Emulation/T2Tools
"""

def find_switch(l, switch, args = 0):

    j = -1

    for i in range(0, len(l)):
        if l[i] == switch:
            if args > 0:
                if i < len(l)-1:
                    # Switch was before the end
                    if args == 1:
                        return l[i], l[i+1]
                    else:
                        return l[i], l[i+1:i+1+args]
                else:
                    return l[i], None
            else:
                return l[i], None

        elif l[i][:len(switch)] == switch:
            # Switch is the first part of an item in the list then return
            # the item split into the switch and the argument. Should only
            # occur for single argument switches. 
            return l[i][:len(switch)], l[i][len(switch):]

    return None, None


def remove_switch(l, switch, args = 0):

    argv = []

    i = 0
    while i < len(l):

        if l[i] == switch:
            i = i + args + 1
        elif l[i][:len(switch)] == switch:
            i = i + args
        else:
            argv.append(l[i])
            i = i + 1

    return argv


def number(size, n):

    # Little endian writing

    s = ""

    while size > 0:
        i = n % 256
        s = s + chr(i)
        n = n / 256
        size = size - 1

    return s


def str2num(size, s):

    i = 0
    n = 0
    while i < size:

        n = n | (ord(s[i]) << (i*8))
        i = i + 1

    return n


def binary(size, n):

    s = size
    i = n
    new = ""
    while (i > 0) & (s > 0):

        if (i & 1)==1:
            new = "1" + new
        else:
            new = "0" + new

        i = i >> 1
        s = s - 1

    if s > 0:
        new = ("0"*s) + new

    return new


def chunk(f, n, data):

    # Chunk ID
    f.write(number(2, n))
    # Chunk length
    f.write(number(4, len(data)))
    # Data
    f.write(data)


def identify_format(adf):

    # Simple test for D and E formats: look for Hugo at 0x401 for D format
    # and Nick at 0x801 for E format
    adf.seek(0x401)
    word1 = adf.read(4)
    adf.seek(0x801)
    word2 = adf.read(4)
    adf.seek(0)

    if word1 == 'Hugo':
        return 'D'
    elif word2 == 'Nick':
        return 'E'
    else:
        return '?'


def read_disc_record(offset):

    sector_size = ord(sectors[offset])    # Total sectors per track (sectors * heads)
    nsectors = ord(sectors[offset + 1])    # Sectors per track
    heads = ord(sectors[offset + 2])    # Heads per track

    type = ord(sectors[offset+3])
    if type == 1:
        density = 'single'        # Single density disc
    elif type == 2:
        density = 'double'        # Double density disc
    elif type == 3:
        density = 'quad'        # Quad density disc
    else:
        density = 'unknown'

    # LowSector
    # StartUp
    # LinkBits
    bit_size = str2num(1, sectors[offset + 6 : offset + 7])        # BitSize (size of ID field?)
    # RASkew
    # BootOpt
    zones = ord(sectors[offset + 10])                # Zones
    # ZoneSpare
    root = sectors[offset + 12 : offset + 15]            # RootDir
    # Identify
    # SequenceSides
    # DoubleStep
    disc_size = str2num(4, sectors[offset + 16 : offset + 20])    # DiscSize
    disc_id   = str2num(2, sectors[offset + 20 : offset + 22])    # DiscId
    disc_name = string.strip(sectors[offset + 22 : offset + 32])    # DiscName

    return {'sectors': nsectors, 'heads': heads, 'density': density, 'disc size': disc_size,
        'disc ID': disc_id, 'disc name': disc_name, 'zones': zones, 'root': root}


def read_disc_info(disc_type):

    global map_start, map_end
    
    checksum = ord(sectors[0])
    first_free = str2num(2, sectors[1:3])

    if disc_type == 'adE':

        record = read_disc_record(4)
        map_start, map_end = 0x40, 0x400
        #map = read_new_map(disc_type, map_start, map_end)
        map = scan_new_map(map_start, map_end)
        
        return record['disc name'], map

    if disc_type == 'adEbig':

        record = read_disc_record(0xc6804)
        map_start, map_end = 0xc6840, 0xc7800
        #map = read_new_map(disc_type, map_start, map_end)
        map = scan_new_map(map_start, map_end)

        return record['disc name'], map

    else:
        return 'Unknown'

#    zone_size = 819200 / record['zones']
#    ids_per_zone = zone_size /

def read_new_map(disc_type, begin, end):

    map = {}

    a = begin
    
    current = None
    
    while a < end:
    
        entry = str2num(2, sectors[a:a+2])
        
        # The next entry to be read will occur one byte after this one
        # unless one of the following checks override this behaviour.
        next = a + 1
        
        # Entry must be above 1 (defect)
        if current is None:
        
            if (entry & 0x00ff) > 1 and (entry & 0x00ff) != 0xff:
            
                # Define a new entry.
                current = entry & 0x7fff
                #print "Begin:", hex(current), hex(a)
                
                if not map.has_key(current):
                
                    map[current] = []
                
                if disc_type == 'adE':
                
                    address = ((a - begin) * sector_size)
                
                elif disc_type == 'adEbig':
                
                    upper = (entry & 0x7f00) >> 8
                    
                    if upper > 1:
                        upper = upper - 1
                    if upper > 3:
                        upper = 3
                    
                    address = ((a - begin) - (upper * 0xc8)) * 0x200
                
                # Add a list containing the start address of the
                # file/directory to the list of objects associated
                # with this file number.
                map[current].append( [address] )
            
            next = a + 1
        
        if (entry & 0x8000) != 0:
        
            if current is not None:
            
                if disc_type == 'adE':
                
                    address = ((a + 2 - begin) * sector_size)
                
                elif disc_type == 'adEbig':
                
                    upper = (entry & 0x7f00) >> 8
                    
                    if upper > 1:
                        upper = upper - 1
                    if upper > 3:
                        upper = 3
                    
                    address = ((a + 2 - begin) - (upper * 0xc8)) * 0x200
                
                # This is the end of the current entry. Modify the latest
                # address to indicate a range of addresses.
                #print "End:", hex(current), hex(a)
                map[current][-1].append(address)
                
                # Unset the current file number.
                current = None
            
            next = a + 2
            
            # Move past the ending bit to an evenly aligned byte.
            #if next % 2 != 0:
            #
            #    next = next + 1
        
        a = next
    
    #for k, v in map.items():
    #
    #    print hex(k), __builtins__.map(lambda x: __builtins__.map(hex, x), v)
    
    return map


def scan_new_map(begin, end):

    map = {}

    a = begin
    
    previous = 0x80
    
    while a < end:
    
        value = str2num(2, sectors[a:a+2])
        entry = value & 0x7fff
        
        next = a + 1
        
        if (entry & 0xff) > 1 and (previous & 0x80) != 0:
        
            #print hex(entry), hex(a)
            
            if not map.has_key(entry):
            
                # Create a new map entry corresponding to this value in which
                # the address of this entry is stored.
                map[entry] = [a]
            
            else:
            
                # Add this address to the map dictionary.
                map[entry].append(a)
        
        previous = value & 0xff
        a = next
    
    return map


def find_in_new_map(disc_type, begin, end, file_no):

    #print "File number:", hex(file_no)
    
    if file_no < 2:
    
        return []
    
    # Note that disc_map is global in this implementation.
    if not disc_map.has_key(file_no):
    
        return []
    
    a = begin
    
    pieces = []
    
    in_piece = 0
    
    # Retrieve the list of possible starting addresses for this file number.
    starts = disc_map[file_no]
    in_starts = 0
    
    #print "Map scan:", map(hex, starts)
    
    while a < end:
    
        if in_piece == 0 and in_starts < len(starts):
        
            a = starts[in_starts]
            in_starts = in_starts + 1
        
        entry = str2num(2, sectors[a:a+2])
        
        # The next entry to be read will occur one byte after this one
        # unless one of the following checks override this behaviour.
        next = a + 1
        
        if (entry & 0x7fff) == file_no:
        
            if disc_type == 'adE':
            
                address = ((a - begin) * sector_size)
            
            elif disc_type == 'adEbig':
            
                upper = (entry & 0x7f00) >> 8
                
                if upper > 1:
                    upper = upper - 1
                if upper > 3:
                    upper = 3
                
                address = ((a - begin) - (upper * 0xc8)) * 0x200
            
            # Add a list containing the start address of the
            # file/directory to the list of objects associated
            # with this file number.
            pieces.append( [address] )
            
            in_piece = 1
            
            next = a + 1
        
        if in_piece == 1 and (entry & 0x8000) != 0:
        
            if disc_type == 'adE':
            
                address = ((a + 2 - begin) * sector_size)
            
            elif disc_type == 'adEbig':
            
                upper = (entry & 0x7f00) >> 8
                
                if upper > 1:
                    upper = upper - 1
                if upper > 3:
                    upper = 3
                
                address = ((a + 2 - begin) - (upper * 0xc8)) * 0x200
            
            # This is the end of the current entry. Modify the latest
            # address to indicate a range of addresses.
            pieces[-1].append(address)
            
            in_piece = 0
            
            next = a + 2
        
        a = next
    
    #print "Pieces:", map(lambda x: map(hex, x), pieces)
    
    return pieces


def read_tracks(f, inter):

    t = ""

    if inter==0:
        try:
            for i in range(0, ntracks):

                t = t + f.read(nsectors * sector_size)

        except IOError:
            print 'Less than %i tracks found.' % ntracks
            f.close()
            sys.exit()

    else:

        # Tracks are interleaved (0 80 1 81 2 82 ... 79 159) so rearrange them
        # into the form (0 1 2 3 ... 159)

        try:
            for i in range(0,ntracks):

                if i < (ntracks/2):
                    f.seek(i*2*nsectors*sector_size, 0)
                    t = t + f.read(nsectors*sector_size)
                else:
                    j = i - (ntracks/2)
                    f.seek(((j*2)+1)*nsectors*sector_size, 0)
                    t = t + f.read(nsectors*sector_size)
        except IOError:
            print 'Less than %i tracks found.' % ntracks
            f.close()
            sys.exit()

    return t


def read_sectors(adf):

    s = []
    try:

        for i in range(0, ntracks):

            for j in range(0, nsectors):

                s.append(adf.read(sector_size))

    except IOError:

        print 'Less than %i tracks x %i sectors found.' % (ntracks, nsectors)
        adf.close()
        sys.exit()

    return s


def read_string(offset):

    s = ""
    o = offset
    while ord(sectors[o]) > 32:
        s = s + sectors[o]
        o = o + 1

    return s


def safe(s):

    new = ""
    for i in s:
        if ord(i) <= 32:
            break

        if ord(i) >= 128:
            c = ord(i)^128
            if c > 32:
                new = new + chr(c)
        else:
            new = new + i

    return new


def read_freespace():

    base = 0

    free = []
    p = 0
    while sectors[base+p] != 0:

        free.append(str2num(3, sectors[base+p:base_p+3]))

    name = sectors[sector_size-9:sector_size-4]

    disc_size = str2num(3, sectors[sector_size-4:sector_size-1])

    checksum0 = str2num(1, sectors[sector_size-1])

    base = sector_size

    p = 0
    while sectors[base+p] != 0:

        free.append(str2num(3, sectors[base+p:base_p+3]))

    name = name + sectors[base+sector_size-10:base+sector_size-5]

    disc_id = str2num(2, sectors[base+sector_size-5:base+sector_size-3])

    boot = str2num(1, sectors[base+sector_size-3])

    checksum1 = str2num(1, sectors[base+sector_size-1])


def read_old_catalogue(disc_type, base):

    global disc_name

    head = base
#    base = sector_size*2
    p = 0

    dir_seq = sectors[head + p]
    dir_start = sectors[head+p+1:head+p+5]
    if dir_start != 'Hugo':
        print 'Not a directory'
        return "", []

    p = p + 5

    files = []

    while ord(sectors[head+p]) != 0:

        old_name = sectors[head+p:head+p+10]
        top_set = 0
        counter = 1
        for i in old_name:
            if (ord(i) & 128) != 0:
                top_set = counter
            counter = counter + 1

        name = safe(sectors[head+p:head+p+10])

        load = str2num(4, sectors[head+p+10:head+p+14])
        exe = str2num(4, sectors[head+p+14:head+p+18])
        length = str2num(4, sectors[head+p+18:head+p+22])

        if disc_type == 'adD':
            inddiscadd = 256 * str2num(3, sectors[head+p+22:head+p+25])
        else:
            inddiscadd = sector_size * str2num(3, sectors[head+p+22:head+p+25])

        olddirobseq = str2num(1, sectors[head+p+25])

#        print string.expandtabs("%s\t%s\t%s\t%s" % (name, "("+binary(8, olddirobseq)+")", hex(load), hex(exe)))

        if disc_type == 'adD':
            if olddirobseq == 0xc:
                lower_dir_name, lower_files = read_old_catalogue(disc_type, inddiscadd)
                files.append([name, lower_files])
            else:
                files.append([name, sectors[inddiscadd:inddiscadd+length], load, exe, length])
        else:
            if (load == 0) & (exe == 0) & (top_set > 2):
                lower_dir_name, lower_files = read_old_catalogue(disc_type, inddiscadd)
                files.append([name, lower_files])
            else:
                files.append([name, sectors[inddiscadd:inddiscadd+length], load, exe, length])


        p = p + 26


    # Go to tail of directory structure (0x200 -- 0x700)

    if disc_type == 'adD':
        tail = head + sector_size    # 1024 bytes
    else:
        tail = head + (sector_size*4)    # 1024 bytes

    dir_end = sectors[tail+sector_size-5:tail+sector_size-1]
    if dir_end != 'Hugo':
        print 'Discrepancy in directory structure'
        return '', files

    if disc_type == 'adD':
        dir_name = safe(sectors[tail+sector_size-16:tail+sector_size-6])
        parent = 256*str2num(3, sectors[tail+sector_size-38:tail+sector_size-35])
        dir_title = sectors[tail+sector_size-35:tail+sector_size-16]
    else:
        dir_name = safe(sectors[tail+sector_size-52:tail+sector_size-42])
        parent = sector_size*str2num(3, sectors[tail+sector_size-42:tail+sector_size-39])
        dir_title = safe(sectors[tail+sector_size-39:tail+sector_size-20])

    if parent == head:
        disc_name = dir_title

#    print "Directory title", dir_title
#    print "Directory name ", dir_name

    endseq = sectors[tail+sector_size-6]
    if endseq != dir_seq:
        print 'Broken directory,', dir_title
        return dir_name, files

    return dir_name, files


def read_new_address(s):

    # From the three character string passed, determine the address on the disc
    value = str2num(3, s)
    
    # This is a SIN (System Internal Number)
    # The bottom 8 bits are the sector offset + 1
    offset = value & 0xff
    if offset != 0:
        address = (offset - 1) * sector_size
    else:
        address = 0
    
    # The top 16 bits are the file number
    file_no = value >> 8
    
    #print "File number:", hex(file_no)
    
    # The pieces of the object are returned as a list of pairs of addresses.
    pieces = find_in_new_map(disc_type, map_start, map_end, file_no)
    
    if pieces == []:
    
        return -1
    
    # Ensure that the first piece of data is read from the appropriate
    # point in the relevant sector.
    
    pieces[0][0] = pieces[0][0] + address
    
    return pieces


def read_new_catalogue(disc_type, base):

    global disc_name

    head = base
    p = 0
    
    #print "Head:", hex(head)
    
    dir_seq = sectors[head + p]
    dir_start = sectors[head+p+1:head+p+5]
    if dir_start != 'Nick':
        print 'Not a directory at '+hex(base)
        #sys.exit()
        return '', []

    p = p + 5

    files = []

    while ord(sectors[head+p]) != 0:
    
        old_name = sectors[head+p:head+p+10]
        top_set = 0
        counter = 1
        for i in old_name:
            if (ord(i) & 128) != 0:
                top_set = counter
            counter = counter + 1

        name = safe(sectors[head+p:head+p+10])

        #print hex(head+p), name

        load = str2num(4, sectors[head+p+10:head+p+14])
        exe = str2num(4, sectors[head+p+14:head+p+18])
        length = str2num(4, sectors[head+p+18:head+p+22])

        inddiscadd = read_new_address(sectors[head+p+22:head+p+25])
        newdiratts = str2num(1, sectors[head+p+25])
        
        #print hex(head+p+22),
        #print "addrs:", map(lambda x: map(hex, x), inddiscadd),
        #print "atts:", hex(newdiratts)
        
        if inddiscadd == -1:

            if (newdiratts & 0x8) != 0:
                print "Couldn't"+' find directory, "%s"' % name
            
            elif length != 0:
            
                print "Couldn't"+' find file, "%s"' % name
            
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
                
                #print inddiscadd
                
                for start, end in inddiscadd:
                
                    #print hex(start), hex(end), "-->"
                    # Try to interpret the data at the referenced address as a
                    # directory.
                    
                    lower_dir_name, lower_files = \
                        read_new_catalogue(disc_type, start)
                    
                    # Store the directory name and file found therein.
                    files.append([name, lower_files])
            
            else:
            
                # Remember that inddiscadd will be a sequence of
                # pairs of addresses.
                
                file = ""
                remaining = length
                
                for start, end in inddiscadd:
                
                    amount = min(remaining, end - start)
                    file = file + sectors[start : (start + amount)]
                    remaining = remaining - amount
                
                files.append([name, file, load, exe, length])

        p = p + 26


    # Go to tail of directory structure (0x800 -- 0xc00)

    tail = head + sector_size

    dir_end = sectors[tail+sector_size-5:tail+sector_size-1]

    if dir_end != 'Nick':
        print 'Discrepancy in directory structure'
        return '', files

    dir_name = safe(sectors[tail+sector_size-16:tail+sector_size-6])
    #parent = read_new_address(
    #    sectors[tail+sector_size-38:tail+sector_size-35], dir = 1
    #    )
    #print "This directory:", hex(head), "Parent:", hex(parent)
    parent = sectors[tail+sector_size-38:tail+sector_size-35]
    
    # 256*str2num(3, sectors[tail+sector_size-38:tail+sector_size-35])
    dir_title = sectors[tail+sector_size-35:tail+sector_size-16]

    if head == 0x800 and disc_type == 'adE':
        dir_name = '$'
    if head == 0xc8800 and disc_type == 'adEbig':
        dir_name = '$'

    endseq = sectors[tail+sector_size-6]
    if endseq != dir_seq:
        print 'Broken directory'
        return dir_name, files

    #print '<--'
    #print

    return dir_name, files


def read_leafname(path):

    pos = string.rfind(path, os.sep)
    if pos != -1:
        return path[pos+1:]
    else:
        return path


def print_catalogue(l, path):

    for i in l:

        name = i[0]
        if type(i[1]) != type([]):
        
            load, exec_addr, length = i[2], i[3], i[4]
            
            if filetypes == 0:
            
                # Load and execution addresses treated as valid.
                print string.expandtabs(
                          "%s.%s\t%X\t%X\t%X" % \
                          ( path, name, load, exec_addr, length ), 16)
            
            else:
            
                # Load address treated as a filetype.
                print string.expandtabs(
                          "%s.%s\t%X\t%X" % \
                          ( path, name, ((load >> 8) & 0xfff), length), 16 )
        
        else:
            print_catalogue(i[1], path + "." + name)


def extract_old_files(l, path):

    for i in l:
    
        name = i[0]
        if type(i[1]) != type([]):
        
            # A file.
            load, exec_addr, length = i[2], i[3], i[4]
            
            if filetypes == 0:
            
                # Load and execution addresses assumed to be valid.
                
                # Create the INF file
                out_file = path + os.sep + name
                inf_file = path + os.sep + name + suffix + "inf"
                
                try:
                    out = open(out_file, "wb")
                    out.write(i[1])
                    out.close()
                except IOError:
                    print "Couldn't open the file, %s" % out_file
                
                try:
                    inf = open(inf_file, "w")
                    load, exec_addr, length = i[2], i[3], i[4]
                    inf.write( "$.%s\t%X\t%X\t%X" % \
                               ( name, load, exec_addr, length ) )
                    inf.close()
                except IOError:
                    print "Couldn't open the file, %s" % inf_file
            
            else:
            
                # Interpret the load address as a filetype.
                out_file = path + os.sep + name + separator + "%x" % \
                           ((load >> 8) & 0xfff)
                
                try:
                    out = open(out_file, "wb")
                    out.write(i[1])
                    out.close()
                except IOError:
                    print "Couldn't open the file, %s" % out_file
        else:
            if name != '$':
                # See if the output directory exists
                try:
                    os.mkdir(path + os.sep + name)
                    print "Created directory "+path + os.sep + name
                except IOError:
                    print "Directory "+read_leafname(path + os.sep + name)+" already exists."

                extract_old_files(i[1], path + os.sep + name)
            else:
                extract_old_files(i[1], path)


def extract_new_files(l, path):

    for i in l:
    
        name = i[0]
        if type(i[1]) != type([]):
        
            # A file.
            load, exec_addr, length = i[2], i[3], i[4]

            if filetypes == 0:
            
                # Load and execution addresses assumed to be valid.
                
                # Create the INF file
                out_file = path + os.sep + name
                inf_file = path + os.sep + name + suffix + "inf"
                
                try:
                    out = open(out_file, "wb")
                    out.write(i[1])
                    out.close()
                except IOError:
                    print "Couldn't open the file, %s" % out_file
                
                try:
                    inf = open(inf_file, "w")
                    load, exec_addr, length = i[2], i[3], i[4]
                    inf.write( "$.%s\t%X\t%X\t%X" % \
                               ( name, load, exec_addr, length ) )
                    inf.close()
                except IOError:
                    print "Couldn't open the file, %s" % inf_file
            else:
            
                # Interpret the load address as a filetype.
                out_file = path + os.sep + name + separator + "%x" % \
                           ((load >> 8) & 0xfff)
                
                try:
                    out = open(out_file, "wb")
                    out.write(i[1])
                    out.close()
                except IOError:
                    print "Couldn't open the file, %s" % out_file
        else:
            if name != '$':
            
                elements = list(os.path.split(path)) + [name]
                
                # Remove any empty list elements.
                elements = filter(lambda x: x != '', elements)
                
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
                                'directory from being created: %s' % \
                                os.path.join(elements)
                            
                            return
                
                except OSError:
                
                    print 'Directory could not be created: %s' % \
                        os.path.join(elements)
                    
                    return

                extract_new_files(i[1], path + os.sep + name)
            else:
                extract_new_files(i[1], path)


import os, string, sys
import cmdsyntax

syntax = """
(
    [-l | --list] [-t | --file-types] <ADF file>
) |
(
    [-d | --create-directory]
    [(-t | --file-types) [(-s separator) | --separator=character]]
    <ADF file> <destination path>
)"""
version = "0.30c (Mon 24th March 2003)"
__version__ = version

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

# Check the properties using the length of the file
adf.seek(0,2)
length = adf.tell()
adf.seek(0,0)

if length == 163840:
    ntracks = 40
    nsectors = 16
    sector_size = 256
    interleave = 0
    disc_type = 'adf'

#if string.lower(adf_file[-4:])==(suffix+"adf"):
elif length == 327680:
    ntracks = 80
    nsectors = 16
    sector_size = 256
    interleave = 0
    disc_type = 'adf'

#elif string.lower(adf_file[-4:])==(suffix+"adl"):
elif length == 655360:
    ntracks = 160
    nsectors = 16        # per track
    sector_size = 256    # in bytes
    interleave = 1
    disc_type = 'adl'

elif length == 819200:

    if identify_format(adf) == 'D':
        ntracks = 80
        nsectors = 10
        sector_size = 1024
        interleave = 0
        disc_type = 'adD'

    elif identify_format(adf) == 'E':
        ntracks = 80
        nsectors = 10
        sector_size = 1024
        interleave = 0
        disc_type = 'adE'
    else:
        print 'Please supply a .adf, .adl or .adD file.'
        print
        sys.exit()

elif length == 1638400:

    ntracks = 80
    nsectors = 20
    sector_size = 1024
    interleave = 0
    disc_type = 'adEbig'

else:
    print 'Please supply a .adf, .adl or .adD file.'
    print
    sys.exit()

# Read tracks
sectors = read_tracks(adf, interleave)

# Close the ADF file
adf.close()

#open('dump', 'wb').write(sectors)
#sys.exit()

disc_name = 'Untitled'

if disc_type == 'adD':

    # Find the root directory name and all the files and directories contained within it
    dir_name, files = read_old_catalogue(disc_type, 0x400)

elif disc_type == 'adE':

    # Read the disc name and map
    disc_name, disc_map = read_disc_info(disc_type)

    # Find the root directory name and all the files and directories contained within it
    dir_name, files = read_new_catalogue(disc_type, 0x800)

elif disc_type == 'adEbig':

    # Read the disc name and map
    disc_name, disc_map = read_disc_info(disc_type)

    # Find the root directory name and all the files and directories contained within it
    dir_name, files = read_new_catalogue(disc_type, 0xc8800)

else:
    # Find the root directory name and all the files and directories contained within it
    dir_name, files = read_old_catalogue(disc_type, 2*sector_size)

# Print catalogue
if listing != 0:

    print 'Contents of', disc_name,':'
    print

    print_catalogue(files, dir_name)

    # Exit
    sys.exit()


# Attempt to create a directory using the output path in case the user wants to
# put the disc inside a directory to be sure that the disc won't overwrite files.

try:
    os.mkdir(out_path)
    print 'Created directory: %s' % out_path
except OSError:
    print "Couldn't create directory: %s" % out_path
    sys.exit()

# Make sure that the disc is put in a directory corresponding to the disc name
# where applicable.

if use_name != 0 and disc_name != '$':

    try:
        os.mkdir(out_path + os.sep + disc_name)
        out_path = out_path + os.sep + disc_name
        print 'Created directory '+out_path
    except IOError:
        print "Couldn't create directory "+read_leafname(out_path)+'.'

# Extract the files

if disc_type == 'adD':
    extract_old_files(files, out_path)

elif disc_type == 'adE':
    extract_new_files(files, out_path)

elif disc_type == 'adEbig':
    extract_new_files(files, out_path)

else:
    extract_old_files(files, out_path)


# Exit
sys.exit()

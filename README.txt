ADFSlib and ADF2INF

Copyright (c) 2000-2011, David Boddie <david@boddie.org.uk>

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


Acknowledgements

Thanks to John Kortink and David Ruck for their assistance and advice.
Any errors or faults in these libraries and tools are not theirs.

Various documents from J.G. Harston (http://mdfs.net/Docs/Comp/Disk/Format/)
and Robin Watts (http://wss.co.uk/pinknoise/Docs/index.html) have proved to be
invaluable references when developing these libraries and tools.


Description

This is a snapshot of my ADFS floppy disc reading library and its associated
utility.

The ADF2INF utility will take advantage of the cmdsyntax module if
available. See

    http://www.boddie.org.uk/david/Projects/Python/CMDSyntax

for details of how to obtain the cmdsyntax module.


Install ADFSlib and ADF2INF (as root) by typing

  python setup.py install

or just use them from the directory in which you unpack them.


History

Name        : ADF2INF.py
Author      : David Boddie
Created     : Wed 18th October 2000
Purpose     : Convert ADFS disc images (ADF) to INF files

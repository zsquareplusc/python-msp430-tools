#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

import urllib2
import tarfile
import os
import sys
import shutil

# XXX method to get latest? currently a version is hardcoded.
URL = 'http://sourceforge.net/projects/mspgcc/files/msp430mcu/msp430mcu-20110612.tar.bz2/download'
ARCHIVE_NAME = 'upstream.tar.bz2'

# set up environment
if os.path.exists('upstream'):
    print "ERROR upstream directory already exists. Manually remove to proceed"
    sys.exit(1)

os.mkdir('upstream')

if os.path.exists(ARCHIVE_NAME):
    print "%s found on disk using it. To download latest data, rename or delete the file." % (ARCHIVE_NAME)
else:
    # download archive from MSPGCC (git web interface)
    print "Downloading archive from sf.net (~3MB). This may take a few minutes..."
    archive = urllib2.urlopen(URL)
    archfile = open(ARCHIVE_NAME, 'wb')
    archfile.write(archive.read())
    archfile.close()
    print "Download complete."


print "Extracting the archive contents..."
tar = tarfile.open(ARCHIVE_NAME, 'r')
for tarinfo in tar:
    #~ print tarinfo.name, "is", tarinfo.size, "bytes in size and is",
    if tarinfo.isreg() and 'upstream' in tarinfo.name:
        filename = os.path.basename(tarinfo.name)
        target_name = os.path.join('upstream', filename)
        shutil.copyfileobj(
                tar.extractfile(tarinfo),
                open(target_name, 'wb'))
tar.close()
print "Completed"

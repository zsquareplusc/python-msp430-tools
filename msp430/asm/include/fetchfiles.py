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
URL = 'http://sourceforge.net/projects/mspgcc/files/msp430mcu/msp430mcu-20130321.tar.bz2/download'
ARCHIVE_NAME = 'upstream.tar.bz2'

# set up environment
if os.path.exists('upstream'):
    sys.stderr.write("ERROR upstream directory already exists. Manually remove to proceed\n")
    sys.exit(1)

os.mkdir('upstream')

if os.path.exists(ARCHIVE_NAME):
    sys.stderr.write("%s found on disk using it. To download latest data, rename or delete the file.\n" % (ARCHIVE_NAME))
else:
    # download archive from MSPGCC (git web interface)
    sys.stderr.write("Downloading archive from sf.net (~15MB). This may take a few minutes...\n")
    archive = urllib2.urlopen(URL)
    archfile = open(ARCHIVE_NAME, 'wb')
    archfile.write(archive.read())
    archfile.close()
    sys.stderr.write("Download complete.\n")


sys.stderr.writet("Extracting the archive contents...\n")
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
sys.stderr.write("Completed\n")

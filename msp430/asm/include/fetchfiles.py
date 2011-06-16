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

URL = 'http://mspgcc.git.sourceforge.net/git/gitweb.cgi?p=mspgcc/msp430mcu;a=snapshot;h=0ae19e5a4b167b21f4b3a5ad65a7bcc63eebad6b;sf=tgz'

# set up environment
if os.path.exists('upstream'):
    print "ERROR upstream directory already exists. Manually remove to proceed"
    sys.exit(1)

os.mkdir('upstream')

if os.path.exists('upstream.tar.gz'):
    print "upstream.tar.gz found on disk using it. To download latest data, rename or delete the file."
else:
    # download archive from MSPGCC (git web interface)
    print "Downloading archive from sf.net (~7MB). This may take a few minutes..."
    archive = urllib2.urlopen(URL)
    archfile = open('upstream.tar.gz', 'wb')
    archfile.write(archive.read())
    archfile.close()
    print "Download complete."


print "Extracting the archive contents..."
tar = tarfile.open('upstream.tar.gz', 'r:gz')
for tarinfo in tar:
    #~ print tarinfo.name, "is", tarinfo.size, "bytes in size and is",
    if tarinfo.isreg():
        filename = os.path.basename(tarinfo.name)
        target_name = os.path.join('upstream', filename)
        shutil.copyfileobj(
                tar.extractfile(tarinfo),
                open(target_name, 'wb'))
tar.close()
print "Completed"

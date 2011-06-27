#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

import xprotocol
from matplotlib.pylab import *

box = xprotocol.XProtocol('/dev/ttyACM0', 2400)
box.open()
#~ for i in range(16):
        #~ print x.decode(x.command('a%02x' % i))

CHANNELS = [0, 4, 5, 7, 8, 9, 10, 11]
rows = [[] for x in CHANNELS]
for n in range(10):
    for n, i in enumerate(CHANNELS):
        rows[n].append(box.decode(box.command('a%02x' % i))[0])

fig = figure()
ax = fig.add_subplot(111)
for y in rows:
    if y:
        x = arange(len(y))
        ax.plot(x,y)
show()
#~ plot(samples)

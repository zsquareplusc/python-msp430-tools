#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2003-2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Helper module to parse IAR listing files.
"""

import re, sys, os

verbosity = 0

symbols = {}

class Module:
    def __init__(self,name):
        self.name = name
        self.labels = []

    def __getitem__(self,value):
        """return address or name of label depending on the argument, None if not found"""
        if type(value) is str: # serach for label name
            for lbl,adr,glob in self.labels:
                if lbl == value:
                    return adr
        elif type(value) is int:  # search for label address
            for lbl,adr,glob in self.labels:
                if adr == value:
                    return lbl
        else:
            raise TypeError("string or integer required")

    def __contains__(self, value):
        for lbl,adr,glob in self.labels:
            if lbl == value:
                return True
        return False

    def getLabels(self):
        return [lbl for lbl,adr,glob in self.labels if glob]

    def display(self):
        print "Module: %s" % self.name
        if self.labels:
            print "\tLabels:"
            for l in self.labels:
                print "\t\t%s \t@0x%04x (%d)" % l
        else:
            print "\tno labels in this module"

#REs for ENTRY LIST
RE_ENTRY = re.compile(r'^  ([\w_\?0-9]+)[\t ]+([A-F0-9]+)',re.I)
RE_ENTRYMODNAME = re.compile(r'^([\w_\?/\\\.0-9]+)[\t ]+\(',re.I)

#REs for SEGMENTS
RE_SEGMENT = re.compile('^([\w_0-9]+)[\t ]+([A-F0-9]+)( - ([A-F0-9]+))?[\t ]+([A-F0-9]+)',re.I)

#REs for MODULE MAP
RE_MP_ENTRYSTART    = re.compile(r'^           =====',re.I)
RE_MP_ENTRY         = re.compile(r'^           ([\w_\?0-9:]+)[\t ]+([A-F0-9]+)',re.I)
RE_MP_LONG_ENTRY    = re.compile(r'^           ([\w_\?0-9:]+)\n',re.I)
RE_MP_LONG_ENTRY_ADDR = re.compile(r'^                                   ([A-F0-9]+) ',re.I)
RE_MP_ENTRYMODNAME  = re.compile(r'MODULE, NAME : ([\w_\?/\\\.0-9]+)',re.I)
RE_MP_ENTRYLOCAL    = re.compile(r'^           LOCAL',re.I)
RE_MP_ENTRYENTRY    = re.compile(r'^           ENTRY',re.I)

RE_CROSSREFERENCE = re.compile('CROSS REFERENCE')
RE_ENTRYLIST = re.compile('ENTRY LIST')
RE_MODULEMAP = re.compile('MODULE MAP')
RE_CALLGRAPH = re.compile('CALL GRAPH')
RE_SEGMENTS = re.compile('SEGMENTS IN ADDRESS ORDER')

class MemMap:
    def __init__(self, filename = None):
        print 'init mem map:', filename
        self.module = 0
        self.modules = []
        self.MP_NONE, self.MP_GLOBAL, self.MP_LOCAL = range(3) # types of labels
        self.modmapstart = self.MP_NONE
        self.long_module_name = 0

        self.sections = [
            (RE_CROSSREFERENCE, self.parseCROSSREFERENCE,"CROSS REFERENCE"),
            (RE_ENTRYLIST,      self.parseENTRYLIST,     "ENTRY LIST"),
            (RE_MODULEMAP,      self.parseMODULEMAP,     "MODULE MAP"),
            (RE_CALLGRAPH,      self.parseCALLGRAPH,     "CALL GRAPH"),
            (RE_SEGMENTS,       self.parseSEGMENTS,      "SEGMENTS IN ADDRESS ORDER"),
        ]
        if filename is not None: self.load(filename)

    def load(self, filename):
        f = open(filename)

        section = -1
        for l in f.readlines():
            for i in range(len(self.sections)):
                g = self.sections[i][0].search(l)
                if g:
                    if verbosity:
                        print "Scanning section", self.sections[i][2]
                    section = i
                    break;
            if section >= 0:
                self.sections[section][1](l)
        f.close()

    def parseCROSSREFERENCE(self, l):
        pass

    def parseENTRYLIST(self, l):
        g = RE_ENTRYMODNAME.search(l)
        if g:
            self.module = Module(g.group(1))
            #modules.append(module)
        g = RE_ENTRY.search(l)
        if self.module and g:
            self.module.labels.append((g.group(1),int(g.group(2), 16)))

    def parseMODULEMAP(self, l):
        g = RE_MP_ENTRYMODNAME.search(l)
        if g:
            self.module = Module(g.group(1))
            self.modules.append(self.module)
            self.modmapstart = 0
            return

        #g = RE_MP_ENTRYSTART.search(l)
        #if g: modmapstart = 1

        g = RE_MP_ENTRYENTRY.search(l)
        if g:
            self.modmapstart = self.MP_GLOBAL
            return

        g = RE_MP_ENTRYLOCAL.search(l)
        if g:
            self.modmapstart = self.MP_LOCAL
            return

        g = RE_MP_LONG_ENTRY.search(l)
        if self.modmapstart and self.module and g:
            self.long_module_name = g.group(1)
            return

        g = RE_MP_LONG_ENTRY_ADDR.search(l)
        if self.modmapstart and self.module and g:
            self.module.labels.append( (self.long_module_name, int(g.group(1),16), self.modmapstart) )
            return

        g = RE_MP_ENTRY.search(l)
        if self.modmapstart and self.module and g:
            self.module.labels.append( (g.group(1),int(g.group(2),16), self.modmapstart) )
            return

    def parseCALLGRAPH(self, l):
        pass

    def parseSEGMENTS(self, l):
        g = RE_SEGMENT.search(l)
        if g:
            seg_name = g.group(1)
            seg_start = int(g.group(2),16)
            if g.group(4):
                seg_end = int(g.group(4),16)
                seg_size = int(g.group(5),16)
            else:
                seg_end = seg_start
                seg_size = 0
            if verbosity:
                print "segment %s from address 0x%04x to 0x%04x size: %d" % (seg_name, seg_start, seg_end, seg_size)


    def __contains__(self, item):
        """check if item is available"""
        for m in self.modules:
            if item in m:
                return True
        return False

    def __getitem__(self, item):
        """get an address or label, raise exception if not found"""
        for m in self.modules:
            k = m[item]
            if k != None:
                return k
        raise IndexError("not found")

    def get(self, item):
        """get an address or label, return None if nothing found"""
        try:
            return self[item]
        except IndexError:
            return None

    def labels(self):
        """get a sorted list of labels of all modules"""
        alllabels = []
        for m in self.modules:
            alllabels.extend(m.getLabels())
        alllabels.sort()
        return alllabels

    def items(self):
        """get a list of pairs (labels, address) of all modules"""
        alllabels = []
        for m in self.modules:
            alllabels.extend([(label, m[label]) for label in m.getLabels()])
        alllabels.sort()
        return alllabels


def label_address_map(filename):
    """\
    Scan the listing and return a dict with variables as keys, address of
    them as values.
    """
    return MemMap(filename)


# module test code
if __name__ == '__main__':
    import pprint
    try:
        programFlash = sys.argv[1]
        memorymap = MemMap(sys.argv[1])
    except Exception, e:
        print "error while reading arguments: %s" % e
        raise SystemExit(1)
    pprint.pprint(symbols)


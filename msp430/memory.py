# $Id: memory.py,v 1.2 2004/03/05 00:32:50 cliechti Exp $
import sys

DEBUG = 0

class Segment:
    """store a string with memory contents along with its startaddress"""
    def __init__(self, startaddress = 0, data=None):
        if data is None:
            self.data = ''
        else:
            self.data = data
        self.startaddress = startaddress

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return "Segment(startaddress = 0x%04x, data=%r)" % (self.startaddress, self.data)

class Memory:
    """represent memory contents. with functions to load files"""
    def __init__(self, filename=None):
        self.segments = []
        if filename:
            self.filename = filename
            self.loadFile(filename)

    def append(self, seg):
        self.segments.append(seg)

    def __getitem__(self, index):
        return self.segments[index]

    def __len__(self):
        return len(self.segments)

    def loadIHex(self, file):
        """load data from a (opened) file in Intel-HEX format"""
        segmentdata = []
        currentAddr = 0
        startAddr   = 0
        lines = file.readlines()
        for l in lines:
            if not l.strip(): continue  #skip empty lines
            if l[0] != ':': raise Exception("File Format Error\n")
            l = l.strip()               #fix CR-LF issues...
            length  = int(l[1:3],16)
            address = int(l[3:7],16)
            type    = int(l[7:9],16)
            check   = int(l[-2:],16)
            if type == 0x00:
                if currentAddr != address:
                    if segmentdata:
                        self.segments.append( Segment(startAddr, ''.join(segmentdata)) )
                    startAddr = currentAddr = address
                    segmentdata = []
                for i in range(length):
                    segmentdata.append( chr(int(l[9+2*i:11+2*i],16)) )
                currentAddr = length + currentAddr
            elif type in (0x01, 0x02, 0x03, 0x04, 0x05):
                pass
            else:
                sys.stderr.write("Ignored unknown field (type 0x%02x) in ihex file.\n" % type)
        if segmentdata:
            self.segments.append( Segment(startAddr, ''.join(segmentdata)) )

    def loadTIText(self, file):
        """load data from a (opened) file in TI-Text format"""
        next        = 1
        startAddr   = 0
        segmentdata = []
        #Convert data for MSP430, TXT-File is parsed line by line
        while next >= 1:
            #Read one line
            l = file.readline()
            if not l: break #EOF
            l = l.strip()
            if l[0] == 'q': break
            elif l[0] == '@':        #if @ => new address => send frame and set new addr.
                #create a new segment
                if segmentdata:
                    self.segments.append( Segment(startAddr, ''.join(segmentdata)) )
                startAddr = int(l[1:],16)
                segmentdata = []
            else:
                for i in l.split():
                    segmentdata.append(chr(int(i,16)))
        if segmentdata:
            self.segments.append( Segment(startAddr, ''.join(segmentdata)) )

    def loadELF(self, file):
        """load data from a (opened) file in ELF object format.
        File must be seekable"""
        import elf
        obj = elf.ELFObject()
        obj.fromFile(file)
        if obj.e_type != elf.ELFObject.ET_EXEC:
            raise Exception("No executable")
        for section in obj.getSections():
            if DEBUG:
                sys.stderr.write("ELF section %s at 0x%04x %d bytes\n" % (section.name, section.lma, len(section.data)))
            if len(section.data):
                self.segments.append( Segment(section.lma, section.data) )
        
    def loadFile(self, filename):
        """fill memory with the contents of a file. file type is determined from extension"""
        #TODO: do a contents based detection
        if filename[-4:].lower() == '.txt':
            self.loadTIText(open(filename, "rb"))
        elif filename[-4:].lower() in ('.a43', '.hex'):
            self.loadIHex(open(filename, "rb"))
        else:
            self.loadELF(open(filename, "rb"))

    def getMemrange(self, fromadr, toadr):
        """get a range of bytes from the memory. unavailable values are filled with 0xff."""
        res = ''
        toadr = toadr + 1   #python indxes are excluding end, so include it
        while fromadr < toadr:
            for seg in self.segments:
                segend = seg.startaddress + len(seg.data)
                if seg.startaddress <= fromadr and fromadr < segend:
                    if toadr > segend:   #not all data in segment
                        catchlength = segend-fromadr
                    else:
                        catchlength = toadr-fromadr
                    res = res + seg.data[fromadr-seg.startaddress : fromadr-seg.startaddress+catchlength]
                    fromadr = fromadr + catchlength    #adjust start
                    if len(res) >= toadr-fromadr:
                        break   #return res
            else:   #undefined memory is filled with 0xff
                    res = res + chr(255)
                    fromadr = fromadr + 1 #adjust start
        return res

"""
Using the MSP430 JTAG interface box for something else: a MMC card reader

                                        +---+                   
+---------+                          NC |O O| NC    top view    
|         |       Adapter Cable      NC |O O| RST               
| M M C   |       MMC -> JTAG       XIN |O O| GND ---------\    
| Card    |                        TEST |O O| TCK -------\ |    
|back side|                        TCLK |O O| TMS -----\ | |    
|         |                        sens |O O| TDI ---\ | | |    
| 7654321 /                      /- VCC |O 1| TDO -\ | | | |    
+--------/    MMC   JTAG         |      +---+      | | | | |    
  ||||||\---> CD    TMS  >-------+-----------------+-+-/ | |    
  |||||\----> DI    TDI  >-------+-----------------+-/   | |    
  ||||\-----> GND        >--\    |                 |     | |    
  |||\------> VCC        >--+----/                 |     | |    
  ||\-------> CLK   TCK  >--+----------------------+-----/ |    
  |\--------> GND        >--O----------------------+-------/    
  \---------> DO    TDO  >-------------------------/            

chris <cliechti@gmx.net>

"""

import hilspi
from HIL import DelayMSec as Wait1ms
from HIL import TMS

try:
    import psyco
    psyco.full()
    print "using psyco to speed it up"
except ImportError:
    pass


# Alternative Names for MMC Commands
# Class 0 - Basic Commands
MMC_GO_IDLE_STATE             =  0
MMC_SEND_OP_COND              =  1
MMC_SEND_CSD                  =  9
MMC_SEND_CID                  = 10
MMC_SEND_STATUS               = 13
# Class 2 - Block Read          
MMC_SET_BLOCKLEN              = 16
MMC_READ_SINGLE_BLOCK         = 17
# Class 4 - Block Write         
MMC_WRITE_BLOCK               = 24
MMC_PROGRAM_CSD               = 27
# Class 6 - Write Protection    
MMC_SET_WRITE_PROT            = 28
MMC_CLR_WRITE_PROT            = 29
MMC_SEND_WRITE_PROT           = 30
# Class 5 - Erase
MMC_TAG_SECTOR_START          = 32
MMC_TAG_SECTOR_END            = 33
MMC_UNTAG_SECTOR              = 34
MMC_TAG_EREASE_GROUP_START    = 35
MMC_TAG_EREASE_GROUP_END      = 36
MMC_UNTAG_EREASE_GROUP        = 37
MMC_EREASE                    = 38
# Class 7 - Lock Card
MMC_LOCK_UNLOCK               = 42
# Extended commands
MMC_READ_OCR                  = 58
MMC_CRC_ON_OFF                = 59


class MMCError(Exception): pass
MMCError_no_answer = MMCError("no answer to command")

def MMC_CS(state):
    TMS(not state)

def SpiByte(byte):
    return ord(hilspi.shift(chr(byte)))

class MMC:
    def get(self):
        """read a command answer, returns the answer byte"""
        byte = 0xFF
        for i in range(10000):
            byte = SpiByte(0xFF)
            if byte != 0xff: break
        else:
            raise MMCError_no_answer
        return byte
    
    def dataToken(self):
        """read until the data start token is received"""
        byte = 0xFF
        for i in range(5000):
            byte = SpiByte(0xff)
            if byte == 0xfe: break
        else:
            raise MMCError_no_answer
        return byte
    
    
    def command(self, command, params):
        """send a command to the card.
        command is the eight bit command id.
        params is a long integer (64 bits) with the command argument"""
        SpiByte(0xFF)
        SpiByte(command|0x40)               # Command
        SpiByte((0xFF000000L & params)>>24)    # msb
        SpiByte((0x00FF0000L & params)>>16)
        SpiByte((0x0000FF00L & params)>>8 )
        SpiByte( 0x000000FFL & params     )    # lsb
        SpiByte(0x95)                       # CRC
        SpiByte(0xFF)
    
    def getResponse(self):
        """read a response of a command"""
        response = 0xFF
        for i in range(64):
            response = SpiByte(0xFF)
            #~ print "MMCGetResponse", response
            if response == 0x00:
                break
            if response == 0x01:
                break
        return response
    
    def getXResponse(self, resp):
        """wait until the specified response is read. used for some commands"""
        response = 0xFF
        for i in range(500):
            response=SpiByte(0xFF)
            if response==resp:
                break
        return response
    
    def init(self):
        """initilize card in SPI mode"""
        #~ print "MMCInit"
        response = 0x01
        MMC_CS(False)
        Wait1ms(500)                       # warten 500ms
        for i in range(10):                # 80 Taktzyklen auf SPI
            SpiByte(0xFF)
        MMC_CS(True)
        self.command(MMC_GO_IDLE_STATE, 0x00000000)
        if self.getResponse() != 0x01:       # check answer
            MMC_CS(False)
            #~ print "MMCInit failed"
            return False                   # Fehler
        while response == 0x01:            # check answer
            MMC_CS(False)
            SpiByte(0xFF)
            MMC_CS(True)
            self.command(MMC_SEND_OP_COND, 0x00000000)
            response = self.getResponse()
        SpiByte(0xFF)
        #~ print "MMCInit done"
        return True                        # MMC wurde erfolgreich initialisiert
    
    def info(self):
        """get a dictionary with some card info in it"""
        info = {}
        self.command(MMC_SEND_CID, 0x00000000)
        if (self.dataToken() != 0xFE):
            raise MMCError("error during CID read")
        hilspi.shift("\xff"*3)
        info["Product Name:"] = hilspi.shift("\xff"*6)
        hilspi.shift("\xff"*7)
        return info
    
    def read(self, sector):
        """read a sector (512 bytes) from the card. argument is the sector number (512 bytes)
           returns a string with the binary data"""
        self.command(MMC_READ_SINGLE_BLOCK, sector*512)
        if self.dataToken() != 0xFE:          # check answer
            raise MMCError_no_answer        # Fehler
        data = hilspi.shift("\xff"*512)
        hilspi.shift("\xff"*2)              # Dummy-CRC
        return data
    
    
    def write(self, sector, data):
        """write the given data in the specified sector"""
        if len(data) != 512:
            raise ValueError("Can only handle blocks of 512 bytes size")
        self.command(MMC_WRITE_BLOCK, sector*512)
        if self.get() == 0xFF:
            raise MMCError_no_answer
        SpiByte(0xFE)                       # Start-Byte
        data = hilspi.shift(data)
        hilspi.shift("\xff"*2)              # Dummy-CRC
        SpiByte(0xFF);                      # lese Antwort-Byte
        for i in range(50000):
            if SpiByte(0xFF) != 0x00:
                break
        else:
            raise MMCError("error while writing data")
    
    
    def connect(self):
        hilspi.init()
        for tries in range(3):
            Wait1ms(200)           # 500ms warten
            if self.init(): break
        else:
            raise MMCError("Can't connect to MMC card")
        Wait1ms(500)               # 500ms warten
    
    def release(self):
        hilspi.close()

if __name__ == '__main__':
    from msp430.util import hexdump
    import time
    mmc = MMC()
    try:
        mmc.connect()
        print mmc.info()
        #show what's there
        hexdump((0, mmc.read(0)))
        #speed test
        t1 = time.time()
        for n in range(10):
            mmc.read(n)
        t2 = time.time()
        dt = t2 - t1
        bytes = n * 512
        print "%d bytes in %.2f seconds -> %.2f bytes/second" % (bytes, dt, bytes/dt)
    finally:
        mmc.release()

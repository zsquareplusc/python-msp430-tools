#!/usr/bin/env python
# $Id: msp430-downloader.py,v 1.12 2007/03/13 11:34:00 cliechti Exp $
"""
Simple tool to download to a MSP430.

This one uses some dialog boxes, which makes it suitable for linking
file extensions to this program, so that a double click in the 
windoze exploder downloads the file.

Now also with the ability to load the configuration from an ini file (.m43)
which itself can be bundled with a binary in a zip file (.z43).

(C) 2004-2007 Chris Liechti <cliechti@gmx.net>
              with inputs from David Brown
"""

import os, sys
import EasyDialogs
import msp430.jtag, msp430.memory
from StringIO import StringIO
import traceback
import ConfigParser
from msp430.jtag import jtag

name = 'msp430-downloader' #os.path.basename(os.path.splitext(sys.argv[0])[0])

# - - - - - - - - - - - - - - - default options - - - - - - - - - - - - - - -
class Options: pass
options = Options()
options.lpt = 'ask'
options.filename = None
options.erase_mode = 'ask'
options.loop = False
options.ask_start = False
options.fake_progress = False
options.debug = False
options.viewer = 'internal'
options.readme = None
options.backend = None
binary = None

# - - - - - - - - - - - - - - - helper dialogboxes - - - - - - - - - - - - - -
def abort_on_error(message):
    print "abort_on_error: %r" % message
    EasyDialogs.Message("%s: %s" % (name, message))
    sys.exit(2)

def abort_on_user_request():
    print "abort_on_user_request"
    sys.exit(0)

# - - - - - - - - - - - - config file interpretation - - - - - - - - - - - - -
def ask_for_binary(allow_manifests=True):
    """show a file open dialog and return a filename"""
    type_list = [
        ('Binraries (*.hex, *.elf, *.a43)', '*.hex;*.elf;*.a43'),
        ('ELF executable (*.elf)', '*.elf'),
        ('Intel-hex (*.a43, *.hex)', '*.a43;*.hex'),
        ('TI-Text (*.txt)', '*.txt'),
        ('All files (*.*)', '*.*'),
    ]
    if allow_manifests:
        type_list.insert(-1, ('Downloader control files (*.m43, *.z43)', '*.m43;*.z43'),)
    return EasyDialogs.AskFileForOpen(
        windowTitle = "Select MSP430 binary for download",
        typeList = type_list
    )


def interpret_config(config, abspath=True):
    """interpret the options in an ini file (ConfigParser object)"""
    if config.has_option('modes', 'erase_mode'):
        options.erase_mode = config.get('modes', 'erase_mode')
    
    if config.has_option('modes', 'interface'):
        options.lpt = config.get('modes', 'interface')
    
    if config.has_option('modes', 'loop'):
        options.loop = config.getboolean('modes', 'loop')
    
    if config.has_option('modes', 'debug'):
        options.debug = config.getboolean('modes', 'debug')
    
    if config.has_option('modes', 'backend'):
        back_name = config.get('modes', 'backend')
        if back_name == 'ti':
            options.backend = jtag.CTYPES_TI
        elif back_name == 'parjtag':
            options.backend = jtag.PARJTAG
        elif back_name == 'mspgcc':
            options.backend = jtag.CTYPES_MSPGCC
        else:
            abort_on_error('Unsupported backend in configuation file: %r' % back_name)
    
    if config.has_option('data', 'filename'):
        options.filename = config.get('data', 'filename')
        #patch relative paths to be relative to the config file
        if abspath and not os.path.isabs(options.filename):
            options.filename = os.path.join(os.path.dirname(config_filename), options.filename)
    
    if config.has_option('data', 'readme'):
        options.readme = config.get('data', 'readme')
        #patch relative paths to be relative to the config file
        if abspath and not os.path.isabs(options.readme):
            options.readme = os.path.abspath(os.path.join(os.path.dirname(config_filename), options.readme))
        if config.has_option('data', 'viewer'):
            options.viewer = config.get('data', 'viewer')

# - - - - - - - - - - - - - load binary or config - - - - - - - - - - - - - - -
# if parameter is given use this filename, open a requester otherwise
if len(sys.argv) < 2:
    options.filename = ask_for_binary()
    if options.filename is None:
        abort_on_user_request()
else:
    options.filename = sys.argv[1]

# - - - - - - - - - - - detect and handle config files  - - - - - - - - - - - -
# interpret manifest files here
if options.filename.endswith('.m43'):
    # this is a simple ini file with settings
    config_filename = options.filename
    options.filename = None
    config = ConfigParser.RawConfigParser()
    config.read(config_filename)
    interpret_config(config)
    if options.readme:
        if options.viewer == 'browser':
            import webbrowser
            webbrowser.open(options.readme)
        else:
            EasyDialogs.Message(open(options.readme).read())
elif options.filename.endswith('.z43'):
    # a zip file containing the manifest file and the binary and a readme
    config_filename = options.filename
    options.filename = None
    import zipfile
    archive = zipfile.ZipFile(config_filename)
    #in a loop, search for the manifest file
    for info in archive.infolist():
        if info.filename.endswith('.m43'):
            config_filename = options.filename
            config = ConfigParser.RawConfigParser()
            config.readfp(StringIO(archive.read(info.filename)))
            interpret_config(config, abspath=False)
    #get binary from zip file
    if options.filename:
        binary = msp430.memory.Memory()   #prepare downloaded data
        binary.loadFile(options.filename, fileobj = StringIO(archive.read(options.filename)))
    #get readme from zip file and display it
    if options.readme:
        readme_text = archive.read(options.readme)
        if options.viewer == 'browser':
            import webbrowser
            import tempfile
            import atexit
            tmp_name = tempfile.mktemp(options.readme)
            tmp = open(tmp_name, 'wb')
            tmp.write(readme_text)
            tmp.close()
            #ensure that the readme is deleted at the end
            def cleanup(filename=tmp_name):
                os.remove(tmp_name)
            atexit.register(cleanup)
            webbrowser.open(tmp_name)
        else:
            EasyDialogs.Message(readme_text)


# checks
if binary is None:
    if options.filename is None:
        options.filename = ask_for_binary()
        if options.filename is None:
            abort_on_user_request()
    if not os.path.isabs(options.filename):
        options.filename = os.path.abspath(options.filename)
    if os.path.isfile(options.filename):
        binary = msp430.memory.load(options.filename) # format=options.input_format)
    else:
        abort_on_error("File not found:\n%s" % (options.filename,))

if options.loop:
    # if in loop mode, ensure that there is a "ready to go" question in the loop
    options.ask_start = True

# init
jtag.init_backend(options.backend)
if jtag.backend == jtag.CTYPES_TI:
    options.fake_progress = True

# - - - - - - - - - - - - - - optional questions - - - - - - - - - - - - - - -
if options.lpt == 'ask':
    #swap the buttons, so that cancel is the sparate button at left
    answer = EasyDialogs.AskYesNoCancel(
        "MSP430 downloader\n\nDownload '%s'?\n\n" % (options.filename,),
        default=0, cancel="USB", yes="Parallel port", no="Cancel"
    )
    if answer == 0: #NO -> abort
        abort_on_user_request()
    elif answer == 1: #YES -> parallel
        options.lpt = "1"
    else:   #CANCEL -> USB
        options.lpt = "TIUSB"

# check for aliases for the interface
if options.lpt == 'parallel':
    options.lpt = '1'

# choose erase mode
if options.erase_mode == 'ask':
    answer = EasyDialogs.AskYesNoCancel("Choose erase mode",
        default=0, yes="ALL", cancel="Main only", no="Cancel")
    if answer == 0:     #NO
        abort_on_user_request()
    elif answer == 1:   #YES
        options.erase_mode = 'mass'
    else:               #CANCEL
        options.erase_mode = 'main'

# - - - - - - - - - - - - - - - - logging - - - - - - - - - - - - - - - - - -
if options.debug:
    print '\n'.join(["%s: %r" % kv for kv in options.__dict__.items()])

# - - - - - - - - - - - - - main programming loop - - - - - - - - - - - - - -
# capture console output
sys.stdout = sys.stderr = StringIO()

class ProgressJTAG(jtag.JTAG):
    def progess_update(self, count, total):
        self.bar.set(100*count/total)

while True:
    if options.ask_start:
        answer = EasyDialogs.AskYesNoCancel(
            """\
            Ready to program...
            
            1. Connect the programmer.
            2. Power on target
            3. Press 'Start'
            """
            ,
            default=0, cancel='Start', yes='', no='Cancel'
        )
        if answer == 0:     #NO -> abort
            print "User aborted"
            break
        elif answer == 1:   #YES -> ??
            sys.exit(1)
        else:               #CANCEL -> start
            pass
    
    try:
        jtagobj = ProgressJTAG()
        if not options.fake_progress:
            jtagobj.showprogess = True
        jtagobj.bar = EasyDialogs.ProgressBar('Programming %r' % options.filename[-50:], 100)
        showError = False
        try:
            connected = False
            jtagobj.data = binary
            jtagobj.bar.label('Connecting...')
            jtagobj.open(options.lpt)               #try to open port
            try:
                jtagobj.connect()                   #try to connect to target
                connected = True
                if options.fake_progress: jtagobj.bar.set(10)
                
                jtagobj.bar.label('Erasing...')
                if options.erase_mode == 'mass' or options.erase_mode == 'all':
                    jtagobj.actionMassErase()
                elif options.erase_mode == 'main':
                    jtagobj.actionMainErase()
                if options.fake_progress: jtagobj.bar.set(20)
                
                showError = True
                jtagobj.bar.label('Programming...')
                jtagobj.actionProgram()
                if options.fake_progress: jtagobj.bar.set(60)
                
                jtagobj.bar.label('Verifying...')
                jtagobj.actionVerify()
                if options.fake_progress: jtagobj.bar.set(100)
            finally:
                if sys.exc_info()[:1]:              #if there is an exception pending
                    jtagobj.verbose = 0             #do not write any more messages
                if connected:
                    jtagobj.bar.label('Reset...')
                    jtagobj.reset(1, 1)             #reset and release target
                jtagobj.close()                     #Release communication port
        finally:
            del jtagobj.bar                         #close progress bar
    except IOError, e:
        if showError:
            EasyDialogs.Message('An error occoured: "%s"\n\nMessages:\n%s' % (e, sys.stdout.getvalue()))
        else:
            EasyDialogs.Message("%s: Can't connect to target" % name)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception, e:
        if options.debug:
            messages = sys.stdout.getvalue()
            sys.__stdout__.write(messages)
            traceback.print_exc(file=sys.__stdout__)
        EasyDialogs.Message('An error occoured: %s\nMessages:\n%s' % (e, sys.stdout.getvalue()))
    else:
        messages = sys.stdout.getvalue()
        if options.debug: sys.__stdout__.write(messages)
        EasyDialogs.Message('Messages:\n%s\nSuccess!' % (messages,))
    if not options.loop: break

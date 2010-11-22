"""\
Helper functions to read and write binary files.
"""

import msp430.memory

def load(filelike):
    """load data from a (opened) file in binary format"""
    memory = msp430.memory.Memory()
    memory.append(msp430.memory.Segment(0, filelike.read()))
    return memory

def save(memory, filelike):
    """output binary to given file object"""
    for segment in sorted(memory.segments):
        # XXX would it be better to fill the gaps between segments?
        filelike.write(segment.data)

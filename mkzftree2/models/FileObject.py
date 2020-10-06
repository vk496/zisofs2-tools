import pathlib
import math
from pathlib import Path
from mkzftree2.iso9660 import *


class commonZisofs:
    blocksize = None # Block size

    def get_blocksize(self):
        # ZISOFS.blocksize = int_to_iso711(int(math.log(blocksize, 2)))
        return 2 ** iso711_to_int(self.blocksize)

class ZISOFS(commonZisofs):
    ## HEADER
    hdr_magic = b'\x37\xE4\x53\x96\xC9\xDB\xD6\x07'  # Magick Header
    ufs_l = None  # Uncompressed size
    hdr_size = int_to_iso711(4) # Header size

    ## Array
    pointers_size = 4

    def __init__(self, size, blocksize):
        self.ufs_l = int_to_iso731(size) # The conversion check the maximum size and raise exception if is exceded
        self.blocksize = int_to_iso711(int(math.log(blocksize, 2)))

    def __bytes__(self):
        header = bytearray()
        header.extend(self.hdr_magic) # 8
        header.extend(self.ufs_l) # 4
        header.extend(self.hdr_size) # 1
        header.extend(self.blocksize) # 1
        header.extend(bytearray(2)) # 2

        return bytes(header)


class ZISOFSv2(commonZisofs):

    ## Header
    hdr_magic = b'\xEF\x22\x55\xA1\xBC\x1B\x95\xA0'  # Magick Header
    hdr_version = int_to_iso711(0)
    hdr_size = int_to_iso711(5) # 24 bytes size
    alg_id = None
    size = None

    # Array
    pointers_size = 8

    def __init__(self, size, blocksize, algorithm):

        self.size = int_to_uint64(size)
        self.blocksize = int_to_iso711(int(math.log(blocksize, 2)))

        if algorithm == 'zlib':
            alg_id = 1
        elif algorithm == 'xz':
            alg_id = 2
        elif algorithm == 'lz4':
            alg_id = 3
        elif algorithm == 'zstd':
            alg_id = 4
        elif algorithm == 'bzip2':
            alg_id = 5
        else:
            raise ValueError(f"Illegal algorithm {algorithm}")
        self.alg_id =  int_to_iso711(alg_id)


    def __bytes__(self):
        header = bytearray()
        header.extend(self.hdr_magic) # 8
        header.extend(self.hdr_version) # 1
        header.extend(self.hdr_size) # 1
        header.extend(self.alg_id) # 1
        header.extend(self.blocksize) # 1
        header.extend(self.size) # 8
        header.extend(bytearray(4)) # 4

        return bytes(header)


class FileObject:
    target_dir = None
    source_dir = None

    # Instance functions
    def __init__(self, source_file, target_file, alg, blocksize, isLegacy):
        self.source_file = source_file
        self.target_file = target_file

        if isLegacy:
            self.header = ZISOFS(self.getInputSize(), blocksize)
        else:
            self.header = ZISOFSv2(self.getInputSize(), blocksize, alg)


    def getFileSource(self):
        return self.source_file

    def getFileTarget(self):
        return self.target_file

    def getInputSize(self):
        return self.source_file.stat().st_size

    def generate_header(self):
        return bytes(self.header)

    def getTablePointers(self, list_pointers=None):
        """
        Return a byte array of the table pointers.
        If no list of pointers are given, return a blank array
        """
        nblocks = int(math.ceil((self.getInputSize() / self.header.get_blocksize())) + 1)

        if list_pointers:
            if len(list_pointers) != nblocks:
                raise ValueError(f"Number of precalculated pointers doesn't correspond to final pointers table")

            data = bytearray()
            if type(self.header) is ZISOFS:
                [data.extend(int_to_iso731(addr)) for addr in list_pointers]
            else:
                [data.extend(uint64_to_two_iso731(addr, one=True)) for addr in list_pointers]
                
            if len(data) != nblocks * self.header.pointers_size:
                raise ValueError(f"Number of precalculated pointers doesn't correspond to final pointers table")

            return bytes(data)
        else:
            return bytes(nblocks * self.header.pointers_size)

    def create_parentDir(self):
        if not self.target_file.parent.exists():
            self.target_file.parent.mkdir(parents=True)

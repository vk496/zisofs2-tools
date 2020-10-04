import pathlib
import math
from pathlib import Path
from mkzftree2.iso9660 import *


class ZISOFS:
    ## HEADER
    hdr_magic = b'\x37\xE4\x53\x96\xC9\xDB\xD6\x07'  # Magick Header
    ufs_l = None  # Uncompressed size
    hdr_size = int_to_iso711(4) # Header size
    hdr_bsize = None # Block size

    ## Array
    pointers_size = 4

    @staticmethod
    def set_blocksize(blocksize):
        ZISOFS.hdr_bsize = int_to_iso711(int(math.log(blocksize, 2)))

    @staticmethod
    def get_blocksize():
        # ZISOFS.hdr_bsize = int_to_iso711(int(math.log(blocksize, 2)))
        return 2 ** iso711_to_int(ZISOFS.hdr_bsize)


    def __init__(self, size):
        self.ufs_l = int_to_iso731(size) # The conversion check the maximum size and raise exception if is exceded

    def __bytes__(self):
        header = bytearray()
        header.extend(self.hdr_magic) # 8
        header.extend(self.ufs_l) # 4
        header.extend(self.hdr_size) # 1
        header.extend(self.hdr_bsize) # 1
        header.extend(bytearray(2)) # 2

        return bytes(header)


class ZISOFSv2(ZISOFS):

    ## Header
    hdr_size = int_to_iso711(8) # 32 bytes size
    ufs_h = None  # Uncompressed size high
    alg_id = None
    alg_strat = int_to_iso711(0)

    # Array
    pointers_size = 8

    def __init__(self, size):
        low, high = uint64_to_two_iso731(size)

        super().__init__(iso731_to_int(low))
        self.ufs_h = high

    @staticmethod
    def set_compressor(algorithm):
        if algorithm == 'zlib':
            alg_id = 0
        elif algorithm == 'xz':
            alg_id = 1
        elif algorithm == 'lz4':
            alg_id = 2
        elif algorithm == 'zstd':
            alg_id = 3
        elif algorithm == 'bzip2':
            alg_id = 4
        else:
            raise ValueError(f"Illegal algorithm {algorithm}")

        ZISOFSv2.alg_id = int_to_iso711(alg_id)


    def __bytes__(self):
        header = bytearray(super().__bytes__())
        header.extend(self.alg_id) # 1
        header.extend(self.alg_strat) # 1
        header.extend(self.ufs_h) # 4
        header.extend(bytearray(10)) # 10

        return bytes(header)


class PointerArray:
    array = []
    total_num = 0

    @staticmethod
    def add_pointer(value):
        PointerArray.array.append(value)


class FileObject:
    size_limit = 2**25  # Files bigger than this, must be processed in multithread if possible
    file_list = []  # Global list of file
    target_dir = None
    source_dir = None
    header_size = 32

    # Class functions

    @staticmethod
    def get_smallfiles():
        ret = []
        for f in FileObject.file_list:
            if f.isSmall():
                ret.append(f)
        return ret

    @staticmethod
    def compressFiles():
        pass

    # Instance functions

    def __init__(self, file, isLegacy):
        self.source_file = file
        self.target_file = FileObject.target_dir / \
            file.relative_to(FileObject.source_dir)

        if isLegacy:
            self.header = ZISOFS(self.getInputSize())
        else:
            self.header = ZISOFSv2(self.getInputSize())

        FileObject.file_list.append(self)

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

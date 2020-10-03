import pathlib, math
from pathlib import Path
from mkzftree2.iso9660 import *


class ZISOFSv2:
    hdr_magic = b'\x37\xE4\x53\x96\xC9\xDB\xD6\x07'
    hdr_size= int_to_iso711(8)
    hdr_bsize= None
    alg_id= None

    @staticmethod
    def set_blocksize(blocksize):
        ZISOFSv2.hdr_bsize=int_to_iso711(int(math.log(blocksize, 2)))
    
    @staticmethod
    def set_compressor(algorithm):
        if algorithm == 'zlib':
            dt = 0
        elif algorithm == 'xz':
            dt = 1
        elif algorithm == 'lz4':
            dt = 2
        elif algorithm == 'zstd':
            dt = 3
        elif algorithm == 'bzip2':
            dt = 4
        else:
            raise ValueError(f"Illegal algorithm {algorithm}")

        ZISOFSv2.alg_id = int_to_iso711(dt)

    @staticmethod
    def generate_header(file_size, algorithm_strategy=0):
        alg_strat= int_to_iso711(algorithm_strategy) # For now, always 0


        ufs_l, ufs_h = uint64_to_two_iso731(file_size)
        header = bytearray()
        header.extend(ZISOFSv2.hdr_magic)
        header.extend(ufs_l)
        header.extend(ZISOFSv2.hdr_size)
        header.extend(ZISOFSv2.hdr_bsize)
        header.extend(ZISOFSv2.alg_id)
        header.extend(alg_strat)
        header.extend(ufs_h)
        header.extend(bytearray(12))
        return bytes(header)
        
class PointerArray:
    array = []
    total_num=0

    @staticmethod
    def add_pointer(value):
        PointerArray.array.append(value)


class FileObject:
    size_limit=2**25 # Files bigger than this, must be processed in multithread if possible
    file_list = [] # Global list of file
    target_dir = None
    source_dir = None
    header_size = 32


    ## Class functions
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


    ## Instance functions
    def __init__(self, file):
        self.source_file = file
        self.target_file = FileObject.target_dir / file.relative_to(FileObject.source_dir)

        FileObject.file_list.append(self)

    def generate_header(self):
        pass

    def create_parentDir(self):
        if not self.target_file.parent.exists():
            self.target_file.parent.mkdir(parents=True)

    def isLess4GB(self):
        return self.source_file.stat().st_size < 2**32
        
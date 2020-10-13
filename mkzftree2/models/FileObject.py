from enum import Enum
import os
from pathlib import Path
import math
from mkzftree2.models.algorithm import Algorithm
from mkzftree2.iso9660 import int_to_iso711, int_to_iso731, iso711_to_int, int_to_uint64, iso731_to_int, uint64_to_int
from mkzftree2.arguments import default_block_sizes
from mkzftree2.utils import IllegalZisofsFormat, NotCompressedFile


class commonZisofs:
    blocksize = None  # Block size
    hdr_size = None
    header = None

    @classmethod
    def get_pointer_value(cls, data):
        if issubclass(cls, ZISOFSv2):
            return uint64_to_int(data)
        elif issubclass(cls, ZISOFS):
            return iso731_to_int(data)
        else:
            raise ValueError

    @classmethod
    def get_header_size(cls):
        """
        docstring
        """
        return 4*iso711_to_int(cls.hdr_size)

    def get_blocksize(self):
        # ZISOFS.blocksize = int_to_iso711(int(math.log(blocksize, 2)))
        return 2 ** iso711_to_int(self.blocksize)

    def __len__(self):
        return 4*iso711_to_int(self.hdr_size)


class ZISOFS(commonZisofs):
    # HEADER
    hdr_magic = b'\x37\xE4\x53\x96\xC9\xDB\xD6\x07'  # Magick Header
    size = None  # Uncompressed size
    hdr_size = int_to_iso711(4)  # Header size

    # Array
    pointers_size = 4

    @staticmethod
    def from_header(header):
        """
        docstring
        """

        header = header[0:ZISOFS.get_header_size()]

        # Make sure is bytes
        if not isinstance(header, (bytes, bytearray)):
            raise ValueError
        # Header magic
        if header[0:8] != ZISOFS.hdr_magic:
            raise NotCompressedFile

        # Correct size
        if len(header) != 4*iso711_to_int(ZISOFS.hdr_size):
            raise IllegalZisofsFormat

        # Header size
        if header[12:13] != ZISOFS.hdr_size:
            raise IllegalZisofsFormat

        zisofs_obj = ZISOFS()

        # File size
        zisofs_obj.size = header[8:12]

        # Blocksize
        if iso711_to_int(header[13:14]) not in default_block_sizes:
            raise IllegalZisofsFormat
        zisofs_obj.blocksize = header[13:14]

        return zisofs_obj

    def set_size(self, size):
        """
        docstring
        """
        self.size = int_to_iso731(size)

    def get_size(self):
        """
        docstring
        """
        return iso731_to_int(self.size)

    def set_blocksize(self, blocksize):
        """
        docstring
        """
        self.blocksize = int_to_iso711(int(math.log(blocksize, 2)))

    def get_algorithm(self):
        """
        docstring
        """
        return Algorithm(1)  # Force return ZLIB compressor

    def __bytes__(self):
        header = bytearray()
        header.extend(self.hdr_magic)  # 8
        header.extend(self.size)  # 4
        header.extend(self.hdr_size)  # 1
        header.extend(self.blocksize)  # 1
        header.extend(bytearray(2))  # 2

        return bytes(header)


class ZISOFSv2(commonZisofs):

    # Header
    hdr_magic = b'\xEF\x22\x55\xA1\xBC\x1B\x95\xA0'  # Magick Header
    hdr_version = int_to_iso711(0)
    hdr_size = int_to_iso711(6)  # 24 bytes size
    alg_id = None
    size = None

    # Array
    pointers_size = 8

    @staticmethod
    def from_header(header):
        """
        docstring
        """

        header = header[0:ZISOFSv2.get_header_size()]
        # Make sure is bytes
        if not isinstance(header, (bytes, bytearray)):
            raise ValueError
        # Header magic
        if header[0:8] != ZISOFSv2.hdr_magic:
            raise NotCompressedFile

        # Correct size
        if len(header) != 4*iso711_to_int(ZISOFSv2.hdr_size):
            raise IllegalZisofsFormat

        # Header size
        if header[9:10] != ZISOFSv2.hdr_size:
            raise IllegalZisofsFormat

        zisofs_obj = ZISOFSv2()

        # Algorithm
        if iso711_to_int(header[10:11]) == 0:
            raise IllegalZisofsFormat
        zisofs_obj.alg_id = header[10:11]

        # Blocksize
        if iso711_to_int(header[11:12]) not in default_block_sizes:
            raise IllegalZisofsFormat
        zisofs_obj.blocksize = header[11:12]

        # File size
        zisofs_obj.size = header[12:20]

        return zisofs_obj

    def set_size(self, size):
        """
        docstring
        """
        self.size = int_to_uint64(size)

    def get_size(self):
        """
        docstring
        """
        return uint64_to_int(self.size)

    def set_blocksize(self, blocksize):
        """
        docstring
        """
        self.blocksize = int_to_iso711(int(math.log(blocksize, 2)))

    def set_alg(self, algorithm):
        """
        docstring
        """
        self.alg_id = int_to_iso711(algorithm.value)

    def get_algorithm(self):
        """
        docstring
        """
        return Algorithm(iso711_to_int(self.alg_id))

    def __bytes__(self):
        header = bytearray()
        header.extend(self.hdr_magic)  # 8
        header.extend(self.hdr_version)  # 1
        header.extend(self.hdr_size)  # 1
        header.extend(self.alg_id)  # 1
        header.extend(self.blocksize)  # 1
        header.extend(self.size)  # 8
        header.extend(bytearray(4))  # 4

        return bytes(header)


class FileObject:

    header = None
    # Instance functions

    def __init__(self, source_file, alg=None, blocksize=None, isLegacy=None):

        if Path(source_file).is_dir():
            raise NotCompressedFile

        self.source_file = source_file

        if all(v is not None for v in [alg, blocksize, isLegacy]):
            if isLegacy:
                self.header = ZISOFS()
                self.header.set_size(self.source_file.stat().st_size)
                self.header.set_blocksize(blocksize)

            else:
                self.header = ZISOFSv2()
                self.header.set_size(self.source_file.stat().st_size)
                self.header.set_blocksize(blocksize)
                self.header.set_alg(alg)
        else:
            with open(self.source_file, 'rb') as in_fd:
                header = in_fd.read(32)

            try:
                hdr_obj = ZISOFSv2.from_header(header)
            except NotCompressedFile:
                # Maybe a v1 ziso?
                hdr_obj = ZISOFS.from_header(header)

            self.header = hdr_obj

    def get_size(self):
        return self.header.get_size()

    def get_chunks(self):
        """
        docstring
        """

        with open(self.source_file, 'rb') as src:
            for i in range(0, self._get_numblocks() - 1):
                yield self.read_block(i, file_descriptor=src)

    # Random access to data
    def get_algorithm(self):
        """
        docstring
        """
        return self.header.get_algorithm()

    def read_block(self, num, count=1, file_descriptor=None):
        def fd_seek(fd, offset):
            if type(fd) == int:
                return os.lseek(fd, offset, os.SEEK_SET)
            else:
                return fd.seek(offset)

        def fd_read(fd, length):
            if type(fd) == int:
                return os.read(fd, length)
            else:
                return fd.read(length)

        valid_blocks = self._get_numblocks() - 1

        if num >= valid_blocks:
            return b''

        psize = self.header.pointers_size  # Pointer size

        # Reuse file descriptor if is given
        if file_descriptor:
            src = file_descriptor
        else:
            src = open(self.source_file, 'rb')

        # First, get the position and size of the desired block
        table_pos = len(self.header) + num * psize
        # Go to the table
        fd_seek(src, table_pos)

        list_offset = []
        for _ in range(count+1):
            list_offset.append(self.header.get_pointer_value(fd_read(src, psize)))

        # Go to the actual data
        data = bytearray()
        for idx, offset in enumerate(list_offset[:-1]):
            total = list_offset[idx+1] - offset
            if (total) != 0: # TODO: Improve list access?
                fd_seek(src, offset)
                data += self.get_algorithm().data_decompress(
                    fd_read(src, total)
                )
            else:
                # Empty block. Must return all zero
                if num == valid_blocks - 1:  # Last one
                    # Last block will have different size
                    si = self.header.get_size() - self.header.get_blocksize() * (valid_blocks-1)
                    data += bytearray(si)
                else:
                    data += bytearray(self.header.get_blocksize())

        if not file_descriptor:
            # It was our file descriptor. Close it
            src.close()

        return data

    def _get_numblocks(self):
        """
        docstring
        """
        return int(
            math.ceil((self.header.get_size() / self.header.get_blocksize())) + 1)

    def generate_header(self):
        return bytes(self.header)

    def getTablePointers(self, list_pointers=None):
        """
        Return a byte array of the table pointers.
        If no list of pointers are given, return a blank array
        """
        nblocks = self._get_numblocks()

        if list_pointers:
            if len(list_pointers) != nblocks:
                raise ValueError(
                    "Number of precalculated pointers doesn't correspond to final pointers table")

            data = bytearray()

            for addr in list_pointers:
                if type(self.header) is ZISOFS:
                    data.extend(int_to_iso731(addr))
                else:
                    data.extend(int_to_uint64(addr))

            if len(data) != nblocks * self.header.pointers_size:
                raise ValueError(
                    "Number of precalculated pointers doesn't correspond to final pointers table")

            return bytes(data)

        return bytes(nblocks * self.header.pointers_size)

from enum import Enum
import math
from mkzftree2.iso9660 import int_to_iso711, int_to_iso731, iso711_to_int, int_to_uint64, iso731_to_int, uint64_to_int
from mkzftree2.arguments import default_block_sizes


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
        # Make sure is bytes
        if not isinstance(header, (bytes, bytearray)):
            raise ValueError
        # Correct size
        if len(header) != 4*iso711_to_int(ZISOFS.hdr_size):
            raise ValueError

        # Header magic
        if header[0:8] != ZISOFS.hdr_magic:
            raise ValueError

        # Header size
        if header[12:13] != ZISOFS.hdr_size:
            raise ValueError

        zisofs_obj = ZISOFS()

        # File size
        zisofs_obj.size = header[8:12]

        # Blocksize
        if iso711_to_int(header[11:12]) not in default_block_sizes:
            raise ValueError
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
        # Make sure is bytes
        if not isinstance(header, (bytes, bytearray)):
            raise ValueError
        # Correct size
        if len(header) != 4*iso711_to_int(ZISOFSv2.hdr_size):
            raise ValueError

        # Header magic
        if header[0:8] != ZISOFSv2.hdr_magic:
            raise ValueError

        # Header size
        if header[9:10] != ZISOFSv2.hdr_size:
            raise ValueError

        zisofs_obj = ZISOFSv2()

        # Algorithm
        if iso711_to_int(header[10:11]) == 0:
            raise ValueError
        zisofs_obj.alg_id = header[10:11]

        # Blocksize
        if iso711_to_int(header[11:12]) not in default_block_sizes:
            raise ValueError
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
        self.alg_id = int_to_iso711(alg_id)

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
                hdr_obj = ZISOFSv2.from_header(
                    header[0:ZISOFSv2.get_header_size()])
            except ValueError:
                # Maybe a v1 ziso?
                hdr_obj = ZISOFS.from_header(
                    header[0:ZISOFS.get_header_size()])

            self.header = hdr_obj

    def get_chunks(self):
        """
        docstring
        """

        for i in range(0, self._get_numblocks() - 1):
            yield self.read_block(i)

    def get_algorithm(self):
        return Algorithm(iso711_to_int(self.header.alg_id))

    # Random access to data
    def read_block(self, num):
        if num >= self._get_numblocks() - 1:
            raise ValueError

        psize = self.header.pointers_size  # Pointer size
        with open(self.source_file, 'rb') as src:
            # First, get the position and size of the desired block
            table_pos = len(self.header) + num * psize
            # Go to the table
            src.seek(table_pos)

            start_offset = self.header.get_pointer_value(src.read(psize))
            end_offset = self.header.get_pointer_value(src.read(psize))

            # Go to the actual data
            src.seek(start_offset)
            data = src.read(end_offset - start_offset)
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
        nblocks = int(
            math.ceil((self.source_file.stat().st_size / self.header.get_blocksize())) + 1)

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

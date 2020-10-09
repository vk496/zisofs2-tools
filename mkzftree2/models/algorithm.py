from enum import Enum

import zlib
import bz2
import lzma
import lz4.frame
import zstandard as zstd

class Algorithm(Enum):
    ZLIB = 1
    XZ = 2
    LZ4 = 3
    ZSTD = 4
    BZIP2 = 5

    @classmethod
    def from_arg(cls, value):
        return Algorithm(Algorithm.list_all().index(value)+1)

    @classmethod
    def list_all(cls):
        return [ i[0].lower() for i in cls.__members__.items() ]

    def data_decompress(self, chunk):
        if self == Algorithm.ZLIB:
            return zlib.decompress(chunk)
        elif self == Algorithm.XZ:
            return lzma.decompress(chunk)
        elif self == Algorithm.LZ4:
            return lz4.frame.decompress(chunk)
        elif self == Algorithm.ZSTD:
            return zstd.ZstdDecompressor().decompress(chunk)
        elif self == Algorithm.BZIP2:
            return bz2.decompress(chunk)
        else:
            raise NotImplementedError(f"{self} compressor not supported")

    def data_compress(self, chunk, preset):
        if self == Algorithm.ZLIB:
            return zlib.compress(chunk, level=preset)
        elif self == Algorithm.XZ:
            return lzma.compress(chunk, preset=preset)
        elif self == Algorithm.LZ4:
            return lz4.frame.compress(chunk, compression_level=preset)
        elif self == Algorithm.ZSTD:
            return zstd.ZstdCompressor(level=preset).compress(chunk)
        elif self == Algorithm.BZIP2:
            return bz2.compress(chunk, compresslevel=preset)
        else:
            raise NotImplementedError(f"{self} compressor not supported")
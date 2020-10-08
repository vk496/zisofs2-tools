from enum import Enum
from mkzftree2.arguments import default_compressors

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
        return Algorithm(default_compressors.index(value))

    def compress(self, chunk, preset):
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
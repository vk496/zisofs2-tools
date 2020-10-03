import lzma
import zlib


def compress_chunk(chunk, alg=None, preset=6, strategy=0):
    if alg == "xz":
        return lzma.compress(chunk, preset=preset)
    elif alg == "zlib":
        return zlib.compress(chunk, level=preset)
    else:
        raise NotImplementedError(f"{alg} compressor not supported")
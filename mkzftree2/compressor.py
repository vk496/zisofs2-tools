import lzma
import zlib
from pathlib import Path

from mkzftree2.models.FileObject import FileObject


def compress_file(input_file, output_file, blocksize=2**32, algorithm='zlib', zlevel=6, force=False, legacy=False):
    if type(input_file) != Path:
        raise ValueError(f"Input type not Path")

    if type(output_file) != Path:
        raise ValueError(f"Output type not Path")

    fobj = FileObject(input_file, legacy)

    fobj.create_parentDir() #If the file must be place in some subfolder

    with open(fobj.getFileSource(), 'rb') as src, open(fobj.getFileTarget(), 'w+b') as dst:
        pointers_table = []
        
        # File header
        ziso_header = fobj.generate_header()
        dst.write(ziso_header)

        for chunk in read_in_chunks(src, blocksize):
            pointers_table.append(dst.tell())
    
            if not all(byte == 0 for byte in chunk):
                # Zero blocks will be skipped
                data = compress_chunk(chunk, alg=algorithm, preset=zlevel)
                dst.write(data)

        pointers_table.append(dst.tell()) # Last block

        if dst.tell() >= src.tell() and not force:
            # Final size is bigger than compressed size
            src.seek(0)
            dst.seek(0)
            dst.write(src.read()) # TODO: Check memory usage for big files
            return False
        else:
            # We confirm that compressed file will be stored. Append pointers table
            dst.seek(len(ziso_header)) # Just after the header
            dst.write(fobj.getTablePointers(list_pointers=pointers_table))
            return True



# https://stackoverflow.com/a/519653
def read_in_chunks(file_object, chunk_size):
    """Lazy function (generator) to read a file piece by piece.
    Default chunk size: 1k."""
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data

def compress_chunk(chunk, alg=None, preset=6, strategy=0):
    if alg == "xz":
        return lzma.compress(chunk, preset=preset)
    elif alg == "zlib":
        return zlib.compress(chunk, level=preset)
    else:
        raise NotImplementedError(f"{alg} compressor not supported")
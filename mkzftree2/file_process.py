from mkzftree2.models.FileObject import FileObject, ZISOFSv2
import math
from mkzftree2.compressor import compress_chunk
from mkzftree2.iso9660 import *

def find_files(source_dir):
    # file_list = []
    for x in source_dir.iterdir():
        if x.is_file():
            FileObject(x)
        elif x.is_dir():
            find_files(x)


def compress_big(alg, zlevel, blocksize, force=False):

    for x in FileObject.file_list:
        
        x.create_parentDir() #If the file must be place in some subfolder

        with open(x.source_file, 'rb') as src, open(x.target_file, 'w+b') as dst:
            initial_size =x.source_file.stat().st_size
            
            nblocks = int(math.floor((initial_size / blocksize)) + 1)
            pointers_table = []

            # write header
            dst.write(ZISOFSv2.generate_header(initial_size))

            # Write pointers table
            if x.isLess4GB():
                dst.write(bytearray(nblocks * 4))
            else:
                dst.write(bytearray(nblocks * 8))

            while True:
                piece = src.read(blocksize)  
                pointers_table.append(dst.tell())
                if not piece:
                    break

                if not all(byte == 0 for byte in piece):
                    # Zero length blocks will be skipped
                    data = compress_chunk(piece, alg=alg, preset=zlevel)
                    dst.write(data)
            
            pointers_table.append(dst.tell()) # Last block

            if dst.tell() >= src.tell() and not force:
                # Final size is not interesting with this compression
                src.seek(0)
                dst.seek(0)
                dst.write(src.read())
            else:
                # We confirm that compressed file will be stored. Append pointers table
                dst.seek(32) # Just after the header
                if x.isLess4GB():
                    [dst.write(int_to_iso731(addr)) for addr in pointers_table]
                else:
                    [dst.write(uint64_to_two_iso731(addr, one=True)) for addr in pointers_table]

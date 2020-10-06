from mkzftree2.models.FileObject import FileObject
import math
from mkzftree2.compressor import compress_chunk
from mkzftree2.iso9660 import *

def find_files(source_dir, legacy=False):
    # file_list = []
    for x in source_dir.iterdir():
        if x.is_file():
            FileObject(x, legacy)
        elif x.is_dir():
            find_files(x, legacy)


def compress_file(alg, zlevel, blocksize, force=False):

    for x in FileObject.file_list:
        
        x.create_parentDir() #If the file must be place in some subfolder

        with open(x.getFileSource(), 'rb') as src, open(x.getFileTarget(), 'w+b') as dst:
            # initial_size =x.source_file.stat().st_size
            
            pointers_table = []

            # write header
            ziso_header = x.generate_header()
            dst.write(ziso_header)

            # Write pointers table template
            dst.write(x.getTablePointers())

            while True:
                piece = src.read(blocksize)  
                if not piece:
                    break

                if not all(byte == 0 for byte in piece):
                    # Zero length blocks will be skipped
                    data = compress_chunk(piece, alg=alg, preset=zlevel)
                    pointers_table.append(dst.tell())
                    dst.write(data)
            
            pointers_table.append(dst.tell()) # Last block

            if dst.tell() >= src.tell() and not force:
                # Final size is not interesting with this compression
                src.seek(0)
                dst.seek(0)
                dst.write(src.read())
            else:
                # We confirm that compressed file will be stored. Append pointers table
                dst.seek(len(ziso_header)) # Just after the header
                dst.write(x.getTablePointers(list_pointers=pointers_table))

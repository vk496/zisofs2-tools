from mkzftree2.models.FileObject import FileObject, ZISOFSv2
import lzma
import math

def find_files(source_dir):
    # file_list = []
    for x in source_dir.iterdir():
        if x.is_file():
            FileObject(x)
        elif x.is_dir():
            find_files(x)

def estimate_final_size(final_size, pointer_list):
    # In the limit case, it would be possible that all addresses
    # fit in 4bytes, but some of them will not if we add the 
    # pointer address. We must check the size progressively
    total_size = 0
    for n in pointer_list:
        if n + total_size < 2**32:
            total_size+=4
        else:
            total_size+=8

    return total_size


def compress_big(alg, zlevel, blocksize, force=False):
    for x in FileObject.file_list:
        
        if not x.target_file.parent.exists():
            x.target_file.parent.mkdir(parents=True)

        with open(x.source_file, 'rb') as src, open(x.target_file, 'wb') as dst:
            initial_size =x.source_file.stat().st_size
            nblocks = math.floor((initial_size + blocksize - 1) / blocksize)
            pointers_table = []

            # write header
            dst.write(ZISOFSv2.generate_header(initial_size))

            while True:
                piece = src.read(blocksize)  
                if not piece:
                    break
                data = lzma.compress(piece)
                pointers_table.append(dst.tell())
                dst.write(data)

            final_compressed_size = estimate_final_size(dst.tell(), pointers_table)
            
            if final_compressed_size >= src.tell() and not force:
                # Final size is not interesting with this compression
                src.seek(0)
                dst.seek(0)
                dst.write(src.read())
            print(pointers_table)

            # while (block := src.read(blocksize)):
            #     dst.write(block)                
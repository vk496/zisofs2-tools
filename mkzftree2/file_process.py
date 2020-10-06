from mkzftree2.models.FileObject import FileObject
import math
from pathlib import Path
from mkzftree2.compressor import compress_file
from mkzftree2.iso9660 import *

def find_files(source_dir, legacy=False):
    list_files = []

    for x in source_dir.iterdir():
        if x.is_file():
            list_files.append(Path(x))
        elif x.is_dir():
            l = find_files(x, legacy=legacy)
            return list_files.extend(l)

    return list_files


def process_files(list_files, source_dir, target_dir, alg, zlevel, blocksize, force=False, legacy=False):
    for f in list_files:
        target_file = target_dir / f.relative_to(source_dir)

        was_compressed = compress_file(
            f, 
            target_file, 
            blocksize=blocksize, 
            algorithm=alg, 
            zlevel=zlevel, 
            force=force, 
            legacy=legacy)
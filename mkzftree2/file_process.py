from mkzftree2.models.FileObject import FileObject
import math
from pathlib import Path
from mkzftree2.compressor import compress_file
from mkzftree2.iso9660 import *

def sizeof_fmt(num, suffix='B'):
    for unit in ['',' Ki',' Mi',' Gi',' Ti',' Pi',' Ei',' Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def find_files(source_dir, restrict_search, legacy=False):
    list_files = []

    #TODO: Handle symbolic links

    for x in source_dir.iterdir():
        if x.is_file():
            if restrict_search:
                if x in restrict_search: list_files.append(x)
            else:
                list_files.append(x)
        elif x.is_dir():
            l = find_files(x, restrict_search, legacy=legacy)
            list_files.extend(l)

    return list_files


def process_files(list_files, source_dir, target_dir, overwrite, alg, zlevel, blocksize, force, legacy):
    osizesum = 0
    csizesum = 0
    for f in list_files:
        target_file = target_dir / f.relative_to(source_dir)

        osizesum += f.stat().st_size
        
        if target_file.exists() and not overwrite:
            csizesum += target_file.stat().st_size
            print(f"{target_file}: SKIPED")
            continue

        ratio = compress_file(
            f, 
            target_file, 
            blocksize=blocksize, 
            algorithm=alg, 
            zlevel=zlevel, 
            force=force, 
            legacy=legacy)

        csizesum += target_file.stat().st_size

        print(f"{target_file}: {ratio}")

    print(f"Total input size : {sizeof_fmt(osizesum)}")
    print(f"Total output size: {sizeof_fmt(csizesum)}")
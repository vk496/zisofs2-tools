from mkzftree2.models.FileObject import FileObject
import math
from pathlib import Path
from mkzftree2.compressor import compress_file
from mkzftree2.iso9660 import *
import os

def sizeof_fmt(num, suffix='B'):
    for unit in ['',' Ki',' Mi',' Gi',' Ti',' Pi',' Ei',' Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def find_files(source_dir, restrict_search, followLinks):
    list_files = []

    for x in source_dir.iterdir():
        # Broken symlinks will be skipped
        if x.is_file():

            if not followLinks and x.is_symlink():
                try:
                    x.resolve().relative_to(source_dir.resolve())
                except ValueError:
                    raise FileExistsError(f'{x} (symlink to {x.resolve()}) is not part of {source_dir}. Consider using --follow-symlinks')

            if restrict_search:
                if x in restrict_search: list_files.append(x)
            else:
                list_files.append(x)
        elif x.is_dir():
            l = find_files(x, restrict_search, followLinks)
            list_files.extend(l)

    return list_files


def process_files(list_files, source_dir, target_dir, overwrite, alg, zlevel, blocksize, force, legacy, followLinks):
    osizesum = 0
    csizesum = 0
    for f in list_files:
        target_file = target_dir / f.relative_to(source_dir)


        if f.is_symlink():
            try:
                f.resolve().relative_to(source_dir.resolve())
            except ValueError as e:
                # The link is outside dir. Just follow the normal process and treat it as file
                pass
            else:
                # The symlink is inside the source dir. Create its correspondent symlink in target_dir
                target_file.symlink_to(os.readlink(f))
                continue
        
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

        print(f"{target_file}: {sizeof_fmt(f.stat().st_size)} -> {sizeof_fmt(target_file.stat().st_size)}")

    print(f"Total input size : {sizeof_fmt(osizesum)}")
    print(f"Total output size: {sizeof_fmt(csizesum)}")
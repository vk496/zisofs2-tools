from mkzftree2.arguments import output_dir
import os
from mkzftree2.compressor import compress_file, uncompress_file
from mkzftree2.utils import clone_dir_attributes


def sizeof_fmt(num, suffix='B'):
    for unit in ['', ' Ki', ' Mi', ' Gi', ' Ti', ' Pi', ' Ei', ' Zi']:
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
                except ValueError as exception:
                    raise FileExistsError(
                        (f'{x} (symlink to {x.resolve()}) is not '
                         'part of {source_dir}. Consider using --follow-symlinks')
                    ) from exception

            if restrict_search:
                if x in restrict_search:
                    list_files.append(x)
            else:
                list_files.append(x)
        elif x.is_dir():
            l = find_files(x, restrict_search, followLinks)
            if l:
                list_files.extend(l)
            else:
                # Empty dir
                list_files.append(x)

    return list_files


def uncompress_files(input_dir, output_dir):
    """
    docstring
    """
    for source_file in input_dir.iterdir():
        target_file = output_dir / source_file.relative_to(input_dir)

        if source_file.is_file():
            # Handle files
            if source_file.is_symlink():
                target_file.symlink_to(os.readlink(source_file))
                continue
            else:
                # Regular file
                uncompress_file(source_file, target_file)
                print(f"{target_file}")

        elif source_file.is_dir():
            target_file.mkdir(parents=True)
            uncompress_files(source_file, target_file)
            # Use fake file to get correct dir path
            clone_dir_attributes(
                (source_file / 'fake.txt').parents, (target_file / 'fake.txt').parents)


def process_files(list_files, source_dir, target_dir, overwrite, alg, zlevel, blocksize, force, legacy, ignore_attributes):
    osizesum = 0
    csizesum = 0
    for f in list_files:
        target_file = target_dir / f.relative_to(source_dir)

        if f.is_symlink():
            try:
                f.resolve().relative_to(source_dir.resolve())
            except ValueError:
                # The link is outside dir. Just follow the normal process and treat it as file
                pass
            else:
                # The symlink is inside the source dir. Create its correspondent symlink in target_dir
                target_file.symlink_to(os.readlink(f))
                continue
        elif f.is_dir():
            # Is a empty dir
            target_file.mkdir(parents=True)
            if not ignore_attributes:
                # Use fake file to get correct dir path
                clone_dir_attributes(
                    (f / 'fake.txt').parents, (target_file / 'fake.txt').parents)

            continue

        osizesum += f.stat().st_size

        if target_file.exists() and not overwrite:
            csizesum += target_file.stat().st_size
            print(f"{target_file}: SKIPED")
            continue

        compress_file(
            f,
            target_file,
            blocksize=blocksize,
            algorithm=alg,
            zlevel=zlevel,
            force=force,
            legacy=legacy)

        csizesum += target_file.stat().st_size

        print(
            f"{target_file}: {sizeof_fmt(f.stat().st_size)} -> {sizeof_fmt(target_file.stat().st_size)}")

    print(f"Total input size : {sizeof_fmt(osizesum)}")
    print(f"Total output size: {sizeof_fmt(csizesum)}")

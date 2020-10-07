import argparse
from pathlib import Path

def input_dir(dir):
    d = Path(dir)
    if d.is_dir() and d.exists():
        if any(d.iterdir()):
            return d
        else:
            raise FileNotFoundError(f"{d} must have any file")
    else:
        raise NotADirectoryError(d)

def output_dir(dir):
    d = Path(dir)
    return d

def input_files(file):
    f = Path(file)
    if not f.exists():
        raise FileNotFoundError(f"Restriction to file {f} not exists")

    return f

default_block_sizes = [15, 16, 17]
default_compressors = ['zlib', 'xz', 'lz4', 'zstd', 'bzip2']


def get_options(args):
    """
    Creates a new argument parser.
    """
    parser = argparse.ArgumentParser('mkzftree2')

    parser.add_argument('in_dir', type=input_dir, action='store', nargs=1, help="Input directory")
    parser.add_argument('out_dir', type=output_dir, action='store', nargs=1, help="Output directory")
    parser.add_argument('file', type=input_files, action='store', nargs='*', help="Optional input file")

    parser.add_argument('-a', choices=default_compressors, default='zlib', type=str, help="Compression algorithm")
    parser.add_argument('-b', '--blocksize', choices=default_block_sizes, type=int, default=15, help="Blocksize can be 15 (32kb), 16 (64kb) or 17 (128kb)")
    parser.add_argument('--follow-symlinks', default=False, action='store_true', help="Process symlinks outside in_dir as regular files")
    parser.add_argument('-f', '--force', default=False, action='store_true', help="Always compress, even if result is larger")
    parser.add_argument('--legacy', default=False, action='store_true', help="Generate old ZISOFSv1 tree")
    parser.add_argument('-o', '--overwrite', default=False, action='store_true', help="Overwrite if file exist (Default: skip)")
    parser.add_argument('-u', '--uncompress', default=False, action='store_true', help="Uncompress mode (Default: compress)")
    parser.add_argument('-v', '--version', action='version', version="1.0")
    parser.add_argument('-z', choices=range(1,10), metavar="[1-9]", type=int, default=6, help="Compression level")

    opt = parser.parse_args(args)

    if opt.legacy and not opt.a == 'zlib':
        raise ValueError(f"Legacy mode only support zlib compressor")


    if (opt.a == 'zlib' or opt.a == 'xz' or opt.a == 'bzip2') and opt.z > 9:
        raise ValueError(f"{opt.a} support up to 9 levels")

    if opt.a == 'lz4' and opt.z > 16:
        raise ValueError(f"{opt.a} support up to 16 levels")

    if opt.a == 'zstd' and opt.z > 22:
        raise ValueError(f"{opt.a} support up to 22 levels")

    return opt

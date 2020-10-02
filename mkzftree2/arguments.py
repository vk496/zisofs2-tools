import argparse
from pathlib import Path

def dir_intree(dir):
    d = Path(dir)
    if d.is_dir() and d.exists():
        if any(d.iterdir()):
            return d
        else:
            raise FileNotFoundError(f"{d} must have any file")
    else:
        raise NotADirectoryError(d)

def dir_outree(dir):
    d = Path(dir)
    if not d.exists() or not any(d.iterdir()):
        return d
    else:
        raise FileExistsError(f"{d} must be empty")



default_block_sizes = [32, 64, 128]


def get_parser():
    """
    Creates a new argument parser.
    """
    parser = argparse.ArgumentParser('mkzftree2')
    parser.add_argument('intree', type=dir_intree, action='store', nargs=1, help="Input directory")
    parser.add_argument('outtree', type=dir_outree, action='store', nargs=1, help="Output directory")
    parser.add_argument('-f', '--force', default=False, action='store_true', help="Always compress, even if result is larger")
    parser.add_argument('-a', choices=['zlib', 'xz', 'lz4'], required=True, type=str, help="Compression algorithm")
    parser.add_argument('-b', '--blocksize', choices=default_block_sizes, type=int, default=32, help="Blocksize can be 32kb, 64kb or 128kb")
    parser.add_argument('-z', choices=range(1,9), metavar="[1-9]", type=int, default=6, help="Compression level")
    parser.add_argument('-v', '--version', action='version', version="1.0")

    return parser

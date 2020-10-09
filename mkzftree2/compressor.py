from pathlib import Path

from mkzftree2.models.FileObject import FileObject
from mkzftree2.arguments import default_block_sizes
from mkzftree2.utils import clone_attributes, clone_dir_attributes
from mkzftree2.models.algoritm import Algorithm

def uncompress_file(input_file, output_file, copy_attributes=True):
    """
    docstring
    """

    in_file = Path(input_file) if not isinstance(
        input_file, Path) else input_file
    out_file = Path(output_file) if not isinstance(
        output_file, Path) else output_file

    try:
        fobj = FileObject(in_file)
    except ValueError:
        # Not compressed. Just copy
        with open(in_file, 'rb') as src, open(out_file, 'wb') as dst:
            dst.write(src.read())  # TODO: Check memory usage for big files
            if copy_attributes:
                clone_attributes(in_file, out_file)
                clone_dir_attributes(in_file.parents, out_file.parents)
            return

    with open(in_file, 'rb') as src, open(out_file, 'wb') as dst:
        alg = fobj.get_algorithm()
        for cdata in fobj.get_chunks():
            raw_data = alg.data_decompress(cdata)
            dst.write(raw_data)  # TODO: Check memory usage for big files

    



def compress_file(input_file, output_file,
                  blocksize=2**15,
                  algorithm='zlib',
                  zlevel=6,
                  force=False,
                  legacy=False,
                  copy_attributes=True):

    in_file = Path(input_file) if not isinstance(
        input_file, Path) else input_file
    out_file = Path(output_file) if not isinstance(
        output_file, Path) else output_file

    if blocksize not in [2**x for x in default_block_sizes]:
        raise ValueError(f"Not a valid {blocksize}")
    algorithm = Algorithm.from_arg(algorithm)

    fobj = FileObject(in_file, alg=algorithm,
                      blocksize=blocksize, isLegacy=legacy)

    # If target directory doesn't exist, create all of them
    if not out_file.parent.exists():
        out_file.parent.mkdir(parents=True)

    with open(in_file, 'rb') as src, open(out_file, 'wb') as dst:
        pointers_table = []

        # File header
        ziso_header = fobj.generate_header()
        dst.write(ziso_header)

        # Pointers table
        dst.write(fobj.getTablePointers())

        for chunk in _read_in_chunks(src, blocksize):
            pointers_table.append(dst.tell())

            if not all(byte == 0 for byte in chunk):
                # Zero blocks will be skipped
                data = algorithm.data_compress(chunk, zlevel)
                dst.write(data)

        pointers_table.append(dst.tell())  # Last block

        ratio = 1

        if dst.tell() >= src.tell() and not force:
            # Final size is bigger than compressed size
            src.seek(0)
            dst.seek(0)
            dst.truncate()  # Remove all content from file
            dst.write(src.read())  # TODO: Check memory usage for big files
        else:
            # Save the ratio
            ratio = dst.tell() / src.tell()
            # We confirm that compressed file will be stored. Append pointers table
            dst.seek(len(ziso_header))  # Just after the header
            dst.write(fobj.getTablePointers(list_pointers=pointers_table))

    # Copy attributes from original file
    if copy_attributes:
        clone_attributes(in_file, out_file)
        clone_dir_attributes(in_file.parents, out_file.parents)

    return ratio


# https://stackoverflow.com/a/519653
def _read_in_chunks(file_object, chunk_size):
    """Lazy function (generator) to read a file piece by piece.
    Default chunk size: 1k."""
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


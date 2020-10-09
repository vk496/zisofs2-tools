from argparse import ArgumentError
import pytest
import hashlib
import random

from pathlib import Path
import shutil
from mkzftree2.compressor import compress_file, uncompress_file
from mkzftree2.arguments import default_block_sizes
from mkzftree2.models.algorithm import Algorithm
from mkzftree2.models.FileObject import ZISOFS, ZISOFSv2, FileObject
from mkzftree2.utils import IllegalArgumentError, NotCompressedFile


def get_md5(infile):
    return hashlib.md5(open(infile,'rb').read()).hexdigest()

@pytest.yield_fixture(scope='session')
def input_file_tuple(tmpdir_factory):

    tmpdir = tmpdir_factory.mktemp("input_dir")

    in_file = Path(tmpdir / 'simple_data.csv')
    print(in_file)

    with in_file.open('w') as src:
        for _ in range(0, 100000):
            src.write("a,b,c,d,e,f,g,h\n")

    hash_md5 = hashlib.md5(open(in_file,'rb').read()).hexdigest()

    yield (in_file, hash_md5)

    shutil.rmtree(str(tmpdir))


@pytest.yield_fixture
def input_file_empty(tmpdir):
    out_file = Path(tmpdir / "__init__.py")
    out_file.touch()
    yield out_file

@pytest.yield_fixture
def input_file_full(tmpdir):
    random.seed(0)
    size=8*10**6

    out_file = Path(tmpdir / "full_random.bin")
    with open(out_file, 'wb') as fout:
        fout.write(random.getrandbits(8*size).to_bytes(size, 'little', signed=False))
    yield out_file

@pytest.yield_fixture
def input_file_holes(tmpdir):
    random.seed(0)
    size=2*10**6 # 2M

    out_file = Path(tmpdir / "holes_random.bin")
    with open(out_file, 'wb') as fout:
        fout.write(random.getrandbits(8*size).to_bytes(size, 'little', signed=False))
        fout.write(b'\x00'*size*3) # 6M
    yield out_file

@pytest.yield_fixture
def output_file(tmpdir):
    out_file = Path(tmpdir / "output.vk496")
    yield out_file
    shutil.rmtree(str(tmpdir))


def test_empty(input_file_empty, output_file):
    compress_file(
        input_file_empty,
        output_file
    )

    assert(output_file.stat().st_size == 0)

@pytest.mark.parametrize('legacy', [False, True])
def test_full(input_file_full, output_file, legacy):

    ratio = compress_file(
        input_file_full,
        output_file,
        legacy=legacy
    )

    with pytest.raises(NotCompressedFile):
        FileObject(output_file)

    assert(ratio == 1)

    ratio = compress_file(
        input_file_full,
        output_file,
        force=True,
        legacy=legacy
    )

    assert(ratio > 1)

    extracted_file = (output_file.parent / 'result_extracted')
    uncompress_file(output_file, extracted_file)

    assert(get_md5(input_file_full) == get_md5(extracted_file))



@pytest.mark.parametrize('legacy', [False, True])
def test_holes(input_file_holes, output_file, legacy):
    ratio = compress_file(
        input_file_holes,
        output_file,
        legacy=legacy
    )

    print('xd')

    assert(ratio < 0.3)
    
    extracted_file = (output_file.parent / 'result_extracted')
    uncompress_file(output_file, extracted_file)

    assert(get_md5(input_file_holes) == get_md5(extracted_file))

    fobj = FileObject(output_file)
    
    # The last 130 pointers must be the same value, since they are zero blocks and must
    # be not writted in the data
    assert (len(set(fobj.precalculated_table[-130:])) == 1)


@pytest.mark.parametrize('blocksize', default_block_sizes)
@pytest.mark.parametrize('alg', Algorithm.list_all())
@pytest.mark.parametrize('legacy', [False, True])
@pytest.mark.parametrize('force', [False, True])
@pytest.mark.parametrize('copy_attributes', [False, True])
def test_compress(input_file_tuple, output_file, alg, blocksize, force, legacy, copy_attributes):

    input_file, md5_input = input_file_tuple

    def call_compress():
        """
        docstring
        """
        return compress_file(
                input_file,
                output_file,
                blocksize=2**blocksize,
                algorithm=alg,
                zlevel=2,
                force=force,
                legacy=legacy,
                copy_attributes=copy_attributes
            )

    if legacy and alg != "zlib":
        with pytest.raises(IllegalArgumentError, match="Legacy only support zlib"):
            call_compress()
        return #Skip the rest
    
    ratio = call_compress()

    # Input file was not modified
    assert(hashlib.md5(open(input_file,'rb').read()).hexdigest() == md5_input)

    # If not force, size must not be greater than original
    if not force:
        assert(ratio < 1)
        output_file.stat().st_size <= input_file.stat().st_size


    with open(output_file,'rb') as cfile:
        header = cfile.read(32) # Read chunk where should be the 
    
    if legacy:
        header_obj = ZISOFS.from_header(header)
    else:
        header_obj = ZISOFSv2.from_header(header)

    assert(header_obj.get_blocksize() == 2**blocksize)
    assert(header_obj.get_size() == input_file.stat().st_size)


    extracted_file = (output_file.parent / 'result_extracted')
    uncompress_file(output_file, extracted_file, copy_attributes=copy_attributes)

    assert(hashlib.md5(open(extracted_file,'rb').read()).hexdigest() == md5_input)


    print(f"ratio: {ratio*100:0.2f}%", end=' ')

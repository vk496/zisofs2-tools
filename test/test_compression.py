from argparse import ArgumentError
import pytest
import hashlib

from pathlib import Path
import shutil
from mkzftree2.compressor import compress_file, uncompress_file
from mkzftree2.arguments import default_block_sizes
from mkzftree2.models.algorithm import Algorithm
from mkzftree2.models.FileObject import ZISOFS, ZISOFSv2
from mkzftree2.utils import IllegalArgumentError


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


@pytest.fixture()
def input_file_empty(tmpdir):
    out_file = Path(tmpdir / "__init__.py")
    out_file.touch()
    return out_file


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

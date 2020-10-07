import pytest
from mkzftree2.compressor import compress_file
from mkzftree2.arguments import default_compressors, default_block_sizes
import shutil, os
from pathlib import Path

@pytest.fixture(scope='session')
def input_file(tmpdir_factory):

    tmpdir = tmpdir_factory.mktemp("input_dir")

    in_file = (tmpdir / 'simple_data.csv')
    print(in_file)

    with in_file.open('w') as src:
        for i in range(0, 100000):
            src.write("a,b,c,d,e,f,g,h\n")

    yield in_file

    shutil.rmtree(str(tmpdir))

@pytest.fixture()
def input_file_empty(tmpdir):
    out_file = Path(tmpdir / "__init__.py")
    out_file.touch()
    return out_file

@pytest.fixture
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
@pytest.mark.parametrize('alg', default_compressors)
@pytest.mark.parametrize('legacy', [False, True])
@pytest.mark.parametrize('zlevel', range(1, 10, 3))
def test_compress(input_file, output_file, alg, blocksize, zlevel, legacy):

    ratio = compress_file(
            input_file, 
            output_file, 
            blocksize=2**blocksize, 
            algorithm=alg, 
            zlevel=zlevel, 
            # force=force, 
            legacy=legacy
            )

    assert(ratio < 1)
    print(f"ratio: {ratio*100:0.2f}%", end=' ')
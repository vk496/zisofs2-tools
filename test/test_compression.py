import pytest
from mkzftree2.compressor import compress_file
from mkzftree2.arguments import default_compressors, default_block_sizes
import shutil, os

@pytest.fixture(scope='session')
def input_file(tmpdir_factory):
    from pathlib import Path

    tmpdir = tmpdir_factory.mktemp("input_dir")

    in_file = (tmpdir / 'simple_data.csv')
    print(in_file)

    with in_file.open('w') as src:
        for i in range(0, 100000):
            src.write("a,b,c,d,e,f,g,h\n")

    yield in_file

    shutil.rmtree(str(tmpdir))

@pytest.fixture
def output_file(tmpdir):
    out_file = tmpdir / "output.vk496"
    yield out_file
    shutil.rmtree(str(tmpdir))


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
import pytest

@pytest.fixture(scope='session')
def input_file(tmpdir_factory):
    from pathlib import Path
    import shutil

    tmpdir = tmpdir_factory.mktemp("input_dir")

    in_file = (tmpdir / 'simple_data.csv')
    print(in_file)

    with in_file.open('w') as in_file:
        for i in range(0, 10**6):
            in_file.write("a,b,c,d,e,f,g,h\n")

    yield in_file

    shutil.rmtree(str(tmpdir))


def test_func2(input_file):

    return 3 + 1
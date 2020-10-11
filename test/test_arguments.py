import pytest

from mkzftree2.arguments import get_options

def test_noarguments(capsys):
    with pytest.raises(SystemExit):
        get_options('')
    assert 'the following arguments are required: in_dir, out_dir' in capsys.readouterr().err


def test_bad_indir():
    with pytest.raises(NotADirectoryError):
        get_options("nodir outdir")

def test_nofiles(tmpdir):
    args = [
        str(tmpdir),
        'outdir'
    ]
    with pytest.raises(FileNotFoundError):
        get_options(args)

def test_basic(input_file_empty):
    args = [
        str(input_file_empty.parent),
        "outdir"
    ]
    get_options(args)
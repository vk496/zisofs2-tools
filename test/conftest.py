from pathlib import Path
import pytest


@pytest.yield_fixture
def input_file_empty(tmpdir):
    out_file = Path(tmpdir / "__init__.py")
    out_file.touch()
    yield out_file
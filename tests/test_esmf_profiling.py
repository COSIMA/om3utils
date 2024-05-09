import pytest
from pathlib import Path

bt2 = pytest.importorskip("bt2", reason="Requires babeltrace2 python bindings")

from om3utils.esmf_profiling import ESMFProfilingParser


def test_read_missing_esmf_profiling_dir():
    with pytest.raises(FileNotFoundError):
        parser = ESMFProfilingParser("benchmark")
        parser.read(Path("garbage"))

import pytest
import tempfile

from pathlib import Path


@pytest.fixture
def clean_tmp_path():
    t = tempfile.TemporaryDirectory(prefix="pytest", ignore_cleanup_errors=True)
    yield Path(t.name)

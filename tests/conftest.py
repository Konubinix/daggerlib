# [[file:testing.org::*SDK test fixtures][SDK test fixtures:1]]
import sys
from pathlib import Path

import pytest

import dagger

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lib import Lib


@pytest.fixture(scope="session")
async def lib():
    await dagger.connect()
    try:
        yield Lib()
    finally:
        await dagger.close()


# SDK test fixtures:1 ends here

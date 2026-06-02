"""Unit tests for the async->sync transliterator (``scripts/gen_sync.py``).

These guard the token-level transform's edge cases. No committed source triggers them
today, so without these the behaviour is only exercised the day someone writes such code
in an async resource — exactly when a silent miscompile would be most surprising.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


def _load_gen_sync() -> ModuleType:
    script = Path(__file__).resolve().parent.parent / "scripts" / "gen_sync.py"
    spec = importlib.util.spec_from_file_location("gen_sync", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_strips_async_await_and_single_trailing_space() -> None:
    g = _load_gen_sync()
    out = g._transform("async def f():\n    return await g()\n", "x.py")
    assert "def f():" in out
    assert "return g()" in out  # one space collapsed, not two
    assert "await" not in out.split('"""')[-1]


def test_await_without_following_space_keeps_next_token() -> None:
    # `await(expr)` has no whitespace token after the keyword; the transform must keep the
    # `(` rather than swallow it (which would corrupt the source into `... expr)`).
    g = _load_gen_sync()
    out = g._transform("x = await(foo())\n", "x.py")
    assert "x = (foo())" in out
    assert "foo())" not in out.replace("(foo())", "")  # no dangling `foo())`


def test_rejects_unsupported_asyncio_member() -> None:
    g = _load_gen_sync()
    with pytest.raises(SystemExit, match=r"asyncio\.gather"):
        g._transform("import asyncio\nx = asyncio.gather()\n", "x.py")


def test_allows_asyncio_sleep() -> None:
    g = _load_gen_sync()
    out = g._transform("import asyncio\nsleep = asyncio.sleep\n", "x.py")
    assert "import time" in out
    assert "sleep = time.sleep" in out
    assert "asyncio" not in out.split('"""')[-1]


def test_asyncio_lock_maps_to_threading_and_keeps_time() -> None:
    # asyncio.Lock -> threading.Lock; asyncio.sleep -> time.sleep; the existing `import time`
    # (kept for monotonic) is not duplicated, and `import asyncio` becomes `import threading`.
    g = _load_gen_sync()
    src = "import asyncio\nimport time\nlock = asyncio.Lock()\nsleep = asyncio.sleep\n"
    out = g._transform(src, "x.py")
    assert "import threading" in out
    assert "lock = threading.Lock()" in out
    assert "sleep = time.sleep" in out
    assert out.count("import time") == 1  # not duplicated
    assert "import asyncio" not in out

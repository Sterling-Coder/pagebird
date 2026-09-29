"""Run a job's QA evaluation in a child process.

Layout scoring re-renders every page of the document, so on a large IDML it
can exhaust memory or crash natively inside PyMuPDF. In the API process that
takes the whole server down (every in-flight request and translation with it);
in a child it costs one failed QA request with a readable error.
"""

from __future__ import annotations

import importlib
import multiprocessing
import os
import signal
import sys

_DEFAULT_TIMEOUT = 240.0  # stay under the ~300s the proxy allows a request
_DEFAULT_MAX_MB = 3072


def _child(conn, fn_spec: str, args: tuple, kwargs: dict, max_mb: int) -> None:
    try:
        if max_mb > 0 and sys.platform.startswith("linux"):
            import resource

            limit = max_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        module, _, name = fn_spec.partition(":")
        result = getattr(importlib.import_module(module), name)(*args, **kwargs)
        conn.send(("ok", result))
    except BaseException as e:  # noqa: BLE001 - everything must reach the parent
        try:
            conn.send(("error", (type(e).__name__, str(e))))
        except Exception:
            pass
    finally:
        conn.close()
        os._exit(0)  # skip interpreter teardown (DB pool threads can hang it)


def run(fn_spec: str, *args, timeout: float | None = None,
        max_mb: int | None = None, **kwargs):
    """Call `module:function(*args, **kwargs)` in a fresh process, return its
    result. Raises KeyError / TimeoutError / RuntimeError like the in-process
    call would have, plus RuntimeError if the child dies without answering."""
    timeout = timeout if timeout is not None else float(
        os.environ.get("PAGEBIRDY_EVAL_TIMEOUT", _DEFAULT_TIMEOUT))
    max_mb = max_mb if max_mb is not None else int(
        os.environ.get("PAGEBIRDY_EVAL_MAX_MB", _DEFAULT_MAX_MB))

    ctx = multiprocessing.get_context("spawn")
    parent, child = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=_child, args=(child, fn_spec, args, kwargs, max_mb),
                       daemon=True)
    proc.start()
    child.close()
    try:
        if not parent.poll(timeout):
            raise TimeoutError(f"evaluation took longer than {timeout:.0f}s")
        try:
            kind, payload = parent.recv()
        except EOFError:
            proc.join(5)
            code = proc.exitcode
            how = (f"killed by {signal.Signals(-code).name}" if code and code < 0
                   else f"exited with code {code}")
            raise RuntimeError(
                f"evaluation process died ({how}); the document is probably too "
                "large to score in the memory available")
    finally:
        parent.close()
        if proc.is_alive():
            proc.kill()
        proc.join(5)

    if kind == "ok":
        return payload
    name, message = payload
    if name == "KeyError":
        raise KeyError(message.strip("'\""))
    if name == "MemoryError":
        raise RuntimeError("evaluation ran out of memory; the document is too large to score")
    raise RuntimeError(f"{name}: {message}")

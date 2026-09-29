import os
import signal
import time


def ok(job_id, **kwargs):
    return {"job_id": job_id, "score": 1, **kwargs}


def missing(job_id, **kwargs):
    raise KeyError(f"job {job_id} not found")


def broken(job_id, **kwargs):
    raise ValueError("bad layout")


def crash(job_id, **kwargs):
    os.kill(os.getpid(), signal.SIGKILL)


def hang(job_id, **kwargs):
    time.sleep(60)

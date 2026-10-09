"""Website translation: fetch one public web page, translate its words, serve
a static, script-free copy.

    fetch     — the only code that touches the network; SSRF-guarded (`fetch.py`)
    html      — the page as `Segment`s and back, structure untouched (`html.py`)
    sanitize  — what the served copy may not contain (`sanitize.py`)
    pipeline  — the stages, on the shared office driver (`pipeline.py`)

The HTTP endpoints live in `pagebirdy/web_api.py`.
"""

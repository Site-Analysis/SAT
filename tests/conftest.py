"""Pytest configuration for SAT integration tests.

Each service ships a package literally named ``app``. We deliberately do NOT add
every service directory to ``sys.path`` here: doing so merges all of them into a
single ``app`` (implicit) namespace package, and submodule resolution then picks
whichever service is earliest on the path — so a temperature test would import
the sunpath ``app`` and vice-versa.

Instead, every ``*_smoke.py`` / validation module inserts only its own service
directory at import time, and CI runs each file in its own pytest process (see
the ``smoke`` job). That keeps exactly one service's ``app`` importable per
process. When running locally, invoke one service's tests at a time
(``pytest tests/sunpath_smoke.py``) for the same reason.
"""

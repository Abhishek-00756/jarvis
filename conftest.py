"""Ensures the project root is on sys.path so `pytest` resolves the
`agent` package without needing `PYTHONPATH=.` set manually. This file's
own location (not the current working directory) is what's added, so it
works whether pytest is invoked from the project root or elsewhere.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

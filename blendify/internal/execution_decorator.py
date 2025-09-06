import os
import sys
import traceback
from functools import wraps

_bpy_exit_bypassed = False


def safe_exit(func):
    """
    A decorator that catches exceptions and modifies the shared state
    before forcing an exit.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            global _bpy_exit_bypassed
            _bpy_exit_bypassed = True

            print(f"blendify caught error: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

            sys.exit(1)
    return wrapper
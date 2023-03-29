"""Error handling"""
from contextlib import contextmanager

from click import Abort

from drift_cli.utils.consoles import error_console


@contextmanager
def error_handle(debug: bool):
    """Wrap try-catch block and print error"""
    if debug:
        # If debug is enabled, we don't want to catch any errors and wrap them
        yield
    else:
        try:
            yield
        except Exception as err:
            error_console.print(f"[{type(err).__name__}] {err}")
            raise Abort() from err

"""Service entry point: python -m univorch.

Sprint 1: keeps the container process alive so the CLI can be used
via 'docker exec'. Replaced by the NiceGUI web server in Sprint 2.
"""

import signal
import sys
import time


def main() -> None:
    """Block until SIGTERM is received."""
    # Respond cleanly to 'docker stop' (which sends SIGTERM).
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()

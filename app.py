"""Small launcher for the Windows desktop application."""

import sys


if __name__ == "__main__":
    if "--check-uia" in sys.argv[1:]:
        from yangi_lotin.selection_probe import SelectionProbe

        probe = SelectionProbe()
        probe.start()
        available = probe.wait_ready()
        if not available and probe.startup_error is not None and sys.stderr is not None:
            print(repr(probe.startup_error), file=sys.stderr)
        probe.stop()
        raise SystemExit(0 if available else 1)

    from yangi_lotin.gui import main

    main()

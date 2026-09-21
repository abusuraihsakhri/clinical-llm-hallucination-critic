"""Compatibility entry point that delegates to the canonical CLI."""
from cli import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())

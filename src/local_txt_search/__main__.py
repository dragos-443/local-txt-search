"""Allow execution with ``python -m local_txt_search``."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())

"""Manual, local-only two-jaw inspection. Refuses without effect."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from static_workbench.week_crossing import (  # noqa: E402
    MAX_DOCUMENT, WeekCrossingRefused, inspect_crossing, parse_document,
)


def read_carrier(path: Path | None):
    if path is None:
        return None
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_DOCUMENT:
        raise WeekCrossingRefused("carrier absent, symlinked or oversized")
    with path.open("rb") as stream:
        content = stream.read(MAX_DOCUMENT + 1)
    return parse_document(content)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect two independent week artifacts; HOLD only")
    parser.add_argument("--notes", type=Path, help="unsigned webZ week JSON parcel")
    parser.add_argument("--docket", type=Path, help="Vault evidence docket JSON")
    parser.add_argument("--asset", type=Path, help="receiver-local asset bytes, never uploaded")
    args = parser.parse_args(argv)
    try:
        result = inspect_crossing(read_carrier(args.notes), read_carrier(args.docket), args.asset)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (WeekCrossingRefused, OSError) as error:
        # Do not echo untrusted content or local paths on errors.
        print("PINCERSMASH refused: " + str(error) if isinstance(error, WeekCrossingRefused)
              else "PINCERSMASH refused: unreadable local file", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

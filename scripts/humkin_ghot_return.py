#!/usr/bin/env python3
"""Run HUMKIN-GHOT-002 only with an explicit, narrowly scoped approval token."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from static_workbench.humkin_ghot import execute_catalog_hash

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--relatte", type=Path, required=True)
    p.add_argument("--ghot", type=Path, required=True)
    p.add_argument("--public-hold", type=Path, required=True)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--approve-public-catalog-hash", action="store_true")
    a = p.parse_args()
    value = execute_catalog_hash(
        a.relatte.resolve(), a.ghot.resolve(), a.public_hold.resolve(),
        a.work.resolve(), "HASH_PUBLIC_CATALOG" if a.approve_public_catalog_hash else None,
    )
    print(json.dumps(value, indent=2))

if __name__ == "__main__":
    main()

"""LAUNCHPAD-001: HOUSE-owned read-only first-flight map.

The operating system owns image/VM/boot evidence. Presence of a source repo,
successful CI or a browser server cannot prove ISO build, guest boot or cold
reconstitution. There is no subprocess, elevated action, network call or write.
"""
from __future__ import annotations

from fastapi import APIRouter

STATIC_OS_REPO = "https://github.com/the-static-collective/static-os"
BRANCH = "feat/launchpad-001-user-bootstrap"


def first_run_map() -> dict:
    """Return a fixed, bounded local interface; no browser-controlled commands."""
    return {
        "format": "house.launchpad/v0.1",
        "phase": "house_running",
        "authority": "none",
        "automatic_actions": [],
        "gates": [
            {
                "id": "house",
                "title": "HOUSE is running",
                "state": "observed_in_this_process",
                "details": "This page is served by local HOUSE. Its source SHA, host setup and persistence are not independently attested here.",
                "command": None,
            },
            {
                "id": "prepare",
                "title": "Prepare the STATIC OS build",
                "state": "not_observed",
                "details": "Clone the dedicated bootstrap candidate and invoke its user-only, pinned HOUSE starter. This does not build or install the OS. Existing local checkout/configuration may require manual inspection.",
                "command": "git clone --branch " + BRANCH + " " + STATIC_OS_REPO + ".git ~/static-os-launchpad && cd ~/static-os-launchpad && bash ./scripts/start-train.sh --check",
            },
            {
                "id": "iso",
                "title": "Build a candidate ISO",
                "state": "not_observed",
                "details": "Use a disposable Debian Bookworm amd64 build VM, not your Zorin host. Read the pinned GENESIS and FLIGHT-003 instructions before invoking the VM-only root build.",
                "command": "python3 scripts/validate-flight-003.py && python3 -m unittest discover -s tests -v && sudo ./scripts/build-iso.sh",
            },
            {
                "id": "guest",
                "title": "Test the candidate in a second VM",
                "state": "not_observed",
                "details": "Boot ISO in disposable BIOS/UEFI guests, detach the guest network, verify HOUSE at loopback and manually run static-elf-proof as the live user. Record independent VM evidence.",
                "command": "systemctl --user status static-workbench.service && static-elf-proof",
            },
            {
                "id": "cold_boot",
                "title": "Carry a new occurrence across cold boot",
                "state": "not_observed",
                "details": "Requires separately provisioned disposable persistent media, an independently observed power-off/new boot, Storyship verify/receive and a fresh independently verified ELF occurrence. Not automated by this page.",
                "command": None,
            },
        ],
        "source": STATIC_OS_REPO + "/blob/" + BRANCH + "/docs/LAUNCHPAD-001.md",
        "nonclaims": [
            "Local page reachability is not source authenticity, boot proof, or an installed OS.",
            "No host packages, VM operations, builds, storage, disk selection, root privilege or auto-promotion are performed.",
            "Manual commands are guidance; only independent observed tests may advance boot/cold-boot gates.",
        ],
    }


def launchpad_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/launchpad")
    def map_first_run() -> dict:
        return first_run_map()

    return router

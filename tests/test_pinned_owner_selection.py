"""WEBZ-003: exact clean pinned owner selection across two reLATTE checkouts."""
from pathlib import Path

import pytest
from static_workbench import field_reseed_crossing as owner
from static_workbench.repos import RepoStatus


def entry(path: Path) -> RepoStatus:
    return RepoStatus(
        name="reLATTE",path=str(path),branch=None,detached=True,
        head="1234567",dirty=False,ahead=None,behind=None,
    )


def test_choose_only_exact_revision_from_multiple_same_named_repositories(tmp_path,monkeypatch):
    old=tmp_path/"old"/"reLATTE"
    new=tmp_path/"new"/"reLATTE"
    old.mkdir(parents=True)
    new.mkdir(parents=True)
    (new/"material-delivery.ts").write_text("export {};")
    monkeypatch.setattr(owner,"_tracked_checkout_matches",lambda root,revision: Path(root)==new)
    selected=owner._find_pinned(
        [entry(old),entry(new)],"reLATTE","a"*40,"material-delivery.ts",
    )
    assert selected==new


def test_two_clean_exact_revision_checkouts_are_ambiguous(tmp_path,monkeypatch):
    a=tmp_path/"first"/"reLATTE"
    b=tmp_path/"second"/"reLATTE"
    a.mkdir(parents=True);b.mkdir(parents=True)
    for path in (a,b):
        (path/"material-delivery.ts").write_text("export {};")
    monkeypatch.setattr(owner,"_tracked_checkout_matches",lambda root,revision: True)
    with pytest.raises(owner.FieldReseedCrossingError,match="ambiguous"):
        owner._find_pinned([entry(a),entry(b)],"reLATTE","a"*40,"material-delivery.ts")


def test_no_matching_named_checkout_still_fails_closed(tmp_path,monkeypatch):
    wrong=tmp_path/"reLATTE"
    wrong.mkdir()
    monkeypatch.setattr(owner,"_tracked_checkout_matches",lambda root,revision: False)
    with pytest.raises(owner.FieldReseedCrossingError,match="pinned revision"):
        owner._find_pinned([entry(wrong)],"reLATTE","a"*40,"material-delivery.ts")

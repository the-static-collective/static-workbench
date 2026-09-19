from pathlib import Path

from static_workbench.journal import Journal


def test_journal_appends_and_reads_newest_first(tmp_path: Path):
    db = tmp_path / "journal.sqlite3"
    journal = Journal(db)

    first = journal.append("workbench.started", {"version": "0.1"})
    second = journal.append("repos.scanned", {"count": 2})

    events = journal.latest(10)
    assert [event.id for event in events] == [second.id, first.id]
    assert events[0].kind == "repos.scanned"
    assert events[0].payload == {"count": 2}


def test_journal_survives_reopen(tmp_path: Path):
    db = tmp_path / "journal.sqlite3"
    Journal(db).append("object.inspected", {"path": "song.txt"})

    reopened = Journal(db)
    events = reopened.latest(10)

    assert len(events) == 1
    assert events[0].kind == "object.inspected"
    assert events[0].payload["path"] == "song.txt"


def test_sense_fields_are_append_only_and_survive_reopen(tmp_path: Path):
    db = tmp_path / "journal.sqlite3"
    journal = Journal(db)

    first = journal.append_sense_field(
        raw_text="The bank moved.",
        parent_id=None,
        payload={"status": "unresolved", "readings": ["bank.financial", "bank.river", "bank.maneuver"]},
    )
    second = journal.append_sense_field(
        raw_text="The bank moved.",
        parent_id=first.id,
        payload={"status": "narrowed", "readings": ["bank.river"]},
    )

    reopened = Journal(db)
    rows = reopened.latest_sense_fields()

    assert [row.id for row in rows[:2]] == [second.id, first.id]
    assert rows[0].parent_id == first.id
    assert rows[1].payload["status"] == "unresolved"
    assert rows[1].payload["readings"] == ["bank.financial", "bank.river", "bank.maneuver"]


def test_get_sense_field_returns_none_for_unknown_id(tmp_path: Path):
    journal = Journal(tmp_path / "journal.sqlite3")

    assert journal.get_sense_field(999) is None

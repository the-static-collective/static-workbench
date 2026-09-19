from collections import namedtuple
from pathlib import Path

from static_workbench.config import RootConfig
from static_workbench.machine import sample_machine


Memory = namedtuple("Memory", "total available percent used free")
Disk = namedtuple("Disk", "total used free percent")
Temp = namedtuple("Temp", "label current high critical")


class FakeProvider:
    def cpu_percent(self, interval=None):
        return 12.5

    def virtual_memory(self):
        return Memory(1000, 600, 40.0, 400, 100)

    def disk_usage(self, path):
        return Disk(10_000, 2_500, 7_500, 25.0)

    def boot_time(self):
        return 100.0

    def sensors_temperatures(self):
        return {"coretemp": [Temp("Package id 0", 58.5, 95.0, 105.0)]}


def test_sample_machine_has_machine_and_root_disks(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()

    snapshot = sample_machine(
        (RootConfig("static", root),),
        provider=FakeProvider(),
        now=lambda: 1000.0,
        loadavg=lambda: (0.1, 0.2, 0.3),
        root_disk_path=root,
    )

    assert snapshot.cpu_percent == 12.5
    assert snapshot.memory.percent == 40.0
    assert snapshot.uptime_seconds == 900.0
    assert snapshot.load_average == (0.1, 0.2, 0.3)
    assert snapshot.root_disk.percent == 25.0
    assert snapshot.configured_roots[0].root_id == "static"
    assert snapshot.temperatures.available is True
    assert snapshot.temperatures.readings[0].current_c == 58.5


class NoSensorProvider(FakeProvider):
    def sensors_temperatures(self):
        raise AttributeError("unsupported")


def test_sample_machine_marks_thermal_sensors_unavailable(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()

    snapshot = sample_machine(
        (RootConfig("static", root),),
        provider=NoSensorProvider(),
        now=lambda: 1000.0,
        loadavg=lambda: (0.0, 0.0, 0.0),
        root_disk_path=root,
    )

    assert snapshot.temperatures.available is False
    assert snapshot.temperatures.readings == ()

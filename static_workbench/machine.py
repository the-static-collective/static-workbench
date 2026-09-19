from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

import psutil

from .config import RootConfig


class TelemetryProvider(Protocol):
    def cpu_percent(self, interval=None): ...
    def virtual_memory(self): ...
    def disk_usage(self, path): ...
    def boot_time(self): ...
    def sensors_temperatures(self): ...


@dataclass(frozen=True)
class MemoryStat:
    total: int
    used: int
    available: int
    percent: float


@dataclass(frozen=True)
class DiskStat:
    path: str
    total: int | None
    used: int | None
    free: int | None
    percent: float | None
    available: bool


@dataclass(frozen=True)
class RootDiskStat(DiskStat):
    root_id: str = ""


@dataclass(frozen=True)
class TemperatureReading:
    sensor: str
    label: str
    current_c: float
    high_c: float | None
    critical_c: float | None


@dataclass(frozen=True)
class TemperatureState:
    available: bool
    readings: tuple[TemperatureReading, ...]


@dataclass(frozen=True)
class MachineSnapshot:
    cpu_percent: float
    memory: MemoryStat
    root_disk: DiskStat
    configured_roots: tuple[RootDiskStat, ...]
    load_average: tuple[float, float, float] | None
    uptime_seconds: float
    temperatures: TemperatureState


def _disk(provider: TelemetryProvider, path: Path) -> DiskStat:
    try:
        usage = provider.disk_usage(str(path))
    except (OSError, FileNotFoundError):
        return DiskStat(str(path), None, None, None, None, False)
    return DiskStat(
        path=str(path),
        total=int(usage.total),
        used=int(usage.used),
        free=int(usage.free),
        percent=float(usage.percent),
        available=True,
    )


def _temperatures(provider: TelemetryProvider) -> TemperatureState:
    try:
        groups = provider.sensors_temperatures()
    except (AttributeError, OSError, NotImplementedError):
        return TemperatureState(False, ())
    if not groups:
        return TemperatureState(False, ())

    readings: list[TemperatureReading] = []
    for sensor, entries in sorted(groups.items()):
        for entry in entries:
            current = getattr(entry, "current", None)
            if current is None:
                continue
            readings.append(
                TemperatureReading(
                    sensor=str(sensor),
                    label=str(getattr(entry, "label", "") or sensor),
                    current_c=float(current),
                    high_c=(float(entry.high) if getattr(entry, "high", None) is not None else None),
                    critical_c=(
                        float(entry.critical)
                        if getattr(entry, "critical", None) is not None
                        else None
                    ),
                )
            )
    return TemperatureState(bool(readings), tuple(readings))


def sample_machine(
    roots: tuple[RootConfig, ...],
    *,
    provider: TelemetryProvider = psutil,
    now: Callable[[], float] = time.time,
    loadavg: Callable[[], tuple[float, float, float]] = os.getloadavg,
    root_disk_path: Path = Path("/"),
) -> MachineSnapshot:
    memory = provider.virtual_memory()
    memory_stat = MemoryStat(
        total=int(memory.total),
        used=int(memory.used),
        available=int(memory.available),
        percent=float(memory.percent),
    )

    root_disk = _disk(provider, root_disk_path)
    configured: list[RootDiskStat] = []
    for root in roots:
        disk = _disk(provider, root.path)
        configured.append(
            RootDiskStat(
                path=disk.path,
                total=disk.total,
                used=disk.used,
                free=disk.free,
                percent=disk.percent,
                available=disk.available,
                root_id=root.id,
            )
        )

    try:
        loads = tuple(float(value) for value in loadavg())
    except OSError:
        loads = None

    return MachineSnapshot(
        cpu_percent=float(provider.cpu_percent(interval=None)),
        memory=memory_stat,
        root_disk=root_disk,
        configured_roots=tuple(configured),
        load_average=loads,
        uptime_seconds=max(0.0, float(now()) - float(provider.boot_time())),
        temperatures=_temperatures(provider),
    )

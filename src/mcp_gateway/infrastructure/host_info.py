from __future__ import annotations

import os
import platform
import socket
from typing import Any

import psutil


class PsutilHostInfoProvider:
    def __init__(self, host_id: str, profile: str):
        self._host_id = host_id
        self._profile = profile

    def identity(self) -> dict[str, Any]:
        return {
            "host_id": self._host_id,
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "uid": os.getuid(),
            "euid": os.geteuid(),
            "profile": self._profile,
        }

    def status(self) -> dict[str, Any]:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return {
            "host_id": self._host_id,
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
            },
            "disk_root": {"total": disk.total, "free": disk.free, "percent": disk.percent},
            "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
        }

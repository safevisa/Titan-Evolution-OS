"""Xvfb sandbox lifecycle for one GUI automation run (M03 phase 1)."""
from __future__ import annotations

import os
import subprocess
import threading
from dataclasses import dataclass, field
from typing import Any

from app.settings import get_settings

_run_lock = threading.Lock()


@dataclass
class SandboxSession:
    display: str
    width: int
    height: int
    _proc: subprocess.Popen[bytes] | None = field(default=None, repr=False)

    def start(self) -> None:
        settings = get_settings()
        if self._proc is not None:
            return
        self._proc = subprocess.Popen(
            [
                "Xvfb",
                self.display,
                "-screen",
                "0",
                f"{self.width}x{self.height}x24",
                "-ac",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        os.environ["DISPLAY"] = self.display

    def stop(self) -> None:
        if self._proc is None:
            return
        try:
            self._proc.terminate()
            self._proc.wait(timeout=5)
        except Exception:
            try:
                self._proc.kill()
            except Exception:
                pass
        self._proc = None


def acquire_run_lock() -> threading.Lock:
    return _run_lock


def open_sandbox() -> SandboxSession:
    settings = get_settings()
    return SandboxSession(
        display=settings.xvfb_display,
        width=settings.screen_width,
        height=settings.screen_height,
    )

"""Hot reload watcher for blueprint.md."""

import os
import threading
import time
from pathlib import Path
from typing import Callable


class BlueprintWatcher:
    """Watches a file and calls a callback on changes."""

    def __init__(self, path: Path, callback: Callable[[], None], poll_interval: float = 1.0):
        self.path = path
        self.callback = callback
        self.poll_interval = poll_interval
        self._stop = threading.Event()
        self._last_mtime = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._last_mtime = self._get_mtime()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _get_mtime(self) -> float:
        try:
            return os.path.getmtime(self.path)
        except OSError:
            return 0.0

    def _run(self) -> None:
        while not self._stop.is_set():
            time.sleep(self.poll_interval)
            mtime = self._get_mtime()
            if self._last_mtime is None or mtime > self._last_mtime:
                self._last_mtime = mtime
                try:
                    self.callback()
                except Exception:
                    # Não queremos parar o watcher por conta de uma falha temporária
                    pass

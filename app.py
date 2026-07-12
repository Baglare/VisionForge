"""VisionForge PySide6 masaüstü uygulamasının başlangıç noktası."""

from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from runtime_paths import ensure_writable_directories, static_resource_path
from ui.main_window import MainWindow


def main() -> int:
    """Qt uygulamasını başlatır ve temiz kapanışı Qt event loop'una bırakır."""
    ensure_writable_directories()
    app = QApplication(sys.argv)
    icon_path = static_resource_path("assets", "branding", "visionforge.ico")
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

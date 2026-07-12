"""VisionForge PySide6 masaüstü uygulamasının başlangıç noktası."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main() -> int:
    """Qt uygulamasını başlatır ve temiz kapanışı Qt event loop'una bırakır."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

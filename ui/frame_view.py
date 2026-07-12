"""Kamera görüntüsünü en-boy oranını koruyarak gösteren Qt widget'ı."""

from __future__ import annotations

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QWidget


class FrameView(QWidget):
    """QImage karelerini letterbox ile gösterir."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._image: QImage | None = None
        self.setMinimumSize(640, 360)

    def set_image(self, image: QImage) -> None:
        """Yeni kamera karesini ayarlar."""
        self._image = image
        self.update()

    def paintEvent(self, event) -> None:
        """Görüntüyü widget alanına oranı bozmadan çizer."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(5, 9, 14))

        if self._image is None or self._image.isNull():
            painter.setPen(QColor(111, 129, 146))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Kamera akışı bekleniyor")
            return

        target = self._scaled_rect(self._image.width(), self._image.height())
        painter.drawImage(target, self._image)

    def _scaled_rect(self, image_width: int, image_height: int) -> QRect:
        """Letterbox hedef dikdörtgenini hesaplar."""
        available = self.rect()
        if image_width <= 0 or image_height <= 0:
            return available

        image_ratio = image_width / image_height
        view_ratio = max(1, available.width()) / max(1, available.height())

        if view_ratio > image_ratio:
            height = available.height()
            width = int(height * image_ratio)
        else:
            width = available.width()
            height = int(width / image_ratio)

        x = available.x() + (available.width() - width) // 2
        y = available.y() + (available.height() - height) // 2
        return QRect(x, y, width, height)

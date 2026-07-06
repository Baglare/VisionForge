# Kullanıcıya kısa süreli, spam yapmayan ekran bildirimleri üretir.

from dataclasses import dataclass
import time


@dataclass
class Notification:
    """Ekranda kısa süre gösterilecek tek bildirimi temsil eder."""

    message: str
    type: str = "info"
    duration: float = 2.6
    created_at: float = 0.0


class NotificationManager:
    """Önemli olayları kısa süreli toast bildirimlerine çevirir."""

    def __init__(self, max_visible: int = 3) -> None:
        self.max_visible = max_visible
        self._notifications: list[Notification] = []
        self._last_by_key: dict[str, float] = {}

    def notify(
        self,
        message: str,
        type: str = "info",
        duration: float = 2.6,
        key: str | None = None,
        min_interval: float = 1.5,
    ) -> None:
        """Yeni bildirim ekler; aynı anahtar kısa sürede tekrar edilirse yoksayar."""
        if not message:
            return

        now = time.monotonic()
        dedupe_key = key or f"{type}:{message}"
        last_time = self._last_by_key.get(dedupe_key)
        if last_time is not None and now - last_time < min_interval:
            return

        self._last_by_key[dedupe_key] = now
        self._notifications.append(
            Notification(
                message=message,
                type=type,
                duration=duration,
                created_at=now,
            )
        )
        self._cleanup(now)

    def active(self) -> list[Notification]:
        """Süresi dolmamış son bildirimleri döndürür."""
        now = time.monotonic()
        self._cleanup(now)
        return self._notifications[-self.max_visible :]

    def _cleanup(self, now: float) -> None:
        """Süresi dolmuş bildirimleri temizler."""
        self._notifications = [
            item
            for item in self._notifications
            if now - item.created_at <= item.duration
        ]

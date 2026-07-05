# El landmark verisinden basit büyü tetikleme durumunu üretir.

from dataclasses import dataclass
import math
import time


@dataclass
class SpellResult:
    """Tek karelik büyü motoru sonucunu temsil eder."""

    has_active_spell: bool
    active_spell_name: str | None
    status: str
    is_on_cooldown: bool
    progress: float


class SpellEngine:
    """İlk MVP büyü sistemi: açık ve sabit avuçtan Donma büyüsü üretir."""

    FREEZE_SPELL_NAME = "Donma"

    def __init__(
        self,
        hold_seconds: float = 0.8,
        cooldown_seconds: float = 2.0,
        effect_seconds: float = 1.1,
    ) -> None:
        self.status = "Avuç mührü bekleniyor"
        self.hold_seconds = hold_seconds
        self.cooldown_seconds = cooldown_seconds
        self.effect_seconds = effect_seconds
        self._pose_started_at: float | None = None
        self._last_palm_center: tuple[float, float, float] | None = None
        self._cooldown_until = 0.0
        self._active_until = 0.0

    def update(self, hand_result, now: float | None = None) -> SpellResult:
        """El algılama sonucuna göre Donma büyüsü durumunu günceller."""
        current_time = now if now is not None else time.monotonic()

        if hand_result is not None and not hand_result.is_active:
            self._pose_started_at = None
            self._last_palm_center = None
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="El algılama pasif",
                is_on_cooldown=False,
                progress=0.0,
            )

        if current_time < self._active_until:
            return self._result(
                has_active_spell=True,
                active_spell_name=self.FREEZE_SPELL_NAME,
                status="Donma büyüsü aktif",
                is_on_cooldown=current_time < self._cooldown_until,
                progress=1.0,
            )

        is_on_cooldown = current_time < self._cooldown_until
        if is_on_cooldown:
            self._pose_started_at = None
            self._last_palm_center = None
            remaining = self._cooldown_until - current_time
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status=f"Bekleme süresi: {remaining:.1f} sn",
                is_on_cooldown=True,
                progress=0.0,
            )

        palm_center = self._open_palm_center(hand_result)
        if palm_center is None:
            self._pose_started_at = None
            self._last_palm_center = None
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Avuç mührü bekleniyor",
                is_on_cooldown=False,
                progress=0.0,
            )

        if (
            self._last_palm_center is not None
            and self._distance(palm_center, self._last_palm_center) > 0.08
        ):
            self._pose_started_at = current_time

        self._last_palm_center = palm_center

        if self._pose_started_at is None:
            self._pose_started_at = current_time

        held_seconds = current_time - self._pose_started_at
        progress = min(1.0, held_seconds / self.hold_seconds)

        if progress >= 1.0:
            self._pose_started_at = None
            self._last_palm_center = None
            self._active_until = current_time + self.effect_seconds
            self._cooldown_until = current_time + self.cooldown_seconds
            return self._result(
                has_active_spell=True,
                active_spell_name=self.FREEZE_SPELL_NAME,
                status="Donma büyüsü aktif",
                is_on_cooldown=True,
                progress=1.0,
            )

        return self._result(
            has_active_spell=False,
            active_spell_name=None,
            status="Avuç mührü hazırlanıyor",
            is_on_cooldown=False,
            progress=progress,
        )

    def list_available_spells(self, profile) -> list[str]:
        """Profilde açık olan büyüleri döndürür."""
        return profile.unlocked_spells

    def _result(
        self,
        has_active_spell: bool,
        active_spell_name: str | None,
        status: str,
        is_on_cooldown: bool,
        progress: float,
    ) -> SpellResult:
        """Sonucu saklar ve çağırana döndürür."""
        self.status = status
        return SpellResult(
            has_active_spell=has_active_spell,
            active_spell_name=active_spell_name,
            status=status,
            is_on_cooldown=is_on_cooldown,
            progress=max(0.0, min(1.0, progress)),
        )

    def _open_palm_center(self, hand_result) -> tuple[float, float, float] | None:
        """Açık ve kullanılabilir ilk avucun merkez noktasını döndürür."""
        if not hand_result or not hand_result.detected or not hand_result.hands:
            return None

        for hand in hand_result.hands:
            if self._is_open_hand(hand.landmarks):
                palm_indices = [0, 5, 9, 13, 17]
                return self._average_point([hand.landmarks[index] for index in palm_indices])

        return None

    def _is_open_hand(self, landmarks: list[tuple[float, float, float]]) -> bool:
        """Parmak uçları avuç merkezinden yeterince açıksa eli açık kabul eder."""
        if len(landmarks) < 21:
            return False

        palm_indices = [0, 5, 9, 13, 17]
        palm_center = self._average_point([landmarks[index] for index in palm_indices])
        palm_width = self._distance(landmarks[5], landmarks[17])
        if palm_width <= 0:
            return False

        fingertip_indices = [4, 8, 12, 16, 20]
        finger_base_indices = [2, 6, 10, 14, 18]
        extended_fingers = 0

        for tip_index, base_index in zip(fingertip_indices, finger_base_indices):
            tip_distance = self._distance(landmarks[tip_index], palm_center)
            base_distance = self._distance(landmarks[base_index], palm_center)
            if tip_distance > base_distance + palm_width * 0.18:
                extended_fingers += 1

        return extended_fingers >= 4

    def _average_point(self, points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
        """Verilen noktaların ortalamasını döndürür."""
        count = len(points)
        return (
            sum(point[0] for point in points) / count,
            sum(point[1] for point in points) / count,
            sum(point[2] for point in points) / count,
        )

    def _distance(self, first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
        """İki normalize landmark noktası arasındaki 2B mesafeyi hesaplar."""
        return math.hypot(first[0] - second[0], first[1] - second[1])

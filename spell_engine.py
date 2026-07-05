# El landmark verisinden basit büyü tetikleme durumunu üretir.

from collections import deque
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
    cooldown_remaining: float = 0.0


class SpellEngine:
    """İlk MVP büyü sistemi: Donma, Ateş ve Kalkan büyülerini üretir."""

    FREEZE_SPELL_NAME = "Donma"
    FIRE_SPELL_NAME = "Ateş"
    SHIELD_SPELL_NAME = "Kalkan"

    def __init__(
        self,
        freeze_hold_seconds: float = 0.8,
        shield_hold_seconds: float = 0.8,
        cooldown_seconds: float = 2.0,
        effect_seconds: float = 1.1,
        fire_history_seconds: float = 1.3,
        fire_seal_window_seconds: float = 0.8,
    ) -> None:
        self.status = "Ateş savurması bekleniyor"
        self.freeze_hold_seconds = freeze_hold_seconds
        self.shield_hold_seconds = shield_hold_seconds
        self.cooldown_seconds = cooldown_seconds
        self.effect_seconds = effect_seconds
        self.fire_history_seconds = fire_history_seconds
        self.fire_seal_window_seconds = fire_seal_window_seconds
        self._freeze_started_at: float | None = None
        self._shield_started_at: float | None = None
        self._last_palm_center: tuple[float, float, float] | None = None
        self._hand_center_history: deque[tuple[float, tuple[float, float, float]]] = deque()
        self._fire_seal_until = 0.0
        self._cooldown_until = 0.0
        self._active_until = 0.0
        self._active_spell_name: str | None = None

    def update(self, hand_result, now: float | None = None) -> SpellResult:
        """El algılama sonucuna göre büyü durumunu günceller."""
        current_time = now if now is not None else time.monotonic()

        if hand_result is not None and not hand_result.is_active:
            self._reset_gesture_state()
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="El algılama pasif",
                is_on_cooldown=False,
                progress=0.0,
            )

        if current_time < self._active_until and self._active_spell_name:
            return self._result(
                has_active_spell=True,
                active_spell_name=self._active_spell_name,
                status=f"{self._active_spell_name} büyüsü aktif",
                is_on_cooldown=current_time < self._cooldown_until,
                progress=1.0,
                cooldown_remaining=max(0.0, self._cooldown_until - current_time),
            )

        self._active_spell_name = None

        if current_time < self._cooldown_until:
            self._reset_gesture_state()
            remaining = self._cooldown_until - current_time
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status=f"Bekleme süresi: {remaining:.1f} sn",
                is_on_cooldown=True,
                progress=0.0,
                cooldown_remaining=remaining,
            )

        hand_center = self._hand_center(hand_result)
        open_palm_center = self._open_palm_center(hand_result)
        if hand_center is None:
            self._reset_gesture_state(keep_history=False)
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Ateş savurması bekleniyor",
                is_on_cooldown=False,
                progress=0.0,
            )

        self._remember_hand_center(current_time, hand_center)

        open_palm_centers = self._open_palm_centers(hand_result)
        shield_result = self._update_shield_spell(current_time, hand_result, open_palm_centers)
        if shield_result is not None:
            return shield_result

        fire_result = self._update_fire_spell(current_time, open_palm_center)
        if fire_result is not None:
            return fire_result

        return self._update_freeze_spell(current_time, open_palm_center)

    def list_available_spells(self, profile) -> list[str]:
        """Profilde açık olan büyüleri döndürür."""
        return profile.unlocked_spells

    def _update_shield_spell(
        self,
        current_time: float,
        hand_result,
        open_palm_centers: list[tuple[float, float, float]],
    ) -> SpellResult | None:
        """İki açık el pozundan Kalkan büyüsünü üretir."""
        two_hands_visible = bool(hand_result and hand_result.hand_count >= 2)
        two_open_hands = len(open_palm_centers) >= 2

        if not two_hands_visible:
            self._shield_started_at = None
            return None

        self._freeze_started_at = None
        self._last_palm_center = None

        if not two_open_hands:
            self._shield_started_at = None
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Kalkan mührü bekleniyor",
                is_on_cooldown=False,
                progress=0.0,
            )

        if self._shield_started_at is None:
            self._shield_started_at = current_time

        held_seconds = current_time - self._shield_started_at
        progress = min(1.0, held_seconds / self.shield_hold_seconds)

        if progress >= 1.0:
            return self._activate_spell(self.SHIELD_SPELL_NAME, current_time)

        return self._result(
            has_active_spell=False,
            active_spell_name=None,
            status="Kalkan mührü bekleniyor",
            is_on_cooldown=False,
            progress=progress,
        )

    def _update_fire_spell(
        self,
        current_time: float,
        open_palm_center: tuple[float, float, float] | None,
    ) -> SpellResult | None:
        """Yatay savurma + açık avuç zincirinden Ateş büyüsünü üretir."""
        if self._fire_seal_until >= current_time:
            progress = 1.0 - max(0.0, self._fire_seal_until - current_time) / self.fire_seal_window_seconds
            self._freeze_started_at = None
            self._last_palm_center = None

            if open_palm_center is not None:
                return self._activate_spell(self.FIRE_SPELL_NAME, current_time)

            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Ateş mührü bekleniyor",
                is_on_cooldown=False,
                progress=progress,
            )

        self._fire_seal_until = 0.0
        if self._has_horizontal_swipe():
            self._fire_seal_until = current_time + self.fire_seal_window_seconds
            self._freeze_started_at = None
            self._last_palm_center = None
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Ateş mührü bekleniyor",
                is_on_cooldown=False,
                progress=0.0,
            )

        return None

    def _update_freeze_spell(
        self,
        current_time: float,
        open_palm_center: tuple[float, float, float] | None,
    ) -> SpellResult:
        """Açık ve kısa süre sabit avuçtan Donma büyüsünü üretir."""
        if open_palm_center is None:
            self._freeze_started_at = None
            self._last_palm_center = None
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Ateş savurması bekleniyor",
                is_on_cooldown=False,
                progress=0.0,
            )

        if (
            self._last_palm_center is not None
            and self._distance(open_palm_center, self._last_palm_center) > 0.08
        ):
            self._freeze_started_at = current_time

        self._last_palm_center = open_palm_center

        if self._freeze_started_at is None:
            self._freeze_started_at = current_time

        held_seconds = current_time - self._freeze_started_at
        progress = min(1.0, held_seconds / self.freeze_hold_seconds)

        if progress >= 1.0:
            return self._activate_spell(self.FREEZE_SPELL_NAME, current_time)

        return self._result(
            has_active_spell=False,
            active_spell_name=None,
            status="Avuç mührü hazırlanıyor",
            is_on_cooldown=False,
            progress=progress,
        )

    def _activate_spell(self, spell_name: str, current_time: float) -> SpellResult:
        """Büyüyü aktif eder ve ortak cooldown başlatır."""
        self._reset_gesture_state()
        self._active_spell_name = spell_name
        self._active_until = current_time + self.effect_seconds
        self._cooldown_until = current_time + self.cooldown_seconds
        return self._result(
            has_active_spell=True,
            active_spell_name=spell_name,
            status=f"{spell_name} büyüsü aktif",
            is_on_cooldown=True,
            progress=1.0,
            cooldown_remaining=self.cooldown_seconds,
        )

    def _result(
        self,
        has_active_spell: bool,
        active_spell_name: str | None,
        status: str,
        is_on_cooldown: bool,
        progress: float,
        cooldown_remaining: float = 0.0,
    ) -> SpellResult:
        """Sonucu saklar ve çağırana döndürür."""
        self.status = status
        return SpellResult(
            has_active_spell=has_active_spell,
            active_spell_name=active_spell_name,
            status=status,
            is_on_cooldown=is_on_cooldown,
            progress=max(0.0, min(1.0, progress)),
            cooldown_remaining=max(0.0, cooldown_remaining),
        )

    def _remember_hand_center(
        self,
        current_time: float,
        hand_center: tuple[float, float, float],
    ) -> None:
        """Son el merkezi geçmişini zaman penceresi içinde tutar."""
        self._hand_center_history.append((current_time, hand_center))
        min_time = current_time - self.fire_history_seconds
        while self._hand_center_history and self._hand_center_history[0][0] < min_time:
            self._hand_center_history.popleft()

    def _has_horizontal_swipe(self) -> bool:
        """Küçük titreşimleri dışlayarak belirgin yatay savurma arar."""
        if len(self._hand_center_history) < 5:
            return False

        first_time, first_center = self._hand_center_history[0]
        last_time, last_center = self._hand_center_history[-1]
        elapsed = last_time - first_time
        if elapsed < 0.18:
            return False

        horizontal_delta = abs(last_center[0] - first_center[0])
        vertical_delta = abs(last_center[1] - first_center[1])

        if horizontal_delta < 0.22:
            return False

        if vertical_delta > 0.18:
            return False

        return horizontal_delta > vertical_delta * 1.8

    def _hand_center(self, hand_result) -> tuple[float, float, float] | None:
        """Algılanan ilk elin yaklaşık merkez noktasını döndürür."""
        if not hand_result or not hand_result.detected or not hand_result.hands:
            return None

        landmarks = hand_result.hands[0].landmarks
        if len(landmarks) < 21:
            return None

        center_indices = [0, 5, 9, 13, 17]
        return self._average_point([landmarks[index] for index in center_indices])

    def _open_palm_center(self, hand_result) -> tuple[float, float, float] | None:
        """Açık ve kullanılabilir ilk avucun merkez noktasını döndürür."""
        centers = self._open_palm_centers(hand_result)
        return centers[0] if centers else None

    def _open_palm_centers(self, hand_result) -> list[tuple[float, float, float]]:
        """Açık ve kullanılabilir avuç merkezlerini döndürür."""
        if not hand_result or not hand_result.detected or not hand_result.hands:
            return []

        centers: list[tuple[float, float, float]] = []
        for hand in hand_result.hands:
            if self._is_open_hand(hand.landmarks):
                palm_indices = [0, 5, 9, 13, 17]
                centers.append(self._average_point([hand.landmarks[index] for index in palm_indices]))

        return centers

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

    def _reset_gesture_state(self, keep_history: bool = True) -> None:
        """Devam eden büyü hazırlık durumlarını temizler."""
        self._freeze_started_at = None
        self._shield_started_at = None
        self._last_palm_center = None
        self._fire_seal_until = 0.0
        if not keep_history:
            self._hand_center_history.clear()

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

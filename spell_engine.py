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
    message: str = ""
    palm_open_score: float = 0.0
    freeze_stability_score: float = 0.0
    fire_horizontal_distance: float = 0.0
    fire_swing_detected: bool = False
    shield_two_hand_score: float = 0.0
    spell_prepare_progress: float = 0.0
    locked_spell_attempt: str = ""


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
        self._locked_message_until = 0.0
        self._locked_spell_attempt = ""
        self._palm_open_history: deque[bool] = deque(maxlen=10)
        self._two_hand_history: deque[bool] = deque(maxlen=10)
        self._two_open_hand_history: deque[bool] = deque(maxlen=10)
        self._freeze_missing_frames = 0
        self._debug_scores = self._empty_debug_scores()

    def update(
        self,
        hand_result,
        allowed_spells: list[str] | None = None,
        detection_profile: str = "Dengeli",
        now: float | None = None,
    ) -> SpellResult:
        """El algılama sonucuna göre büyü durumunu günceller."""
        current_time = now if now is not None else time.monotonic()
        profile = self._profile_config(detection_profile)
        allowed_spells = allowed_spells or [
            self.FREEZE_SPELL_NAME,
            self.FIRE_SPELL_NAME,
            self.SHIELD_SPELL_NAME,
        ]

        if hand_result is not None and not hand_result.is_active:
            self._reset_gesture_state()
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="El algılama pasif",
                is_on_cooldown=False,
                progress=0.0,
            )

        if current_time < self._locked_message_until:
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Lonca yetkisi yetersiz",
                is_on_cooldown=False,
                progress=0.0,
                message="Büyü kilitli",
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
        raw_open_palm_centers = self._open_palm_centers(hand_result)
        open_palm_center = raw_open_palm_centers[0] if raw_open_palm_centers else None
        self._update_smoothing_scores(hand_result, raw_open_palm_centers, profile)
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

        shield_result = self._update_shield_spell(
            current_time,
            hand_result,
            raw_open_palm_centers,
            allowed_spells,
            profile,
        )
        if shield_result is not None:
            return shield_result

        fire_result = self._update_fire_spell(current_time, open_palm_center, allowed_spells, profile)
        if fire_result is not None:
            return fire_result

        return self._update_freeze_spell(current_time, open_palm_center, allowed_spells, profile)

    def list_available_spells(self, profile) -> list[str]:
        """Profilde açık olan büyüleri döndürür."""
        return profile.unlocked_spells

    def _update_shield_spell(
        self,
        current_time: float,
        hand_result,
        open_palm_centers: list[tuple[float, float, float]],
        allowed_spells: list[str],
        profile: dict,
    ) -> SpellResult | None:
        """İki açık el pozundan Kalkan büyüsünü üretir."""
        two_hands_visible = bool(hand_result and hand_result.hand_count >= 2)
        two_open_hands = len(open_palm_centers) >= 2
        shield_score = self._debug_scores["shield_two_hand_score"]

        if not two_hands_visible:
            self._shield_started_at = None
            return None

        self._freeze_started_at = None
        self._last_palm_center = None

        if not two_open_hands or shield_score < profile["shield_score_threshold"]:
            self._shield_started_at = None
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Kalkan mührü bekleniyor",
                is_on_cooldown=False,
                progress=min(0.5, shield_score),
            )

        if self._shield_started_at is None:
            self._shield_started_at = current_time

        held_seconds = current_time - self._shield_started_at
        progress = min(1.0, held_seconds / profile["shield_hold_seconds"])

        if progress >= 1.0:
            return self._activate_spell(self.SHIELD_SPELL_NAME, current_time, allowed_spells)

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
        allowed_spells: list[str],
        profile: dict,
    ) -> SpellResult | None:
        """Yatay savurma + açık avuç zincirinden Ateş büyüsünü üretir."""
        if self._fire_seal_until >= current_time:
            progress = 1.0 - max(0.0, self._fire_seal_until - current_time) / profile["fire_seal_window_seconds"]
            self._freeze_started_at = None
            self._last_palm_center = None

            if open_palm_center is not None and self._debug_scores["palm_open_score"] >= profile["palm_score_threshold"]:
                return self._activate_spell(self.FIRE_SPELL_NAME, current_time, allowed_spells)

            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Ateş mührü bekleniyor",
                is_on_cooldown=False,
                progress=progress,
            )

        self._fire_seal_until = 0.0
        if self._has_horizontal_swipe(profile):
            self._debug_scores["fire_swing_detected"] = True
            self._fire_seal_until = current_time + profile["fire_seal_window_seconds"]
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
        allowed_spells: list[str],
        profile: dict,
    ) -> SpellResult:
        """Açık ve kısa süre sabit avuçtan Donma büyüsünü üretir."""
        palm_score = self._debug_scores["palm_open_score"]
        if open_palm_center is None or palm_score < profile["palm_score_threshold"]:
            self._freeze_missing_frames += 1
            if self._freeze_missing_frames > profile["freeze_missing_tolerance"]:
                self._freeze_started_at = None
                self._last_palm_center = None
            self._last_palm_center = None
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Ateş savurması bekleniyor",
                is_on_cooldown=False,
                progress=0.0 if self._freeze_started_at is None else palm_score * 0.35,
            )

        self._freeze_missing_frames = 0
        stability_score = 1.0
        if (
            self._last_palm_center is not None
            and self._distance(open_palm_center, self._last_palm_center) > profile["freeze_stability_distance"]
        ):
            stability_score = 0.0
            self._freeze_started_at = current_time

        self._debug_scores["freeze_stability_score"] = stability_score
        self._last_palm_center = open_palm_center

        if self._freeze_started_at is None:
            self._freeze_started_at = current_time

        held_seconds = current_time - self._freeze_started_at
        progress = min(1.0, held_seconds / profile["freeze_hold_seconds"])
        progress = min(progress, (palm_score + stability_score) / 2)

        if progress >= 1.0:
            return self._activate_spell(self.FREEZE_SPELL_NAME, current_time, allowed_spells)

        return self._result(
            has_active_spell=False,
            active_spell_name=None,
            status="Avuç mührü hazırlanıyor",
            is_on_cooldown=False,
            progress=progress,
        )

    def _activate_spell(
        self,
        spell_name: str,
        current_time: float,
        allowed_spells: list[str],
    ) -> SpellResult:
        """Büyüyü aktif eder ve ortak cooldown başlatır."""
        self._reset_gesture_state()
        if spell_name not in allowed_spells:
            self._locked_message_until = current_time + 1.2
            self._locked_spell_attempt = spell_name
            return self._result(
                has_active_spell=False,
                active_spell_name=None,
                status="Lonca yetkisi yetersiz",
                is_on_cooldown=False,
                progress=0.0,
                message="Büyü kilitli",
            )

        self._active_spell_name = spell_name
        self._locked_spell_attempt = ""
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
        message: str = "",
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
            message=message,
            palm_open_score=self._debug_scores["palm_open_score"],
            freeze_stability_score=self._debug_scores["freeze_stability_score"],
            fire_horizontal_distance=self._debug_scores["fire_horizontal_distance"],
            fire_swing_detected=self._debug_scores["fire_swing_detected"],
            shield_two_hand_score=self._debug_scores["shield_two_hand_score"],
            spell_prepare_progress=max(0.0, min(1.0, progress)),
            locked_spell_attempt=self._locked_spell_attempt,
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

    def _has_horizontal_swipe(self, profile: dict) -> bool:
        """Küçük titreşimleri dışlayarak belirgin yatay savurma arar."""
        self._debug_scores["fire_horizontal_distance"] = self._horizontal_swipe_distance()
        self._debug_scores["fire_swing_detected"] = False
        if len(self._hand_center_history) < 5:
            return False

        first_time, first_center = self._hand_center_history[0]
        last_time, last_center = self._hand_center_history[-1]
        elapsed = last_time - first_time
        if elapsed < profile["fire_min_elapsed"]:
            return False

        horizontal_delta = abs(last_center[0] - first_center[0])
        vertical_delta = abs(last_center[1] - first_center[1])
        self._debug_scores["fire_horizontal_distance"] = horizontal_delta

        if horizontal_delta < profile["fire_min_horizontal_distance"]:
            return False

        if vertical_delta > profile["fire_max_vertical_distance"]:
            return False

        return horizontal_delta > vertical_delta * profile["fire_direction_ratio"]

    def _horizontal_swipe_distance(self) -> float:
        """Debug için mevcut el geçmişindeki yatay mesafeyi döndürür."""
        if len(self._hand_center_history) < 2:
            return 0.0
        return abs(self._hand_center_history[-1][1][0] - self._hand_center_history[0][1][0])

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

    def _update_smoothing_scores(self, hand_result, open_palm_centers, profile: dict) -> None:
        """Tek karelik el kararlarını kısa geçmiş skorlarına dönüştürür."""
        hand_detected = bool(hand_result and hand_result.detected and hand_result.hands)
        two_hands_visible = bool(hand_result and hand_result.hand_count >= 2)
        palm_open = hand_detected and len(open_palm_centers) >= 1
        two_open_hands = two_hands_visible and len(open_palm_centers) >= 2

        self._palm_open_history.append(palm_open)
        self._two_hand_history.append(two_hands_visible)
        self._two_open_hand_history.append(two_open_hands)

        self._debug_scores["palm_open_score"] = self._history_score(self._palm_open_history)
        two_hand_score = self._history_score(self._two_hand_history)
        two_open_score = self._history_score(self._two_open_hand_history)
        self._debug_scores["shield_two_hand_score"] = min(two_hand_score, two_open_score)

    def _history_score(self, history: deque[bool]) -> float:
        """Boolean geçmişten 0-1 arası oran döndürür."""
        if not history:
            return 0.0
        return sum(1 for item in history if item) / len(history)

    def _profile_config(self, detection_profile: str) -> dict:
        """Algılama profiline göre büyü karar eşiklerini döndürür."""
        configs = {
            "Hassas": {
                "palm_score_threshold": 0.45,
                "shield_score_threshold": 0.45,
                "freeze_hold_seconds": 0.65,
                "shield_hold_seconds": 0.65,
                "freeze_stability_distance": 0.10,
                "freeze_missing_tolerance": 4,
                "fire_min_elapsed": 0.16,
                "fire_min_horizontal_distance": 0.18,
                "fire_max_vertical_distance": 0.22,
                "fire_direction_ratio": 1.45,
                "fire_seal_window_seconds": 0.95,
            },
            "Dengeli": {
                "palm_score_threshold": 0.58,
                "shield_score_threshold": 0.58,
                "freeze_hold_seconds": self.freeze_hold_seconds,
                "shield_hold_seconds": self.shield_hold_seconds,
                "freeze_stability_distance": 0.08,
                "freeze_missing_tolerance": 3,
                "fire_min_elapsed": 0.18,
                "fire_min_horizontal_distance": 0.22,
                "fire_max_vertical_distance": 0.18,
                "fire_direction_ratio": 1.8,
                "fire_seal_window_seconds": self.fire_seal_window_seconds,
            },
            "Kararlı": {
                "palm_score_threshold": 0.72,
                "shield_score_threshold": 0.72,
                "freeze_hold_seconds": 0.95,
                "shield_hold_seconds": 0.95,
                "freeze_stability_distance": 0.055,
                "freeze_missing_tolerance": 2,
                "fire_min_elapsed": 0.22,
                "fire_min_horizontal_distance": 0.28,
                "fire_max_vertical_distance": 0.14,
                "fire_direction_ratio": 2.2,
                "fire_seal_window_seconds": 0.65,
            },
        }
        return configs.get(detection_profile, configs["Dengeli"])

    def _empty_debug_scores(self) -> dict:
        """Büyü karar debug skorlarının varsayılanlarını döndürür."""
        return {
            "palm_open_score": 0.0,
            "freeze_stability_score": 0.0,
            "fire_horizontal_distance": 0.0,
            "fire_swing_detected": False,
            "shield_two_hand_score": 0.0,
        }

    def _reset_gesture_state(self, keep_history: bool = True) -> None:
        """Devam eden büyü hazırlık durumlarını temizler."""
        self._freeze_started_at = None
        self._shield_started_at = None
        self._last_palm_center = None
        self._fire_seal_until = 0.0
        self._freeze_missing_frames = 0
        if not keep_history:
            self._hand_center_history.clear()
            self._palm_open_history.clear()
            self._two_hand_history.clear()
            self._two_open_hand_history.clear()
            self._debug_scores = self._empty_debug_scores()

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

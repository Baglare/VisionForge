"""Tam doğrulanmış kullanıcı için kısa süreli yüz kaybı toleransı yönetir."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import time


GRACE_PERIOD_SECONDS = 10.0


class VerificationSessionState(StrEnum):
    """Doğrulama oturumunun UI ve debug tarafına açık durumları."""

    UNAUTHENTICATED = "UNAUTHENTICATED"
    PENDING_SEAL = "PENDING_SEAL"
    VERIFIED = "VERIFIED"
    GRACE_PERIOD = "GRACE_PERIOD"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class VerificationSessionSnapshot:
    """Tek karede UI ve debug tarafına aktarılacak oturum özeti."""

    session_state: str
    verified_face_label: str | None
    is_grace_active: bool
    grace_remaining_seconds: float
    last_seen_time: float | None
    verification_status: str


class VerificationSession:
    """Stabil yüz doğrulaması sonrasında oturumu süre temelli korur."""

    def __init__(self, grace_period_seconds: float = GRACE_PERIOD_SECONDS) -> None:
        self.grace_period_seconds = float(grace_period_seconds)
        self._state = VerificationSessionState.UNAUTHENTICATED
        self._verified_face_label: str | None = None
        self._last_seen_time: float | None = None
        self._grace_started_at: float | None = None

    @property
    def state(self) -> VerificationSessionState:
        """Güncel oturum durumunu döndürür."""
        return self._state

    @property
    def verified_face_label(self) -> str | None:
        """Tam doğrulanmış kullanıcının yüz etiketini döndürür."""
        return self._verified_face_label

    def reset(self) -> VerificationSessionSnapshot:
        """Oturumu güvenli şekilde temizler."""
        self._state = VerificationSessionState.UNAUTHENTICATED
        self._verified_face_label = None
        self._last_seen_time = None
        self._grace_started_at = None
        return self.snapshot()

    def update(
        self,
        *,
        stable_face_label: str | None,
        full_verified_label: str | None,
        now: float | None = None,
        pending_label: str | None = None,
    ) -> VerificationSessionSnapshot:
        """Stabil yüz ve tam doğrulama bilgisiyle oturumu günceller."""
        current_time = time.monotonic() if now is None else float(now)

        if self._verified_face_label and stable_face_label:
            if stable_face_label != self._verified_face_label:
                self.reset()

        if full_verified_label:
            self._mark_verified(full_verified_label, current_time)
            return self.snapshot(current_time)

        if self._state == VerificationSessionState.VERIFIED:
            if stable_face_label == self._verified_face_label:
                self._last_seen_time = current_time
                return self.snapshot(current_time)

            self._state = VerificationSessionState.GRACE_PERIOD
            self._grace_started_at = current_time
            return self.snapshot(current_time)

        if self._state == VerificationSessionState.GRACE_PERIOD:
            if stable_face_label == self._verified_face_label:
                self._mark_verified(stable_face_label, current_time)
                return self.snapshot(current_time)

            if self._grace_remaining(current_time) > 0:
                return self.snapshot(current_time)

            self._state = VerificationSessionState.EXPIRED
            self._verified_face_label = None
            self._last_seen_time = None
            self._grace_started_at = None
            return self.snapshot(current_time)

        pending_face_label = pending_label or stable_face_label
        if pending_face_label:
            self._state = VerificationSessionState.PENDING_SEAL
            return self.snapshot(current_time)

        if self._state == VerificationSessionState.EXPIRED:
            return self.snapshot(current_time)

        self._state = VerificationSessionState.UNAUTHENTICATED
        return self.snapshot(current_time)

    def snapshot(self, now: float | None = None) -> VerificationSessionSnapshot:
        """Mevcut oturum bilgisini veri nesnesi olarak döndürür."""
        current_time = time.monotonic() if now is None else float(now)
        grace_remaining = self._grace_remaining(current_time)
        return VerificationSessionSnapshot(
            session_state=self._state.value,
            verified_face_label=self._verified_face_label,
            is_grace_active=self._state == VerificationSessionState.GRACE_PERIOD and grace_remaining > 0,
            grace_remaining_seconds=grace_remaining,
            last_seen_time=self._last_seen_time,
            verification_status=self._verification_status(grace_remaining),
        )

    def _mark_verified(self, face_label: str, now: float) -> None:
        """Kullanıcıyı tam doğrulanmış olarak işaretler."""
        self._state = VerificationSessionState.VERIFIED
        self._verified_face_label = face_label
        self._last_seen_time = now
        self._grace_started_at = None

    def _grace_remaining(self, now: float) -> float:
        """Grace period için kalan saniyeyi döndürür."""
        if self._grace_started_at is None:
            return 0.0
        elapsed = max(0.0, now - self._grace_started_at)
        return max(0.0, self.grace_period_seconds - elapsed)

    def _verification_status(self, grace_remaining: float) -> str:
        """UI için kısa doğrulama durumunu üretir."""
        if self._state == VerificationSessionState.VERIFIED:
            return "Doğrulandı"
        if self._state == VerificationSessionState.GRACE_PERIOD and grace_remaining > 0:
            return "Oturum korunuyor"
        if self._state == VerificationSessionState.EXPIRED:
            return "Doğrulama süresi doldu"
        if self._state == VerificationSessionState.PENDING_SEAL:
            return "Yüz tanındı, mühür bekleniyor"
        return "Bekleniyor"

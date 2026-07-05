# Kamera görüntüsündeki QR tabanlı lonca mührünü okur.

from dataclasses import dataclass

import cv2

from guild_profile import GuildProfile, find_profile_by_seal_code


@dataclass
class GuildSealResult:
    """Tek karelik lonca mührü okuma sonucunu temsil eder."""

    detected: bool
    code: str | None = None
    matched: bool = False
    mismatch: bool = False
    message: str = ""


class GuildSealDetector:
    """OpenCV QRCodeDetector ile lonca mührü kodu okur."""

    def __init__(self) -> None:
        self._detector = cv2.QRCodeDetector()

    def detect(self, frame, candidate_profile: GuildProfile | None = None) -> GuildSealResult:
        """Kameradaki QR kodu okur ve aday profille eşleşmeyi kontrol eder."""
        if frame is None:
            return GuildSealResult(detected=False)

        try:
            code, _, _ = self._detector.detectAndDecode(frame)
        except Exception as error:
            return GuildSealResult(detected=False, message=f"Lonca mührü okunamadı: {error}")

        code = code.strip() if code else ""
        if not code:
            return GuildSealResult(detected=False)

        seal_profile = find_profile_by_seal_code(code)
        if candidate_profile and candidate_profile.guild_seal_code:
            if code == candidate_profile.guild_seal_code:
                return GuildSealResult(detected=True, code=code, matched=True)
            if seal_profile is not None:
                return GuildSealResult(
                    detected=True,
                    code=code,
                    matched=False,
                    mismatch=True,
                    message="Mühür kullanıcıyla eşleşmedi",
                )

        return GuildSealResult(
            detected=True,
            code=code,
            matched=False,
            mismatch=seal_profile is not None,
            message="Mühür kullanıcıyla eşleşmedi" if seal_profile is not None else "Bilinmeyen lonca mührü",
        )

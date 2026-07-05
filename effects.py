# Kamera görüntüsü üzerine basit lonca/profil arayüzü çizer.

import cv2


class Effects:
    """Profil paneli ve ileride eklenecek görsel efektler için temel sınıf."""

    def __init__(self) -> None:
        self.status = "hazır"

    def draw_profile_panel(self, frame, profile, status_text: str = "Kamera modu aktif"):
        """Canlı kamera karesinin üzerine basit bir profil paneli çizer."""
        frame_width = frame.shape[1]
        panel_x = 24
        panel_y = 24
        panel_width = min(560, max(320, frame_width - 48))
        panel_height = 155
        padding = 18

        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (25, 25, 35),
            -1,
        )
        cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)

        cv2.rectangle(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (120, 190, 255),
            2,
        )

        lines = [
            profile.rank,
            profile.username,
            f"Açık Büyüler: {', '.join(profile.unlocked_spells)}",
            f"Durum: {status_text}",
        ]

        text_x = panel_x + padding
        text_y = panel_y + 34

        for index, line in enumerate(lines):
            color = (245, 245, 245) if index != 0 else (120, 220, 255)
            self._draw_text_fit(
                frame=frame,
                text=line,
                origin=(text_x, text_y + index * 30),
                max_width=panel_width - padding * 2,
                color=color,
            )

        return frame

    def draw_face_box(self, frame, box: tuple[int, int, int, int] | None):
        """Algılanan yüzün etrafına sade bir kutu çizer."""
        if box is None:
            return frame

        x, y, width, height = box
        cv2.rectangle(
            frame,
            (x, y),
            (x + width, y + height),
            (120, 220, 255),
            2,
        )
        return frame

    def _draw_text_fit(self, frame, text: str, origin: tuple[int, int], max_width: int, color) -> None:
        """Metni panel genişliğine göre küçük adımlarla sığdırır."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.68
        thickness = 2

        while font_scale > 0.42:
            text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
            if text_size[0] <= max_width:
                break
            font_scale -= 0.04

        cv2.putText(
            frame,
            text,
            origin,
            font,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA,
        )

    def apply_profile_effect(self, frame, profile):
        """Profil görünümüne efekt uygulamak için yer tutucu."""
        return self.draw_profile_panel(frame, profile)

    def apply_spell_effect(self, frame, spell_name: str):
        """Büyü etkisini görüntüye uygulamak için yer tutucu."""
        return frame

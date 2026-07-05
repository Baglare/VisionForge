# Kamera görüntüsü üzerine basit lonca/profil arayüzü çizer.

import cv2


HAND_CONNECTIONS = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (13, 17),
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),
]


class Effects:
    """Profil paneli ve ileride eklenecek görsel efektler için temel sınıf."""

    def __init__(self) -> None:
        self.status = "hazır"

    def draw_profile_panel(
        self,
        frame,
        profile,
        status_text: str = "Kamera modu aktif",
        hand_status_text: str | None = None,
    ):
        """Canlı kamera karesinin üzerine kompakt profil kartı çizer."""
        frame_width = frame.shape[1]
        panel_x = 24
        panel_y = 24
        panel_width = min(390, max(300, frame_width - 48))
        panel_height = 132
        padding = 14

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
            f"Kullanıcı: {profile.username}",
            f"Rütbe: {profile.rank}",
            f"Durum: {status_text}",
            f"El Durumu: {hand_status_text or 'El bekleniyor'}",
        ]

        text_x = panel_x + padding
        text_y = panel_y + 28

        for index, line in enumerate(lines):
            color = (245, 245, 245) if index != 1 else (120, 220, 255)
            self._draw_text_fit(
                frame=frame,
                text=line,
                origin=(text_x, text_y + index * 25),
                max_width=panel_width - padding * 2,
                color=color,
                font_scale=0.58,
            )

        return frame

    def draw_spell_status_panel(self, frame, spell_result):
        """Aktif büyü, cooldown ve hazırlık bilgisini kompakt panelde gösterir."""
        frame_width = frame.shape[1]
        panel_x = 24
        panel_y = 168
        panel_width = min(390, max(300, frame_width - 48))
        panel_height = 92 if not spell_result or spell_result.progress <= 0 or spell_result.has_active_spell else 118
        padding = 14

        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (22, 28, 42),
            -1,
        )
        cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)
        cv2.rectangle(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (170, 190, 255),
            2,
        )

        active_spell = "Yok"
        cooldown_text = "Hazır"
        progress = 0.0
        if spell_result:
            if spell_result.has_active_spell and spell_result.active_spell_name:
                active_spell = spell_result.active_spell_name
            if spell_result.cooldown_remaining > 0:
                cooldown_text = f"{spell_result.cooldown_remaining:.1f} sn"
            progress = spell_result.progress

        lines = [
            f"Aktif Büyü: {active_spell}",
            f"Cooldown: {cooldown_text}",
        ]
        if spell_result and not spell_result.has_active_spell and progress > 0:
            lines.append(f"Hazırlık: %{int(progress * 100)}")

        text_x = panel_x + padding
        text_y = panel_y + 30
        for index, line in enumerate(lines):
            color = (245, 245, 245) if index != 0 else (255, 220, 120)
            self._draw_text_fit(
                frame=frame,
                text=line,
                origin=(text_x, text_y + index * 26),
                max_width=panel_width - padding * 2,
                color=color,
                font_scale=0.62,
            )

        return frame

    def draw_spellbook_panel(self, frame, profile):
        """Açık ve kilitli büyüleri gösteren sağ paneli çizer."""
        frame_height, frame_width = frame.shape[:2]
        panel_width = min(360, max(285, frame_width // 3))
        panel_height = min(360, frame_height - 48)
        panel_x = max(24, frame_width - panel_width - 24)
        panel_y = 24
        padding = 14

        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (20, 24, 36),
            -1,
        )
        cv2.addWeighted(overlay, 0.76, frame, 0.24, 0, frame)
        cv2.rectangle(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (255, 220, 120),
            2,
        )

        usage_text = {
            "Donma": "Avucu açık tut",
            "Ateş": "Yatay savur + avuç göster",
            "Kalkan": "İki açık el göster",
        }

        text_x = panel_x + padding
        text_y = panel_y + 30
        max_width = panel_width - padding * 2

        self._draw_text_fit(frame, "Büyü Defteri", (text_x, text_y), max_width, (255, 220, 120), font_scale=0.72)
        text_y += 32
        self._draw_text_fit(frame, "Açık Büyüler", (text_x, text_y), max_width, (120, 220, 255), font_scale=0.58)
        text_y += 26

        for spell_name in profile.unlocked_spells:
            detail = usage_text.get(spell_name, "Kullanım bilgisi yok")
            self._draw_text_fit(
                frame,
                f"{spell_name}: {detail}",
                (text_x, text_y),
                max_width,
                (245, 245, 245),
                font_scale=0.50,
            )
            text_y += 24

        text_y += 10
        self._draw_text_fit(frame, "Kilitli Büyüler", (text_x, text_y), max_width, (170, 170, 190), font_scale=0.58)
        text_y += 26

        for spell_name in profile.locked_spells:
            self._draw_text_fit(
                frame,
                f"- {spell_name}",
                (text_x, text_y),
                max_width,
                (145, 145, 165),
                font_scale=0.50,
            )
            text_y += 23

        return frame

    def draw_spell_effect(self, frame, spell_result, hand_result=None, face_result=None):
        """Aktif büyü adına göre uygun basit ekran efektini çizer."""
        if not spell_result or not spell_result.has_active_spell:
            return frame

        if spell_result.active_spell_name == "Donma":
            return self.draw_freeze_effect(frame, spell_result)

        if spell_result.active_spell_name == "Ateş":
            return self.draw_fire_effect(frame, spell_result, hand_result)

        if spell_result.active_spell_name == "Kalkan":
            return self.draw_shield_effect(frame, spell_result, face_result)

        return frame

    def draw_freeze_effect(self, frame, spell_result):
        """Donma büyüsü aktifken kısa ve sade bir soğuk ekran efekti çizer."""
        if (
            not spell_result
            or not spell_result.has_active_spell
            or spell_result.active_spell_name != "Donma"
        ):
            return frame

        frame_height, frame_width = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame_width, frame_height), (255, 190, 90), -1)
        cv2.addWeighted(overlay, 0.24, frame, 0.76, 0, frame)

        crack_color = (255, 245, 220)
        crack_lines = [
            ((frame_width // 5, frame_height // 4), (frame_width // 3, frame_height // 3)),
            ((frame_width // 3, frame_height // 3), (frame_width // 4, frame_height // 2)),
            ((frame_width * 4 // 5, frame_height // 5), (frame_width * 2 // 3, frame_height // 2)),
            ((frame_width * 2 // 3, frame_height // 2), (frame_width * 3 // 4, frame_height * 2 // 3)),
            ((frame_width // 2, frame_height * 3 // 4), (frame_width // 2 + 70, frame_height * 2 // 3)),
        ]
        for start_point, end_point in crack_lines:
            cv2.line(frame, start_point, end_point, crack_color, 2, cv2.LINE_AA)

        text = "DONMA BÜYÜSÜ"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.15
        thickness = 3
        text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
        text_x = max(20, (frame_width - text_size[0]) // 2)
        text_y = max(80, frame_height // 2)
        cv2.putText(frame, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
        cv2.putText(frame, text, (text_x, text_y), font, font_scale, (120, 220, 255), 1, cv2.LINE_AA)

        return frame

    def draw_fire_effect(self, frame, spell_result, hand_result=None):
        """Ateş büyüsü aktifken kısa ve sade bir sıcak ekran efekti çizer."""
        if (
            not spell_result
            or not spell_result.has_active_spell
            or spell_result.active_spell_name != "Ateş"
        ):
            return frame

        frame_height, frame_width = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame_width, frame_height), (30, 90, 255), -1)
        cv2.addWeighted(overlay, 0.20, frame, 0.80, 0, frame)

        origin = self._hand_effect_origin(frame, hand_result)
        if origin is None:
            origin = (frame_width // 2, frame_height // 2)

        ring_color = (40, 160, 255)
        ray_color = (60, 210, 255)
        cv2.circle(frame, origin, 42, ring_color, 3, cv2.LINE_AA)
        cv2.circle(frame, origin, 72, (30, 90, 255), 2, cv2.LINE_AA)

        ray_offsets = [
            (95, 0),
            (-95, 0),
            (65, 55),
            (-65, 55),
            (65, -55),
            (-65, -55),
        ]
        for offset_x, offset_y in ray_offsets:
            end_point = (
                max(0, min(frame_width - 1, origin[0] + offset_x)),
                max(0, min(frame_height - 1, origin[1] + offset_y)),
            )
            cv2.line(frame, origin, end_point, ray_color, 3, cv2.LINE_AA)

        text = "ATEŞ BÜYÜSÜ"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.15
        thickness = 3
        text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
        text_x = max(20, (frame_width - text_size[0]) // 2)
        text_y = max(80, frame_height // 2)
        cv2.putText(frame, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
        cv2.putText(frame, text, (text_x, text_y), font, font_scale, (40, 160, 255), 1, cv2.LINE_AA)

        return frame

    def draw_shield_effect(self, frame, spell_result, face_result=None):
        """Kalkan büyüsü aktifken sade bir koruma halkası efekti çizer."""
        if (
            not spell_result
            or not spell_result.has_active_spell
            or spell_result.active_spell_name != "Kalkan"
        ):
            return frame

        frame_height, frame_width = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame_width, frame_height), (180, 160, 40), -1)
        cv2.addWeighted(overlay, 0.16, frame, 0.84, 0, frame)

        center, axes = self._shield_geometry(frame, face_result)
        cv2.ellipse(frame, center, axes, 0, 0, 360, (255, 220, 120), 3, cv2.LINE_AA)
        cv2.ellipse(frame, center, (axes[0] + 22, axes[1] + 30), 0, 0, 360, (120, 220, 255), 2, cv2.LINE_AA)
        cv2.ellipse(frame, center, (max(20, axes[0] - 22), max(30, axes[1] - 30)), 0, 0, 360, (255, 245, 210), 1, cv2.LINE_AA)

        marker_points = [
            (center[0], max(0, center[1] - axes[1] - 24)),
            (min(frame_width - 1, center[0] + axes[0] + 24), center[1]),
            (center[0], min(frame_height - 1, center[1] + axes[1] + 24)),
            (max(0, center[0] - axes[0] - 24), center[1]),
        ]
        for point in marker_points:
            cv2.circle(frame, point, 6, (255, 245, 210), -1, cv2.LINE_AA)
            cv2.circle(frame, point, 9, (255, 220, 120), 1, cv2.LINE_AA)

        text = "KALKAN BÜYÜSÜ"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.05
        thickness = 3
        text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
        text_x = max(20, (frame_width - text_size[0]) // 2)
        text_y = max(80, center[1] + axes[1] + 58)
        text_y = min(frame_height - 28, text_y)
        cv2.putText(frame, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
        cv2.putText(frame, text, (text_x, text_y), font, font_scale, (255, 220, 120), 1, cv2.LINE_AA)

        return frame

    def draw_hand_landmarks(self, frame, hand_result):
        """Algılanan el landmark noktalarını ve bağlantılarını çizer."""
        if not hand_result or not hand_result.detected or not hand_result.hands:
            return frame

        frame_height, frame_width = frame.shape[:2]

        for hand in hand_result.hands:
            points = [
                (
                    max(0, min(frame_width - 1, int(x * frame_width))),
                    max(0, min(frame_height - 1, int(y * frame_height))),
                )
                for x, y, _ in hand.landmarks
            ]

            if len(points) != 21:
                continue

            for start_index, end_index in HAND_CONNECTIONS:
                cv2.line(
                    frame,
                    points[start_index],
                    points[end_index],
                    (120, 220, 255),
                    2,
                    cv2.LINE_AA,
                )

            for point in points:
                cv2.circle(frame, point, 4, (245, 245, 245), -1, cv2.LINE_AA)
                cv2.circle(frame, point, 5, (120, 220, 255), 1, cv2.LINE_AA)

        return frame

    def _hand_effect_origin(self, frame, hand_result) -> tuple[int, int] | None:
        """Efektin elde başlayacağı yaklaşık ekran noktasını döndürür."""
        if not hand_result or not hand_result.detected or not hand_result.hands:
            return None

        landmarks = hand_result.hands[0].landmarks
        if len(landmarks) < 21:
            return None

        frame_height, frame_width = frame.shape[:2]
        center_indices = [0, 5, 9, 13, 17]
        center_x = sum(landmarks[index][0] for index in center_indices) / len(center_indices)
        center_y = sum(landmarks[index][1] for index in center_indices) / len(center_indices)

        return (
            max(0, min(frame_width - 1, int(center_x * frame_width))),
            max(0, min(frame_height - 1, int(center_y * frame_height))),
        )

    def _shield_geometry(self, frame, face_result) -> tuple[tuple[int, int], tuple[int, int]]:
        """Yüz kutusu varsa kalkanı kullanıcıya, yoksa ekran merkezine yerleştirir."""
        frame_height, frame_width = frame.shape[:2]
        if face_result and face_result.box is not None:
            x, y, width, height = face_result.box
            center = (x + width // 2, min(frame_height - 1, y + height))
            axes = (
                max(90, int(width * 1.45)),
                max(130, int(height * 1.75)),
            )
            return center, axes

        return (
            (frame_width // 2, frame_height // 2),
            (max(110, frame_width // 5), max(150, frame_height // 3)),
        )

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

    def _draw_text_fit(
        self,
        frame,
        text: str,
        origin: tuple[int, int],
        max_width: int,
        color,
        font_scale: float = 0.68,
    ) -> None:
        """Metni panel genişliğine göre küçük adımlarla sığdırır."""
        font = cv2.FONT_HERSHEY_SIMPLEX
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

# Kamera görüntüsü üzerine basit lonca/profil arayüzü çizer.

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


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
        self._font_cache: dict[int, ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}

    def draw_head_profile_tag(self, frame, profile, face_result=None, verification_status: str = ""):
        """Profil bilgisini yüz/kafa üstünde küçük ve sade bir etiket olarak gösterir."""
        frame_height, frame_width = frame.shape[:2]
        if face_result and face_result.box is not None:
            x, y, width, height = face_result.box
            center_x = x + width // 2
            tag_y = max(10, y - 66)
            tag_width = min(240, max(160, width + 60))
        else:
            center_x = frame_width // 2
            tag_y = 24
            tag_width = 210

        tag_x = max(12, min(frame_width - tag_width - 12, center_x - tag_width // 2))
        tag_height = 58
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (tag_x, tag_y),
            (tag_x + tag_width, tag_y + tag_height),
            (18, 22, 32),
            -1,
        )
        cv2.addWeighted(overlay, 0.52, frame, 0.48, 0, frame)
        cv2.rectangle(
            frame,
            (tag_x, tag_y),
            (tag_x + tag_width, tag_y + tag_height),
            (110, 180, 210),
            1,
        )

        short_status = self._short_verification_status(verification_status)
        lines = [profile.username, profile.rank, short_status]
        for index, line in enumerate(lines):
            color = (255, 220, 120) if index == 0 else (245, 245, 245)
            self._draw_centered_text_fit(
                frame,
                line,
                (tag_x, tag_y + 6 + index * 17),
                tag_width - 20,
                color,
                font_scale=0.38,
            )

        return frame

    def draw_profile_panel(
        self,
        frame,
        profile,
        status_text: str = "Kamera modu aktif",
        hand_status_text: str | None = None,
        verification_status: str | None = None,
        hint_text: str | None = None,
    ):
        """Canlı kamera karesinin üzerine kompakt profil kartı çizer."""
        frame_width = frame.shape[1]
        panel_x = 24
        panel_y = 24
        panel_width = min(390, max(300, frame_width - 48))
        extra_lines = int(verification_status is not None) + int(hint_text is not None)
        panel_height = 132 + extra_lines * 24
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
        if verification_status:
            lines.append(f"Doğrulama: {verification_status}")
        if hint_text:
            lines.append(hint_text)

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

    def draw_enrollment_panel(self, frame, enrollment_status):
        """Kayıt/eğitim modunda yüz örneği toplama bilgisini gösterir."""
        if not enrollment_status or not enrollment_status.is_active:
            return frame

        frame_height, frame_width = frame.shape[:2]
        panel_width = min(520, max(340, frame_width - 48))
        panel_height = 190
        panel_x = max(24, (frame_width - panel_width) // 2)
        panel_y = max(24, (frame_height - panel_height) // 2)
        padding = 18

        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (18, 24, 38),
            -1,
        )
        cv2.addWeighted(overlay, 0.62, frame, 0.38, 0, frame)
        cv2.rectangle(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (210, 180, 110),
            1,
        )

        progress = 0.0
        if enrollment_status.target_count > 0:
            progress = min(1.0, enrollment_status.sample_count / enrollment_status.target_count)

        lines = [
            "Büyücü Kaydı",
            f"Kullanıcı: {enrollment_status.username}",
            f"Örnek: {enrollment_status.sample_count}/{enrollment_status.target_count}",
            f"Yönlendirme: {enrollment_status.instruction}",
            enrollment_status.message,
        ]
        if enrollment_status.qr_path:
            lines.append(f"QR dosyası: {enrollment_status.qr_path}")

        text_x = panel_x + padding
        text_y = panel_y + 34
        max_width = panel_width - padding * 2
        for index, line in enumerate(lines):
            color = (255, 220, 120) if index == 0 else (245, 245, 245)
            self._draw_text_fit(
                frame,
                line,
                (text_x, text_y + index * 25),
                max_width,
                color,
                font_scale=0.58 if index else 0.70,
            )

        bar_x = panel_x + padding
        bar_y = panel_y + panel_height - 28
        bar_width = panel_width - padding * 2
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + 10), (65, 70, 90), -1)
        cv2.rectangle(
            frame,
            (bar_x, bar_y),
            (bar_x + int(bar_width * progress), bar_y + 10),
            (120, 220, 255),
            -1,
        )

        return frame

    def draw_settings_menu(self, frame, settings: dict):
        """Q menüsü açıkken çalışma zamanı ayarlarını gösterir."""
        if not settings.get("show_settings_menu", False):
            return frame

        panel_x = 24
        panel_y = 24
        panel_width = 455
        panel_height = 276
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (16, 20, 30),
            -1,
        )
        cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)
        cv2.rectangle(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (255, 220, 120),
            2,
        )

        mode = "QR + Yüz" if settings.get("verification_requires_qr", True) else "Yalnızca Yüz"
        lines = [
            "Ayar Menüsü  (Q: kapat, Esc: çıkış)",
            f"1 - El landmark/debug: {self._on_off(settings.get('show_hand_debug', False))}",
            f"2 - Yüz kutusu/debug: {self._on_off(settings.get('show_face_debug', False))}",
            f"3 - Doğrulama modu: {mode}",
            f"4 - Büyü Defteri: {self._on_off(settings.get('show_spellbook', True))}",
            f"5 - Debug Sayfası: {self._on_off(settings.get('show_debug_page', False))}",
            f"6 - Büyü efektleri: {self._on_off(settings.get('spell_effects_enabled', True))}",
            f"7 - Kamera aynalama: {self._on_off(settings.get('mirror_camera', False))}",
            "0 - Doğrulama oturumunu sıfırla",
        ]

        for index, line in enumerate(lines):
            color = (255, 220, 120) if index == 0 else (245, 245, 245)
            self._draw_text_fit(
                frame,
                line,
                (panel_x + 16, panel_y + 18 + index * 27),
                panel_width - 32,
                color,
                font_scale=0.56 if index else 0.62,
            )

        return frame

    def draw_debug_panel(self, frame, debug_info: dict):
        """Debug sayfası açıkken ham durum bilgilerini gösterir."""
        if not debug_info.get("show_debug_page", False):
            return frame

        frame_height, frame_width = frame.shape[:2]
        panel_width = min(430, max(320, frame_width // 3))
        panel_height = 420
        panel_x = max(16, frame_width - panel_width - 18)
        panel_y = max(18, frame_height - panel_height - 18)

        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (16, 20, 30),
            -1,
        )
        cv2.addWeighted(overlay, 0.58, frame, 0.42, 0, frame)
        cv2.rectangle(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (120, 190, 255),
            1,
        )

        lines = [
            "Debug",
            f"Yüz: {debug_info.get('face_status', '-')}",
            f"El: {debug_info.get('hand_status', '-')}",
            f"QR: {debug_info.get('qr_status', '-')}",
            f"Yüz tanıma: {debug_info.get('identity_status', '-')}",
            f"Tanınan kullanıcı: {debug_info.get('recognized_user', '-')}",
            f"Aktif profil: {debug_info.get('active_profile', '-')}",
            f"Doğrulama modu: {debug_info.get('verification_mode', '-')}",
            f"Doğrulama: {debug_info.get('verification_status', '-')}",
            f"İzinli büyüler: {debug_info.get('allowed_spells', '-')}",
            f"Kilit denemesi: {debug_info.get('attempted_locked_spell', '-')}",
            f"Yüz skoru: {debug_info.get('face_score', '-')}",
            f"FPS: {debug_info.get('fps', '-')}",
            f"Cooldown: {debug_info.get('cooldown', '-')}",
            f"Trial state: {debug_info.get('trial_state', '-')}",
            f"Trial step: {debug_info.get('trial_current_step', '-')}",
            f"Trial required: {debug_info.get('trial_required_spell', '-')}",
            f"Trial mühürler: {debug_info.get('trial_completed_steps', '-')}",
            f"Trial mesaj: {debug_info.get('last_trial_message', '-')}",
        ]
        for index, line in enumerate(lines):
            color = (120, 220, 255) if index == 0 else (235, 235, 235)
            self._draw_text_fit(
                frame,
                line,
                (panel_x + 14, panel_y + 18 + index * 24),
                panel_width - 28,
                color,
                font_scale=0.50 if index else 0.58,
            )

        return frame

    def draw_spell_status_panel(self, frame, spell_result):
        """Aktif büyü, cooldown ve hazırlık bilgisini kompakt panelde gösterir."""
        frame_width = frame.shape[1]
        panel_x = 24
        panel_y = 24
        panel_width = min(315, max(260, frame_width - 48))
        show_spell_message = bool(
            spell_result
            and not spell_result.has_active_spell
            and (
                spell_result.progress > 0
                or spell_result.message
                or spell_result.status == "Lonca yetkisi yetersiz"
            )
        )
        panel_height = 104 if show_spell_message else 80
        padding = 14

        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (22, 28, 42),
            -1,
        )
        cv2.addWeighted(overlay, 0.50, frame, 0.50, 0, frame)
        cv2.rectangle(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (150, 170, 220),
            1,
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
        if spell_result and not spell_result.has_active_spell and spell_result.message:
            lines.append(spell_result.message)
        elif spell_result and not spell_result.has_active_spell and spell_result.status == "Lonca yetkisi yetersiz":
            lines.append("Lonca yetkisi yetersiz")
        elif spell_result and not spell_result.has_active_spell and progress > 0:
            lines.append(f"Hazırlık: %{int(progress * 100)}")

        text_x = panel_x + padding
        text_y = panel_y + 27
        for index, line in enumerate(lines):
            color = (245, 245, 245) if index != 0 else (255, 220, 120)
            self._draw_text_fit(
                frame=frame,
                text=line,
                origin=(text_x, text_y + index * 23),
                max_width=panel_width - padding * 2,
                color=color,
                font_scale=0.54,
            )

        return frame

    def draw_spellbook_panel(self, frame, profile, page: int = 0):
        """Açık ve kilitli büyüleri kitap görünümünde gösterir."""
        frame_height, frame_width = frame.shape[:2]
        book_width = min(520, max(360, frame_width // 2))
        book_height = min(330, max(240, frame_height - 70))
        book_x = max(18, frame_width - book_width - 22)
        book_y = 34

        if page <= 0:
            return self._draw_spellbook_cover(frame, book_x, book_y, book_width, book_height)

        page_gap = 8
        page_width = (book_width - page_gap) // 2
        left_rect = (book_x, book_y, page_width, book_height)
        right_rect = (book_x + page_width + page_gap, book_y, page_width, book_height)

        overlay = frame.copy()
        cv2.rectangle(overlay, (book_x, book_y), (book_x + book_width, book_y + book_height), (30, 26, 20), -1)
        cv2.addWeighted(overlay, 0.42, frame, 0.58, 0, frame)
        self._draw_book_page(frame, left_rect, f"Sayfa {page * 2 - 1}")
        self._draw_book_page(frame, right_rect, f"Sayfa {page * 2}")

        spells = self._spellbook_entries(profile)
        start_index = (page - 1) * 2
        left_entries = spells[start_index:start_index + 1]
        right_entries = spells[start_index + 1:start_index + 2]
        self._draw_spell_entries(frame, left_rect, left_entries)
        self._draw_spell_entries(frame, right_rect, right_entries)

        footer = "← / → sayfa"
        self._draw_text_fit(
            frame,
            footer,
            (book_x + 12, book_y + book_height - 24),
            book_width - 24,
            (190, 170, 120),
            font_scale=0.42,
        )

        return frame

    def draw_trial_panel(self, frame, trial_status):
        """Mühürlü Kapı trial ilerlemesini küçük bir panelde gösterir."""
        if trial_status is None:
            return frame
        if trial_status.state == "idle":
            return frame

        panel_x = 24
        panel_y = 118
        panel_width = 315
        panel_height = 134
        padding = 14

        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (18, 22, 32),
            -1,
        )
        cv2.addWeighted(overlay, 0.48, frame, 0.52, 0, frame)
        cv2.rectangle(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (150, 170, 220),
            1,
        )

        state_text = {
            "idle": "Kapalı",
            "active": "Aktif",
            "completed": "Tamamlandı",
        }.get(trial_status.state, trial_status.state)
        required_spell = trial_status.required_spell or "-"
        lines = [
            f"Trial: {trial_status.name}",
            f"Durum: {state_text}",
            f"Sıradaki Büyü: {required_spell}",
            f"Mühürler: {trial_status.completed_count}/{trial_status.total_steps}",
        ]
        if trial_status.message:
            lines.append(trial_status.message)

        for index, line in enumerate(lines):
            color = (255, 220, 120) if index == 0 else (235, 235, 235)
            if "kilitli" in line.lower() or line == "Yanlış büyü":
                color = (80, 140, 255)
            self._draw_text_fit(
                frame,
                line,
                (panel_x + padding, panel_y + 18 + index * 21),
                panel_width - padding * 2,
                color,
                font_scale=0.45 if index else 0.50,
            )

        self._draw_trial_seals(frame, panel_x + padding, panel_y + panel_height - 24, trial_status)

        if trial_status.is_completed:
            self._draw_trial_completed_banner(frame)

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
        self._draw_text(
            frame,
            text,
            (text_x, text_y - text_size[1]),
            (255, 255, 255),
            font_size=34,
        )
        self._draw_text(
            frame,
            text,
            (text_x, text_y - text_size[1]),
            (120, 220, 255),
            font_size=34,
        )

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
        self._draw_text(
            frame,
            text,
            (text_x, text_y - text_size[1]),
            (255, 255, 255),
            font_size=34,
        )
        self._draw_text(
            frame,
            text,
            (text_x, text_y - text_size[1]),
            (40, 160, 255),
            font_size=34,
        )

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
        self._draw_text(
            frame,
            text,
            (text_x, text_y - text_size[1]),
            (255, 255, 255),
            font_size=32,
        )
        self._draw_text(
            frame,
            text,
            (text_x, text_y - text_size[1]),
            (255, 220, 120),
            font_size=32,
        )

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

    def _draw_trial_seals(self, frame, x: int, y: int, trial_status) -> None:
        """Trial panelinde Donma, Ateş ve Kalkan mühür noktalarını çizer."""
        spells = ["Donma", "Ateş", "Kalkan"]
        completed = set(trial_status.completed_steps)
        colors = {
            "Donma": (255, 220, 120),
            "Ateş": (40, 160, 255),
            "Kalkan": (120, 220, 255),
        }

        for index, spell_name in enumerate(spells):
            center = (x + 24 + index * 46, y)
            color = colors.get(spell_name, (220, 220, 220))
            if spell_name in completed:
                cv2.circle(frame, center, 10, color, -1, cv2.LINE_AA)
                cv2.circle(frame, center, 13, (245, 245, 245), 1, cv2.LINE_AA)
            else:
                cv2.circle(frame, center, 10, (70, 72, 82), -1, cv2.LINE_AA)
                cv2.circle(frame, center, 12, color, 1, cv2.LINE_AA)

    def _draw_trial_completed_banner(self, frame) -> None:
        """Trial tamamlandığında kısa Kapı Açıldı yazısı çizer."""
        frame_height, frame_width = frame.shape[:2]
        text = "Kapı Açıldı"
        banner_width = min(360, frame_width - 48)
        banner_height = 54
        banner_x = max(24, (frame_width - banner_width) // 2)
        banner_y = max(24, frame_height // 2 - banner_height // 2)

        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (banner_x, banner_y),
            (banner_x + banner_width, banner_y + banner_height),
            (24, 24, 34),
            -1,
        )
        cv2.addWeighted(overlay, 0.56, frame, 0.44, 0, frame)
        cv2.rectangle(
            frame,
            (banner_x, banner_y),
            (banner_x + banner_width, banner_y + banner_height),
            (255, 220, 120),
            1,
        )
        self._draw_centered_text_fit(
            frame,
            text,
            (banner_x, banner_y + 13),
            banner_width - 20,
            (255, 220, 120),
            font_scale=0.68,
        )

    def _draw_spellbook_cover(self, frame, x: int, y: int, width: int, height: int):
        """Büyü kitabı kapak sayfasını çizer."""
        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y), (x + width, y + height), (24, 20, 34), -1)
        cv2.addWeighted(overlay, 0.60, frame, 0.40, 0, frame)
        cv2.rectangle(frame, (x, y), (x + width, y + height), (220, 190, 120), 2)
        cv2.rectangle(frame, (x + 16, y + 16), (x + width - 16, y + height - 16), (120, 220, 255), 1)
        self._draw_text_fit(
            frame,
            "Büyü Kitabı",
            (x + 34, y + height // 2 - 26),
            width - 68,
            (255, 220, 120),
            font_scale=0.92,
        )
        self._draw_text_fit(
            frame,
            "Sağ ok ile aç",
            (x + 36, y + height // 2 + 22),
            width - 72,
            (235, 235, 235),
            font_scale=0.52,
        )
        return frame

    def _draw_book_page(self, frame, rect: tuple[int, int, int, int], title: str) -> None:
        """Tek kitap sayfasını çizer."""
        x, y, width, height = rect
        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y), (x + width, y + height), (45, 38, 28), -1)
        cv2.addWeighted(overlay, 0.56, frame, 0.44, 0, frame)
        cv2.rectangle(frame, (x, y), (x + width, y + height), (190, 165, 105), 1)
        self._draw_text_fit(frame, title, (x + 12, y + 16), width - 24, (255, 220, 120), font_scale=0.48)

    def _draw_spell_entries(self, frame, rect: tuple[int, int, int, int], entries: list[dict]) -> None:
        """Kitap sayfasındaki büyü girişlerini çizer."""
        x, y, width, _ = rect
        text_y = y + 54
        if not entries:
            self._draw_text_fit(frame, "Boş sayfa", (x + 12, text_y), width - 24, (170, 165, 150), font_scale=0.46)
            return

        for entry in entries:
            status_color = (120, 220, 255) if entry["unlocked"] else (150, 145, 150)
            title = entry["name"] if entry["unlocked"] else f"{entry['name']}  Kilitli"
            self._draw_text_fit(frame, title, (x + 12, text_y), width - 24, status_color, font_scale=0.56)
            text_y += 32

            if entry["unlocked"]:
                detail_lines = [
                    f"Tür: {entry['type']}",
                    f"Tetikleme: {entry['trigger']}",
                    f"Etki: {entry['effect']}",
                ]
            else:
                detail_lines = [
                    f"Tür: {entry['type']}",
                    "Durum: Kilitli",
                    "Not: Daha yüksek rütbe gerekli",
                ]

            for detail in detail_lines:
                self._draw_text_fit(frame, detail, (x + 12, text_y), width - 24, (235, 235, 235), font_scale=0.40)
                text_y += 28

    def _spellbook_entries(self, profile) -> list[dict]:
        """Profildeki açık/kilitli büyülerden kitap girişleri üretir."""
        spell_details = {
            "Donma": {
                "type": "Sabit mühür",
                "trigger": "Avucu açık tut",
                "effect": "Soğuk büyü aktivasyonu",
            },
            "Ateş": {
                "type": "Hareket zinciri",
                "trigger": "Yatay savur + avuç göster",
                "effect": "Ateş büyüsü aktivasyonu",
            },
            "Kalkan": {
                "type": "Çift el mührü",
                "trigger": "İki açık el göster",
                "effect": "Koruyucu büyü aktivasyonu",
            },
        }
        entries: list[dict] = []
        for spell_name in profile.unlocked_spells:
            details = spell_details.get(
                spell_name,
                {
                    "type": "Bilinmeyen",
                    "trigger": "Kullanım bilgisi yok",
                    "effect": "Etki bilgisi yok",
                },
            )
            entries.append(
                {
                    "name": spell_name,
                    "type": details["type"],
                    "trigger": details["trigger"],
                    "effect": details["effect"],
                    "unlocked": True,
                }
            )
        for spell_name in profile.locked_spells:
            entries.append(
                {
                    "name": spell_name,
                    "type": spell_details.get(spell_name, {}).get("type", "Kilitli büyü"),
                    "trigger": "",
                    "effect": "",
                    "unlocked": False,
                }
            )
        return entries

    def _on_off(self, enabled: bool) -> str:
        """Ayar menüsü için açık/kapalı metni döndürür."""
        return "Açık" if enabled else "Kapalı"

    def _short_verification_status(self, status: str) -> str:
        """Profil etiketi için doğrulama durumunu kısaltır."""
        mapping = {
            "Bekleniyor": "Bekleniyor",
            "Misafir": "Misafir",
            "Yüz tanındı, mühür bekleniyor": "Mühür bekleniyor",
            "Yüz tanındı": "Yüz tanındı",
            "Yüz + lonca mührü onaylandı": "Yüz + mühür onaylandı",
            "Mühür kullanıcıyla eşleşmedi": "Mühür eşleşmedi",
            "Yüz tanıma pasif": "Yüz tanıma pasif",
        }
        return mapping.get(status, status or "Bekleniyor")

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

    def _draw_centered_text_fit(
        self,
        frame,
        text: str,
        origin: tuple[int, int],
        max_width: int,
        color,
        font_scale: float = 0.68,
    ) -> None:
        """Türkçe karakter destekli metni verilen alan içinde ortalar."""
        font_size = max(14, int(font_scale * 32))

        while font_size > 13:
            font = self._get_font(font_size)
            text_width = self._text_width(text, font)
            if text_width <= max_width:
                break
            font_size -= 1

        font = self._get_font(font_size)
        text_width = self._text_width(text, font)
        text_x = origin[0] + max(0, (max_width - text_width) // 2) + 10
        self._draw_text(frame, text, (text_x, origin[1]), color, font_size=font_size)

    def _draw_text_fit(
        self,
        frame,
        text: str,
        origin: tuple[int, int],
        max_width: int,
        color,
        font_scale: float = 0.68,
    ) -> None:
        """Türkçe karakter destekli metni panel genişliğine sığdırır."""
        font_size = max(14, int(font_scale * 32))

        while font_size > 13:
            font = self._get_font(font_size)
            text_width = self._text_width(text, font)
            if text_width <= max_width:
                break
            font_size -= 1

        self._draw_text(
            frame,
            text,
            origin,
            color,
            font_size=font_size,
        )

    def _draw_text(
        self,
        frame,
        text: str,
        origin: tuple[int, int],
        color,
        font_size: int,
    ) -> None:
        """OpenCV karesine Pillow ile Unicode destekli metin çizer."""
        if not text:
            return

        font = self._get_font(font_size)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)
        draw = ImageDraw.Draw(image)
        rgb_color = (int(color[2]), int(color[1]), int(color[0]))
        draw.text(origin, text, font=font, fill=rgb_color)
        frame[:] = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    def _get_font(self, font_size: int):
        """Windows'ta Türkçe destekli sistem fontunu döndürür."""
        if font_size in self._font_cache:
            return self._font_cache[font_size]

        font_candidates = [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
        ]

        for font_path in font_candidates:
            try:
                font = ImageFont.truetype(font_path, font_size)
                self._font_cache[font_size] = font
                return font
            except OSError:
                continue

        font = ImageFont.load_default()
        self._font_cache[font_size] = font
        return font

    def _text_width(self, text: str, font) -> int:
        """Pillow fontu ile metin genişliğini hesaplar."""
        bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]

    def apply_profile_effect(self, frame, profile):
        """Profil görünümüne efekt uygulamak için yer tutucu."""
        return self.draw_profile_panel(frame, profile)

    def apply_spell_effect(self, frame, spell_name: str):
        """Büyü etkisini görüntüye uygulamak için yer tutucu."""
        return frame

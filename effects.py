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


UI_THEME = {
    "panel_bg": (14, 18, 28),
    "panel_border": (120, 170, 210),
    "panel_border_soft": (90, 118, 150),
    "text": (238, 238, 238),
    "muted": (175, 178, 186),
    "accent": (255, 220, 120),
    "danger": (80, 140, 255),
    "freeze": (255, 215, 120),
    "fire": (45, 145, 255),
    "shield": (135, 215, 255),
    "panel_alpha": 0.38,
    "panel_alpha_strong": 0.48,
    "panel_alpha_light": 0.30,
    "padding": 14,
}


class Effects:
    """Profil paneli ve ileride eklenecek görsel efektler için temel sınıf."""

    def __init__(self) -> None:
        self.status = "hazır"
        self._font_cache: dict[int, ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}

    def draw_head_profile_tag(self, frame, profile, face_result=None, verification_status: str = ""):
        """Profil bilgisini yüz/kafa üstünde sade yazı olarak gösterir."""
        frame_height, frame_width = frame.shape[:2]
        if face_result and face_result.box is not None:
            x, y, width, height = face_result.box
            center_x = x + width // 2
            tag_y = max(10, y - 54)
            tag_width = min(230, max(160, width + 54))
        else:
            center_x = frame_width // 2
            tag_y = 24
            tag_width = 210

        tag_x = max(12, min(frame_width - tag_width - 12, center_x - tag_width // 2))
        guild_name = getattr(profile, "guild_name", "Loncasız" if getattr(profile, "is_guest", False) else "Bağımsız Büyücüler")
        lines = [profile.username, profile.rank, guild_name]
        for index, line in enumerate(lines):
            color = UI_THEME["accent"] if index == 0 else UI_THEME["text"]
            if index == 2:
                color = UI_THEME["muted"] if guild_name == "Loncasız" else UI_THEME["shield"]
            self._draw_centered_text_shadow_fit(
                frame,
                line,
                (tag_x, tag_y + index * 15),
                tag_width - 20,
                color,
                font_scale=0.34 if index else 0.36,
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
        panel_height = 245
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
            f"Aşama: {getattr(enrollment_status, 'stage_name', '-')}",
            (
                "Aşama Örneği: "
                f"{getattr(enrollment_status, 'stage_sample_count', 0)}/"
                f"{getattr(enrollment_status, 'stage_target_count', 0)}"
            ),
            f"Toplam Örnek: {enrollment_status.sample_count}/{enrollment_status.target_count}",
            f"Reddedilen: {getattr(enrollment_status, 'rejected_count', 0)}",
            f"Kalite: {getattr(enrollment_status, 'quality_status', '-')}",
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
        panel_height = 334
        self._draw_panel(
            frame,
            panel_x,
            panel_y,
            panel_width,
            panel_height,
            alpha=UI_THEME["panel_alpha_strong"],
            border_color=UI_THEME["accent"],
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
            f"8 - Sistem Durumu: {self._on_off(settings.get('show_system_status', False))}",
            f"9 - Algılama Profili: {settings.get('detection_profile', 'Dengeli')}",
            "0 - Doğrulama oturumunu sıfırla",
            "D - Debug sayfasını değiştir",
        ]

        for index, line in enumerate(lines):
            color = UI_THEME["accent"] if index == 0 else UI_THEME["text"]
            if ": Açık" in line or "Yalnızca Yüz" in line:
                color = UI_THEME["shield"]
            elif ": Kapalı" in line:
                color = UI_THEME["muted"]
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
        panel_width = min(460, max(330, frame_width // 3))
        panel_height = min(frame_height - 36, 440)
        panel_x = max(16, frame_width - panel_width - 18)
        panel_y = max(18, frame_height - panel_height - 18)

        self._draw_panel(
            frame,
            panel_x,
            panel_y,
            panel_width,
            panel_height,
            alpha=UI_THEME["panel_alpha_strong"],
            border_color=UI_THEME["panel_border"],
        )

        page_index = int(debug_info.get("debug_page", 0)) % 4
        pages = [
            (
                "Genel",
                [
                    f"FPS: {debug_info.get('fps', '-')}",
                    f"Algılama profili: {debug_info.get('detection_profile', '-')}",
                    f"Doğrulama modu: {debug_info.get('verification_mode', '-')}",
                    f"Aktif profil: {debug_info.get('active_profile', '-')}",
                    f"Allowed spells: {debug_info.get('allowed_spells', '-')}",
                    f"Kamera aynalama: {debug_info.get('mirror_camera', '-')}",
                ],
            ),
            (
                "Yüz / Doğrulama",
                [
                    f"face_detected: {debug_info.get('face_detected', '-')}",
                    f"face_detection_score: {debug_info.get('face_detection_score', '-')}",
                    f"face_box: {debug_info.get('face_box', '-')}",
                    f"face_identity_label: {debug_info.get('face_identity_label', '-')}",
                    f"face_identity_score: {debug_info.get('face_identity_score', '-')}",
                    f"face_identity_variant: {debug_info.get('face_identity_variant', '-')}",
                    f"face_quality_message: {debug_info.get('face_quality_message', '-')}",
                    f"QR durumu: {debug_info.get('qr_status', '-')}",
                    f"verification_status: {debug_info.get('verification_status', '-')}",
                ],
            ),
            (
                "El / Tracker",
                [
                    f"raw_hand_detected: {debug_info.get('raw_hand_detected', '-')}",
                    f"raw_hand_count: {debug_info.get('raw_hand_count', '-')}",
                    f"raw_handedness: {debug_info.get('raw_handedness', '-')}",
                    f"hand_detector_active: {debug_info.get('hand_detector_active', '-')}",
                    f"tracker_source: {debug_info.get('tracker_source', '-')}",
                    f"tracker_hand_detected: {debug_info.get('tracker_hand_detected', '-')}",
                    f"tracker_hand_count: {debug_info.get('tracker_hand_count', '-')}",
                    f"active_hand: {debug_info.get('tracker_active_hand', '-')}",
                    f"smoothed_hand_center: {debug_info.get('tracker_smoothed_hand_center', '-')}",
                    f"hand_velocity: {debug_info.get('tracker_hand_velocity', '-')}",
                    f"tracking_quality: {debug_info.get('tracker_quality', '-')}",
                    f"missing_time: {debug_info.get('tracker_missing_time', '-')}",
                    f"quality_warnings: {debug_info.get('tracker_quality_warnings', '-')}",
                    f"brightness: {debug_info.get('tracker_brightness', '-')}",
                    f"blur_score: {debug_info.get('tracker_blur', '-')}",
                    f"hand_near_edge: {debug_info.get('tracker_hand_near_edge', '-')}",
                ],
            ),
            (
                "Büyü / Trial",
                [
                    f"active_spell: {debug_info.get('active_spell', '-')}",
                    f"cooldown: {debug_info.get('cooldown', '-')}",
                    f"spell_uses_tracker: {debug_info.get('spell_uses_tracker', '-')}",
                    f"tracker_source_used: {debug_info.get('tracker_source_used', '-')}",
                    f"freeze_state: {debug_info.get('freeze_state', '-')}",
                    f"freeze_elapsed: {debug_info.get('freeze_elapsed_time', '-')}/{debug_info.get('freeze_required_time', '-')}",
                    f"freeze_progress: {debug_info.get('freeze_progress_raw', '-')}/{debug_info.get('freeze_progress_display', '-')}",
                    f"freeze_velocity: {debug_info.get('freeze_velocity', '-')}",
                    f"freeze_deadzone: {debug_info.get('freeze_velocity_deadzone', '-')}",
                    f"freeze_is_stable: {debug_info.get('freeze_is_stable', '-')}",
                    f"freeze_block: {debug_info.get('freeze_block_reason', '-')}",
                    f"palm_open_score: {debug_info.get('palm_open_score', '-')}",
                    f"freeze_stability_score: {debug_info.get('freeze_stability_score', '-')}",
                    f"competing_candidate: {debug_info.get('competing_spell_candidate', '-')}",
                    f"fire_state: {debug_info.get('fire_state', '-')}",
                    f"fire_candidate_active: {debug_info.get('fire_candidate_active', '-')}",
                    f"fire_start_reason: {debug_info.get('fire_start_reason', '-')}",
                    f"fire_min_distance_met: {debug_info.get('fire_min_distance_met', '-')}",
                    f"fire_travel_distance: {debug_info.get('fire_travel_distance', '-')}",
                    f"fire_required_distance: {debug_info.get('fire_required_distance', '-')}",
                    f"fire_missing_time: {debug_info.get('fire_missing_time', '-')}",
                    f"fire_seal_window_active: {debug_info.get('fire_seal_window_active', '-')}",
                    f"shield_two_hand_score: {debug_info.get('shield_two_hand_score', '-')}",
                    f"locked_spell_attempt: {debug_info.get('locked_spell_attempt', '-')}",
                    f"trial_state: {debug_info.get('trial_state', '-')}",
                    f"trial_required_spell: {debug_info.get('trial_required_spell', '-')}",
                    f"trial_progress: {debug_info.get('trial_completed_steps', '-')}",
                ],
            ),
        ]
        title, page_lines = pages[page_index]
        lines = [f"Debug {page_index + 1}/4 - {title}", *page_lines, "D: sonraki sayfa"]
        text_step = max(15, min(20, (panel_height - 34) // max(1, len(lines) - 1)))
        for index, line in enumerate(lines):
            color = UI_THEME["shield"] if index == 0 else UI_THEME["text"]
            if len(line) > 62:
                line = f"{line[:59]}..."
            self._draw_text_fit(
                frame,
                line,
                (panel_x + 14, panel_y + 18 + index * text_step),
                panel_width - 28,
                color,
                font_scale=0.36 if index else 0.52,
            )

        return frame

    def draw_system_status_panel(self, frame, status_items):
        """Model, profil ve QR dosya durumlarını sade bir panelde gösterir."""
        if not status_items:
            return frame

        frame_height, frame_width = frame.shape[:2]
        panel_width = min(440, max(330, frame_width // 3))
        panel_height = 230
        panel_x = max(16, frame_width - panel_width - 18)
        panel_y = max(18, frame_height - panel_height - 18)

        self._draw_panel(
            frame,
            panel_x,
            panel_y,
            panel_width,
            panel_height,
            alpha=UI_THEME["panel_alpha"],
            border_color=UI_THEME["panel_border_soft"],
        )

        self._draw_text_fit(
            frame,
            "Sistem Durumu",
            (panel_x + 14, panel_y + 16),
            panel_width - 28,
            UI_THEME["accent"],
            font_scale=0.58,
        )

        for index, item in enumerate(status_items):
            status = item.status_text
            line = f"{item.label}: {status}"
            if not item.exists and item.hint:
                line = f"{line} - {item.hint}"
            color = UI_THEME["text"] if item.exists else UI_THEME["shield"]
            if item.required and not item.exists:
                color = UI_THEME["danger"]
            self._draw_text_fit(
                frame,
                line,
                (panel_x + 14, panel_y + 48 + index * 27),
                panel_width - 28,
                color,
                font_scale=0.43,
            )

        return frame

    def draw_registration_hint(self, frame, message: str):
        """Kayıt yoksa kullanıcıya küçük bir E ile kayıt yönlendirmesi gösterir."""
        if not message:
            return frame

        frame_height, frame_width = frame.shape[:2]
        panel_width = min(360, frame_width - 48)
        panel_height = 38
        panel_x = 24
        panel_y = max(24, frame_height - panel_height - 24)

        self._draw_panel(
            frame,
            panel_x,
            panel_y,
            panel_width,
            panel_height,
            alpha=UI_THEME["panel_alpha_light"],
            border_color=UI_THEME["panel_border_soft"],
        )
        self._draw_text_fit(
            frame,
            message,
            (panel_x + 12, panel_y + 9),
            panel_width - 24,
            (235, 235, 235),
            font_scale=0.44,
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
        padding = UI_THEME["padding"]

        active_spell = "Yok"
        cooldown_text = "Hazır"
        prep_text = "Hazırlık: Yok"
        progress = 0.0
        progress_spell = None
        if spell_result:
            if spell_result.has_active_spell and spell_result.active_spell_name:
                active_spell = spell_result.active_spell_name
                prep_text = "Hazırlık: Tetiklendi"
                progress_spell = spell_result.active_spell_name
            if spell_result.cooldown_remaining > 0:
                cooldown_text = f"{spell_result.cooldown_remaining:.1f} sn"
            progress = spell_result.progress
            if not spell_result.has_active_spell and progress > 0:
                prep_text = f"{spell_result.status}: %{int(progress * 100)}"
                progress_spell = self._spell_name_from_status(spell_result.status)

        lines = [
            f"Aktif Büyü: {active_spell}",
            f"Cooldown: {cooldown_text}",
            prep_text,
        ]
        if spell_result and not spell_result.has_active_spell and spell_result.message:
            lines[-1] = spell_result.message
        elif spell_result and not spell_result.has_active_spell and spell_result.status == "Lonca yetkisi yetersiz":
            lines[-1] = "Lonca yetkisi yetersiz"

        show_progress = bool(
            spell_result
            and (
                (not spell_result.has_active_spell and progress > 0)
                or (spell_result.has_active_spell and progress > 0)
            )
        )
        line_gap = 23
        bar_height = 8
        bar_gap = 10
        panel_height = padding * 2 + len(lines) * line_gap
        if show_progress:
            panel_height += bar_gap + bar_height
        panel_height = max(86, panel_height)

        self._draw_panel(
            frame,
            panel_x,
            panel_y,
            panel_width,
            panel_height,
            alpha=UI_THEME["panel_alpha"],
            border_color=UI_THEME["panel_border_soft"],
        )

        text_x = panel_x + padding
        text_y = panel_y + padding + 4
        for index, line in enumerate(lines):
            color = UI_THEME["text"] if index != 0 else UI_THEME["accent"]
            if index == 2 and line != "Hazırlık: Yok":
                color = self._spell_color(progress_spell)
            self._draw_text_fit(
                frame=frame,
                text=line,
                origin=(text_x, text_y + index * line_gap),
                max_width=panel_width - padding * 2,
                color=color,
                font_scale=0.54,
            )

        if show_progress:
            bar_x = panel_x + padding
            bar_y = panel_y + panel_height - padding - bar_height
            self._draw_progress_bar(
                frame,
                bar_x,
                bar_y,
                panel_width - padding * 2,
                8,
                progress,
                self._spell_color(progress_spell),
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

        self._draw_panel(
            frame,
            book_x,
            book_y,
            book_width,
            book_height,
            alpha=0.24,
            bg_color=(30, 26, 20),
            border_color=(115, 95, 65),
        )
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
        padding = UI_THEME["padding"]

        self._draw_panel(
            frame,
            panel_x,
            panel_y,
            panel_width,
            panel_height,
            alpha=UI_THEME["panel_alpha"],
            border_color=UI_THEME["panel_border_soft"],
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
            color = UI_THEME["accent"] if index == 0 else UI_THEME["text"]
            if "kilitli" in line.lower() or line == "Yanlış büyü":
                color = UI_THEME["danger"]
            self._draw_text_fit(
                frame,
                line,
                (panel_x + padding, panel_y + 18 + index * 21),
                panel_width - padding * 2,
                color,
                font_scale=0.45 if index else 0.50,
            )

        self._draw_trial_seals(frame, panel_x + padding, panel_y + panel_height - 28, trial_status)

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
            center = (x + 26 + index * 76, y - 6)
            color = colors.get(spell_name, (220, 220, 220))
            is_completed = spell_name in completed
            is_next = trial_status.state == "active" and trial_status.required_spell == spell_name
            if is_next:
                cv2.circle(frame, center, 16, (55, 58, 72), -1, cv2.LINE_AA)
                cv2.circle(frame, center, 18, UI_THEME["accent"], 1, cv2.LINE_AA)
            if spell_name in completed:
                cv2.circle(frame, center, 10, color, -1, cv2.LINE_AA)
                cv2.circle(frame, center, 14, UI_THEME["text"], 1, cv2.LINE_AA)
            else:
                cv2.circle(frame, center, 9, (58, 62, 72), -1, cv2.LINE_AA)
                cv2.circle(frame, center, 12, color if is_next else (88, 92, 105), 1, cv2.LINE_AA)
            label_color = color if is_completed or is_next else UI_THEME["muted"]
            self._draw_centered_text_fit(
                frame,
                spell_name,
                (center[0] - 34, y + 8),
                68,
                label_color,
                font_scale=0.30,
            )

    def _draw_trial_completed_banner(self, frame) -> None:
        """Trial tamamlandığında kısa Kapı Açıldı yazısı çizer."""
        frame_height, frame_width = frame.shape[:2]
        text = "Kapı Açıldı"
        banner_width = min(360, frame_width - 48)
        banner_height = 54
        banner_x = max(24, (frame_width - banner_width) // 2)
        banner_y = max(24, frame_height // 2 - banner_height // 2)

        self._draw_panel(
            frame,
            banner_x,
            banner_y,
            banner_width,
            banner_height,
            alpha=0.46,
            border_color=UI_THEME["accent"],
        )
        self._draw_centered_text_fit(
            frame,
            text,
            (banner_x, banner_y + 13),
            banner_width - 20,
            UI_THEME["accent"],
            font_scale=0.68,
        )

    def _draw_spellbook_cover(self, frame, x: int, y: int, width: int, height: int):
        """Büyü kitabı kapak sayfasını çizer."""
        self._draw_panel(
            frame,
            x,
            y,
            width,
            height,
            alpha=0.42,
            bg_color=(24, 20, 34),
            border_color=UI_THEME["accent"],
        )
        cv2.rectangle(frame, (x + 16, y + 16), (x + width - 16, y + height - 16), UI_THEME["shield"], 1)
        self._draw_text_fit(
            frame,
            "Büyü Kitabı",
            (x + 34, y + height // 2 - 26),
            width - 68,
            UI_THEME["accent"],
            font_scale=0.92,
        )
        self._draw_text_fit(
            frame,
            "Sağ ok ile aç",
            (x + 36, y + height // 2 + 22),
            width - 72,
            UI_THEME["text"],
            font_scale=0.52,
        )
        return frame

    def _draw_book_page(self, frame, rect: tuple[int, int, int, int], title: str) -> None:
        """Tek kitap sayfasını çizer."""
        x, y, width, height = rect
        self._draw_panel(
            frame,
            x,
            y,
            width,
            height,
            alpha=0.38,
            bg_color=(45, 38, 28),
            border_color=(190, 165, 105),
        )
        self._draw_text_fit(frame, title, (x + 12, y + 16), width - 24, UI_THEME["accent"], font_scale=0.48)

    def _draw_spell_entries(self, frame, rect: tuple[int, int, int, int], entries: list[dict]) -> None:
        """Kitap sayfasındaki büyü girişlerini çizer."""
        x, y, width, _ = rect
        text_y = y + 54
        if not entries:
            self._draw_text_fit(frame, "Boş sayfa", (x + 12, text_y), width - 24, (170, 165, 150), font_scale=0.46)
            return

        for entry in entries:
            status_color = UI_THEME["shield"] if entry["unlocked"] else UI_THEME["muted"]
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
                self._draw_text_fit(frame, detail, (x + 12, text_y), width - 24, UI_THEME["text"], font_scale=0.40)
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
            "Misafir": "Loncasız",
            "Yüz tanındı, mühür bekleniyor": "Mühür bekleniyor",
            "Yüz tanındı": "Yüz tanındı",
            "Yüz + lonca mührü onaylandı": "Mühür onaylandı",
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

    def _draw_panel(
        self,
        frame,
        x: int,
        y: int,
        width: int,
        height: int,
        alpha: float | None = None,
        bg_color=None,
        border_color=None,
        border_thickness: int = 1,
    ) -> None:
        """Ortak yarı saydam panel arka planı ve ince sınır çizer."""
        alpha = UI_THEME["panel_alpha"] if alpha is None else alpha
        bg_color = UI_THEME["panel_bg"] if bg_color is None else bg_color
        border_color = UI_THEME["panel_border"] if border_color is None else border_color
        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y), (x + width, y + height), bg_color, -1)
        cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)
        cv2.rectangle(frame, (x, y), (x + width, y + height), border_color, border_thickness)

    def _draw_progress_bar(
        self,
        frame,
        x: int,
        y: int,
        width: int,
        height: int,
        progress: float,
        color,
    ) -> None:
        """Hazırlık durumunu küçük ve sade bir bar olarak gösterir."""
        progress = max(0.0, min(1.0, progress or 0.0))
        cv2.rectangle(frame, (x, y), (x + width, y + height), (48, 52, 64), -1)
        fill_width = int(width * progress)
        if fill_width > 0:
            cv2.rectangle(frame, (x, y), (x + fill_width, y + height), color, -1)
        cv2.rectangle(frame, (x, y), (x + width, y + height), UI_THEME["panel_border_soft"], 1)

    def _spell_color(self, spell_name: str | None):
        """Büyü adına göre kullanıcı arayüzü vurgu rengini döndürür."""
        if spell_name == "Donma":
            return UI_THEME["freeze"]
        if spell_name == "Ateş":
            return UI_THEME["fire"]
        if spell_name == "Kalkan":
            return UI_THEME["shield"]
        return UI_THEME["accent"]

    def _spell_name_from_status(self, status: str) -> str | None:
        """Hazırlık durumu metninden büyü adını çıkarır."""
        if not status:
            return None
        for spell_name in ("Donma", "Ateş", "Kalkan"):
            if status.startswith(spell_name) or spell_name in status:
                return spell_name
        if "Avuç" in status:
            return "Donma"
        return None

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

    def _draw_centered_text_shadow_fit(
        self,
        frame,
        text: str,
        origin: tuple[int, int],
        max_width: int,
        color,
        font_scale: float = 0.68,
    ) -> None:
        """Panel kullanmadan okunur kalması için metni ince gölgeyle ortalar."""
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
        text_y = origin[1]
        shadow_color = (8, 10, 14)
        for offset_x, offset_y in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            self._draw_text(frame, text, (text_x + offset_x, text_y + offset_y), shadow_color, font_size=font_size)
        self._draw_text(frame, text, (text_x, text_y), color, font_size=font_size)

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


_SPELLBOOK_DETAILS = {
    "Donma": {
        "type": "Sabit mühür",
        "trigger": "Avucu açık tut",
        "effect": "Kısa süreli soğuk büyü aktivasyonu",
        "required_rank": "Misafir Büyücü",
    },
    "Ateş": {
        "type": "Hareket zinciri",
        "trigger": "Kontrollü yatay süpürme + avuç göster",
        "effect": "Kısa ateş patlaması",
        "required_rank": "S-Seviye Büyücü",
    },
    "Kalkan": {
        "type": "Çift el mührü",
        "trigger": "İki açık el göster",
        "effect": "Koruyucu kalkan aktivasyonu",
        "required_rank": "S-Seviye Büyücü",
    },
    "Şimşek": {
        "type": "Yüksek hız mührü",
        "trigger": "Kilitli",
        "effect": "İleri seviye saldırı büyüsü",
        "required_rank": "S+ Seviye",
    },
    "Alan Mührü": {
        "type": "Bölgesel kontrol",
        "trigger": "Kilitli",
        "effect": "Alan etkili mühür aktivasyonu",
        "required_rank": "A-Seviye veya üstü",
    },
    "Zaman Kırığı": {
        "type": "Üst düzey mühür",
        "trigger": "Kilitli",
        "effect": "Zaman temalı ileri seviye büyü",
        "required_rank": "S+ Seviye",
    },
}

_SPELLBOOK_ORDER = [
    "Donma",
    "Ateş",
    "Kalkan",
    "Şimşek",
    "Alan Mührü",
    "Zaman Kırığı",
]


def _vf_spellbook_spells(profile):
    open_spells = set(getattr(profile, "open_spells", None) or getattr(profile, "unlocked_spells", None) or [])
    locked_spells = set(getattr(profile, "locked_spells", None) or [])
    ordered = list(_SPELLBOOK_ORDER)

    for spell_name in [*open_spells, *locked_spells]:
        if spell_name not in ordered:
            ordered.append(spell_name)

    spells = []
    for spell_name in ordered:
        details = dict(
            _SPELLBOOK_DETAILS.get(
                spell_name,
                {
                    "type": "Lonca büyüsü",
                    "trigger": "Kilitli",
                    "effect": "Büyü defterinde kayıtlı",
                    "required_rank": "Lonca yetkisi gerekli",
                },
            )
        )
        details["name"] = spell_name
        details["status"] = "Açık" if spell_name in open_spells else "Kilitli"
        spells.append(details)

    return spells


def _vf_rect(frame, x1, y1, x2, y2, color, alpha=0.45, border=None, border_thickness=1):
    height, width = frame.shape[:2]
    x1 = max(0, min(width - 1, int(x1)))
    y1 = max(0, min(height - 1, int(y1)))
    x2 = max(x1 + 1, min(width, int(x2)))
    y2 = max(y1 + 1, min(height, int(y2)))

    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    if border:
        cv2.rectangle(frame, (x1, y1), (x2, y2), border, border_thickness)


def _vf_text(frame, text, x, y, scale=0.42, color=(235, 235, 225), thickness=1):
    cv2.putText(frame, str(text), (int(x) + 1, int(y) + 1), cv2.FONT_HERSHEY_SIMPLEX, scale, (18, 15, 12), thickness + 1, cv2.LINE_AA)
    cv2.putText(frame, str(text), (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def _vf_center_text(frame, text, x1, x2, y, scale=0.62, color=(238, 226, 185), thickness=1):
    text = str(text)
    max_width = max(20, int(x2 - x1 - 16))
    fitted_scale = scale
    while fitted_scale > 0.34 and cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fitted_scale, thickness)[0][0] > max_width:
        fitted_scale -= 0.04
    text_width = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fitted_scale, thickness)[0][0]
    _vf_text(frame, text, x1 + ((x2 - x1 - text_width) / 2), y, fitted_scale, color, thickness)


def _vf_wrap(text, max_width, scale=0.38, thickness=1):
    words = str(text).split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        width = cv2.getTextSize(candidate, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)[0][0]
        if current and width > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def _vf_spellbook_field(frame, label, value, x, y, max_width, muted=False):
    label_color = (210, 190, 135) if muted else (90, 230, 245)
    value_color = (176, 170, 158) if muted else (238, 235, 220)
    _vf_text(frame, f"{label}:", x, y, 0.36, label_color)
    y += 17
    for line in _vf_wrap(value, max_width, 0.36):
        _vf_text(frame, line, x + 8, y, 0.36, value_color)
        y += 16
    return y + 3


def _vf_draw_spellbook_page(frame, spell, rect):
    x1, y1, x2, y2 = rect
    is_locked = spell["status"] == "Kilitli"
    page_color = (74, 62, 44) if is_locked else (86, 72, 48)
    border_color = (118, 112, 95) if is_locked else (95, 205, 225)
    title_color = (150, 150, 145) if is_locked else (245, 226, 140)
    max_width = x2 - x1 - 28

    _vf_rect(frame, x1, y1, x2, y2, page_color, 0.58, border_color, 1)
    _vf_center_text(frame, spell["name"], x1, x2, y1 + 31, 0.52, title_color, 1)

    status_color = (135, 135, 135) if is_locked else (80, 220, 155)
    _vf_center_text(frame, spell["status"], x1, x2, y1 + 53, 0.35, status_color, 1)

    y = y1 + 78
    y = _vf_spellbook_field(frame, "Tür", spell["type"], x1 + 14, y, max_width, is_locked)
    y = _vf_spellbook_field(frame, "Tetikleme", spell["trigger"], x1 + 14, y, max_width, is_locked)
    y = _vf_spellbook_field(frame, "Etki", spell["effect"], x1 + 14, y, max_width, is_locked)
    _vf_spellbook_field(frame, "Gereken rütbe", spell["required_rank"], x1 + 14, y, max_width, is_locked)


def _vf_draw_spellbook_panel(self, frame, profile, page=0, *args, **kwargs):
    """Kapak + iki sayfa düzeninde, sayfa başına tek büyü gösteren Büyü Kitabı."""
    height, width = frame.shape[:2]
    book_width = min(max(380, int(width * 0.56)), width - 36)
    book_height = min(max(292, int(height * 0.58)), height - 76)
    x1 = max(18, width - book_width - 18)
    y1 = max(44, int(height * 0.10))
    x2 = x1 + book_width
    y2 = y1 + book_height

    if page <= 0:
        _vf_rect(frame, x1, y1, x2, y2, (42, 34, 27), 0.62, (92, 220, 238), 1)
        _vf_center_text(frame, "Büyü Kitabı", x1, x2, y1 + int(book_height * 0.37), 0.82, (245, 222, 135), 2)
        _vf_center_text(frame, "VisionForge Lonca Arşivi", x1, x2, y1 + int(book_height * 0.50), 0.43, (235, 232, 218), 1)
        _vf_center_text(frame, "Sağ ok ile aç", x1, x2, y2 - 34, 0.36, (168, 225, 235), 1)
        return frame

    spells = _vf_spellbook_spells(profile)
    max_page = max(1, (len(spells) + 1) // 2)
    page = max(1, min(int(page), max_page))
    start_index = (page - 1) * 2

    _vf_rect(frame, x1, y1, x2, y2, (32, 27, 24), 0.42, (82, 96, 105), 1)
    gutter_x = x1 + book_width // 2
    cv2.line(frame, (gutter_x, y1 + 12), (gutter_x, y2 - 12), (92, 85, 72), 1)

    padding = 13
    gap = 10
    page_width = (book_width - (padding * 2) - gap) // 2
    left_rect = (x1 + padding, y1 + padding, x1 + padding + page_width, y2 - padding)
    right_rect = (left_rect[2] + gap, y1 + padding, x2 - padding, y2 - padding)

    for spell, rect in zip(spells[start_index : start_index + 2], [left_rect, right_rect]):
        _vf_draw_spellbook_page(frame, spell, rect)

    if start_index + 1 >= len(spells):
        _vf_rect(frame, *right_rect, (58, 50, 40), 0.36, (95, 90, 78), 1)
        _vf_center_text(frame, "Boş Sayfa", right_rect[0], right_rect[2], right_rect[1] + 42, 0.42, (150, 145, 132), 1)

    footer = f"Sayfa {start_index + 1}-{min(start_index + 2, len(spells))}"
    _vf_center_text(frame, footer, x1, x2, y2 - 8, 0.30, (172, 180, 176), 1)
    return frame


Effects.draw_spellbook_panel = _vf_draw_spellbook_panel


try:
    from PIL import Image as _VFImage
    from PIL import ImageDraw as _VFImageDraw
    from PIL import ImageFont as _VFImageFont
except ImportError:
    _VFImage = None
    _VFImageDraw = None
    _VFImageFont = None

import numpy as _vf_np

_ORIGINAL_CV2_PUT_TEXT = cv2.putText
_ORIGINAL_CV2_GET_TEXT_SIZE = cv2.getTextSize
_UNICODE_FONT_CACHE = {}
_UNICODE_FONT_PATHS = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
]


def _unicode_font_size(font_scale):
    return max(9, int(round(float(font_scale) * 31)))


def _load_unicode_font(font_size):
    if _VFImageFont is None:
        return None

    font_size = int(font_size)
    if font_size in _UNICODE_FONT_CACHE:
        return _UNICODE_FONT_CACHE[font_size]

    for font_path in _UNICODE_FONT_PATHS:
        try:
            font = _VFImageFont.truetype(font_path, font_size)
            _UNICODE_FONT_CACHE[font_size] = font
            return font
        except OSError:
            continue

    font = _VFImageFont.load_default()
    _UNICODE_FONT_CACHE[font_size] = font
    return font


def _bgr_to_rgba(color):
    if color is None:
        return (255, 255, 255, 255)

    if len(color) >= 3:
        return (
            int(max(0, min(255, color[2]))),
            int(max(0, min(255, color[1]))),
            int(max(0, min(255, color[0]))),
            255,
        )

    value = int(max(0, min(255, color[0])))
    return (value, value, value, 255)


def draw_unicode_text(
    frame,
    text,
    position,
    font_size,
    color=(255, 255, 255),
    anchor="ls",
    stroke_width=0,
    stroke_fill=None,
):
    """OpenCV BGR frame üzerine Türkçe karakter destekli metin çizer."""
    if _VFImage is None or _VFImageDraw is None or _VFImageFont is None:
        return frame

    if frame is None:
        return frame

    text = str(text)
    if not text:
        return frame

    font = _load_unicode_font(font_size)
    if font is None:
        return frame

    x, y = int(position[0]), int(position[1])
    stroke_width = max(0, int(stroke_width))
    fill = _bgr_to_rgba(color)
    stroke_fill_rgba = _bgr_to_rgba(stroke_fill if stroke_fill is not None else color)

    measure = _VFImage.new("RGBA", (1, 1), (0, 0, 0, 0))
    measure_draw = _VFImageDraw.Draw(measure)

    try:
        bbox = measure_draw.textbbox((0, 0), text, font=font, anchor=anchor, stroke_width=stroke_width)
    except (TypeError, ValueError):
        anchor = None
        bbox = measure_draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)

    padding = max(3, stroke_width + 2)
    patch_width = max(1, bbox[2] - bbox[0] + padding * 2)
    patch_height = max(1, bbox[3] - bbox[1] + padding * 2)
    origin_x = x + bbox[0] - padding
    origin_y = y + bbox[1] - padding

    patch = _VFImage.new("RGBA", (patch_width, patch_height), (0, 0, 0, 0))
    draw = _VFImageDraw.Draw(patch)
    draw_position = (padding - bbox[0], padding - bbox[1])

    if anchor:
        draw.text(
            draw_position,
            text,
            font=font,
            fill=fill,
            anchor=anchor,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill_rgba,
        )
    else:
        draw.text(
            draw_position,
            text,
            font=font,
            fill=fill,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill_rgba,
        )

    frame_height, frame_width = frame.shape[:2]
    x1 = max(0, origin_x)
    y1 = max(0, origin_y)
    x2 = min(frame_width, origin_x + patch_width)
    y2 = min(frame_height, origin_y + patch_height)

    if x1 >= x2 or y1 >= y2:
        return frame

    patch_x1 = x1 - origin_x
    patch_y1 = y1 - origin_y
    patch_x2 = patch_x1 + (x2 - x1)
    patch_y2 = patch_y1 + (y2 - y1)

    patch_array = _vf_np.asarray(patch, dtype=_vf_np.float32)[patch_y1:patch_y2, patch_x1:patch_x2]
    rgb = patch_array[:, :, :3]
    alpha = patch_array[:, :, 3:4] / 255.0
    if not alpha.any():
        return frame

    bgr = rgb[:, :, ::-1]
    roi = frame[y1:y2, x1:x2].astype(_vf_np.float32)
    blended = (bgr * alpha) + (roi * (1.0 - alpha))
    frame[y1:y2, x1:x2] = blended.astype(frame.dtype)
    return frame


def draw_centered_unicode_text(frame, text, center, font_size, color=(255, 255, 255), stroke_width=0, stroke_fill=None):
    """OpenCV BGR frame üzerine ortalanmış Türkçe karakter destekli metin çizer."""
    return draw_unicode_text(
        frame,
        text,
        center,
        font_size,
        color=color,
        anchor="mm",
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
    )


def _unicode_get_text_size(text, fontFace, fontScale, thickness=1):
    if _VFImage is None or _VFImageDraw is None or _VFImageFont is None:
        return _ORIGINAL_CV2_GET_TEXT_SIZE(text, fontFace, fontScale, thickness)

    font_size = _unicode_font_size(fontScale)
    font = _load_unicode_font(font_size)
    if font is None:
        return _ORIGINAL_CV2_GET_TEXT_SIZE(text, fontFace, fontScale, thickness)

    measure = _VFImage.new("RGBA", (1, 1), (0, 0, 0, 0))
    draw = _VFImageDraw.Draw(measure)
    stroke_width = max(0, int(thickness) - 1)
    bbox = draw.textbbox((0, 0), str(text), font=font, stroke_width=stroke_width)
    width = max(1, bbox[2] - bbox[0])
    height = max(1, bbox[3] - bbox[1])
    baseline = max(2, int(font_size * 0.22))
    return (width, height), baseline


def _unicode_put_text(
    image,
    text,
    org,
    fontFace,
    fontScale,
    color,
    thickness=1,
    lineType=None,
    bottomLeftOrigin=False,
):
    if _VFImage is None or _VFImageDraw is None or _VFImageFont is None:
        if lineType is None:
            return _ORIGINAL_CV2_PUT_TEXT(image, text, org, fontFace, fontScale, color, thickness)
        return _ORIGINAL_CV2_PUT_TEXT(image, text, org, fontFace, fontScale, color, thickness, lineType)

    font_size = _unicode_font_size(fontScale)
    stroke_width = max(0, int(thickness) - 1)
    stroke_fill = color
    y = image.shape[0] - int(org[1]) if bottomLeftOrigin else int(org[1])
    return draw_unicode_text(
        image,
        text,
        (int(org[0]), y),
        font_size,
        color=color,
        anchor="ls",
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
    )


cv2.getTextSize = _unicode_get_text_size
cv2.putText = _unicode_put_text

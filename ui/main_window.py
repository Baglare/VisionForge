"""VisionForge için sayfa tabanlı PySide6 ana pencere kabuğu."""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from effects import _SPELLBOOK_DETAILS
from system_status import get_system_status
from ui.camera_worker import CameraWorker
from ui.frame_view import FrameView
from ui.theme import application_stylesheet


PAGE_ORDER = ("live", "spellbook", "trial", "enrollment", "settings", "system", "debug")
SPELLBOOK_PAGES = (None, "Donma", "Ateş", "Kalkan")
TRIAL_STEPS = ("Donma", "Ateş", "Kalkan")
DEBUG_FIELDS = {
    "Genel": (
        ("FPS", "fps"),
        ("Kamera çözünürlüğü", "capture_resolution"),
        ("Algılama profili", "detection_profile"),
        ("Kamera aynalama", "mirror_camera"),
    ),
    "Yüz / Doğrulama": (
        ("Yüz algılandı", "face_detected"),
        ("Yüz skoru", "face_identity_score"),
        ("Stabil etiket", "face_identity_stable_label"),
        ("Stabilite sayısı", "face_identity_stability_count"),
        ("Oturum durumu", "session_state"),
        ("Grace kalan süre", "grace_remaining_seconds"),
        ("QR durumu", "qr_status"),
        ("Doğrulama modu", "verification_mode"),
    ),
    "El / Tracker": (
        ("El algılandı", "hand_detected"),
        ("El sayısı", "raw_hand_count"),
        ("Sağ / sol el", "raw_handedness"),
        ("Tracking source", "tracker_source"),
        ("Tracking quality", "tracker_quality"),
        ("Parlaklık", "tracker_brightness"),
        ("Blur", "tracker_blur"),
        ("Quality warnings", "tracker_quality_warnings"),
    ),
    "Büyü / Trial": (
        ("Aktif büyü", "active_spell"),
        ("Cooldown", "cooldown"),
        ("Hazırlık ilerlemesi", "spell_prepare_progress"),
        ("Donma durumu", "freeze_state"),
        ("Ateş hareket mesafesi", "fire_horizontal_distance"),
        ("Kalkan iki el skoru", "shield_two_hand_score"),
        ("Trial durumu", "trial_state"),
        ("Aktif Trial adımı", "trial_required_spell"),
        ("Tamamlanan adımlar", "trial_completed_steps"),
    ),
}


class MainWindow(QMainWindow):
    """VisionForge'un sayfa navigasyonunu ve mevcut worker veri akışını yönetir."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VisionForge")
        self.resize(1360, 820)
        self.setMinimumSize(1180, 700)
        self._worker_thread: QThread | None = None
        self._worker: CameraWorker | None = None
        self._last_payload: dict = {}
        self._current_page = "live"
        self._nav_buttons: dict[str, QPushButton] = {}
        self._last_settings_state: tuple | None = None
        self._debug_value_labels: dict[str, QLabel] = {}
        self._last_debug_update = 0.0
        self._camera_frame_received = False
        self._capture_resolution = "Bekleniyor"
        self._system_rows: dict[str, tuple[QLabel, QLabel]] = {}
        self._enrollment_request_pending = False

        self.frame_view = FrameView()
        self.top_user_label = QLabel("Misafir")
        self.top_rank_label = QLabel("Misafir Büyücü")
        self.top_verification_label = QLabel("Doğrulama: Bekleniyor")
        self.top_grace_label = QLabel("")
        self.spell_label = QLabel("Aktif Büyü: Yok")
        self.allowed_spells_label = QLabel("Açık Büyüler: Donma")
        self.trial_label = QLabel("Trial: Kapalı")
        self.session_label = QLabel("Doğrulama oturumu: Bekleniyor")
        self.live_user_label = QLabel("Misafir")
        self.live_rank_label = QLabel("Misafir Büyücü")
        self.live_grace_label = QLabel("Pasif")
        self.live_prepare_label = QLabel("%0")
        self.live_cooldown_label = QLabel("Hazır")
        self.live_trial_step_label = QLabel("-")
        self.live_trial_progress_label = QLabel("0/3")
        self.live_resolution_label = QLabel("Bekleniyor")
        self.live_fps_label = QLabel("FPS -")
        self.live_camera_status_label = QLabel("Kamera bekleniyor")
        self.live_trial_button = QPushButton("Başlat / Yeniden Başlat")
        self.registration_label = QLabel("Kayıt durumu bekleniyor")
        self.system_label = QLabel("Sistem Durumu: kamera başlatılıyor")
        self.notifications_label = QLabel("")

        self.trial_state_label = QLabel("Bekleniyor")
        self.trial_message_label = QLabel("T ile Trial başlat")
        self.trial_completed_label = QLabel("-")
        self.trial_pending_label = QLabel("Donma, Ateş, Kalkan")
        self.trial_progress_bar = QProgressBar()
        self.trial_step_labels: dict[str, QLabel] = {}
        self.trial_start_button = QPushButton("Trial Başlat / Yeniden Başlat")

        self.hand_debug_checkbox = QCheckBox("El landmark göster")
        self.face_debug_checkbox = QCheckBox("Yüz kutusu göster")
        self.mirror_checkbox = QCheckBox("Kamera aynalama")
        self.spell_effects_checkbox = QCheckBox("Büyü efektleri")
        self.verification_mode_combo = QComboBox()
        self.detection_profile_combo = QComboBox()

        self.debug_tabs = QTabWidget()
        self.system_refresh_button = QPushButton("Yenile")

        self.enrollment_username_input = QLineEdit()
        self.enrollment_method_combo = QComboBox()
        self.enrollment_folder_input = QLineEdit()
        self.enrollment_folder_widget = QWidget()
        self.enrollment_start_button = QPushButton("Kayıt Başlat")
        self.enrollment_cancel_button = QPushButton("İptal / Sıfırla")
        self.enrollment_validation_label = QLabel("")
        self.enrollment_state_label = QLabel("Bekliyor")
        self.enrollment_stage_label = QLabel("-")
        self.enrollment_instruction_label = QLabel("Kullanıcı adı ve kayıt yöntemi seçin.")
        self.enrollment_stage_count_label = QLabel("0/0")
        self.enrollment_total_count_label = QLabel("0/0")
        self.enrollment_quality_label = QLabel("-")
        self.enrollment_message_label = QLabel("Kayıt bekleniyor")
        self.enrollment_import_label = QLabel("Kabul: 0 · Red: 0")
        self.enrollment_stage_progress = QProgressBar()
        self.enrollment_total_progress = QProgressBar()
        self.enrollment_completion_frame = QFrame()
        self.enrollment_completion_label = QLabel("")
        self.enrollment_qr_path = QLineEdit()

        self.spellbook_page_label = QLabel("Kapak · 0/3")
        self.spellbook_title_label = QLabel("Büyü Kitabı")
        self.spellbook_status_label = QLabel("VisionForge Lonca Arşivi")
        self.spellbook_type_label = QLabel("")
        self.spellbook_trigger_label = QLabel("Sağ ok veya Sonraki ile aç")
        self.spellbook_rank_label = QLabel("")
        self.spellbook_description_label = QLabel("Aktif profile ait büyü yetkilerini görüntüler.")
        self.previous_spellbook_button = QPushButton("Önceki")
        self.next_spellbook_button = QPushButton("Sonraki")

        self.page_stack = QStackedWidget()
        self._build_ui()
        self._create_actions()
        self._start_worker()
        self._send_action("close_spellbook")

    def closeEvent(self, event) -> None:
        """Pencere kapanırken kamera thread'ini temiz kapatır."""
        self._stop_worker()
        super().closeEvent(event)

    def keyPressEvent(self, event) -> None:
        """Mevcut VisionForge kısayollarını Qt üzerinden yönetir."""
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.close()
            return
        if key == Qt.Key.Key_B:
            self._toggle_spellbook_page()
        elif key == Qt.Key.Key_T:
            self._send_action("start_trial")
        elif key == Qt.Key.Key_R:
            self._send_action("reset_auth")
        elif key == Qt.Key.Key_E:
            self._navigate_to("enrollment")
        elif key == Qt.Key.Key_H:
            self._send_action("toggle_hand_debug")
        elif key == Qt.Key.Key_G:
            self._send_action("toggle_demo")
        elif key == Qt.Key.Key_N:
            self._send_action("demo_next")
        elif key == Qt.Key.Key_P:
            self._send_action("demo_previous")
        elif key == Qt.Key.Key_Q:
            self._send_action("toggle_settings")
        elif key == Qt.Key.Key_D:
            if self._current_page == "debug":
                self._cycle_debug_tab()
            else:
                self._send_action("next_debug_page")
        elif key == Qt.Key.Key_Right and self._current_page == "spellbook":
            self._change_spellbook_page(1)
        elif key == Qt.Key.Key_Left and self._current_page == "spellbook":
            self._change_spellbook_page(-1)
        elif key == Qt.Key.Key_1:
            self._send_action("toggle_hand_debug")
        elif key == Qt.Key.Key_2:
            self._send_action("toggle_face_debug")
        elif key == Qt.Key.Key_3:
            self._send_action("cycle_verification_mode")
        elif key == Qt.Key.Key_4:
            self._toggle_spellbook_page()
        elif key == Qt.Key.Key_5:
            self._send_action("toggle_debug")
        elif key == Qt.Key.Key_6:
            self._send_action("toggle_spell_effects")
        elif key == Qt.Key.Key_7:
            self._send_action("toggle_mirror")
        elif key == Qt.Key.Key_8:
            self._send_action("toggle_system_status")
        elif key == Qt.Key.Key_9:
            self._send_action("cycle_detection_profile")
        elif key == Qt.Key.Key_0:
            self._send_action("reset_auth")
        else:
            super().keyPressEvent(event)

    def _build_ui(self) -> None:
        """Üst çubuk, navigasyon ve sayfa yığınını kurar."""
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._top_bar(), 0)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(12, 12, 12, 12)
        body_layout.setSpacing(12)
        body_layout.addWidget(self._navigation_panel(), 0)

        pages = {
            "live": self._live_page(),
            "spellbook": self._spellbook_page(),
            "trial": self._trial_page(),
            "enrollment": self._enrollment_page(),
            "settings": self._settings_page(),
            "system": self._system_page(),
            "debug": self._debug_page(),
        }
        for page_name in PAGE_ORDER:
            self.page_stack.addWidget(pages[page_name])

        body_layout.addWidget(self.page_stack, 1)
        root_layout.addWidget(body, 1)
        self.setCentralWidget(root)
        self._apply_style()
        self._navigate_to("live", sync_engine=False)

    def _top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("TopBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 9, 18, 9)
        layout.setSpacing(9)

        brand_block = QVBoxLayout()
        brand_block.setSpacing(0)
        brand = QLabel("VisionForge")
        brand.setObjectName("BrandLabel")
        brand_subtitle = QLabel("Arcane Vision Interface")
        brand_subtitle.setObjectName("BrandSubtitle")
        brand_block.addWidget(brand)
        brand_block.addWidget(brand_subtitle)
        layout.addLayout(brand_block)
        layout.addStretch(1)

        for label in (self.top_user_label, self.top_rank_label, self.top_verification_label, self.top_grace_label):
            label.setProperty("badge", True)
        self.top_user_label.setProperty("state", "neutral")
        self.top_user_label.setObjectName("UserBadge")
        self.top_rank_label.setProperty("state", "rank")
        self.top_rank_label.setObjectName("RankBadge")
        self.top_verification_label.setProperty("state", "neutral")
        self.top_verification_label.setObjectName("VerificationBadge")
        self.top_grace_label.setProperty("state", "warning")
        self.top_grace_label.setObjectName("GraceBadge")
        layout.addWidget(self.top_user_label)
        layout.addWidget(self.top_rank_label)
        layout.addWidget(self.top_verification_label)
        self.top_grace_label.hide()
        layout.addWidget(self.top_grace_label)
        return bar

    def _navigation_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("NavPanel")
        panel.setFixedWidth(188)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(9, 14, 9, 12)
        layout.setSpacing(6)

        heading = QLabel("ANA")
        heading.setObjectName("NavGroupLabel")
        layout.addWidget(heading)

        primary_pages = (
            ("live", "Canlı Görüş"),
            ("spellbook", "Büyü Kitabı"),
            ("trial", "Trial"),
        )
        utility_pages = (
            ("settings", "Ayarlar"),
            ("system", "Sistem Durumu"),
            ("debug", "Debug"),
        )

        def add_navigation_button(page_name: str, title: str) -> None:
            button = QPushButton(title)
            button.setCheckable(True)
            button.setProperty("nav", True)
            button.clicked.connect(lambda checked=False, name=page_name: self._navigate_to(name))
            self._nav_buttons[page_name] = button
            layout.addWidget(button)

        for page_name, title in primary_pages:
            add_navigation_button(page_name, title)

        layout.addSpacing(6)
        add_navigation_button("enrollment", "Kayıt")
        layout.addStretch(1)

        tools_heading = QLabel("ARAÇLAR")
        tools_heading.setObjectName("NavGroupLabel")
        layout.addWidget(tools_heading)
        for page_name, title in utility_pages:
            add_navigation_button(page_name, title)

        layout.addSpacing(8)
        footer = QFrame()
        footer.setObjectName("NavFooter")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(8, 7, 8, 7)
        footer_layout.setSpacing(2)
        shortcuts = QLabel("B: Kitap  ·  T: Trial\nE: Kayıt  ·  Esc: Çıkış")
        shortcuts.setObjectName("ShortcutHint")
        shortcuts.setWordWrap(True)
        footer_layout.addWidget(shortcuts)
        layout.addWidget(footer)
        return panel

    def _live_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        camera_column = QVBoxLayout()
        camera_column.setSpacing(7)
        camera_header = QHBoxLayout()
        camera_header.setSpacing(7)
        live_title = QLabel("Canlı Görüş")
        live_title.setObjectName("LivePageTitle")
        for label in (self.live_resolution_label, self.live_fps_label, self.live_camera_status_label):
            label.setObjectName("CameraMeta")
            label.setProperty("state", "neutral")
        camera_header.addWidget(live_title)
        camera_header.addStretch(1)
        camera_header.addWidget(self.live_resolution_label)
        camera_header.addWidget(self.live_fps_label)
        camera_header.addWidget(self.live_camera_status_label)
        camera_column.addLayout(camera_header)

        camera_card = QFrame()
        camera_card.setObjectName("CameraCard")
        camera_layout = QVBoxLayout(camera_card)
        camera_layout.setContentsMargins(1, 1, 1, 1)
        camera_layout.addWidget(self.frame_view, 1)
        camera_column.addWidget(camera_card, 1)
        layout.addLayout(camera_column, 1)

        sidebar = QScrollArea()
        sidebar.setObjectName("LiveSidebar")
        sidebar.setWidgetResizable(True)
        sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sidebar.setMinimumWidth(280)
        sidebar.setMaximumWidth(330)
        sidebar_content = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_content)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(8)
        sidebar_layout.addWidget(
            self._live_status_card(
                "OTURUM",
                (
                    ("Kullanıcı", self.live_user_label),
                    ("Rütbe", self.live_rank_label),
                    ("Doğrulama", self.session_label),
                    ("Grace", self.live_grace_label),
                ),
            )
        )
        sidebar_layout.addWidget(
            self._live_status_card(
                "AKTİF BÜYÜ",
                (
                    ("Büyü", self.spell_label),
                    ("Hazırlık", self.live_prepare_label),
                    ("Cooldown", self.live_cooldown_label),
                    ("Açık büyüler", self.allowed_spells_label),
                ),
            )
        )
        self.live_trial_button.clicked.connect(lambda: self._send_action("start_trial"))
        sidebar_layout.addWidget(
            self._live_status_card(
                "TRIAL",
                (
                    ("Durum", self.trial_label),
                    ("Mevcut adım", self.live_trial_step_label),
                    ("İlerleme", self.live_trial_progress_label),
                ),
                self.live_trial_button,
            )
        )
        self.notifications_label.setWordWrap(True)
        self.notifications_label.setObjectName("NotificationText")
        notification_card = self._info_card("SON BİLDİRİM", self.notifications_label)
        notification_card.setMaximumHeight(130)
        sidebar_layout.addWidget(notification_card)
        sidebar_layout.addStretch(1)
        sidebar.setWidget(sidebar_content)
        layout.addWidget(sidebar, 0)
        return page

    def _spellbook_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 4, 8, 8)
        layout.setSpacing(12)

        title_row = QHBoxLayout()
        title = QLabel("Büyü Kitabı")
        title.setObjectName("PageTitle")
        title_row.addWidget(title)
        title_row.addStretch(1)
        self.spellbook_page_label.setProperty("role", "muted")
        title_row.addWidget(self.spellbook_page_label)
        layout.addLayout(title_row)

        card = QFrame()
        card.setObjectName("SpellbookCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(14)
        self.spellbook_title_label.setObjectName("SpellbookTitle")
        self.spellbook_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spellbook_status_label.setObjectName("SpellbookStatus")
        self.spellbook_status_label.setProperty("state", "cover")
        self.spellbook_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addStretch(1)
        card_layout.addWidget(self.spellbook_title_label)
        card_layout.addWidget(self.spellbook_status_label)
        card_layout.addSpacing(12)
        for label in (
            self.spellbook_type_label,
            self.spellbook_trigger_label,
            self.spellbook_rank_label,
            self.spellbook_description_label,
        ):
            label.setWordWrap(True)
            card_layout.addWidget(label)
        card_layout.addStretch(1)
        layout.addWidget(card, 1)

        controls = QHBoxLayout()
        controls.addStretch(1)
        self.previous_spellbook_button.clicked.connect(lambda: self._change_spellbook_page(-1))
        self.next_spellbook_button.clicked.connect(lambda: self._change_spellbook_page(1))
        controls.addWidget(self.previous_spellbook_button)
        controls.addWidget(self.next_spellbook_button)
        layout.addLayout(controls)
        return page

    def _trial_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 4, 8, 8)
        layout.setSpacing(12)

        title = QLabel("Trial")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Mühürlü Kapı · Donma → Ateş → Kalkan")
        subtitle.setProperty("role", "muted")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        steps_card = QFrame()
        steps_card.setObjectName("PageCard")
        steps_layout = QVBoxLayout(steps_card)
        steps_layout.setContentsMargins(22, 20, 22, 20)
        steps_layout.setSpacing(10)
        for index, spell_name in enumerate(TRIAL_STEPS, start=1):
            label = QLabel(f"{index}. {spell_name} · Bekliyor")
            label.setObjectName("TrialStep")
            label.setProperty("state", "pending")
            self.trial_step_labels[spell_name] = label
            steps_layout.addWidget(label)

        self.trial_progress_bar.setRange(0, len(TRIAL_STEPS))
        self.trial_progress_bar.setValue(0)
        self.trial_progress_bar.setFormat("%v/%m adım")
        steps_layout.addSpacing(8)
        steps_layout.addWidget(self.trial_progress_bar)

        details = QGridLayout()
        details.setHorizontalSpacing(18)
        details.setVerticalSpacing(8)
        rows = (
            ("Durum", self.trial_state_label),
            ("Tamamlanan", self.trial_completed_label),
            ("Bekleyen", self.trial_pending_label),
            ("Mesaj", self.trial_message_label),
        )
        for row, (label_text, value_label) in enumerate(rows):
            key_label = QLabel(label_text)
            key_label.setProperty("role", "muted")
            value_label.setWordWrap(True)
            details.addWidget(key_label, row, 0)
            details.addWidget(value_label, row, 1)
        steps_layout.addLayout(details)

        self.trial_start_button.clicked.connect(lambda: self._send_action("start_trial"))
        layout.addWidget(steps_card, 1)
        layout.addWidget(self.trial_start_button, 0, Qt.AlignmentFlag.AlignLeft)
        return page

    def _enrollment_page(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(8, 4, 8, 8)
        page_layout.setSpacing(10)
        title = QLabel("Kayıt / Yüz Eğitimi")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Mevcut canlı kamera veya fotoğraf import akışıyla yerel büyücü profili oluşturun.")
        subtitle.setProperty("role", "muted")
        page_layout.addWidget(title)
        page_layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setObjectName("EnrollmentScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 4, 0)
        content_layout.setSpacing(10)

        start_card = QFrame()
        start_card.setObjectName("EnrollmentCard")
        start_layout = QGridLayout(start_card)
        start_layout.setContentsMargins(18, 16, 18, 16)
        start_layout.setHorizontalSpacing(14)
        start_layout.setVerticalSpacing(9)
        start_title = QLabel("KAYIT BAŞLANGICI")
        start_title.setObjectName("CardTitle")
        self.enrollment_username_input.setPlaceholderText("Büyücü kullanıcı adı")
        self.enrollment_method_combo.addItems(["Canlı Kamera", "Fotoğraf İçe Aktarma"])
        self.enrollment_folder_input.setReadOnly(True)
        self.enrollment_folder_input.setPlaceholderText("Fotoğraf klasörü seçilmedi")
        browse_button = QPushButton("Klasör Seç")
        browse_button.clicked.connect(self._choose_enrollment_directory)
        folder_layout = QHBoxLayout(self.enrollment_folder_widget)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_layout.setSpacing(8)
        folder_layout.addWidget(self.enrollment_folder_input, 1)
        folder_layout.addWidget(browse_button)
        self.enrollment_method_combo.currentTextChanged.connect(self._update_enrollment_method)
        self.enrollment_start_button.clicked.connect(self._start_enrollment_from_ui)
        self.enrollment_cancel_button.clicked.connect(self._cancel_enrollment_from_ui)
        self.enrollment_validation_label.setObjectName("EnrollmentMessage")
        self.enrollment_validation_label.setWordWrap(True)

        start_layout.addWidget(start_title, 0, 0, 1, 2)
        start_layout.addWidget(QLabel("Kullanıcı adı"), 1, 0)
        start_layout.addWidget(self.enrollment_username_input, 2, 0)
        start_layout.addWidget(QLabel("Kayıt yöntemi"), 1, 1)
        start_layout.addWidget(self.enrollment_method_combo, 2, 1)
        start_layout.addWidget(self.enrollment_folder_widget, 3, 0, 1, 2)
        button_row = QHBoxLayout()
        button_row.addWidget(self.enrollment_start_button)
        button_row.addWidget(self.enrollment_cancel_button)
        button_row.addStretch(1)
        start_layout.addLayout(button_row, 4, 0, 1, 2)
        start_layout.addWidget(self.enrollment_validation_label, 5, 0, 1, 2)

        status_card = QFrame()
        status_card.setObjectName("EnrollmentCard")
        status_layout = QGridLayout(status_card)
        status_layout.setContentsMargins(18, 16, 18, 16)
        status_layout.setHorizontalSpacing(18)
        status_layout.setVerticalSpacing(8)
        status_title = QLabel("CANLI KAYIT DURUMU")
        status_title.setObjectName("CardTitle")
        self.enrollment_state_label.setObjectName("EnrollmentStatus")
        self.enrollment_state_label.setProperty("state", "neutral")
        self.enrollment_instruction_label.setWordWrap(True)
        self.enrollment_quality_label.setWordWrap(True)
        self.enrollment_message_label.setWordWrap(True)
        self.enrollment_import_label.setWordWrap(True)
        self.enrollment_stage_progress.setRange(0, 1)
        self.enrollment_stage_progress.setValue(0)
        self.enrollment_stage_progress.setFormat("Aşama: %v/%m")
        self.enrollment_total_progress.setRange(0, 1)
        self.enrollment_total_progress.setValue(0)
        self.enrollment_total_progress.setFormat("Genel: %v/%m")

        status_layout.addWidget(status_title, 0, 0)
        status_layout.addWidget(self.enrollment_state_label, 0, 1, Qt.AlignmentFlag.AlignRight)
        status_rows = (
            ("Mevcut aşama", self.enrollment_stage_label),
            ("Aşama açıklaması", self.enrollment_instruction_label),
            ("Aşama örnekleri", self.enrollment_stage_count_label),
            ("Toplam örnek", self.enrollment_total_count_label),
            ("Kalite", self.enrollment_quality_label),
            ("Mesaj", self.enrollment_message_label),
            ("Import özeti", self.enrollment_import_label),
        )
        for row, (label_text, value_label) in enumerate(status_rows, start=1):
            key_label = QLabel(label_text)
            key_label.setProperty("role", "muted")
            status_layout.addWidget(key_label, row, 0)
            status_layout.addWidget(value_label, row, 1)
        progress_row = len(status_rows) + 1
        status_layout.addWidget(self.enrollment_stage_progress, progress_row, 0, 1, 2)
        status_layout.addWidget(self.enrollment_total_progress, progress_row + 1, 0, 1, 2)
        status_layout.setColumnStretch(1, 1)

        self.enrollment_completion_frame.setObjectName("EnrollmentResultCard")
        completion_layout = QVBoxLayout(self.enrollment_completion_frame)
        completion_layout.setContentsMargins(18, 16, 18, 16)
        completion_layout.setSpacing(8)
        completion_title = QLabel("KAYIT TAMAMLANDI")
        completion_title.setObjectName("CardTitle")
        self.enrollment_completion_label.setWordWrap(True)
        self.enrollment_qr_path.setReadOnly(True)
        self.enrollment_qr_path.setPlaceholderText("Lonca mührü yolu")
        completion_layout.addWidget(completion_title)
        completion_layout.addWidget(self.enrollment_completion_label)
        completion_layout.addWidget(self.enrollment_qr_path)
        self.enrollment_completion_frame.hide()

        content_layout.addWidget(start_card)
        content_layout.addWidget(status_card)
        content_layout.addWidget(self.enrollment_completion_frame)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        page_layout.addWidget(scroll, 1)
        self._update_enrollment_method()
        return page

    def _settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 4, 8, 8)
        layout.setSpacing(12)
        title = QLabel("Ayarlar")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Değişiklikler mevcut VisionEngine ayarlarına uygulanır ve kalıcı olarak kaydedilir.")
        subtitle.setProperty("role", "muted")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setObjectName("SettingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 4, 0)
        content_layout.setSpacing(10)
        cards = QWidget()
        cards.setMaximumWidth(820)
        cards_grid = QGridLayout(cards)
        cards_grid.setContentsMargins(0, 0, 0, 0)
        cards_grid.setHorizontalSpacing(10)
        cards_grid.setVerticalSpacing(10)

        display_card = QFrame()
        display_card.setObjectName("SettingCard")
        display_layout = QVBoxLayout(display_card)
        display_layout.setContentsMargins(18, 16, 18, 16)
        display_layout.setSpacing(7)
        display_title = QLabel("GÖRÜNTÜ VE OVERLAY")
        display_title.setObjectName("CardTitle")
        display_layout.addWidget(display_title)
        checkboxes = (
            (self.hand_debug_checkbox, "set_hand_debug"),
            (self.face_debug_checkbox, "set_face_debug"),
            (self.mirror_checkbox, "set_mirror"),
            (self.spell_effects_checkbox, "set_spell_effects"),
        )
        for checkbox, action_name in checkboxes:
            checkbox.toggled.connect(
                lambda checked, name=action_name: self._send_action(f"{name}:{int(checked)}")
            )
            display_layout.addWidget(checkbox)
        display_layout.addStretch(1)

        mode_card = QFrame()
        mode_card.setObjectName("SettingCard")
        mode_layout = QVBoxLayout(mode_card)
        mode_layout.setContentsMargins(18, 16, 18, 16)
        mode_layout.setSpacing(7)
        mode_title = QLabel("ALGILAMA VE DOĞRULAMA")
        mode_title.setObjectName("CardTitle")
        mode_layout.addWidget(mode_title)
        verification_label = QLabel("Doğrulama modu")
        verification_label.setProperty("role", "muted")
        self.verification_mode_combo.addItems(["QR + Yüz", "Yalnızca Yüz"])
        self.verification_mode_combo.currentTextChanged.connect(
            lambda value: self._send_action(f"set_verification_mode:{value}")
        )
        mode_layout.addWidget(verification_label)
        mode_layout.addWidget(self.verification_mode_combo)

        detection_label = QLabel("Algılama profili")
        detection_label.setProperty("role", "muted")
        self.detection_profile_combo.addItems(["Hassas", "Dengeli", "Kararlı"])
        self.detection_profile_combo.currentTextChanged.connect(
            lambda value: self._send_action(f"set_detection_profile:{value}")
        )
        mode_layout.addSpacing(5)
        mode_layout.addWidget(detection_label)
        mode_layout.addWidget(self.detection_profile_combo)
        mode_layout.addStretch(1)

        cards_grid.addWidget(display_card, 0, 0)
        cards_grid.addWidget(mode_card, 0, 1)
        cards_grid.setColumnStretch(0, 1)
        cards_grid.setColumnStretch(1, 1)
        content_layout.addWidget(cards, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        return page

    def _system_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 4, 8, 8)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Sistem Durumu")
        title.setObjectName("PageTitle")
        self.system_refresh_button.clicked.connect(self._refresh_system_status)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.system_refresh_button)
        layout.addLayout(header)

        subtitle = QLabel("Kamera, modeller, profiller ve lonca mührü kaynakları")
        subtitle.setProperty("role", "muted")
        layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        rows_layout = QVBoxLayout(content)
        rows_layout.setContentsMargins(0, 0, 0, 0)
        rows_layout.setSpacing(8)
        labels = ["Kamera", *[item.label for item in get_system_status()]]
        for label_text in labels:
            row = QFrame()
            row.setObjectName("SystemRow")
            row_layout = QGridLayout(row)
            row_layout.setContentsMargins(14, 11, 14, 11)
            name_label = QLabel(label_text)
            status_label = QLabel("Bekleniyor")
            status_label.setObjectName("StatusValue")
            status_label.setProperty("state", "pending")
            hint_label = QLabel("")
            hint_label.setProperty("role", "muted")
            hint_label.setWordWrap(True)
            row_layout.addWidget(name_label, 0, 0)
            row_layout.addWidget(status_label, 0, 1, Qt.AlignmentFlag.AlignRight)
            row_layout.addWidget(hint_label, 1, 0, 1, 2)
            self._system_rows[label_text] = (status_label, hint_label)
            rows_layout.addWidget(row)
        rows_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        self._refresh_system_status()
        return page

    def _debug_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 4, 8, 8)
        layout.setSpacing(12)
        title = QLabel("Debug")
        title.setObjectName("PageTitle")
        subtitle = QLabel("VisionEngine debug_info verileri · D ile bölüm değiştir")
        subtitle.setProperty("role", "muted")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        for tab_name, fields in DEBUG_FIELDS.items():
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            grid = QGridLayout(content)
            grid.setContentsMargins(18, 16, 18, 16)
            grid.setHorizontalSpacing(24)
            grid.setVerticalSpacing(9)
            for row, (display_name, key) in enumerate(fields):
                name_label = QLabel(display_name)
                name_label.setProperty("role", "muted")
                value_label = QLabel("-")
                value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                value_label.setWordWrap(True)
                grid.addWidget(name_label, row, 0)
                grid.addWidget(value_label, row, 1)
                self._debug_value_labels[key] = value_label
            grid.setColumnStretch(1, 1)
            grid.setRowStretch(len(fields), 1)
            scroll.setWidget(content)
            self.debug_tabs.addTab(scroll, tab_name)

        layout.addWidget(self.debug_tabs, 1)
        return page

    def _simple_action_page(
        self,
        title: str,
        subtitle: str,
        content_label: QLabel,
        button_title: str,
        action: str,
    ) -> QWidget:
        page = self._simple_page(title, subtitle, content_label)
        button = QPushButton(button_title)
        button.clicked.connect(lambda: self._send_action(action))
        page.layout().insertWidget(page.layout().count() - 1, button, 0, Qt.AlignmentFlag.AlignLeft)
        return page

    def _simple_page(self, title: str, subtitle: str, content_label: QLabel) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 4, 8, 8)
        layout.setSpacing(12)
        title_label = QLabel(title)
        title_label.setObjectName("PageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setProperty("role", "muted")
        content_label.setWordWrap(True)
        card = QFrame()
        card.setObjectName("PageCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.addWidget(content_label)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addWidget(card, 1)
        layout.addStretch(0)
        return page

    def _info_card(self, title: str, content: QLabel) -> QWidget:
        content.setWordWrap(True)
        frame = QFrame()
        frame.setObjectName("InfoCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        layout.addWidget(title_label)
        layout.addWidget(content)
        return frame

    def _live_status_card(
        self,
        title: str,
        rows: tuple[tuple[str, QLabel], ...],
        action_button: QPushButton | None = None,
    ) -> QWidget:
        """Canlı Görüş sağ sütunu için sabit, kompakt bilgi kartı oluşturur."""
        frame = QFrame()
        frame.setObjectName("InfoCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(13, 11, 13, 11)
        layout.setSpacing(7)
        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        layout.addWidget(title_label)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(5)
        for row, (key, value_label) in enumerate(rows):
            key_label = QLabel(key)
            key_label.setObjectName("MetricKey")
            value_label.setObjectName("MetricValue")
            value_label.setWordWrap(True)
            grid.addWidget(key_label, row, 0)
            grid.addWidget(value_label, row, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        if action_button is not None:
            action_button.setProperty("compact", True)
            layout.addWidget(action_button)
        return frame

    def _create_actions(self) -> None:
        """Pencere genelinde çalışan çıkış ve kitap kısayollarını oluşturur."""
        actions = (
            ("Çıkış", Qt.Key.Key_Escape, self.close),
            ("Büyü Kitabı", Qt.Key.Key_B, self._toggle_spellbook_page),
            ("Önceki Kitap Sayfası", Qt.Key.Key_Left, lambda: self._change_spellbook_page(-1)),
            ("Sonraki Kitap Sayfası", Qt.Key.Key_Right, lambda: self._change_spellbook_page(1)),
        )
        for title, key, callback in actions:
            action = QAction(title, self)
            action.setShortcut(QKeySequence(key))
            action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
            action.triggered.connect(callback)
            self.addAction(action)

    def _navigate_to(self, page_name: str, sync_engine: bool = True) -> None:
        """İstenen Qt sayfasını gösterir ve aktif navigasyon durumunu günceller."""
        if page_name not in PAGE_ORDER:
            return
        previous_page = self._current_page
        self._current_page = page_name
        self.page_stack.setCurrentIndex(PAGE_ORDER.index(page_name))
        for name, button in self._nav_buttons.items():
            button.setChecked(name == page_name)

        if not sync_engine or previous_page == page_name:
            return
        if page_name == "spellbook":
            self._send_action("open_spellbook")
        elif previous_page == "spellbook":
            self._send_action("close_spellbook")
        if page_name == "system":
            self._refresh_system_status()
        elif page_name == "debug" and self._last_payload:
            self._update_debug(self._last_payload, force=True)
        elif page_name == "settings" and self._last_payload:
            self._update_settings(self._last_payload, force=True)
        elif page_name == "enrollment" and self._last_payload:
            self._update_enrollment(self._last_payload, force=True)

    def _cycle_debug_tab(self) -> None:
        """D tuşuyla dört sabit debug bölümünü sırayla seçer."""
        if self._current_page != "debug":
            return
        next_index = (self.debug_tabs.currentIndex() + 1) % self.debug_tabs.count()
        self.debug_tabs.setCurrentIndex(next_index)
        self._send_action("next_debug_page")

    def _toggle_spellbook_page(self) -> None:
        """B ile Canlı Görüş ve Büyü Kitabı arasında geçiş yapar."""
        if self._current_page == "live":
            self._navigate_to("spellbook")
        elif self._current_page == "spellbook":
            self._navigate_to("live")

    def _change_spellbook_page(self, direction: int) -> None:
        """Kitap aktifken mevcut VisionEngine sayfa aksiyonunu gönderir."""
        if self._current_page != "spellbook":
            return
        if direction > 0 and not self.next_spellbook_button.isEnabled():
            return
        if direction < 0 and not self.previous_spellbook_button.isEnabled():
            return
        action = "next_spellbook_page" if direction > 0 else "previous_spellbook_page"
        self._send_action(action)

    def _update_enrollment_method(self, *_args) -> None:
        """Fotoğraf importuna ait klasör alanını seçili yönteme göre gösterir."""
        is_import = self.enrollment_method_combo.currentText() == "Fotoğraf İçe Aktarma"
        self.enrollment_folder_widget.setVisible(is_import)

    def _choose_enrollment_directory(self) -> None:
        """Fotoğraf import klasörünü Qt dosya diyaloğuyla seçer."""
        selected = QFileDialog.getExistingDirectory(self, "Yüz fotoğrafları klasörünü seç")
        if selected:
            self.enrollment_folder_input.setText(selected)
            self.enrollment_validation_label.setText("")

    def _start_enrollment_from_ui(self) -> None:
        """Qt girişlerini doğrulayıp mevcut worker kuyruğuna kayıt komutu gönderir."""
        username = self.enrollment_username_input.text().strip()
        if not username:
            self.enrollment_validation_label.setText("Kullanıcı adı boş bırakılamaz.")
            self._set_widget_state(self.enrollment_validation_label, "error")
            return
        if self._enrollment_request_pending:
            return

        is_import = self.enrollment_method_combo.currentText() == "Fotoğraf İçe Aktarma"
        import_directory = self.enrollment_folder_input.text().strip()
        if is_import and not import_directory:
            self.enrollment_validation_label.setText("Fotoğraf içe aktarma için bir klasör seçin.")
            self._set_widget_state(self.enrollment_validation_label, "warning")
            return

        self.enrollment_validation_label.setText("Kayıt başlatılıyor…")
        self._set_widget_state(self.enrollment_validation_label, "neutral")
        self._enrollment_request_pending = True
        self.enrollment_start_button.setEnabled(False)
        self._send_action(
            {
                "command": "start_enrollment",
                "username": username,
                "mode": "import" if is_import else "camera",
                "import_directory": import_directory or None,
            }
        )

    def _cancel_enrollment_from_ui(self) -> None:
        """Mevcut manager durumunu worker üzerinden sıfırlar."""
        self._enrollment_request_pending = False
        self.enrollment_start_button.setEnabled(True)
        self.enrollment_username_input.setEnabled(True)
        self.enrollment_method_combo.setEnabled(True)
        self.enrollment_validation_label.setText("Kayıt sıfırlanıyor…")
        self._set_widget_state(self.enrollment_validation_label, "neutral")
        self._send_action({"command": "cancel_enrollment"})

    def _start_worker(self) -> None:
        """Kamera worker'ını ayrı thread'de başlatır."""
        if self._worker_thread is not None:
            return
        self._worker_thread = QThread(self)
        self._worker = CameraWorker()
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.start)
        self._worker.frame_ready.connect(self._on_frame_ready)
        self._worker.error.connect(self._on_worker_error)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)
        self._worker_thread.finished.connect(self._on_thread_finished)
        self._worker_thread.start()

    def _stop_worker(self) -> None:
        """Kamera worker'ını durdurur ve thread'in kapanmasını bekler."""
        if self._worker is not None:
            self._worker.stop()
        if self._worker_thread is not None:
            self._worker_thread.quit()
            self._worker_thread.wait(3000)
        self._worker = None
        self._worker_thread = None

    def _send_action(self, action) -> None:
        """Worker'a kullanıcı aksiyonunu iletir."""
        if self._worker is not None:
            self._worker.request_action(action)

    def _on_frame_ready(self, image, payload: dict) -> None:
        """Worker'dan gelen kare ve durum bilgisini ilgili Qt sayfalarına uygular."""
        self._last_payload = payload
        self.frame_view.set_image(image)
        first_camera_frame = not self._camera_frame_received
        self._camera_frame_received = True
        self._capture_resolution = f"{image.width()}x{image.height()}"
        self.live_resolution_label.setText(self._capture_resolution)
        self.live_fps_label.setText(f"FPS {payload.get('debug_info', {}).get('fps', '-')}")
        self.live_camera_status_label.setText("Kamera aktif")
        self._set_widget_state(self.live_camera_status_label, "verified")
        self._update_profile(payload)
        if self._current_page == "enrollment":
            self._update_enrollment(payload)
        self._update_spell(payload)
        self._update_trial(payload)
        self._update_spellbook(payload)
        self._update_settings(payload)
        self._update_debug(payload)
        self._update_notifications(payload)
        if first_camera_frame and self._current_page == "system":
            self._refresh_system_status()

    def _update_profile(self, payload: dict) -> None:
        username = payload.get("username") or "Misafir"
        if username == "-":
            username = "Misafir"
        rank = payload.get("rank") or "Misafir Büyücü"
        if rank == "-":
            rank = "Misafir Büyücü"
        verification = payload.get("verification_status") or "Bekleniyor"
        self.top_user_label.setText(username)
        self.top_rank_label.setText(rank)
        self.top_verification_label.setText(verification)
        self.live_user_label.setText(username)
        self.live_rank_label.setText(rank)
        self.session_label.setText(verification)

        grace = float(payload.get("grace_remaining_seconds", 0.0) or 0.0)
        in_grace = payload.get("session_state") == "GRACE_PERIOD" and grace > 0
        self.top_grace_label.setVisible(in_grace)
        self.top_grace_label.setText(f"Grace: {grace:.1f} sn" if in_grace else "")
        self.live_grace_label.setText(f"{grace:.1f} sn" if in_grace else "Pasif")

        verification_lower = verification.lower()
        if in_grace:
            verification_state = "warning"
        elif any(value in verification_lower for value in ("onaylandı", "tanındı", "doğrulandı")):
            verification_state = "verified"
        elif any(value in verification_lower for value in ("hata", "eşleşmedi", "süresi doldu", "expired")):
            verification_state = "error"
        else:
            verification_state = "neutral"
        self._set_widget_state(self.top_verification_label, verification_state)
        self._set_widget_state(self.session_label, verification_state)
        self._set_widget_state(self.live_grace_label, "warning" if in_grace else "neutral")

        enrollment = payload.get("enrollment")
        if enrollment is not None and getattr(enrollment, "is_active", False):
            self.registration_label.setText(
                f"Kullanıcı: {getattr(enrollment, 'username', '-')}\n"
                f"Aşama: {getattr(enrollment, 'stage_name', '-')}\n"
                f"Örnek: {getattr(enrollment, 'sample_count', 0)}/{getattr(enrollment, 'target_count', 0)}\n"
                f"Kalite: {getattr(enrollment, 'quality_status', '-')}\n"
                f"Mesaj: {getattr(enrollment, 'message', '-')}"
            )
        else:
            self.registration_label.setText(
                f"Aktif kullanıcı: {username}\n"
                f"Doğrulama: {verification}\n"
                "Yeni kayıt başlatmak için Kayıt Başlat düğmesini veya E tuşunu kullan."
            )

    def _update_spell(self, payload: dict) -> None:
        cooldown = float(payload.get("cooldown", 0.0) or 0.0)
        progress = float(payload.get("prepare_progress", 0.0) or 0.0)
        active_spell = payload.get("active_spell", "Yok")
        self.spell_label.setText(active_spell)
        self.live_prepare_label.setText(f"%{int(progress * 100)} · {payload.get('spell_status', '-')}")
        self.live_cooldown_label.setText(f"{cooldown:.1f} sn" if cooldown > 0 else "Hazır")
        self.allowed_spells_label.setText(", ".join(payload.get("allowed_spells", [])) or "-")
        self._set_widget_state(self.spell_label, "rank" if active_spell != "Yok" else "neutral")

    def _update_trial(self, payload: dict) -> None:
        state = payload.get("trial_state", "idle")
        completed_steps = list(payload.get("trial_completed_steps", []))
        required_spell = payload.get("trial_required_spell", "-")
        completed_set = set(completed_steps)
        pending_steps = [step for step in TRIAL_STEPS if step not in completed_set]

        state_text = {"idle": "Bekliyor", "active": "Aktif", "completed": "Tamamlandı"}.get(state, state)
        self.trial_label.setText(state_text)
        self.live_trial_step_label.setText(required_spell if required_spell != "-" else "Tamamlandı")
        self.live_trial_progress_label.setText(payload.get("trial_progress", "0/3"))
        self._set_widget_state(
            self.trial_label,
            "verified" if state == "completed" else ("warning" if state == "active" else "neutral"),
        )
        self.trial_state_label.setText(state_text)
        self.trial_completed_label.setText(", ".join(completed_steps) or "-")
        self.trial_pending_label.setText(", ".join(pending_steps) or "-")
        self.trial_message_label.setText(payload.get("trial_message", "-"))
        self.trial_progress_bar.setValue(len(completed_steps))

        for index, spell_name in enumerate(TRIAL_STEPS, start=1):
            if spell_name in completed_set:
                step_state, step_text = "complete", "Tamamlandı"
            elif state == "active" and spell_name == required_spell:
                step_state, step_text = "active", "Aktif"
            else:
                step_state, step_text = "pending", "Bekliyor"
            label = self.trial_step_labels[spell_name]
            label.setText(f"{index}. {spell_name} · {step_text}")
            self._set_widget_state(label, step_state)

    def _update_spellbook(self, payload: dict) -> None:
        page = max(0, min(3, int(payload.get("spellbook_page", 0) or 0)))
        self.previous_spellbook_button.setEnabled(page > 0)
        self.next_spellbook_button.setEnabled(page < 3)

        spell_name = SPELLBOOK_PAGES[page]
        if spell_name is None:
            self.spellbook_page_label.setText("Kapak · 0/3")
            self.spellbook_title_label.setText("Büyü Kitabı")
            self._set_spellbook_status("VisionForge Lonca Arşivi", "cover")
            self.spellbook_type_label.setText("")
            self.spellbook_trigger_label.setText("Sağ ok veya Sonraki ile aç")
            self.spellbook_rank_label.setText("")
            self.spellbook_description_label.setText("Aktif profile ait büyü yetkilerini görüntüler.")
            return

        details = _SPELLBOOK_DETAILS[spell_name]
        is_open = spell_name in set(payload.get("allowed_spells", []))
        self.spellbook_page_label.setText(f"Sayfa {page}/3")
        self.spellbook_title_label.setText(spell_name)
        self._set_spellbook_status("Durum: Açık" if is_open else "Durum: Kilitli", "open" if is_open else "locked")
        self.spellbook_type_label.setText(f"Tür: {details['type']}")
        self.spellbook_trigger_label.setText(f"Tetikleme: {details['trigger']}")
        self.spellbook_rank_label.setText(f"Gereken yetki veya rütbe: {details['required_rank']}")
        self.spellbook_description_label.setText(f"Açıklama: {details['effect']}")

    def _update_enrollment(self, payload: dict, force: bool = False) -> None:
        if self._current_page != "enrollment" and not force:
            return
        status = payload.get("enrollment")
        if status is None:
            if not self._enrollment_request_pending:
                self.enrollment_state_label.setText("Bekliyor")
                self._set_widget_state(self.enrollment_state_label, "neutral")
                self.enrollment_stage_label.setText("-")
                self.enrollment_instruction_label.setText("Kullanıcı adı ve kayıt yöntemi seçin.")
                self.enrollment_stage_count_label.setText("0/0")
                self.enrollment_total_count_label.setText("0/0")
                self.enrollment_quality_label.setText("-")
                self.enrollment_message_label.setText("Kayıt bekleniyor")
                self.enrollment_import_label.setText("Kabul: 0 · Red: 0")
                self.enrollment_stage_progress.setRange(0, 1)
                self.enrollment_stage_progress.setValue(0)
                self.enrollment_total_progress.setRange(0, 1)
                self.enrollment_total_progress.setValue(0)
                self.enrollment_completion_frame.hide()
            return

        self._enrollment_request_pending = False
        is_active = bool(getattr(status, "is_active", False))
        is_complete = bool(getattr(status, "is_complete", False))
        username = str(getattr(status, "username", "") or "")
        sample_count = int(getattr(status, "sample_count", 0) or 0)
        target_count = max(1, int(getattr(status, "target_count", 1) or 1))
        stage_sample_count = int(getattr(status, "stage_sample_count", 0) or 0)
        stage_target_count = max(1, int(getattr(status, "stage_target_count", 1) or 1))
        rejected_count = int(getattr(status, "rejected_count", 0) or 0)
        message = str(getattr(status, "message", "") or "-")
        quality_status = str(getattr(status, "quality_status", "") or "-")
        import_report = str(getattr(status, "import_report", "") or "")
        qr_path = str(getattr(status, "qr_path", "") or "")

        if username:
            self.enrollment_username_input.setText(username)
        controls_enabled = not is_active
        self.enrollment_username_input.setEnabled(controls_enabled)
        self.enrollment_method_combo.setEnabled(controls_enabled)
        self.enrollment_folder_widget.setEnabled(controls_enabled)
        self.enrollment_start_button.setEnabled(controls_enabled)

        if is_complete:
            state_text, state_style = "Tamamlandı", "verified"
        elif is_active:
            state_text, state_style = "Aktif", "warning"
        else:
            state_text, state_style = "Bekliyor", "neutral"
        self.enrollment_state_label.setText(state_text)
        self._set_widget_state(self.enrollment_state_label, state_style)
        self.enrollment_stage_label.setText(
            str(getattr(status, "stage_name", "") or "-") if is_active or is_complete else "-"
        )
        self.enrollment_instruction_label.setText(str(getattr(status, "instruction", "") or "-"))
        self.enrollment_stage_count_label.setText(f"{stage_sample_count}/{stage_target_count}")
        self.enrollment_total_count_label.setText(f"{sample_count}/{target_count}")
        self.enrollment_quality_label.setText(quality_status)
        self.enrollment_message_label.setText(message)
        import_text = f"Kabul: {sample_count} · Red: {rejected_count}"
        if import_report:
            import_text = f"{import_text}\n{import_report}"
        self.enrollment_import_label.setText(import_text)
        self.enrollment_stage_progress.setRange(0, stage_target_count)
        self.enrollment_stage_progress.setValue(min(stage_sample_count, stage_target_count))
        self.enrollment_total_progress.setRange(0, target_count)
        self.enrollment_total_progress.setValue(min(sample_count, target_count))

        self.enrollment_completion_frame.setVisible(is_complete)
        if is_complete:
            self.enrollment_completion_label.setText(
                "Yüz modeli eğitildi\n"
                "Kullanıcı profili oluşturuldu\n"
                f"Lonca mührü oluşturuldu\nToplam kullanılan örnek: {sample_count}"
            )
            self.enrollment_qr_path.setText(qr_path)

        self.enrollment_validation_label.setText("")

    def _set_spellbook_status(self, text: str, state: str) -> None:
        self.spellbook_status_label.setText(text)
        self.spellbook_status_label.setProperty("state", state)
        self.spellbook_status_label.style().unpolish(self.spellbook_status_label)
        self.spellbook_status_label.style().polish(self.spellbook_status_label)

    def _update_settings(self, payload: dict, force: bool = False) -> None:
        settings = payload.get("settings", {})
        mode = "QR + Yüz" if settings.get("verification_requires_qr", True) else "Yalnızca Yüz"
        state = (
            bool(settings.get("show_hand_debug", False)),
            bool(settings.get("show_face_debug", False)),
            bool(settings.get("mirror_camera", False)),
            bool(settings.get("spell_effects_enabled", True)),
            mode,
            settings.get("detection_profile", "Dengeli"),
        )
        if not force and state == self._last_settings_state:
            return
        self._last_settings_state = state
        widgets_and_values = (
            (self.hand_debug_checkbox, state[0]),
            (self.face_debug_checkbox, state[1]),
            (self.mirror_checkbox, state[2]),
            (self.spell_effects_checkbox, state[3]),
            (self.verification_mode_combo, state[4]),
            (self.detection_profile_combo, state[5]),
        )
        for widget, value in widgets_and_values:
            widget.blockSignals(True)
            if isinstance(widget, QCheckBox):
                widget.setChecked(value)
            else:
                widget.setCurrentText(value)
            widget.blockSignals(False)

    def _refresh_system_status(self) -> None:
        """Dosya/model durumunu yalnızca sayfa açılışında veya Yenile ile okur."""
        camera_status, camera_hint = self._system_rows["Kamera"]
        camera_status.setText("Var" if self._camera_frame_received else "Bekleniyor")
        camera_hint.setText(
            f"Aktif kamera akışı · {self._capture_resolution}"
            if self._camera_frame_received
            else "İlk kamera karesi bekleniyor"
        )
        self._set_widget_state(camera_status, "ok" if self._camera_frame_received else "pending")

        for item in get_system_status():
            status_label, hint_label = self._system_rows[item.label]
            status_label.setText(item.status_text)
            hint_label.setText(item.hint or item.importance_text)
            self._set_widget_state(status_label, "ok" if item.exists else "warning")

    def _update_debug(self, payload: dict, force: bool = False) -> None:
        if self._current_page != "debug" and not force:
            return
        now = time.monotonic()
        if not force and now - self._last_debug_update < 0.25:
            return
        self._last_debug_update = now
        debug = dict(payload.get("debug_info", {}))
        debug["capture_resolution"] = self._capture_resolution
        debug["trial_completed_steps"] = ", ".join(payload.get("trial_completed_steps", [])) or "-"
        for key, label in self._debug_value_labels.items():
            label.setText(str(debug.get(key, "-")))

    def _set_widget_state(self, widget: QWidget, state: str) -> None:
        if widget.property("state") == state:
            return
        widget.setProperty("state", state)
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _update_notifications(self, payload: dict) -> None:
        notifications = payload.get("notifications", [])
        recent = [str(message).replace("\n", " ")[:160] for message in notifications[-2:]]
        self.notifications_label.setText("\n".join(recent) if recent else "Bildirim yok")

    def _on_worker_error(self, message: str) -> None:
        """Worker hatasını sistem sayfasına ve kullanıcıya gösterir."""
        self.system_label.setText(f"Hata:\n{message}")
        if "Kamera" in self._system_rows:
            status_label, hint_label = self._system_rows["Kamera"]
            status_label.setText("Hata")
            hint_label.setText(message)
            self._set_widget_state(status_label, "warning")
        self.live_camera_status_label.setText("Kamera hatası")
        self._set_widget_state(self.live_camera_status_label, "error")
        QMessageBox.warning(self, "VisionForge", message)

    def _on_thread_finished(self) -> None:
        """Thread referanslarını temizler."""
        self._worker = None
        self._worker_thread = None
        if self.isVisible():
            self.live_camera_status_label.setText("Kamera pasif")
            self._set_widget_state(self.live_camera_status_label, "neutral")

    def _apply_style(self) -> None:
        """Ortak koyu temayı pencereye uygular."""
        self.setStyleSheet(application_stylesheet())

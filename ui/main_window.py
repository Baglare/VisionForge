"""VisionForge için PySide6 ana pencere kabuğu."""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.camera_worker import CameraWorker
from ui.frame_view import FrameView


class MainWindow(QMainWindow):
    """Modern, yeniden boyutlandırılabilir VisionForge masaüstü kabuğu."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VisionForge")
        self.resize(1360, 820)
        self._worker_thread: QThread | None = None
        self._worker: CameraWorker | None = None
        self._last_payload: dict = {}

        self.frame_view = FrameView()
        self.profile_label = QLabel("Profil bekleniyor")
        self.verification_label = QLabel("Doğrulama: Bekleniyor")
        self.grace_label = QLabel("")
        self.spell_label = QLabel("Aktif Büyü: Yok")
        self.trial_label = QLabel("Trial: Kapalı")
        self.spellbook_label = QLabel("Büyü Kitabı: açık büyüler burada listelenir.")
        self.system_label = QLabel("Sistem Durumu: kamera başlatılıyor")
        self.debug_label = QLabel("Debug kapalı")
        self.notifications_label = QLabel("")

        self._build_ui()
        self._create_actions()
        self._start_worker()

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
            self._send_action("toggle_spellbook")
        elif key == Qt.Key.Key_T:
            self._send_action("start_trial")
        elif key == Qt.Key.Key_R:
            self._send_action("reset_auth")
        elif key == Qt.Key.Key_E:
            self._send_action("start_enrollment")
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
            self._send_action("next_debug_page")
        elif key == Qt.Key.Key_Right:
            self._send_action("next_spellbook_page")
        elif key == Qt.Key.Key_Left:
            self._send_action("previous_spellbook_page")
        elif key == Qt.Key.Key_1:
            self._send_action("toggle_hand_debug")
        elif key == Qt.Key.Key_2:
            self._send_action("toggle_face_debug")
        elif key == Qt.Key.Key_3:
            self._send_action("cycle_verification_mode")
        elif key == Qt.Key.Key_4:
            self._send_action("toggle_spellbook")
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
        """Ana pencere layout'unu kurar."""
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        root_layout.addWidget(self._navigation_panel(), 0)
        root_layout.addWidget(self._center_panel(), 1)
        root_layout.addWidget(self._right_panel(), 0)
        self.setCentralWidget(root)
        self._apply_style()

    def _navigation_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("NavPanel")
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("VisionForge"))

        buttons = [
            ("Canlı Görüş", None),
            ("Büyü Kitabı", "toggle_spellbook"),
            ("Trial", "start_trial"),
            ("Kayıt", "start_enrollment"),
            ("Ayarlar", "toggle_settings"),
            ("Sistem Durumu", "toggle_system_status"),
            ("Debug", "toggle_debug"),
        ]
        for title, action in buttons:
            button = QPushButton(title)
            if action:
                button.clicked.connect(lambda checked=False, action=action: self._send_action(action))
            layout.addWidget(button)

        layout.addStretch(1)
        layout.addWidget(QLabel("Kısayollar\nB: Kitap\nT: Trial\nR: Reset\nE: Kayıt\nEsc: Çıkış"))
        return panel

    def _center_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        top = QFrame()
        top.setObjectName("TopPanel")
        top_layout = QVBoxLayout(top)
        top_layout.addWidget(self.profile_label)
        top_layout.addWidget(self.verification_label)
        top_layout.addWidget(self.grace_label)
        layout.addWidget(top, 0)
        layout.addWidget(self.frame_view, 1)
        self.notifications_label.setWordWrap(True)
        layout.addWidget(self.notifications_label, 0)
        return panel

    def _right_panel(self) -> QWidget:
        panel = QScrollArea()
        panel.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        for label in (
            self.spell_label,
            self.trial_label,
            self.spellbook_label,
            self.system_label,
            self.debug_label,
        ):
            label.setWordWrap(True)
            frame = QFrame()
            frame.setObjectName("InfoCard")
            frame_layout = QVBoxLayout(frame)
            frame_layout.addWidget(label)
            layout.addWidget(frame)
        layout.addStretch(1)
        panel.setWidget(content)
        panel.setMinimumWidth(330)
        return panel

    def _create_actions(self) -> None:
        """Menü kısayolları için Qt action nesneleri oluşturur."""
        exit_action = QAction("Çıkış", self)
        exit_action.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        exit_action.triggered.connect(self.close)
        self.addAction(exit_action)

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

    def _send_action(self, action: str) -> None:
        """Worker'a kullanıcı aksiyonunu iletir."""
        if self._worker is not None:
            self._worker.request_action(action)

    def _on_frame_ready(self, image, payload: dict) -> None:
        """Worker'dan gelen kare ve durum bilgisini UI'ye uygular."""
        self._last_payload = payload
        self.frame_view.set_image(image)
        self._update_profile(payload)
        self._update_spell(payload)
        self._update_trial(payload)
        self._update_spellbook(payload)
        self._update_system(payload)
        self._update_debug(payload)
        self._update_notifications(payload)

    def _update_profile(self, payload: dict) -> None:
        enrollment = payload.get("enrollment")
        self.profile_label.setText(
            f"{payload.get('username', '-')}\n"
            f"{payload.get('rank', '-')}\n"
            f"{payload.get('guild_name', '-')}"
        )
        if enrollment is not None and getattr(enrollment, "is_active", False):
            self.verification_label.setText(
                f"Kayıt: {getattr(enrollment, 'username', '-')}\n"
                f"Aşama: {getattr(enrollment, 'stage_name', '-')}\n"
                f"Örnek: {getattr(enrollment, 'sample_count', 0)}/{getattr(enrollment, 'target_count', 0)}\n"
                f"Kalite: {getattr(enrollment, 'quality_status', '-')}"
            )
        else:
            self.verification_label.setText(
                f"Doğrulama: {payload.get('verification_status', '-')}\n"
                f"Yüz: {payload.get('status_text', '-')}\n"
                f"El: {payload.get('hand_status_text', '-')}"
            )
        grace = float(payload.get("grace_remaining_seconds", 0.0) or 0.0)
        if payload.get("session_state") == "GRACE_PERIOD" and grace > 0:
            self.grace_label.setText(f"Oturum korunuyor\nYüzünü tekrar göster · {grace:.1f} sn")
        elif payload.get("session_state") == "EXPIRED":
            self.grace_label.setText("Doğrulama süresi doldu\nYüzünü ve gerekiyorsa lonca mührünü yeniden göster")
        else:
            self.grace_label.setText("")

    def _update_spell(self, payload: dict) -> None:
        cooldown = float(payload.get("cooldown", 0.0) or 0.0)
        progress = float(payload.get("prepare_progress", 0.0) or 0.0)
        self.spell_label.setText(
            f"Aktif Büyü: {payload.get('active_spell', 'Yok')}\n"
            f"Durum: {payload.get('spell_status', '-')}\n"
            f"Cooldown: {cooldown:.1f} sn\n"
            f"Hazırlık: %{int(progress * 100)}\n"
            f"Açık Büyüler: {', '.join(payload.get('allowed_spells', [])) or '-'}"
        )

    def _update_trial(self, payload: dict) -> None:
        self.trial_label.setText(
            f"Trial: {payload.get('trial_state', '-')}\n"
            f"Sıradaki Büyü: {payload.get('trial_required_spell', '-')}\n"
            f"Mühürler: {payload.get('trial_progress', '-')}\n"
            f"Mesaj: {payload.get('trial_message', '-')}"
        )

    def _update_spellbook(self, payload: dict) -> None:
        settings = payload.get("settings", {})
        visible = "Açık" if settings.get("show_spellbook", False) else "Kapalı"
        self.spellbook_label.setText(
            f"Büyü Kitabı: {visible}\n"
            f"Sayfa: {payload.get('spellbook_page', 0)}\n"
            f"Açık Büyüler: {', '.join(payload.get('allowed_spells', [])) or '-'}\n"
            "B ile aç/kapat, sağ/sol ok ile sayfa değiştir."
        )

    def _update_system(self, payload: dict) -> None:
        settings = payload.get("settings", {})
        mode = "QR + Yüz" if settings.get("verification_requires_qr", True) else "Yalnızca Yüz"
        lines = [
            "Ayarlar",
            f"Q menüsü: {'Açık' if settings.get('show_settings_menu') else 'Kapalı'}",
            f"Doğrulama modu: {mode}",
            f"Algılama profili: {settings.get('detection_profile', '-')}",
            f"El çizimi: {'Açık' if settings.get('show_hand_debug') else 'Kapalı'}",
            f"Yüz kutusu: {'Açık' if settings.get('show_face_debug') else 'Kapalı'}",
            f"Kamera aynalama: {'Açık' if settings.get('mirror_camera') else 'Kapalı'}",
        ]
        if settings.get("show_settings_menu"):
            lines.extend(
                [
                    "",
                    "1 El çizimi | 2 Yüz kutusu",
                    "3 Doğrulama | 4 Kitap",
                    "5 Debug | 6 Efekt | 7 Ayna",
                    "8 Sistem | 9 Profil | 0 Reset",
                ]
            )
        if settings.get("show_system_status"):
            lines.append("")
            lines.append("Sistem Durumu")
            for item in payload.get("system_items", []):
                hint = f" - {item.get('hint')}" if item.get("hint") else ""
                lines.append(f"{item.get('label')}: {item.get('status')}{hint}")
        self.system_label.setText("\n".join(lines))

    def _update_debug(self, payload: dict) -> None:
        debug = payload.get("debug_info", {})
        settings = payload.get("settings", {})
        if not settings.get("show_debug_page", False):
            self.debug_label.setText("Debug kapalı")
            return
        lines = [
            f"Debug sayfa: {debug.get('debug_page', '-')}",
            f"FPS: {debug.get('fps', '-')}",
            f"Session: {debug.get('session_state', '-')}",
            f"Grace: {debug.get('grace_remaining_seconds', '-')}",
            f"Face label: {debug.get('face_identity_stable_label', '-')}",
            f"Face score: {debug.get('face_identity_score', '-')}",
            f"Hands: {debug.get('raw_hand_count', '-')}",
            f"Tracker: {debug.get('tracker_source', '-')}",
            f"Trial: {debug.get('trial_state', '-')}",
        ]
        self.debug_label.setText("\n".join(lines))

    def _update_notifications(self, payload: dict) -> None:
        notifications = payload.get("notifications", [])
        self.notifications_label.setText("\n".join(notifications[-3:]))

    def _on_worker_error(self, message: str) -> None:
        """Worker hatasını kullanıcıya gösterir."""
        self.system_label.setText(f"Hata:\n{message}")
        QMessageBox.warning(self, "VisionForge", message)

    def _on_thread_finished(self) -> None:
        """Thread referanslarını temizler."""
        self._worker = None
        self._worker_thread = None

    def _apply_style(self) -> None:
        """Sade ve koyu masaüstü temasını uygular."""
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #11151b;
                color: #e8edf2;
                font-family: Segoe UI, Arial;
                font-size: 13px;
            }
            QPushButton {
                background: #1d2733;
                border: 1px solid #344150;
                border-radius: 6px;
                padding: 9px 12px;
                text-align: left;
            }
            QPushButton:hover {
                background: #263446;
            }
            #NavPanel, #TopPanel, #InfoCard {
                background: #171d25;
                border: 1px solid #2b3542;
                border-radius: 8px;
            }
            QLabel {
                color: #e8edf2;
            }
            QScrollArea {
                border: none;
            }
            """
        )

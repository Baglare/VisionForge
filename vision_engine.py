"""OpenCV pencere döngüsünden bağımsız VisionForge görüntü işleme çekirdeği."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import time

import cv2

from auth.verification_session import VerificationSession
from demo_guide import DemoGuide
from detectors.face_detector import FaceDetectionResult, FaceDetector
from detectors.face_identity_detector import FaceIdentityDetector
from detectors.guild_seal_detector import GuildSealDetector
from detectors.hand_detector import HandData, HandDetectionResult, HandDetector
from effects import Effects
from enrollment.enrollment_manager import EnrollmentManager, EnrollmentStatus
from guild_profile import find_profile_by_face_label, guest_profile, repair_local_profiles
from settings_manager import load_ui_settings, save_ui_settings
from spell_engine import SpellEngine
from system_status import get_system_status, has_registered_wizard
from tracking.hand_state_tracker import HandStateTracker
from trial_engine import TrialEngine, TrialStatus
from ui_notifications import Notification, NotificationManager


RIGHT_ARROW_ACTION = "next_spellbook_page"
LEFT_ARROW_ACTION = "previous_spellbook_page"


@dataclass
class VisionEngineResult:
    """UI katmanına tek karelik işleme sonucunu taşır."""

    display_frame: object
    active_profile: object
    allowed_spells: list[str]
    verification_status: str
    session_state: str
    grace_remaining_seconds: float
    spell_result: object | None
    trial_status: TrialStatus
    debug_info: dict
    notifications: list[Notification]
    enrollment_status: EnrollmentStatus | None = None
    status_text: str = ""
    hand_status_text: str = ""
    spellbook_page: int = 0
    ui_settings: dict = field(default_factory=dict)


class VisionEngine:
    """Dedektörleri, doğrulamayı, büyüleri ve OpenCV overlay çizimlerini yönetir."""

    def __init__(self) -> None:
        self.effects = Effects()
        self.spell_engine = SpellEngine()
        self.trial_engine = TrialEngine()
        self.demo_guide = DemoGuide()
        self.enrollment_manager = EnrollmentManager()
        self.face_identity_detector = FaceIdentityDetector()
        self.guild_seal_detector = GuildSealDetector()
        self.hand_state_tracker = HandStateTracker()
        self.notification_manager = NotificationManager()
        self.verification_session = VerificationSession()

        self.ui_settings = load_ui_settings()
        self.ui_settings["debug_page"] = int(self.ui_settings.get("debug_page", 0)) % 4
        self.spellbook_page = 0
        self.face_history = deque(maxlen=8)
        self.face_confirmed = False
        self.missing_face_frames = 0
        self.enrollment_reload_done = False
        self.last_enrollment_status: EnrollmentStatus | None = None
        self.last_frame_time = time.monotonic()
        self.fps = 0.0
        self.notification_state = {
            "verification_status": "",
            "recognized_user": "-",
            "active_spell_name": "",
            "locked_spell_attempt": "",
            "trial_state": "idle",
        }

        self.face_detector = FaceDetector(**self._face_detector_options(self.ui_settings["detection_profile"]))
        self.hand_detector = HandDetector(**self._hand_detector_options(self.ui_settings["detection_profile"]))
        self._emit_startup_warnings()

    def process_frame(self, processing_frame) -> VisionEngineResult:
        """Tek ham kamera karesini işler ve UI'ye aktarılacak sonucu döndürür."""
        display_frame = (
            cv2.flip(processing_frame, 1)
            if self.ui_settings["mirror_camera"]
            else processing_frame.copy()
        )
        self._update_fps()

        face_result = self.face_detector.detect(processing_frame)
        display_face_result = self._to_display_face_result(
            face_result,
            display_frame.shape[1],
            self.ui_settings["mirror_camera"],
        )
        self.face_confirmed, self.missing_face_frames = self._update_face_confirmation(
            face_result,
            self.face_history,
            self.face_confirmed,
            self.missing_face_frames,
        )

        if self.enrollment_manager.is_active:
            return self._process_enrollment_frame(processing_frame, display_frame, face_result, display_face_result)

        hand_result = self.hand_detector.detect(processing_frame)
        hand_state = self.hand_state_tracker.update(
            processing_frame,
            hand_result,
            detection_profile=self.ui_settings.get("detection_profile", "Dengeli"),
        )
        display_hand_result = self._to_display_hand_result(hand_result, self.ui_settings["mirror_camera"])

        auth_state = self._resolve_auth_state(processing_frame, face_result)
        active_profile = auth_state["active_profile"]
        allowed_spells = auth_state["allowed_spells"]
        verification_status = auth_state["verification_status"]
        session_snapshot = auth_state["session_snapshot"]
        self._emit_auth_notifications(auth_state)

        status_text = "Büyücü algılandı" if self.face_confirmed and face_result.detected else "Büyücü bekleniyor"
        if not hand_result.is_active:
            hand_status_text = "El algılama pasif"
        else:
            hand_status_text = "El algılandı" if hand_result.detected else "El bekleniyor"

        spell_result = self.spell_engine.update(
            hand_result,
            allowed_spells=allowed_spells,
            detection_profile=self.ui_settings.get("detection_profile", "Dengeli"),
            frame=processing_frame,
            hand_state=hand_state,
        )
        active_trial_spell = spell_result.active_spell_name if spell_result.has_active_spell else None
        trial_status = self.trial_engine.update(
            active_spell_name=active_trial_spell,
            allowed_spells=allowed_spells,
        )
        self._emit_spell_notifications(spell_result)
        self._emit_trial_notifications(trial_status)
        self._update_demo_guide(verification_status, active_trial_spell, trial_status)

        display_frame = self._draw_camera_overlays(
            display_frame,
            active_profile,
            display_face_result,
            display_hand_result,
            spell_result,
        )
        debug_info = self._debug_info(
            face_result=face_result,
            hand_result=hand_result,
            hand_state=hand_state,
            auth_state=auth_state,
            active_profile=active_profile,
            allowed_spells=allowed_spells,
            spell_result=spell_result,
            trial_status=trial_status,
            hand_status_text=hand_status_text,
        )

        return VisionEngineResult(
            display_frame=display_frame,
            active_profile=active_profile,
            allowed_spells=allowed_spells,
            verification_status=verification_status,
            session_state=session_snapshot.session_state,
            grace_remaining_seconds=session_snapshot.grace_remaining_seconds,
            spell_result=spell_result,
            trial_status=trial_status,
            debug_info=debug_info,
            notifications=self.notification_manager.active(),
            enrollment_status=self.last_enrollment_status,
            status_text=status_text,
            hand_status_text=hand_status_text,
            spellbook_page=self.spellbook_page,
            ui_settings=self.ui_settings.copy(),
        )

    def handle_action(self, action) -> None:
        """Qt tarafındaki tuş ve buton aksiyonlarını engine durumuna uygular."""
        if isinstance(action, dict):
            command = action.get("command")
            if command == "start_enrollment":
                self.start_enrollment(
                    username=str(action.get("username", "")),
                    mode=str(action.get("mode", "camera")),
                    import_directory=action.get("import_directory"),
                )
            elif command == "cancel_enrollment":
                self.cancel_enrollment()
            return

        settings_changed = False

        if action == "toggle_spellbook":
            self.ui_settings["show_spellbook"] = not self.ui_settings["show_spellbook"]
            settings_changed = True
        elif action == "open_spellbook":
            if not self.ui_settings["show_spellbook"]:
                self.ui_settings["show_spellbook"] = True
                settings_changed = True
        elif action == "close_spellbook":
            if self.ui_settings["show_spellbook"]:
                self.ui_settings["show_spellbook"] = False
                settings_changed = True
        elif action == "toggle_hand_debug":
            self.ui_settings["show_hand_debug"] = not self.ui_settings["show_hand_debug"]
            settings_changed = True
        elif action.startswith("set_hand_debug:"):
            enabled = action.endswith(":1")
            if self.ui_settings["show_hand_debug"] != enabled:
                self.ui_settings["show_hand_debug"] = enabled
                settings_changed = True
        elif action == "toggle_face_debug":
            self.ui_settings["show_face_debug"] = not self.ui_settings["show_face_debug"]
            settings_changed = True
        elif action.startswith("set_face_debug:"):
            enabled = action.endswith(":1")
            if self.ui_settings["show_face_debug"] != enabled:
                self.ui_settings["show_face_debug"] = enabled
                settings_changed = True
        elif action == "toggle_debug":
            self.ui_settings["show_debug_page"] = not self.ui_settings["show_debug_page"]
            settings_changed = True
        elif action == "toggle_system_status":
            self.ui_settings["show_system_status"] = not self.ui_settings.get("show_system_status", False)
        elif action == "toggle_settings":
            self.ui_settings["show_settings_menu"] = not self.ui_settings.get("show_settings_menu", False)
        elif action == "toggle_spell_effects":
            self.ui_settings["spell_effects_enabled"] = not self.ui_settings["spell_effects_enabled"]
            settings_changed = True
        elif action.startswith("set_spell_effects:"):
            enabled = action.endswith(":1")
            if self.ui_settings["spell_effects_enabled"] != enabled:
                self.ui_settings["spell_effects_enabled"] = enabled
                settings_changed = True
        elif action == "toggle_mirror":
            self.ui_settings["mirror_camera"] = not self.ui_settings["mirror_camera"]
            self.verification_session.reset()
            self.face_identity_detector.reset_stability()
            settings_changed = True
        elif action.startswith("set_mirror:"):
            enabled = action.endswith(":1")
            if self.ui_settings["mirror_camera"] != enabled:
                self.ui_settings["mirror_camera"] = enabled
                self.verification_session.reset()
                self.face_identity_detector.reset_stability()
                settings_changed = True
        elif action == "cycle_verification_mode":
            self.ui_settings["verification_requires_qr"] = not self.ui_settings["verification_requires_qr"]
            self.verification_session.reset()
            mode_text = "QR + Yüz" if self.ui_settings["verification_requires_qr"] else "Yalnızca Yüz"
            self.notification_manager.notify(f"Doğrulama modu: {mode_text}", type="info", key="verification-mode")
            settings_changed = True
        elif action.startswith("set_verification_mode:"):
            mode_text = action.split(":", 1)[1]
            if mode_text in {"QR + Yüz", "Yalnızca Yüz"}:
                requires_qr = mode_text == "QR + Yüz"
                if self.ui_settings["verification_requires_qr"] != requires_qr:
                    self.ui_settings["verification_requires_qr"] = requires_qr
                    self.verification_session.reset()
                    self.notification_manager.notify(
                        f"Doğrulama modu: {mode_text}",
                        type="info",
                        key="verification-mode",
                    )
                    settings_changed = True
        elif action == "cycle_detection_profile":
            self.ui_settings["detection_profile"] = self._next_detection_profile(
                self.ui_settings.get("detection_profile", "Dengeli")
            )
            self._apply_detection_profile(self.ui_settings["detection_profile"])
            settings_changed = True
        elif action.startswith("set_detection_profile:"):
            detection_profile = action.split(":", 1)[1]
            if detection_profile in {"Hassas", "Dengeli", "Kararlı"}:
                if self.ui_settings.get("detection_profile") != detection_profile:
                    self.ui_settings["detection_profile"] = detection_profile
                    self._apply_detection_profile(detection_profile)
                    settings_changed = True
        elif action == "reset_auth":
            self.verification_session.reset()
            self.face_identity_detector.reload()
            self.notification_manager.notify("Doğrulama oturumu sıfırlandı", type="info", key="auth-reset")
        elif action == "start_trial":
            self.trial_engine.start_or_restart()
            self.notification_manager.notify("Mühürlü Kapı başladı", type="trial", key="trial-start")
        elif action == "start_enrollment":
            self.start_enrollment()
        elif action == "toggle_demo":
            demo_action = self.demo_guide.toggle()
            if demo_action == "started":
                self.notification_manager.notify("Demo Rehberi başladı", type="info", key="demo-guide-start")
        elif action == "demo_next":
            if self.demo_guide.next() == "completed":
                self.notification_manager.notify("Demo tamamlandı", type="success", key="demo-complete")
        elif action == "demo_previous":
            self.demo_guide.previous()
        elif action == "next_debug_page" and self.ui_settings.get("show_debug_page", False):
            self.ui_settings["debug_page"] = (int(self.ui_settings.get("debug_page", 0)) + 1) % 4
        elif action == RIGHT_ARROW_ACTION and self.ui_settings["show_spellbook"]:
            self.spellbook_page = min(3, self.spellbook_page + 1)
        elif action == LEFT_ARROW_ACTION and self.ui_settings["show_spellbook"]:
            self.spellbook_page = max(0, self.spellbook_page - 1)

        if settings_changed:
            save_ui_settings(self.ui_settings)

    def start_enrollment(
        self,
        username: str | None = None,
        mode: str | None = None,
        import_directory: str | None = None,
    ) -> None:
        """Mevcut kayıt/import akışını başlatır ve gerekirse modeli yeniden yükler."""
        if username is not None and mode is not None:
            enrollment_status = self.enrollment_manager.start_with_options(
                username,
                mode,
                face_detector=self.face_detector,
                import_directory=import_directory,
            )
        else:
            enrollment_status = self.enrollment_manager.start(face_detector=self.face_detector)
        self.last_enrollment_status = enrollment_status
        if enrollment_status.message:
            self.notification_manager.notify(enrollment_status.message, type="info", key="enrollment-start", duration=4.0)
        if enrollment_status.is_complete:
            self._reload_after_enrollment(enrollment_status)

    def cancel_enrollment(self) -> None:
        """Aktif kayıt/import durumunu manager üzerinden güvenli biçimde sıfırlar."""
        self.last_enrollment_status = self.enrollment_manager.reset()
        self.enrollment_reload_done = False
        self.notification_manager.notify("Kayıt sıfırlandı", type="info", key="enrollment-cancel")

    def close(self) -> None:
        """Dedektör kaynaklarını güvenli şekilde kapatır."""
        if self.face_detector is not None:
            self.face_detector.close()
        if self.hand_detector is not None:
            self.hand_detector.close()

    def _process_enrollment_frame(self, processing_frame, display_frame, face_result, display_face_result) -> VisionEngineResult:
        """Kayıt modu aktifken tek kareyi işler."""
        enrollment_status = self.enrollment_manager.update(processing_frame, face_result)
        self.last_enrollment_status = enrollment_status
        if enrollment_status.is_complete and not self.enrollment_reload_done:
            self._reload_after_enrollment(enrollment_status)
            self.enrollment_reload_done = True

        if self.ui_settings["show_face_debug"] and display_face_result.detected and display_face_result.box is not None:
            display_frame = self.effects.draw_face_box(display_frame, display_face_result.box)

        if enrollment_status.is_complete and getattr(self.enrollment_manager, "completed_at", 0.0):
            if time.monotonic() - self.enrollment_manager.completed_at > 3.0:
                self.enrollment_manager.is_active = False
                self.enrollment_reload_done = False

        guest = guest_profile()
        trial_status = self.trial_engine.status()
        snapshot = self.verification_session.snapshot()
        return VisionEngineResult(
            display_frame=display_frame,
            active_profile=guest,
            allowed_spells=guest.unlocked_spells,
            verification_status="Kayıt modu",
            session_state=snapshot.session_state,
            grace_remaining_seconds=snapshot.grace_remaining_seconds,
            spell_result=None,
            trial_status=trial_status,
            debug_info={"enrollment": enrollment_status.message},
            notifications=self.notification_manager.active(),
            enrollment_status=enrollment_status,
            status_text="Kayıt modu",
            hand_status_text="Kayıt sırasında el algılama pasif",
            spellbook_page=self.spellbook_page,
            ui_settings=self.ui_settings.copy(),
        )

    def _reload_after_enrollment(self, enrollment_status) -> None:
        """Kayıt sonrası profil ve yüz modelini yeniden okur."""
        repair_local_profiles()
        self.face_identity_detector.reload()
        self.verification_session.reset()
        self.notification_manager.notify("Kayıt tamamlandı", type="success", key="enrollment-complete", min_interval=9999.0)
        if getattr(enrollment_status, "qr_path", None):
            self.notification_manager.notify("Lonca mührü oluşturuldu", type="success", key="guild-seal-created", min_interval=9999.0)

    def _draw_camera_overlays(self, frame, active_profile, display_face_result, display_hand_result, spell_result):
        """Sadece görüntüyle doğrudan ilişkili overlay'leri çizer."""
        if self.ui_settings["show_hand_debug"] and display_hand_result.detected:
            frame = self.effects.draw_hand_landmarks(frame, display_hand_result)

        if self.ui_settings["show_face_debug"] and self.face_confirmed and display_face_result.detected and display_face_result.box is not None:
            frame = self.effects.draw_face_box(frame, display_face_result.box)

        if self.ui_settings["spell_effects_enabled"] and spell_result is not None:
            frame = self.effects.draw_spell_effect(frame, spell_result, display_hand_result, display_face_result)

        frame = self.effects.draw_head_profile_tag(
            frame,
            active_profile,
            face_result=display_face_result if display_face_result.detected else None,
            verification_status="",
        )

        return frame

    def _resolve_auth_state(self, frame, face_result) -> dict:
        """Yüz kimliği, QR ve VerificationSession ile aktif yetkiyi belirler."""
        guest = guest_profile()
        base = self._auth_base()

        if not face_result.detected or face_result.box is None:
            self.face_identity_detector.reset_stability()
            snapshot = self.verification_session.update(stable_face_label=None, full_verified_label=None)
            return self._auth_from_session(snapshot, base, "Bekleniyor")

        if not self.face_identity_detector.is_available:
            self.face_identity_detector.reset_stability()
            snapshot = self.verification_session.update(stable_face_label=None, full_verified_label=None)
            auth = self._auth_from_session(snapshot, base, "Yüz tanıma pasif")
            auth.update({"identity_status": self.face_identity_detector.warning_message or "pasif"})
            return auth

        identity_result = self.face_identity_detector.predict(frame, face_result.box)
        identity_debug = self._identity_debug_fields(identity_result)
        identity_status = self._identity_debug_status(identity_result)
        face_score = self._face_score_debug(identity_result)

        if not identity_result.is_active:
            snapshot = self.verification_session.update(stable_face_label=None, full_verified_label=None)
            auth = self._auth_from_session(snapshot, base, "Yüz tanıma pasif")
            auth.update(
                {
                    "identity_status": identity_result.message or "pasif",
                    "face_quality_message": identity_result.message or "pasif",
                    **identity_debug,
                }
            )
            return auth

        candidate_profile = find_profile_by_face_label(identity_result.face_label) if identity_result.matched else None
        candidate_label = candidate_profile.face_label if candidate_profile else None
        full_verified_label = None
        seal_result = None
        mismatch = False

        if candidate_profile is not None:
            if self.ui_settings["verification_requires_qr"]:
                seal_result = self.guild_seal_detector.detect(frame, candidate_profile)
                mismatch = bool(seal_result.mismatch)
                if seal_result.matched:
                    full_verified_label = candidate_label
            else:
                full_verified_label = candidate_label
        elif self.ui_settings["verification_requires_qr"]:
            seal_result = self.guild_seal_detector.detect(frame, None)
            mismatch = bool(seal_result and seal_result.mismatch)

        snapshot = self.verification_session.update(
            stable_face_label=candidate_label,
            full_verified_label=full_verified_label,
            pending_label=candidate_label if candidate_profile is not None else None,
        )
        auth = self._auth_from_session(snapshot, base, "")
        auth.update(
            {
                "identity_status": identity_status,
                "qr_status": self._qr_debug_status(seal_result),
                "recognized_user": candidate_profile.username if candidate_profile else (identity_result.face_label or "-"),
                "face_score": face_score,
                **identity_debug,
            }
        )

        if auth["session_snapshot"].verified_face_label:
            return auth

        if mismatch:
            auth["verification_status"] = "Mühür kullanıcıyla eşleşmedi"
            return auth

        if candidate_profile is not None:
            auth["verification_status"] = "Yüz tanındı, mühür bekleniyor" if self.ui_settings["verification_requires_qr"] else "Yüz tanındı"
            auth["active_profile"] = guest
            auth["allowed_spells"] = guest.unlocked_spells
            return auth

        auth["verification_status"] = "Misafir"
        auth["active_profile"] = guest
        auth["allowed_spells"] = guest.unlocked_spells
        return auth

    def _auth_base(self) -> dict:
        """Auth sonucunun varsayılan debug alanlarını üretir."""
        guest = guest_profile()
        return {
            "active_profile": guest,
            "allowed_spells": guest.unlocked_spells,
            "verification_status": "Bekleniyor",
            "identity_status": "yüz yok",
            "qr_status": "okunmadı",
            "recognized_user": "-",
            "face_score": "-",
            "face_identity_label": "-",
            "face_identity_score": "-",
            "face_identity_threshold": self._score_debug(getattr(self.face_identity_detector, "threshold", None)),
            "face_identity_match_status": "bekleniyor",
            "face_identity_stable_label": "-",
            "face_identity_stability_count": "0",
            "face_identity_variant": "-",
            "face_quality_message": "-",
            "identity_health_warnings": "; ".join(getattr(self.face_identity_detector, "health_warnings", []))
            if getattr(self.face_identity_detector, "health_warnings", [])
            else "-",
        }

    def _auth_from_session(self, snapshot, base: dict, fallback_status: str) -> dict:
        """VerificationSession sonucundan aktif profil/yetki üretir."""
        auth = dict(base)
        auth["session_snapshot"] = snapshot
        if snapshot.verified_face_label:
            profile = find_profile_by_face_label(snapshot.verified_face_label)
            if profile is not None:
                auth["active_profile"] = profile
                auth["allowed_spells"] = profile.unlocked_spells
                auth["recognized_user"] = profile.username
                if snapshot.is_grace_active:
                    auth["verification_status"] = "Oturum korunuyor"
                elif self.ui_settings["verification_requires_qr"]:
                    auth["verification_status"] = "Yüz + lonca mührü onaylandı"
                else:
                    auth["verification_status"] = "Yüz tanındı"
                return auth

        auth["verification_status"] = snapshot.verification_status if snapshot.session_state == "EXPIRED" else (fallback_status or snapshot.verification_status)
        return auth

    def _debug_info(
        self,
        *,
        face_result,
        hand_result,
        hand_state,
        auth_state,
        active_profile,
        allowed_spells,
        spell_result,
        trial_status,
        hand_status_text,
    ) -> dict:
        """Qt debug paneli için mevcut debug alanlarını üretir."""
        snapshot = auth_state["session_snapshot"]
        return {
            "show_debug_page": self.ui_settings["show_debug_page"],
            "debug_page": self.ui_settings.get("debug_page", 0),
            "detection_profile": self.ui_settings.get("detection_profile", "Dengeli"),
            "mirror_camera": "Açık" if self.ui_settings["mirror_camera"] else "Kapalı",
            "face_status": "var" if face_result.detected else "yok",
            "face_detected": str(bool(face_result.detected)),
            "face_detection_score": self._score_debug(face_result.confidence),
            "face_box": self._box_debug(face_result.box),
            "face_detector_active": str(bool(face_result.is_active)),
            "hand_status": hand_status_text,
            "hand_detected": str(bool(hand_result.detected)),
            "hand_count": str(hand_result.hand_count),
            "handedness": self._handedness_debug(hand_result),
            "raw_hand_detected": str(bool(hand_result.detected)),
            "raw_hand_count": str(hand_result.hand_count),
            "raw_handedness": self._handedness_debug(hand_result),
            "hand_detector_active": str(bool(hand_result.is_active)),
            "tracker_source": hand_state.tracking_source,
            "tracker_hand_detected": str(bool(hand_state.hand_detected)),
            "tracker_active_hand": hand_state.active_hand,
            "tracker_hand_count": str(hand_state.hand_count),
            "tracker_handedness": ", ".join(hand_state.handedness) if hand_state.handedness else "-",
            "tracker_hand_center": self._point_debug(hand_state.hand_center),
            "tracker_smoothed_hand_center": self._point_debug(hand_state.smoothed_hand_center),
            "tracker_hand_velocity": self._point_debug(hand_state.hand_velocity),
            "tracker_palm_open_score": self._score_debug(hand_state.palm_open_score),
            "tracker_two_hand_score": self._score_debug(hand_state.two_hand_score),
            "tracker_quality": self._score_debug(hand_state.tracking_quality),
            "tracker_missing_time": self._score_debug(hand_state.missing_time),
            "tracker_quality_warnings": ", ".join(hand_state.quality_warnings) if hand_state.quality_warnings else "-",
            "tracker_brightness": self._score_debug(hand_state.brightness_score),
            "tracker_blur": self._score_debug(hand_state.blur_score),
            "tracker_hand_near_edge": str(bool(hand_state.hand_near_edge)),
            "qr_status": auth_state["qr_status"],
            "identity_status": auth_state["identity_status"],
            "face_identity_label": auth_state.get("face_identity_label", "-"),
            "face_identity_score": auth_state.get("face_identity_score", "-"),
            "face_identity_threshold": auth_state.get("face_identity_threshold", "-"),
            "face_identity_match_status": auth_state.get("face_identity_match_status", "-"),
            "face_identity_stable_label": auth_state.get("face_identity_stable_label", "-"),
            "face_identity_stability_count": auth_state.get("face_identity_stability_count", "-"),
            "face_identity_variant": auth_state.get("face_identity_variant", "-"),
            "face_quality_message": auth_state.get("face_quality_message", "-"),
            "identity_health_warnings": auth_state.get("identity_health_warnings", "-"),
            "recognized_user": auth_state.get("recognized_user", "-"),
            "active_profile": f"{active_profile.username} / {active_profile.rank}",
            "allowed_spells": ", ".join(allowed_spells) if allowed_spells else "-",
            "attempted_locked_spell": self._attempted_locked_spell_debug(spell_result),
            "face_score": auth_state.get("face_score", "-"),
            "fps": f"{self.fps:.1f}",
            "cooldown": f"{spell_result.cooldown_remaining:.1f} sn" if spell_result and spell_result.cooldown_remaining > 0 else "hazır",
            "active_spell": spell_result.active_spell_name if spell_result and spell_result.active_spell_name else "Yok",
            "session_state": snapshot.session_state,
            "verified_face_label": snapshot.verified_face_label or "-",
            "is_grace_active": str(bool(snapshot.is_grace_active)),
            "grace_remaining_seconds": self._score_debug(snapshot.grace_remaining_seconds),
            "last_seen_time": self._score_debug(snapshot.last_seen_time),
            "verification_status": auth_state["verification_status"],
            "verification_mode": "QR + Yüz" if self.ui_settings["verification_requires_qr"] else "Yalnızca Yüz",
            "trial_state": trial_status.state,
            "trial_current_step": trial_status.current_step,
            "trial_required_spell": trial_status.required_spell or "-",
            "trial_completed_steps": f"{trial_status.completed_count}/{trial_status.total_steps}",
            "last_trial_message": trial_status.message,
            **self._spell_debug(spell_result),
        }

    def _spell_debug(self, spell_result) -> dict:
        """SpellResult debug alanlarını güvenli şekilde sözlüğe çevirir."""
        if spell_result is None:
            return {}
        return {
            "spell_uses_tracker": str(bool(spell_result.spell_uses_tracker)),
            "tracker_source_used": spell_result.tracker_source_used,
            "freeze_state": spell_result.freeze_state,
            "freeze_elapsed_time": self._score_debug(spell_result.freeze_elapsed_time),
            "freeze_required_time": self._score_debug(spell_result.freeze_required_time),
            "freeze_progress_raw": self._score_debug(spell_result.freeze_progress_raw),
            "freeze_progress_display": self._score_debug(spell_result.freeze_progress_display),
            "freeze_velocity": self._score_debug(spell_result.freeze_velocity),
            "freeze_velocity_deadzone": self._score_debug(spell_result.freeze_velocity_deadzone),
            "freeze_is_stable": str(bool(spell_result.freeze_is_stable)),
            "freeze_block_reason": spell_result.freeze_block_reason,
            "competing_spell_candidate": spell_result.competing_spell_candidate,
            "palm_open_score": self._score_debug(spell_result.palm_open_score),
            "freeze_stability_score": self._score_debug(spell_result.freeze_stability_score),
            "fire_horizontal_distance": self._score_debug(spell_result.fire_horizontal_distance),
            "fire_swing_detected": str(bool(spell_result.fire_swing_detected)),
            "fire_state": spell_result.fire_state,
            "fire_candidate_active": str(bool(spell_result.fire_candidate_active)),
            "fire_start_reason": spell_result.fire_start_reason,
            "fire_min_distance_met": str(bool(spell_result.fire_min_distance_met)),
            "fire_start_x": self._score_debug(spell_result.fire_start_x),
            "fire_current_x": self._score_debug(spell_result.fire_current_x),
            "fire_required_distance": self._score_debug(spell_result.fire_required_distance),
            "fire_travel_distance": self._score_debug(spell_result.fire_travel_distance),
            "fire_missing_time": self._score_debug(spell_result.fire_missing_time),
            "fire_seal_window_active": str(bool(spell_result.fire_seal_window_active)),
            "hand_tracking_quality_message": spell_result.hand_tracking_quality_message or "-",
            "shield_two_hand_score": self._score_debug(spell_result.shield_two_hand_score),
            "spell_prepare_progress": self._score_debug(spell_result.spell_prepare_progress),
            "locked_spell_attempt": spell_result.locked_spell_attempt or "-",
        }

    def _update_demo_guide(self, verification_status: str, active_spell_name: str | None, trial_status) -> None:
        """Demo rehberi olaylarını mevcut akıştan besler."""
        demo_event = self.demo_guide.update(
            {
                "verification_status": verification_status,
                "spellbook_open": self.ui_settings["show_spellbook"],
                "spellbook_page": self.spellbook_page,
                "active_spell_name": active_spell_name,
                "trial_state": trial_status.state,
            }
        )
        if demo_event == "completed":
            self.notification_manager.notify("Demo tamamlandı", type="success", key="demo-complete", min_interval=9999.0)

    def _emit_startup_warnings(self) -> None:
        """Eksik kritik kaynakları tek seferlik bildirimlere çevirir."""
        if self.face_identity_detector.warning_message:
            self.notification_manager.notify(self.face_identity_detector.warning_message, type="warning", duration=4.0, key="identity-warning")
        if self.face_detector.warning_message:
            self.notification_manager.notify(self.face_detector.warning_message, type="warning", duration=4.0, key="face-warning")
        if self.hand_detector.warning_message:
            self.notification_manager.notify(self.hand_detector.warning_message, type="warning", duration=4.0, key="hand-warning")
        if any(item.required and not item.exists for item in get_system_status()):
            self.notification_manager.notify("Eksik model dosyası", type="warning", duration=4.0, key="missing-required-model", min_interval=9999.0)

    def _emit_auth_notifications(self, auth_state: dict) -> None:
        """Doğrulama durum değişikliklerini kısa bildirimlere çevirir."""
        verification_status = auth_state.get("verification_status", "")
        recognized_user = auth_state.get("recognized_user", "-")
        stable_label = auth_state.get("face_identity_stable_label", "-")

        if recognized_user != "-" and stable_label not in ("", "-") and recognized_user != self.notification_state.get("recognized_user"):
            self.notification_manager.notify(f"{recognized_user} tanındı", type="success", key=f"recognized:{recognized_user}", min_interval=8.0)
            self.notification_state["recognized_user"] = recognized_user
        elif recognized_user == "-":
            self.notification_state["recognized_user"] = "-"

        if verification_status == self.notification_state.get("verification_status"):
            return

        if verification_status == "Yüz tanındı, mühür bekleniyor":
            self.notification_manager.notify("Lonca mührü bekleniyor", type="warning", key="guild-seal-waiting", min_interval=5.0)
        elif verification_status == "Yüz + lonca mührü onaylandı":
            self.notification_manager.notify("Lonca mührü onaylandı", type="success", key="guild-seal-approved", min_interval=5.0)
        elif verification_status == "Mühür kullanıcıyla eşleşmedi":
            self.notification_manager.notify("Mühür kullanıcıyla eşleşmedi", type="error", key="guild-seal-mismatch", min_interval=5.0)
        elif verification_status == "Oturum korunuyor":
            self.notification_manager.notify("Oturum korunuyor", type="warning", key="grace-active", min_interval=5.0)
        elif verification_status == "Doğrulama süresi doldu":
            self.notification_manager.notify("Doğrulama süresi doldu", type="warning", key="grace-expired", min_interval=5.0)

        self.notification_state["verification_status"] = verification_status

    def _emit_spell_notifications(self, spell_result) -> None:
        """Büyü tetikleme ve kilitli büyü denemelerini bildirimlere çevirir."""
        active_spell_name = getattr(spell_result, "active_spell_name", None)
        if getattr(spell_result, "has_active_spell", False) and active_spell_name:
            if active_spell_name != self.notification_state.get("active_spell_name"):
                self.notification_manager.notify(f"{active_spell_name} büyüsü", type="spell", key=f"spell:{active_spell_name}", min_interval=2.0)
                self.notification_state["active_spell_name"] = active_spell_name
        else:
            self.notification_state["active_spell_name"] = ""

        locked_spell_attempt = self._attempted_locked_spell_debug(spell_result)
        if locked_spell_attempt != "-" and locked_spell_attempt != self.notification_state.get("locked_spell_attempt"):
            self.notification_manager.notify("Büyü kilitli", type="warning", key=f"locked-spell:{locked_spell_attempt}", min_interval=2.5)
            self.notification_state["locked_spell_attempt"] = locked_spell_attempt
        elif locked_spell_attempt == "-":
            self.notification_state["locked_spell_attempt"] = ""

    def _emit_trial_notifications(self, trial_status) -> None:
        """Trial durum değişikliklerini kısa bildirimlere çevirir."""
        trial_state = getattr(trial_status, "state", "idle")
        if trial_state == self.notification_state.get("trial_state"):
            return
        if trial_state == "active":
            self.notification_manager.notify("Mühürlü Kapı başladı", type="trial", key="trial-start", min_interval=2.0)
        elif trial_state == "completed":
            self.notification_manager.notify("Kapı açıldı", type="trial", key="trial-complete", min_interval=5.0)
        self.notification_state["trial_state"] = trial_state

    def _update_fps(self) -> None:
        """Frame zamanından yumuşatılmış FPS hesaplar."""
        now = time.monotonic()
        elapsed = max(0.001, now - self.last_frame_time)
        self.fps = 0.9 * self.fps + 0.1 * (1.0 / elapsed) if self.fps else (1.0 / elapsed)
        self.last_frame_time = now

    def _update_face_confirmation(self, face_result, face_history, face_confirmed: bool, missing_face_frames: int):
        """Yüz var/yok durumunu birkaç karelik pencereyle yumuşatır."""
        face_history.append(bool(face_result.detected))
        detected_count = sum(face_history)
        if detected_count >= 5:
            return True, 0
        if face_result.detected:
            return face_confirmed, 0
        missing_face_frames += 1
        if missing_face_frames >= 4:
            return False, missing_face_frames
        return face_confirmed, missing_face_frames

    def _face_detector_options(self, detection_profile: str) -> dict:
        if detection_profile == "Hassas":
            return {"min_detection_confidence": 0.45}
        if detection_profile == "Kararlı":
            return {"min_detection_confidence": 0.72}
        return {"min_detection_confidence": 0.6}

    def _hand_detector_options(self, detection_profile: str) -> dict:
        if detection_profile == "Hassas":
            return {
                "num_hands": 2,
                "min_hand_detection_confidence": 0.35,
                "min_hand_presence_confidence": 0.35,
                "min_tracking_confidence": 0.35,
            }
        if detection_profile == "Kararlı":
            return {
                "num_hands": 2,
                "min_hand_detection_confidence": 0.65,
                "min_hand_presence_confidence": 0.65,
                "min_tracking_confidence": 0.65,
            }
        return {
            "num_hands": 2,
            "min_hand_detection_confidence": 0.5,
            "min_hand_presence_confidence": 0.5,
            "min_tracking_confidence": 0.5,
        }

    def _apply_detection_profile(self, detection_profile: str) -> None:
        """Algılama profili değişince dedektörleri yeniden başlatır."""
        self.face_detector.close()
        self.hand_detector.close()
        self.face_detector = FaceDetector(**self._face_detector_options(detection_profile))
        self.hand_detector = HandDetector(**self._hand_detector_options(detection_profile))
        self.hand_state_tracker = HandStateTracker()

    def _next_detection_profile(self, current_profile: str) -> str:
        profiles = ["Hassas", "Dengeli", "Kararlı"]
        if current_profile not in profiles:
            return "Dengeli"
        return profiles[(profiles.index(current_profile) + 1) % len(profiles)]

    def _to_display_face_result(self, face_result, frame_width: int, mirror_camera: bool):
        if not mirror_camera or face_result.box is None:
            return face_result
        return FaceDetectionResult(
            detected=face_result.detected,
            confidence=face_result.confidence,
            box=self._mirror_box(face_result.box, frame_width),
            is_active=face_result.is_active,
            message=face_result.message,
        )

    def _to_display_hand_result(self, hand_result, mirror_camera: bool):
        if not mirror_camera or not hand_result.hands:
            return hand_result
        mirrored_hands = []
        for hand in hand_result.hands:
            mirrored_landmarks = [(1.0 - x, y, z) for x, y, z in hand.landmarks]
            mirrored_hands.append(
                HandData(
                    handedness=self._mirror_handedness(hand.handedness),
                    confidence=hand.confidence,
                    landmarks=mirrored_landmarks,
                )
            )
        return HandDetectionResult(
            detected=hand_result.detected,
            hand_count=hand_result.hand_count,
            hands=mirrored_hands,
            is_active=hand_result.is_active,
            message=hand_result.message,
        )

    def _mirror_box(self, box: tuple[int, int, int, int], frame_width: int) -> tuple[int, int, int, int]:
        x, y, width, height = box
        return max(0, frame_width - x - width), y, width, height

    def _mirror_handedness(self, label: str) -> str:
        if label == "Left":
            return "Right"
        if label == "Right":
            return "Left"
        return label

    def _identity_debug_status(self, identity_result) -> str:
        label = identity_result.raw_face_label or identity_result.face_label or "etiket yok"
        score = "skor yok"
        if identity_result.confidence is not None:
            score = f"{identity_result.confidence:.1f}"
        match_status = identity_result.match_status or ("eşleşti" if identity_result.matched else "eşleşmedi")
        return f"{label} / {score} / {match_status}"

    def _face_score_debug(self, identity_result) -> str:
        if identity_result.confidence is None:
            return "-"
        return f"{identity_result.confidence:.1f}"

    def _identity_debug_fields(self, identity_result) -> dict:
        health_warnings = getattr(identity_result, "health_warnings", None) or []
        return {
            "face_identity_label": identity_result.raw_face_label or identity_result.face_label or "-",
            "face_identity_score": self._face_score_debug(identity_result),
            "face_identity_threshold": self._score_debug(getattr(identity_result, "threshold", None)),
            "face_identity_match_status": identity_result.match_status or "-",
            "face_identity_stable_label": identity_result.stable_face_label or "-",
            "face_identity_stability_count": str(getattr(identity_result, "stability_count", 0)),
            "face_identity_variant": identity_result.selected_variant or "-",
            "face_quality_message": identity_result.quality_message or "-",
            "identity_health_warnings": "; ".join(health_warnings) if health_warnings else "-",
        }

    def _attempted_locked_spell_debug(self, spell_result) -> str:
        if spell_result is None:
            return "-"
        for attribute_name in ("attempted_spell_name", "locked_spell_name", "requested_spell_name"):
            value = getattr(spell_result, attribute_name, None)
            if value:
                return str(value)
        status = getattr(spell_result, "status", "")
        message = getattr(spell_result, "message", "")
        if status == "Lonca yetkisi yetersiz":
            return message or status
        if "kilit" in str(message).lower():
            return str(message)
        return "-"

    def _score_debug(self, score) -> str:
        if score is None:
            return "-"
        return f"{float(score):.2f}"

    def _box_debug(self, box) -> str:
        if box is None:
            return "-"
        x, y, width, height = box
        return f"{x},{y},{width},{height}"

    def _point_debug(self, point) -> str:
        if point is None:
            return "-"
        return ", ".join(f"{float(value):.2f}" for value in point[:2])

    def _handedness_debug(self, hand_result) -> str:
        if not hand_result or not hand_result.hands:
            return "-"
        labels = [hand.handedness for hand in hand_result.hands if hand.handedness]
        return ", ".join(labels) if labels else "-"

    def _qr_debug_status(self, seal_result) -> str:
        if seal_result is None:
            return "okunmadı"
        if seal_result.matched:
            return "eşleşti"
        if seal_result.mismatch:
            return "eşleşmedi"
        if seal_result.detected:
            return seal_result.message or "okundu"
        return "okunmadı"

    def system_status_items(self):
        """Qt paneli için güncel sistem durumu satırlarını döndürür."""
        return get_system_status()

    def has_registered_wizard(self) -> bool:
        """Kayıtlı kullanıcı var mı bilgisini döndürür."""
        return has_registered_wizard()

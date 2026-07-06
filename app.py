# VisionForge masaüstü uygulamasının başlangıç noktası.

from collections import deque
import time

import cv2

from camera import Camera, CameraError
from detectors.face_detector import FaceDetectionResult, FaceDetector, FaceDetectorError
from detectors.face_identity_detector import FaceIdentityDetector
from detectors.guild_seal_detector import GuildSealDetector
from detectors.hand_detector import HandData, HandDetectionResult, HandDetector, HandDetectorError
from effects import Effects
from enrollment.enrollment_manager import EnrollmentManager
from guild_profile import find_profile_by_face_label, guest_profile
from settings_manager import load_ui_settings, save_ui_settings
from spell_engine import SpellEngine
from system_status import get_system_status, has_registered_wizard
from trial_engine import TrialEngine


RIGHT_ARROW_KEYS = {83, 2555904, 65363}
LEFT_ARROW_KEYS = {81, 2424832, 65361}


def main() -> None:
    """Kamera görüntüsünü açar, doğrulama ve büyü akışlarını çalıştırır."""
    camera = None
    face_detector = None
    hand_detector = None
    effects = Effects()
    spell_engine = SpellEngine()
    trial_engine = TrialEngine()
    enrollment_manager = EnrollmentManager()
    face_identity_detector = FaceIdentityDetector()
    guild_seal_detector = GuildSealDetector()

    ui_settings = load_ui_settings()

    face_history = deque(maxlen=8)
    face_confirmed = False
    missing_face_frames = 0
    verified_face_label: str | None = None
    enrollment_reload_done = False
    spellbook_page = 0
    last_frame_time = time.monotonic()
    fps = 0.0

    if face_identity_detector.warning_message:
        print(face_identity_detector.warning_message)

    try:
        face_detector = FaceDetector(**_face_detector_options(ui_settings["detection_profile"]))
        if face_detector.warning_message:
            print(face_detector.warning_message)

        hand_detector = HandDetector(**_hand_detector_options(ui_settings["detection_profile"]))
        if hand_detector.warning_message:
            print(hand_detector.warning_message)

        camera = Camera(source=0, window_name="VisionForge - Kamera Modu")
        camera.start()

        print("VisionForge kamera modu aktif.")
        print("Q: ayar menüsü, E: kayıt/import, T: Trial, R: sıfırla, B: büyü kitabı, H: el çizimi, Esc: çıkış.")

        while True:
            processing_frame = camera.read_frame()
            display_frame = (
                cv2.flip(processing_frame, 1)
                if ui_settings["mirror_camera"]
                else processing_frame.copy()
            )

            now = time.monotonic()
            elapsed = max(0.001, now - last_frame_time)
            fps = 0.9 * fps + 0.1 * (1.0 / elapsed) if fps else (1.0 / elapsed)
            last_frame_time = now

            face_result = face_detector.detect(processing_frame)
            display_face_result = _to_display_face_result(
                face_result,
                display_frame.shape[1],
                ui_settings["mirror_camera"],
            )
            face_confirmed, missing_face_frames = _update_face_confirmation(
                face_result,
                face_history,
                face_confirmed,
                missing_face_frames,
            )

            if enrollment_manager.is_active:
                enrollment_status = enrollment_manager.update(processing_frame, face_result)
                if enrollment_status.is_complete and not enrollment_reload_done:
                    face_identity_detector.reload()
                    if face_identity_detector.warning_message:
                        print(face_identity_detector.warning_message)
                    enrollment_reload_done = True

                if (
                    ui_settings["show_face_debug"]
                    and display_face_result.detected
                    and display_face_result.box is not None
                ):
                    display_frame = effects.draw_face_box(display_frame, display_face_result.box)

                display_frame = effects.draw_enrollment_panel(display_frame, enrollment_status)
                display_frame = effects.draw_settings_menu(display_frame, ui_settings)
                camera.show_frame(display_frame)
                key = camera.read_key()
                verified_face_label, spellbook_page = _handle_key(
                    key,
                    ui_settings,
                    verified_face_label,
                    spellbook_page,
                    enrollment_manager,
                    face_identity_detector,
                    face_detector,
                    hand_detector,
                    trial_engine,
                    allow_enrollment_start=False,
                )
                if camera.is_close_key(key):
                    break

                if enrollment_status.is_complete and getattr(enrollment_manager, "completed_at", 0.0):
                    if time.monotonic() - enrollment_manager.completed_at > 3.0:
                        enrollment_manager.is_active = False
                continue

            hand_result = hand_detector.detect(processing_frame)
            display_hand_result = _to_display_hand_result(
                hand_result,
                ui_settings["mirror_camera"],
            )
            auth_state = _resolve_auth_state(
                frame=processing_frame,
                face_result=face_result,
                face_identity_detector=face_identity_detector,
                guild_seal_detector=guild_seal_detector,
                verified_face_label=verified_face_label,
                verification_requires_qr=ui_settings["verification_requires_qr"],
            )
            verified_face_label = auth_state["verified_face_label"]
            active_profile = auth_state["active_profile"]
            allowed_spells = auth_state["allowed_spells"]
            verification_status = auth_state["verification_status"]

            status_text = "Büyücü algılandı" if face_confirmed and face_result.detected else "Büyücü bekleniyor"
            if not hand_result.is_active:
                hand_status_text = "El algılama pasif"
            else:
                hand_status_text = "El algılandı" if hand_result.detected else "El bekleniyor"

            spell_result = spell_engine.update(
                hand_result,
                allowed_spells=allowed_spells,
                detection_profile=ui_settings.get("detection_profile", "Dengeli"),
                frame=processing_frame,
            )
            active_trial_spell = spell_result.active_spell_name if spell_result.has_active_spell else None
            trial_status = trial_engine.update(
                active_spell_name=active_trial_spell,
                allowed_spells=allowed_spells,
            )

            if ui_settings["show_hand_debug"] and display_hand_result.detected:
                display_frame = effects.draw_hand_landmarks(display_frame, display_hand_result)

            if (
                ui_settings["show_face_debug"]
                and face_confirmed
                and display_face_result.detected
                and display_face_result.box is not None
            ):
                display_frame = effects.draw_face_box(display_frame, display_face_result.box)

            if ui_settings["spell_effects_enabled"]:
                display_frame = effects.draw_spell_effect(
                    display_frame,
                    spell_result,
                    display_hand_result,
                    display_face_result,
                )

            display_frame = effects.draw_head_profile_tag(
                display_frame,
                active_profile,
                face_result=display_face_result if display_face_result.detected else None,
                verification_status=verification_status,
            )
            display_frame = effects.draw_spell_status_panel(display_frame, spell_result)
            display_frame = effects.draw_trial_panel(display_frame, trial_status)
            if not has_registered_wizard():
                display_frame = effects.draw_registration_hint(
                    display_frame,
                    "Kayıtlı büyücü yok. E ile kayıt başlat.",
                )

            if ui_settings["show_spellbook"]:
                display_frame = effects.draw_spellbook_panel(display_frame, active_profile, page=spellbook_page)

            debug_info = {
                "show_debug_page": ui_settings["show_debug_page"],
                "detection_profile": ui_settings.get("detection_profile", "Dengeli"),
                "face_status": "var" if face_result.detected else "yok",
                "face_detected": str(bool(face_result.detected)),
                "face_detection_score": _score_debug(face_result.confidence),
                "face_box": _box_debug(face_result.box),
                "face_detector_active": str(bool(face_result.is_active)),
                "hand_status": hand_status_text,
                "hand_detected": str(bool(hand_result.detected)),
                "hand_count": str(hand_result.hand_count),
                "handedness": _handedness_debug(hand_result),
                "hand_detector_active": str(bool(hand_result.is_active)),
                "qr_status": auth_state["qr_status"],
                "identity_status": auth_state["identity_status"],
                "face_identity_label": auth_state.get("face_identity_label", "-"),
                "face_identity_score": auth_state.get("face_identity_score", "-"),
                "face_identity_variant": auth_state.get("face_identity_variant", "-"),
                "face_quality_message": auth_state.get("face_quality_message", "-"),
                "recognized_user": auth_state.get("recognized_user", "-"),
                "active_profile": f"{active_profile.username} / {active_profile.rank}",
                "allowed_spells": ", ".join(allowed_spells) if allowed_spells else "-",
                "attempted_locked_spell": _attempted_locked_spell_debug(spell_result),
                "face_score": auth_state.get("face_score", "-"),
                "fps": f"{fps:.1f}",
                "cooldown": f"{spell_result.cooldown_remaining:.1f} sn" if spell_result.cooldown_remaining > 0 else "hazır",
                "palm_open_score": _score_debug(spell_result.palm_open_score),
                "freeze_stability_score": _score_debug(spell_result.freeze_stability_score),
                "fire_horizontal_distance": _score_debug(spell_result.fire_horizontal_distance),
                "fire_swing_detected": str(bool(spell_result.fire_swing_detected)),
                "fire_state": spell_result.fire_state,
                "fire_start_x": _score_debug(spell_result.fire_start_x),
                "fire_current_x": _score_debug(spell_result.fire_current_x),
                "fire_required_distance": _score_debug(spell_result.fire_required_distance),
                "fire_travel_distance": _score_debug(spell_result.fire_travel_distance),
                "fire_missing_time": _score_debug(spell_result.fire_missing_time),
                "fire_seal_window_active": str(bool(spell_result.fire_seal_window_active)),
                "hand_tracking_quality_message": spell_result.hand_tracking_quality_message or "-",
                "shield_two_hand_score": _score_debug(spell_result.shield_two_hand_score),
                "spell_prepare_progress": _score_debug(spell_result.spell_prepare_progress),
                "locked_spell_attempt": spell_result.locked_spell_attempt or "-",
                "verification_status": verification_status,
                "verification_mode": "QR + Yüz" if ui_settings["verification_requires_qr"] else "Yalnızca Yüz",
                "trial_state": trial_status.state,
                "trial_current_step": trial_status.current_step,
                "trial_required_spell": trial_status.required_spell or "-",
                "trial_completed_steps": f"{trial_status.completed_count}/{trial_status.total_steps}",
                "last_trial_message": trial_status.message,
            }
            display_frame = effects.draw_debug_panel(display_frame, debug_info)
            if ui_settings.get("show_system_status", False):
                display_frame = effects.draw_system_status_panel(display_frame, get_system_status())
            display_frame = effects.draw_settings_menu(display_frame, ui_settings)

            camera.show_frame(display_frame)

            key = camera.read_key()
            verified_face_label, spellbook_page = _handle_key(
                key,
                ui_settings,
                verified_face_label,
                spellbook_page,
                enrollment_manager,
                face_identity_detector,
                face_detector,
                hand_detector,
                trial_engine,
                allow_enrollment_start=True,
            )

            if camera.is_close_key(key):
                break

    except CameraError as error:
        print(f"Kamera hatası: {error}")
    except FaceDetectorError as error:
        print(f"Yüz algılama hatası: {error}")
    except HandDetectorError as error:
        print(f"El algılama hatası: {error}")
    except ValueError as error:
        print(f"Profil hatası: {error}")
    finally:
        if hand_detector is not None:
            hand_detector.close()
        if face_detector is not None:
            face_detector.close()
        if camera is not None:
            camera.stop()


def _update_face_confirmation(face_result, face_history, face_confirmed: bool, missing_face_frames: int):
    """Yüz var/yok durumunu kısa geçmişle sabitler."""
    if face_result.detected:
        face_history.append(True)
        missing_face_frames = 0
    else:
        face_history.append(False)
        missing_face_frames += 1

    if not face_confirmed and sum(face_history) >= 5:
        face_confirmed = True
    if face_confirmed and missing_face_frames >= 4:
        face_confirmed = False
        face_history.clear()

    return face_confirmed, missing_face_frames


def _face_detector_options(detection_profile: str) -> dict:
    """Algılama profiline göre FaceDetector seçeneklerini döndürür."""
    confidence_by_profile = {
        "Hassas": 0.45,
        "Dengeli": 0.60,
        "Kararlı": 0.75,
    }
    return {
        "min_detection_confidence": confidence_by_profile.get(detection_profile, 0.60),
    }


def _hand_detector_options(detection_profile: str) -> dict:
    """Algılama profiline göre HandDetector seçeneklerini döndürür."""
    profile_options = {
        "Hassas": {
            "min_hand_detection_confidence": 0.35,
            "min_hand_presence_confidence": 0.35,
            "min_tracking_confidence": 0.35,
        },
        "Dengeli": {
            "min_hand_detection_confidence": 0.50,
            "min_hand_presence_confidence": 0.50,
            "min_tracking_confidence": 0.50,
        },
        "Kararlı": {
            "min_hand_detection_confidence": 0.65,
            "min_hand_presence_confidence": 0.65,
            "min_tracking_confidence": 0.65,
        },
    }
    return profile_options.get(detection_profile, profile_options["Dengeli"])


def _apply_detection_profile(face_detector, hand_detector, detection_profile: str) -> None:
    """Algılama profilini mevcut detector örneklerine uygular."""
    if face_detector is not None:
        face_options = _face_detector_options(detection_profile)
        face_detector.min_detection_confidence = face_options["min_detection_confidence"]
        face_detector.close()
        face_detector.initialize()
        if face_detector.warning_message:
            print(face_detector.warning_message)

    if hand_detector is not None:
        hand_options = _hand_detector_options(detection_profile)
        hand_detector.min_hand_detection_confidence = hand_options["min_hand_detection_confidence"]
        hand_detector.min_hand_presence_confidence = hand_options["min_hand_presence_confidence"]
        hand_detector.min_tracking_confidence = hand_options["min_tracking_confidence"]
        hand_detector.close()
        hand_detector.initialize()
        if hand_detector.warning_message:
            print(hand_detector.warning_message)


def _next_detection_profile(current_profile: str) -> str:
    """Q menüsü için algılama profilini sıradaki değere taşır."""
    profiles = ["Hassas", "Dengeli", "Kararlı"]
    try:
        current_index = profiles.index(current_profile)
    except ValueError:
        return "Hassas"
    return profiles[(current_index + 1) % len(profiles)]


def _to_display_face_result(face_result, frame_width: int, mirror_camera: bool):
    """Yüz sonucunu ekrandaki aynalama durumuna göre çizim koordinatına çevirir."""
    if not mirror_camera or face_result is None or face_result.box is None:
        return face_result

    return FaceDetectionResult(
        detected=face_result.detected,
        confidence=face_result.confidence,
        box=_mirror_box(face_result.box, frame_width),
        is_active=face_result.is_active,
        message=face_result.message,
    )


def _to_display_hand_result(hand_result, mirror_camera: bool):
    """El landmark sonucunu ekrandaki aynalama durumuna göre çevirir."""
    if not mirror_camera or hand_result is None or not hand_result.hands:
        return hand_result

    mirrored_hands = []
    for hand in hand_result.hands:
        mirrored_hands.append(
            HandData(
                handedness=_mirror_handedness(hand.handedness),
                confidence=hand.confidence,
                landmarks=[
                    (max(0.0, min(1.0, 1.0 - x)), y, z)
                    for x, y, z in hand.landmarks
                ],
            )
        )

    return HandDetectionResult(
        detected=hand_result.detected,
        hand_count=hand_result.hand_count,
        hands=mirrored_hands,
        is_active=hand_result.is_active,
        message=hand_result.message,
    )


def _mirror_box(box: tuple[int, int, int, int], frame_width: int) -> tuple[int, int, int, int]:
    """OpenCV kutusunu yatay aynalama sonrası ekrandaki yerine taşır."""
    x, y, width, height = box
    mirrored_x = max(0, frame_width - x - width)
    return mirrored_x, y, width, height


def _mirror_handedness(label: str) -> str:
    """Aynalı ekranda sağ/sol el etiketini tersler."""
    if label == "Left":
        return "Right"
    if label == "Right":
        return "Left"
    return label


def _handle_key(
    key: int,
    ui_settings: dict,
    verified_face_label: str | None,
    spellbook_page: int,
    enrollment_manager: EnrollmentManager,
    face_identity_detector: FaceIdentityDetector,
    face_detector: FaceDetector | None,
    hand_detector: HandDetector | None,
    trial_engine: TrialEngine,
    allow_enrollment_start: bool,
) -> tuple[str | None, int]:
    """Klavye kısayollarını tek merkezden işler."""
    if key < 0:
        return verified_face_label, spellbook_page

    settings_changed = False

    if key in (ord("q"), ord("Q")):
        ui_settings["show_settings_menu"] = not ui_settings["show_settings_menu"]
        return verified_face_label, spellbook_page

    if key in RIGHT_ARROW_KEYS and ui_settings["show_spellbook"]:
        return verified_face_label, min(3, spellbook_page + 1)

    if key in LEFT_ARROW_KEYS and ui_settings["show_spellbook"]:
        return verified_face_label, max(0, spellbook_page - 1)

    if key in (ord("b"), ord("B")):
        ui_settings["show_spellbook"] = not ui_settings["show_spellbook"]
        settings_changed = True
    elif key in (ord("h"), ord("H")):
        ui_settings["show_hand_debug"] = not ui_settings["show_hand_debug"]
        settings_changed = True
    elif key in (ord("r"), ord("R")):
        verified_face_label = None
        print("Doğrulama oturumu sıfırlandı.")
    elif key in (ord("t"), ord("T")):
        trial_engine.start_or_restart()
        print("Mühürlü Kapı Trial başlatıldı.")
    elif key in (ord("e"), ord("E")) and allow_enrollment_start:
        enrollment_status = enrollment_manager.start(face_detector=face_detector)
        if enrollment_status.message:
            print(enrollment_status.message)
        if enrollment_status.is_complete:
            face_identity_detector.reload()
            if face_identity_detector.warning_message:
                print(face_identity_detector.warning_message)

    if ui_settings["show_settings_menu"]:
        if key == ord("1"):
            ui_settings["show_hand_debug"] = not ui_settings["show_hand_debug"]
            settings_changed = True
        elif key == ord("2"):
            ui_settings["show_face_debug"] = not ui_settings["show_face_debug"]
            settings_changed = True
        elif key == ord("3"):
            ui_settings["verification_requires_qr"] = not ui_settings["verification_requires_qr"]
            verified_face_label = None
            settings_changed = True
        elif key == ord("4"):
            ui_settings["show_spellbook"] = not ui_settings["show_spellbook"]
            settings_changed = True
        elif key == ord("5"):
            ui_settings["show_debug_page"] = not ui_settings["show_debug_page"]
            settings_changed = True
        elif key == ord("6"):
            ui_settings["spell_effects_enabled"] = not ui_settings["spell_effects_enabled"]
            settings_changed = True
        elif key == ord("7"):
            ui_settings["mirror_camera"] = not ui_settings["mirror_camera"]
            verified_face_label = None
            settings_changed = True
        elif key == ord("8"):
            ui_settings["show_system_status"] = not ui_settings.get("show_system_status", False)
        elif key == ord("9"):
            ui_settings["detection_profile"] = _next_detection_profile(
                ui_settings.get("detection_profile", "Dengeli")
            )
            _apply_detection_profile(face_detector, hand_detector, ui_settings["detection_profile"])
            settings_changed = True
        elif key == ord("0"):
            verified_face_label = None
            face_identity_detector.reload()
            print("Doğrulama oturumu sıfırlandı.")

    if settings_changed:
        save_ui_settings(ui_settings)

    return verified_face_label, spellbook_page


def _resolve_auth_state(
    frame,
    face_result,
    face_identity_detector: FaceIdentityDetector,
    guild_seal_detector: GuildSealDetector,
    verified_face_label: str | None,
    verification_requires_qr: bool,
) -> dict:
    """Yüz kimliği + lonca mührü sonucundan aktif profili ve yetkiyi belirler."""
    guest = guest_profile()

    base = {
        "active_profile": guest,
        "allowed_spells": guest.unlocked_spells,
        "verification_status": "Bekleniyor",
        "verified_face_label": None,
        "identity_status": "yüz yok",
        "qr_status": "okunmadı",
        "recognized_user": "-",
        "face_score": "-",
        "face_identity_label": "-",
        "face_identity_score": "-",
        "face_identity_variant": "-",
        "face_quality_message": "-",
    }

    if not face_result.detected or face_result.box is None:
        return base

    if not face_identity_detector.is_available:
        base.update(
            {
                "allowed_spells": guest.unlocked_spells,
                "verification_status": "Yüz tanıma pasif",
                "identity_status": face_identity_detector.warning_message or "pasif",
            }
        )
        return base

    identity_result = face_identity_detector.predict(frame, face_result.box)
    if not identity_result.is_active:
        base.update(
            {
                "allowed_spells": guest.unlocked_spells,
                "verification_status": "Yüz tanıma pasif",
                "identity_status": identity_result.message or "pasif",
                "face_quality_message": identity_result.message or "pasif",
            }
        )
        return base

    identity_status = _identity_debug_status(identity_result)
    face_score = _face_score_debug(identity_result)
    identity_debug = _identity_debug_fields(identity_result)
    candidate_profile = find_profile_by_face_label(identity_result.face_label)
    if not identity_result.matched or candidate_profile is None:
        seal_result = guild_seal_detector.detect(frame, None) if verification_requires_qr else None
        base.update(
            {
                "allowed_spells": guest.unlocked_spells,
                "verification_status": "Mühür kullanıcıyla eşleşmedi" if seal_result and seal_result.mismatch else "Misafir",
                "identity_status": identity_status,
                "qr_status": _qr_debug_status(seal_result),
                "recognized_user": identity_result.face_label or "-",
                "face_score": face_score,
                **identity_debug,
            }
        )
        return base

    if not verification_requires_qr:
        return {
            "active_profile": candidate_profile,
            "allowed_spells": candidate_profile.unlocked_spells,
            "verification_status": "Yüz tanındı",
            "verified_face_label": candidate_profile.face_label,
            "identity_status": identity_status,
            "qr_status": "devre dışı",
            "recognized_user": candidate_profile.username,
            "face_score": face_score,
            **identity_debug,
        }

    seal_result = guild_seal_detector.detect(frame, candidate_profile)
    if seal_result.mismatch:
        return {
            "active_profile": guest,
            "allowed_spells": guest.unlocked_spells,
            "verification_status": "Mühür kullanıcıyla eşleşmedi",
            "verified_face_label": None,
            "identity_status": identity_status,
            "qr_status": _qr_debug_status(seal_result),
            "recognized_user": candidate_profile.username,
            "face_score": face_score,
            **identity_debug,
        }

    if seal_result.matched or verified_face_label == candidate_profile.face_label:
        return {
            "active_profile": candidate_profile,
            "allowed_spells": candidate_profile.unlocked_spells,
            "verification_status": "Yüz + lonca mührü onaylandı",
            "verified_face_label": candidate_profile.face_label,
            "identity_status": identity_status,
            "qr_status": _qr_debug_status(seal_result) if seal_result.detected else "oturum onaylı",
            "recognized_user": candidate_profile.username,
            "face_score": face_score,
            **identity_debug,
        }

    return {
        "active_profile": guest,
        "allowed_spells": guest.unlocked_spells,
        "verification_status": "Yüz tanındı, mühür bekleniyor",
        "verified_face_label": None,
        "identity_status": identity_status,
        "qr_status": _qr_debug_status(seal_result),
        "recognized_user": candidate_profile.username,
        "face_score": face_score,
        **identity_debug,
    }


def _identity_debug_status(identity_result) -> str:
    """Debug paneli için yüz tanıma etiketini ve skorunu özetler."""
    label = identity_result.face_label or "etiket yok"
    score = "skor yok"
    if identity_result.confidence is not None:
        score = f"{identity_result.confidence:.1f}"
    match_status = "eşleşti" if identity_result.matched else "eşleşmedi"
    return f"{label} / {score} / {match_status}"


def _face_score_debug(identity_result) -> str:
    """Debug paneli için yalnızca yüz tanıma skorunu döndürür."""
    if identity_result.confidence is None:
        return "-"
    return f"{identity_result.confidence:.1f}"


def _identity_debug_fields(identity_result) -> dict:
    """Debug paneli için yüz tanıma ayrıntılarını döndürür."""
    return {
        "face_identity_label": identity_result.face_label or "-",
        "face_identity_score": _face_score_debug(identity_result),
        "face_identity_variant": identity_result.selected_variant or "-",
        "face_quality_message": identity_result.quality_message or "-",
    }


def _attempted_locked_spell_debug(spell_result) -> str:
    """Debug panelinde kilitli büyü denemesini güvenli şekilde gösterir."""
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


def _score_debug(score) -> str:
    """Debug paneli için skor değerini kısa metne çevirir."""
    if score is None:
        return "-"
    return f"{float(score):.2f}"


def _box_debug(box) -> str:
    """Debug paneli için yüz kutusu koordinatını kısa metne çevirir."""
    if box is None:
        return "-"
    x, y, width, height = box
    return f"{x},{y},{width},{height}"


def _handedness_debug(hand_result) -> str:
    """Debug paneli için algılanan el yönlerini listeler."""
    if not hand_result or not hand_result.hands:
        return "-"
    labels = [hand.handedness for hand in hand_result.hands if hand.handedness]
    return ", ".join(labels) if labels else "-"


def _qr_debug_status(seal_result) -> str:
    """Debug paneli için QR durumunu sadeleştirir."""
    if seal_result is None:
        return "okunmadı"
    if seal_result.matched:
        return "eşleşti"
    if seal_result.mismatch:
        return "eşleşmedi"
    if seal_result.detected:
        return seal_result.message or "okundu"
    return "okunmadı"


if __name__ == "__main__":
    main()

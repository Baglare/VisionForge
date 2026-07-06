# VisionForge masaüstü uygulamasının başlangıç noktası.

from collections import deque
import time

import cv2

from camera import Camera, CameraError
from detectors.face_detector import FaceDetector, FaceDetectorError
from detectors.face_identity_detector import FaceIdentityDetector
from detectors.guild_seal_detector import GuildSealDetector
from detectors.hand_detector import HandDetector, HandDetectorError
from effects import Effects
from enrollment.enrollment_manager import EnrollmentManager
from guild_profile import find_profile_by_face_label, guest_profile
from spell_engine import SpellEngine


RIGHT_ARROW_KEYS = {83, 2555904, 65363}
LEFT_ARROW_KEYS = {81, 2424832, 65361}


def main() -> None:
    """Kamera görüntüsünü açar, doğrulama ve büyü akışlarını çalıştırır."""
    camera = None
    face_detector = None
    hand_detector = None
    effects = Effects()
    spell_engine = SpellEngine()
    enrollment_manager = EnrollmentManager()
    face_identity_detector = FaceIdentityDetector()
    guild_seal_detector = GuildSealDetector()

    ui_settings = {
        "show_settings_menu": False,
        "show_hand_debug": False,
        "show_face_debug": False,
        "verification_requires_qr": True,
        "show_spellbook": True,
        "show_debug_page": False,
        "spell_effects_enabled": True,
        "mirror_camera": False,
    }

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
        face_detector = FaceDetector()
        if face_detector.warning_message:
            print(face_detector.warning_message)

        hand_detector = HandDetector()
        if hand_detector.warning_message:
            print(hand_detector.warning_message)

        camera = Camera(source=0, window_name="VisionForge - Kamera Modu")
        camera.start()

        print("VisionForge kamera modu aktif.")
        print("Q: ayar menüsü, E: kayıt, R: sıfırla, B: büyü kitabı, H: el çizimi, Esc: çıkış.")

        while True:
            frame = camera.read_frame()
            if ui_settings["mirror_camera"]:
                frame = cv2.flip(frame, 1)

            now = time.monotonic()
            elapsed = max(0.001, now - last_frame_time)
            fps = 0.9 * fps + 0.1 * (1.0 / elapsed) if fps else (1.0 / elapsed)
            last_frame_time = now

            face_result = face_detector.detect(frame)
            face_confirmed, missing_face_frames = _update_face_confirmation(
                face_result,
                face_history,
                face_confirmed,
                missing_face_frames,
            )

            if enrollment_manager.is_active:
                enrollment_status = enrollment_manager.update(frame, face_result)
                if enrollment_status.is_complete and not enrollment_reload_done:
                    face_identity_detector.reload()
                    if face_identity_detector.warning_message:
                        print(face_identity_detector.warning_message)
                    enrollment_reload_done = True

                if ui_settings["show_face_debug"] and face_result.detected and face_result.box is not None:
                    frame = effects.draw_face_box(frame, face_result.box)

                frame = effects.draw_enrollment_panel(frame, enrollment_status)
                frame = effects.draw_settings_menu(frame, ui_settings)
                camera.show_frame(frame)
                key = camera.read_key()
                verified_face_label, spellbook_page = _handle_key(
                    key,
                    ui_settings,
                    verified_face_label,
                    spellbook_page,
                    enrollment_manager,
                    face_identity_detector,
                    allow_enrollment_start=False,
                )
                if camera.is_close_key(key):
                    break

                if enrollment_status.is_complete and getattr(enrollment_manager, "completed_at", 0.0):
                    if time.monotonic() - enrollment_manager.completed_at > 3.0:
                        enrollment_manager.is_active = False
                continue

            hand_result = hand_detector.detect(frame)
            auth_state = _resolve_auth_state(
                frame=frame,
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

            spell_result = spell_engine.update(hand_result, allowed_spells=allowed_spells)

            if ui_settings["show_hand_debug"] and hand_result.detected:
                frame = effects.draw_hand_landmarks(frame, hand_result)

            if ui_settings["show_face_debug"] and face_confirmed and face_result.detected and face_result.box is not None:
                frame = effects.draw_face_box(frame, face_result.box)

            if ui_settings["spell_effects_enabled"]:
                frame = effects.draw_spell_effect(frame, spell_result, hand_result, face_result)

            frame = effects.draw_head_profile_tag(
                frame,
                active_profile,
                face_result=face_result if face_result.detected else None,
                verification_status=verification_status,
            )
            frame = effects.draw_spell_status_panel(frame, spell_result)

            if ui_settings["show_spellbook"]:
                frame = effects.draw_spellbook_panel(frame, active_profile, page=spellbook_page)

            debug_info = {
                "show_debug_page": ui_settings["show_debug_page"],
                "face_status": "var" if face_result.detected else "yok",
                "hand_status": hand_status_text,
                "qr_status": auth_state["qr_status"],
                "identity_status": auth_state["identity_status"],
                "active_profile": f"{active_profile.username} / {active_profile.rank}",
                "fps": f"{fps:.1f}",
                "cooldown": f"{spell_result.cooldown_remaining:.1f} sn" if spell_result.cooldown_remaining > 0 else "hazır",
                "verification_status": verification_status,
            }
            frame = effects.draw_debug_panel(frame, debug_info)
            frame = effects.draw_settings_menu(frame, ui_settings)

            camera.show_frame(frame)

            key = camera.read_key()
            verified_face_label, spellbook_page = _handle_key(
                key,
                ui_settings,
                verified_face_label,
                spellbook_page,
                enrollment_manager,
                face_identity_detector,
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


def _handle_key(
    key: int,
    ui_settings: dict,
    verified_face_label: str | None,
    spellbook_page: int,
    enrollment_manager: EnrollmentManager,
    face_identity_detector: FaceIdentityDetector,
    allow_enrollment_start: bool,
) -> tuple[str | None, int]:
    """Klavye kısayollarını tek merkezden işler."""
    if key < 0:
        return verified_face_label, spellbook_page

    if key in (ord("q"), ord("Q")):
        ui_settings["show_settings_menu"] = not ui_settings["show_settings_menu"]
        return verified_face_label, spellbook_page

    if key in RIGHT_ARROW_KEYS and ui_settings["show_spellbook"]:
        return verified_face_label, min(3, spellbook_page + 1)

    if key in LEFT_ARROW_KEYS and ui_settings["show_spellbook"]:
        return verified_face_label, max(0, spellbook_page - 1)

    if key in (ord("b"), ord("B")):
        ui_settings["show_spellbook"] = not ui_settings["show_spellbook"]
    elif key in (ord("h"), ord("H")):
        ui_settings["show_hand_debug"] = not ui_settings["show_hand_debug"]
    elif key in (ord("r"), ord("R")):
        verified_face_label = None
        print("Doğrulama oturumu sıfırlandı.")
    elif key in (ord("e"), ord("E")) and allow_enrollment_start:
        enrollment_status = enrollment_manager.start()
        if enrollment_status.message:
            print(enrollment_status.message)

    if ui_settings["show_settings_menu"]:
        if key == ord("1"):
            ui_settings["show_hand_debug"] = not ui_settings["show_hand_debug"]
        elif key == ord("2"):
            ui_settings["show_face_debug"] = not ui_settings["show_face_debug"]
        elif key == ord("3"):
            ui_settings["verification_requires_qr"] = not ui_settings["verification_requires_qr"]
            verified_face_label = None
        elif key == ord("4"):
            ui_settings["show_spellbook"] = not ui_settings["show_spellbook"]
        elif key == ord("5"):
            ui_settings["show_debug_page"] = not ui_settings["show_debug_page"]
        elif key == ord("6"):
            ui_settings["spell_effects_enabled"] = not ui_settings["spell_effects_enabled"]
        elif key == ord("7"):
            ui_settings["mirror_camera"] = not ui_settings["mirror_camera"]
            verified_face_label = None
        elif key == ord("0"):
            verified_face_label = None
            face_identity_detector.reload()
            print("Doğrulama oturumu sıfırlandı.")

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
        "allowed_spells": [],
        "verification_status": "Bekleniyor",
        "verified_face_label": None,
        "identity_status": "yüz yok",
        "qr_status": "okunmadı",
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
            }
        )
        return base

    candidate_profile = find_profile_by_face_label(identity_result.face_label)
    if not identity_result.matched or candidate_profile is None:
        seal_result = guild_seal_detector.detect(frame, None) if verification_requires_qr else None
        base.update(
            {
                "allowed_spells": guest.unlocked_spells,
                "verification_status": "Mühür kullanıcıyla eşleşmedi" if seal_result and seal_result.mismatch else "Misafir",
                "identity_status": "eşleşme yok",
                "qr_status": _qr_debug_status(seal_result),
            }
        )
        return base

    if not verification_requires_qr:
        return {
            "active_profile": candidate_profile,
            "allowed_spells": candidate_profile.unlocked_spells,
            "verification_status": "Yüz tanındı",
            "verified_face_label": candidate_profile.face_label,
            "identity_status": f"tanındı: {candidate_profile.face_label}",
            "qr_status": "devre dışı",
        }

    seal_result = guild_seal_detector.detect(frame, candidate_profile)
    if seal_result.mismatch:
        return {
            "active_profile": guest,
            "allowed_spells": guest.unlocked_spells,
            "verification_status": "Mühür kullanıcıyla eşleşmedi",
            "verified_face_label": None,
            "identity_status": f"tanındı: {candidate_profile.face_label}",
            "qr_status": _qr_debug_status(seal_result),
        }

    if seal_result.matched or verified_face_label == candidate_profile.face_label:
        return {
            "active_profile": candidate_profile,
            "allowed_spells": candidate_profile.unlocked_spells,
            "verification_status": "Yüz + lonca mührü onaylandı",
            "verified_face_label": candidate_profile.face_label,
            "identity_status": f"tanındı: {candidate_profile.face_label}",
            "qr_status": _qr_debug_status(seal_result) if seal_result.detected else "oturum onaylı",
        }

    return {
        "active_profile": guest,
        "allowed_spells": guest.unlocked_spells,
        "verification_status": "Yüz tanındı, mühür bekleniyor",
        "verified_face_label": None,
        "identity_status": f"tanındı: {candidate_profile.face_label}",
        "qr_status": _qr_debug_status(seal_result),
    }


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

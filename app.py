# VisionForge masaüstü uygulamasının başlangıç noktası.

from collections import deque
import time

from camera import Camera, CameraError
from detectors.face_detector import FaceDetector, FaceDetectorError
from detectors.face_identity_detector import FaceIdentityDetector
from detectors.guild_seal_detector import GuildSealDetector
from detectors.hand_detector import HandDetector, HandDetectorError
from effects import Effects
from enrollment.enrollment_manager import EnrollmentManager
from guild_profile import find_profile_by_face_label, guest_profile
from spell_engine import SpellEngine


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

    face_history = deque(maxlen=8)
    face_confirmed = False
    missing_face_frames = 0
    show_spellbook = True
    show_hand_debug = True
    verified_face_label: str | None = None
    enrollment_reload_done = False

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
        print("E: kayıt, R: doğrulamayı sıfırla, B: büyü defteri, H: el çizimi, q/Esc: çıkış.")

        while True:
            frame = camera.read_frame()
            face_result = face_detector.detect(frame)

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

            if enrollment_manager.is_active:
                enrollment_status = enrollment_manager.update(frame, face_result)
                if enrollment_status.is_complete and not enrollment_reload_done:
                    face_identity_detector.reload()
                    if face_identity_detector.warning_message:
                        print(face_identity_detector.warning_message)
                    enrollment_reload_done = True

                if face_result.detected and face_result.box is not None:
                    frame = effects.draw_face_box(frame, face_result.box)

                frame = effects.draw_enrollment_panel(frame, enrollment_status)
                camera.show_frame(frame)
                key = camera.read_key()
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
            )
            verified_face_label = auth_state["verified_face_label"]
            active_profile = auth_state["active_profile"]
            allowed_spells = auth_state["allowed_spells"]
            verification_status = auth_state["verification_status"]

            status_text = "Büyücü algılandı" if face_confirmed else "Büyücü bekleniyor"
            if not face_result.detected:
                status_text = "Büyücü bekleniyor"

            if not hand_result.is_active:
                hand_status_text = "El algılama pasif"
            else:
                hand_status_text = "El algılandı" if hand_result.detected else "El bekleniyor"

            spell_result = spell_engine.update(hand_result, allowed_spells=allowed_spells)

            if show_hand_debug and hand_result.detected:
                frame = effects.draw_hand_landmarks(frame, hand_result)

            if face_confirmed and face_result.detected and face_result.box is not None:
                frame = effects.draw_face_box(frame, face_result.box)

            frame = effects.draw_spell_effect(frame, spell_result, hand_result, face_result)

            hint_text = None
            if not face_identity_detector.has_registered_model():
                hint_text = "E ile büyücü kaydı başlat"

            frame = effects.draw_profile_panel(
                frame,
                active_profile,
                status_text=status_text,
                hand_status_text=hand_status_text,
                verification_status=verification_status,
                hint_text=hint_text,
            )
            frame = effects.draw_spell_status_panel(frame, spell_result)
            if show_spellbook:
                frame = effects.draw_spellbook_panel(frame, active_profile)

            camera.show_frame(frame)

            key = camera.read_key()
            if key in (ord("b"), ord("B")):
                show_spellbook = not show_spellbook
            elif key in (ord("h"), ord("H")):
                show_hand_debug = not show_hand_debug
            elif key in (ord("r"), ord("R")):
                verified_face_label = None
                print("Doğrulama oturumu sıfırlandı.")
            elif key in (ord("e"), ord("E")):
                enrollment_reload_done = False
                enrollment_status = enrollment_manager.start()
                if enrollment_status.message:
                    print(enrollment_status.message)

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


def _resolve_auth_state(
    frame,
    face_result,
    face_identity_detector: FaceIdentityDetector,
    guild_seal_detector: GuildSealDetector,
    verified_face_label: str | None,
) -> dict:
    """Yüz kimliği + lonca mührü sonucundan aktif profili ve yetkiyi belirler."""
    guest = guest_profile()

    if not face_result.detected or face_result.box is None:
        return {
            "active_profile": guest,
            "allowed_spells": [],
            "verification_status": "Bekleniyor",
            "verified_face_label": None,
        }

    if not face_identity_detector.is_available:
        return {
            "active_profile": guest,
            "allowed_spells": guest.unlocked_spells,
            "verification_status": "Yüz tanıma pasif",
            "verified_face_label": None,
        }

    identity_result = face_identity_detector.predict(frame, face_result.box)
    if not identity_result.is_active:
        return {
            "active_profile": guest,
            "allowed_spells": guest.unlocked_spells,
            "verification_status": "Yüz tanıma pasif",
            "verified_face_label": None,
        }

    candidate_profile = find_profile_by_face_label(identity_result.face_label)
    seal_result = guild_seal_detector.detect(frame, candidate_profile)

    if not identity_result.matched or candidate_profile is None:
        if seal_result.mismatch:
            return {
                "active_profile": guest,
                "allowed_spells": guest.unlocked_spells,
                "verification_status": "Mühür kullanıcıyla eşleşmedi",
                "verified_face_label": None,
            }
        return {
            "active_profile": guest,
            "allowed_spells": guest.unlocked_spells,
            "verification_status": "Misafir",
            "verified_face_label": None,
        }

    if seal_result.mismatch:
        return {
            "active_profile": guest,
            "allowed_spells": guest.unlocked_spells,
            "verification_status": "Mühür kullanıcıyla eşleşmedi",
            "verified_face_label": None,
        }

    if seal_result.matched or verified_face_label == candidate_profile.face_label:
        return {
            "active_profile": candidate_profile,
            "allowed_spells": candidate_profile.unlocked_spells,
            "verification_status": "Yüz + lonca mührü onaylandı",
            "verified_face_label": candidate_profile.face_label,
        }

    return {
        "active_profile": guest,
        "allowed_spells": guest.unlocked_spells,
        "verification_status": "Yüz tanındı, mühür bekleniyor",
        "verified_face_label": None,
    }


if __name__ == "__main__":
    main()

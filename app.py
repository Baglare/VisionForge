# VisionForge masaüstü uygulamasının başlangıç noktası.

from collections import deque

from camera import Camera, CameraError
from detectors.face_detector import FaceDetector, FaceDetectorError
from detectors.hand_detector import HandDetector, HandDetectorError
from effects import Effects
from guild_profile import load_default_profile
from spell_engine import SpellEngine


def main() -> None:
    """Kamera görüntüsünü açar ve üzerine lonca profil panelini çizer."""
    camera = None
    face_detector = None
    hand_detector = None
    effects = Effects()
    spell_engine = SpellEngine()
    face_history = deque(maxlen=8)
    face_confirmed = False
    missing_face_frames = 0
    show_spellbook = True
    show_hand_debug = True

    try:
        face_detector = FaceDetector()
        if face_detector.warning_message:
            print(face_detector.warning_message)

        hand_detector = HandDetector()
        if hand_detector.warning_message:
            print(hand_detector.warning_message)

        profile = load_default_profile("baglare")
        camera = Camera(source=0, window_name="VisionForge - Kamera Modu")
        camera.start()

        print("VisionForge kamera modu aktif.")
        print("Çıkış için kamera penceresindeyken q veya Esc tuşuna basın.")

        while True:
            frame = camera.read_frame()
            face_result = face_detector.detect(frame)
            hand_result = hand_detector.detect(frame)
            spell_result = spell_engine.update(hand_result)

            if not face_result.is_active:
                face_history.clear()
                face_confirmed = False
                missing_face_frames = 0
                status_text = "Yüz algılama pasif"
            else:
                face_history.append(face_result.detected)

                if face_result.detected:
                    missing_face_frames = 0
                else:
                    missing_face_frames += 1

                if not face_confirmed and sum(face_history) >= 5:
                    face_confirmed = True

                if face_confirmed and missing_face_frames >= 4:
                    face_confirmed = False
                    face_history.clear()

                status_text = "Büyücü algılandı" if face_confirmed else "Büyücü bekleniyor"

            if not hand_result.is_active:
                hand_status_text = "El algılama pasif"
            else:
                hand_status_text = "El algılandı" if hand_result.detected else "El bekleniyor"

            if show_hand_debug and hand_result.detected:
                frame = effects.draw_hand_landmarks(frame, hand_result)

            if face_confirmed and face_result.detected and face_result.box is not None:
                frame = effects.draw_face_box(frame, face_result.box)

            frame = effects.draw_spell_effect(frame, spell_result, hand_result, face_result)

            frame = effects.draw_profile_panel(
                frame,
                profile,
                status_text=status_text,
                hand_status_text=hand_status_text,
            )
            frame = effects.draw_spell_status_panel(frame, spell_result)
            if show_spellbook:
                frame = effects.draw_spellbook_panel(frame, profile)

            camera.show_frame(frame)

            key = camera.read_key()
            if key in (ord("b"), ord("B")):
                show_spellbook = not show_spellbook
            elif key in (ord("h"), ord("H")):
                show_hand_debug = not show_hand_debug

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


if __name__ == "__main__":
    main()

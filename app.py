# VisionForge masaüstü uygulamasının başlangıç noktası.

from collections import deque

from camera import Camera, CameraError
from detectors.face_detector import FaceDetector, FaceDetectorError
from effects import Effects
from guild_profile import load_default_profile


def main() -> None:
    """Kamera görüntüsünü açar ve üzerine lonca profil panelini çizer."""
    camera = None
    face_detector = None
    effects = Effects()
    face_history = deque(maxlen=8)
    face_confirmed = False
    missing_face_frames = 0

    try:
        face_detector = FaceDetector()
        if face_detector.warning_message:
            print(face_detector.warning_message)

        profile = load_default_profile("baglare")
        camera = Camera(source=0, window_name="VisionForge - Kamera Modu")
        camera.start()

        print("VisionForge kamera modu aktif.")
        print("Çıkış için kamera penceresindeyken q veya Esc tuşuna basın.")

        while True:
            frame = camera.read_frame()
            face_result = face_detector.detect(frame)

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

            frame = effects.draw_profile_panel(
                frame,
                profile,
                status_text=status_text,
            )

            if face_confirmed and face_result.detected and face_result.box is not None:
                frame = effects.draw_face_box(frame, face_result.box)

            camera.show_frame(frame)

            if camera.should_close():
                break

    except CameraError as error:
        print(f"Kamera hatası: {error}")
    except FaceDetectorError as error:
        print(f"Yüz algılama hatası: {error}")
    except ValueError as error:
        print(f"Profil hatası: {error}")
    finally:
        if face_detector is not None:
            face_detector.close()
        if camera is not None:
            camera.stop()


if __name__ == "__main__":
    main()

# VisionForge masaüstü uygulamasının başlangıç noktası.

from camera import Camera, CameraError
from effects import Effects
from guild_profile import load_default_profile


def main() -> None:
    """Kamera görüntüsünü açar ve üzerine lonca profil panelini çizer."""
    camera = None
    effects = Effects()

    try:
        profile = load_default_profile("baglare")
        camera = Camera(source=0, window_name="VisionForge - Kamera Modu")
        camera.start()

        print("VisionForge kamera modu aktif.")
        print("Çıkış için kamera penceresindeyken q veya Esc tuşuna basın.")

        while True:
            frame = camera.read_frame()
            frame = effects.draw_profile_panel(
                frame,
                profile,
                status_text="Kamera modu aktif",
            )

            camera.show_frame(frame)

            if camera.should_close():
                break

    except CameraError as error:
        print(f"Kamera hatası: {error}")
    except ValueError as error:
        print(f"Profil hatası: {error}")
    finally:
        if camera is not None:
            camera.stop()


if __name__ == "__main__":
    main()

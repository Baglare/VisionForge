# Uygulama içinden yeni büyücü kaydı, yüz eğitimi ve lonca mührü üretimi yapar.

from dataclasses import dataclass
from pathlib import Path
import secrets
import time

import cv2
import qrcode

from detectors.face_identity_detector import extract_face_image, train_lbph_from_gallery
from guild_profile import build_local_profile, project_root, sanitize_username, save_local_profile


@dataclass
class EnrollmentStatus:
    """Kayıt modunun ekranda gösterilecek durumunu temsil eder."""

    is_active: bool
    is_complete: bool
    username: str = ""
    sample_count: int = 0
    target_count: int = 30
    instruction: str = ""
    message: str = ""
    qr_path: str | None = None


class EnrollmentManager:
    """Kamera karesinden yüz örneği toplayıp yerel tanıma modeli eğitir."""

    INSTRUCTIONS = [
        "Kameraya düz bak",
        "Hafif sağa dön",
        "Hafif sola dön",
        "Biraz yaklaş",
        "Biraz uzaklaş",
    ]

    def __init__(self, samples_per_user: int = 30) -> None:
        self.root = project_root()
        self.samples_per_user = samples_per_user
        self.gallery_root = self.root / "data" / "face_gallery"
        self.import_root = self.root / "data" / "import_faces"
        self.model_path = self.root / "models" / "face_recognizer_lbph.yml"
        self.labels_path = self.root / "data" / "face_labels.json"
        self.seal_root = self.root / "assets" / "guild_seals"
        self.is_active = False
        self.is_complete = False
        self.username = ""
        self.face_label = ""
        self.sample_dir: Path | None = None
        self.sample_count = 0
        self.message = ""
        self.qr_path: Path | None = None
        self._last_sample_at = 0.0
        self.completed_at = 0.0

    def start(self, face_detector=None) -> EnrollmentStatus:
        """Yeni kullanıcı adını ve kayıt kaynağını alır."""
        username = self._ask_username()
        if not username:
            return self.status(message="Kayıt iptal edildi.")

        try:
            face_label = sanitize_username(username)
        except ValueError as error:
            return self.status(message=str(error))

        self.username = username.strip()
        self.face_label = face_label
        self.sample_dir = self.gallery_root / face_label
        mode = self._ask_enrollment_mode()
        if not mode:
            return self.status(message="Kayıt iptal edildi.")

        self._prepare_user_workspace()

        if mode == "import":
            return self._import_images(face_detector)

        return self._start_camera_capture()

    def _prepare_user_workspace(self) -> None:
        """Kullanıcının yerel kayıt klasörlerini hazırlar."""
        if self.sample_dir is None:
            self.sample_dir = self.gallery_root / self.face_label

        self.sample_dir.mkdir(parents=True, exist_ok=True)
        self.import_root.mkdir(parents=True, exist_ok=True)
        self.seal_root.mkdir(parents=True, exist_ok=True)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.labels_path.parent.mkdir(parents=True, exist_ok=True)

        for old_sample in self.sample_dir.glob("sample_*.png"):
            old_sample.unlink()

    def _start_camera_capture(self) -> EnrollmentStatus:
        """Canlı kamera üzerinden örnek toplama modunu başlatır."""
        self.is_active = True
        self.is_complete = False
        self.sample_count = 0
        self.message = "Yüz örnekleri toplanıyor."
        self.qr_path = None
        self._last_sample_at = 0.0
        self.completed_at = 0.0
        return self.status()

    def update(self, frame, face_result) -> EnrollmentStatus:
        """Kayıt modunda yüz örneği toplar ve yeterli örnekten sonra eğitim yapar."""
        if not self.is_active:
            return self.status()

        if self.is_complete:
            return self.status()

        if face_result is None or not face_result.detected or face_result.box is None:
            self.message = "Yüz bulunamadı, kameraya bak."
            return self.status()

        now = time.monotonic()
        if now - self._last_sample_at < 0.08:
            return self.status()

        face_image = extract_face_image(frame, face_result.box)
        if face_image is None:
            self.message = "Yüz kutusu küçük veya bozuk, biraz daha net dur."
            return self.status()

        self.sample_count += 1
        sample_path = self.sample_dir / f"sample_{self.sample_count:03d}.png"
        cv2.imwrite(str(sample_path), face_image)
        self._last_sample_at = now
        self.message = "Yüz örneği alındı."

        if self.sample_count >= self.samples_per_user:
            try:
                self._finish_enrollment()
            except Exception as error:
                self.message = f"Kayıt tamamlanamadı: {error}"
                self.is_active = False

        return self.status()

    def cancel(self) -> EnrollmentStatus:
        """Kayıt modunu kapatır."""
        self.is_active = False
        return self.status(message="Kayıt modu kapatıldı.")

    def status(self, message: str | None = None) -> EnrollmentStatus:
        """Güncel kayıt durumunu döndürür."""
        return EnrollmentStatus(
            is_active=self.is_active,
            is_complete=self.is_complete,
            username=self.username,
            sample_count=self.sample_count,
            target_count=self.samples_per_user,
            instruction=self._current_instruction(),
            message=message if message is not None else self.message,
            qr_path=str(self.qr_path) if self.qr_path else None,
        )

    def _finish_enrollment(self) -> None:
        """Yeterli örnekten sonra model eğitir, profil ve QR üretir."""
        trained_count = train_lbph_from_gallery(self.gallery_root, self.model_path, self.labels_path)

        seal_code = f"VISIONFORGE_GUILD_{self.face_label.upper()}_{secrets.token_hex(5).upper()}"
        profile = build_local_profile(self.username, seal_code)
        save_local_profile(profile)

        self.qr_path = self.seal_root / f"{self.face_label}_seal.png"
        qr_image = qrcode.make(seal_code)
        qr_image.save(self.qr_path)

        self.is_complete = True
        self.completed_at = time.monotonic()
        self.message = f"Kayıt tamamlandı. {trained_count} örnek ile model eğitildi."

    def _current_instruction(self) -> str:
        """Örnek sayısına göre kullanıcı yönlendirmesi döndürür."""
        if self.is_complete:
            return "Kayıt tamamlandı"
        if not self.is_active:
            return "E ile yeni büyücü kaydı başlat"

        segment_size = max(1, self.samples_per_user // len(self.INSTRUCTIONS))
        index = min(len(self.INSTRUCTIONS) - 1, self.sample_count // segment_size)
        return self.INSTRUCTIONS[index]

    def _ask_username(self) -> str | None:
        """Tkinter ile kullanıcı adı alır; olmazsa terminal input kullanır."""
        try:
            import tkinter as tk
            from tkinter import simpledialog

            root = tk.Tk()
            root.withdraw()
            username = simpledialog.askstring("VisionForge", "Büyücü adını gir:")
            root.destroy()
            return username
        except Exception:
            try:
                return input("Büyücü adını gir: ")
            except EOFError:
                return None

    def _ask_enrollment_mode(self) -> str:
        """Kayıt kaynağı seçimini alır."""
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            choice = messagebox.askyesnocancel(
                "VisionForge",
                "Kayıt kaynağı seç:\n\nEvet: Canlı kamera kaydı\nHayır: Görsel import",
            )
            root.destroy()
            if choice is None:
                return ""
            return "camera" if choice else "import"
        except Exception:
            try:
                choice = input("Kayıt kaynağı seç (1: Canlı kamera, 2: Görsel import): ").strip()
            except EOFError:
                return "camera"

            if choice == "2":
                return "import"
            if choice in {"", "1"}:
                return "camera"
            return ""

    def _ask_import_directory(self) -> Path:
        """Görsel import klasörünü seçtirir; olmazsa varsayılan klasörü kullanır."""
        default_dir = self.import_root / self.face_label
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            selected = filedialog.askdirectory(
                title="Yüz fotoğrafları klasörünü seç",
                initialdir=str(default_dir.parent),
            )
            root.destroy()
            if selected:
                return Path(selected)
        except Exception:
            try:
                typed_path = input(f"Görsel klasörü [{default_dir}]: ").strip()
                if typed_path:
                    return Path(typed_path)
            except EOFError:
                pass

        default_dir.mkdir(parents=True, exist_ok=True)
        return default_dir

    def _import_images(self, face_detector) -> EnrollmentStatus:
        """Klasördeki fotoğraflardan yüz örneği çıkarıp eğitimi tamamlar."""
        self.is_active = False
        self.is_complete = False
        self.sample_count = 0
        self.qr_path = None
        self.completed_at = 0.0

        if face_detector is None or not getattr(face_detector, "is_available", False):
            self.message = "Görsel import için yüz algılama modeli aktif olmalı."
            return self.status(message=self.message)

        source_dir = self._ask_import_directory()
        image_paths = list(self._iter_image_paths(source_dir))
        if not image_paths:
            self.message = f"Görsel bulunamadı. Fotoğrafları şu klasöre koy: {source_dir}"
            return self.status(message=self.message)

        for image_path in image_paths:
            image = cv2.imread(str(image_path))
            if image is None:
                continue

            face_result = face_detector.detect(image)
            if not face_result.detected or face_result.box is None:
                continue

            face_image = extract_face_image(image, face_result.box)
            if face_image is None:
                continue

            self.sample_count += 1
            sample_path = self.sample_dir / f"sample_import_{self.sample_count:03d}.png"
            cv2.imwrite(str(sample_path), face_image)

        if self.sample_count <= 0:
            self.message = "Import edilen görsellerde geçerli yüz örneği bulunamadı."
            return self.status(message=self.message)

        try:
            self._finish_enrollment()
        except Exception as error:
            self.message = f"Import eğitimi tamamlanamadı: {error}"
            return self.status(message=self.message)

        self.is_active = False
        return self.status(message=f"Görsel import tamamlandı. {self.sample_count} örnek işlendi.")

    def _iter_image_paths(self, source_dir: Path):
        """Desteklenen görsel dosyalarını klasörden okur."""
        extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        if not source_dir.exists() or not source_dir.is_dir():
            return

        for path in sorted(source_dir.iterdir()):
            if path.is_file() and path.suffix.lower() in extensions:
                yield path

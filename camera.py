# Kamera bağlantısını ve canlı görüntü akışını yönetir.

import cv2


class CameraError(RuntimeError):
    """Kamera başlatma veya okuma sırasında oluşan anlaşılır hata."""


class Camera:
    """OpenCV üzerinden varsayılan kamerayı kontrol eder."""

    def __init__(self, source: int = 0, window_name: str = "VisionForge") -> None:
        self.source = source
        self.window_name = window_name
        self.capture = None
        self.is_running = False

    def start(self) -> None:
        """Varsayılan kamerayı açar."""
        self.capture = cv2.VideoCapture(self.source)

        if not self.capture.isOpened():
            self.capture.release()
            self.capture = None
            raise CameraError(
                "Kamera açılamadı. Kameranın bağlı, açık ve başka bir uygulama "
                "tarafından kullanılmıyor olduğundan emin olun."
            )

        self.is_running = True

    def read_frame(self):
        """Kameradan tek bir canlı görüntü karesi okur."""
        if self.capture is None or not self.is_running:
            raise CameraError("Kamera başlatılmadan görüntü okunamaz.")

        success, frame = self.capture.read()
        if not success or frame is None:
            raise CameraError("Kameradan görüntü alınamadı.")

        return frame

    def show_frame(self, frame) -> None:
        """Verilen görüntü karesini OpenCV penceresinde gösterir."""
        cv2.imshow(self.window_name, frame)

    def read_key(self, delay: int = 1) -> int:
        """OpenCV penceresinden tek tuş okur."""
        return cv2.waitKey(delay) & 0xFF

    def is_close_key(self, key: int) -> bool:
        """q veya Esc tuşunun kapatma isteği olup olmadığını döndürür."""
        return key == ord("q") or key == 27

    def should_close(self, delay: int = 1) -> bool:
        """q veya Esc tuşuna basıldığında pencereyi kapatma isteğini döndürür."""
        return self.is_close_key(self.read_key(delay))

    def stop(self) -> None:
        """Kamera kaynağını ve OpenCV pencerelerini güvenli şekilde kapatır."""
        if self.capture is not None:
            self.capture.release()
            self.capture = None

        self.is_running = False
        cv2.destroyAllWindows()

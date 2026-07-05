# Kullanici yuzunu algilama akisi icin temel sinif iskeletidir.


class FaceDetector:
    """Yuz algilama davranisinin ileride genisletilecegi sinif."""

    def __init__(self) -> None:
        self.name = "FaceDetector"
        self.is_ready = False

    def initialize(self) -> None:
        """Yuz algilama modelinin hazirlanacagi yer tutucu."""
        self.is_ready = True

    def detect(self, frame):
        """Verilen goruntu karesinde yuz aramak icin kullanilacak yer tutucu."""
        return []

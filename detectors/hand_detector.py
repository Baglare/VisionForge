# Kullanici el hareketlerini algilama akisi icin temel sinif iskeletidir.


class HandDetector:
    """El algilama davranisinin ileride genisletilecegi sinif."""

    def __init__(self) -> None:
        self.name = "HandDetector"
        self.is_ready = False

    def initialize(self) -> None:
        """El algilama modelinin hazirlanacagi yer tutucu."""
        self.is_ready = True

    def detect(self, frame):
        """Verilen goruntu karesinde el veya hareket aramak icin yer tutucu."""
        return []

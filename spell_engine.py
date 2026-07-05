# El hareketlerinden buyu komutlarina gecis yapacak motorun iskeletidir.


class SpellEngine:
    """Buyu komutu uretme mantiginin ileride eklenecegi sinif."""

    def __init__(self) -> None:
        self.status = "beklemede"

    def interpret_gesture(self, gesture_data):
        """Algilanan hareket verisini buyu komutuna cevirmek icin yer tutucu."""
        return None

    def list_available_spells(self, profile) -> list[str]:
        """Profilde acik olan buyuleri dondurur."""
        return profile.unlocked_spells

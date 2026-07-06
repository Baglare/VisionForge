# Portfolyo demosu sırasında kullanıcıya sıradaki adımı gösteren hafif rehber.

from dataclasses import dataclass
import time


@dataclass(frozen=True)
class DemoStep:
    """Demo rehberindeki tek adımı temsil eder."""

    title: str
    message: str
    event_key: str = ""
    shortcut_hint: tuple[str, ...] = ()


@dataclass
class DemoGuideStatus:
    """Ekranda çizilecek demo rehberi durumunu temsil eder."""

    state: str
    current_step: int
    total_steps: int
    title: str
    message: str
    shortcut_hints: tuple[str, ...]
    step_completed: bool = False


class DemoGuide:
    """Demo adımlarını manuel ve basit olaylarla ilerletir."""

    STEPS = [
        DemoStep(
            "Kamera ve profil",
            "Yüzünü kameraya göster. Kayıtlı değilsen E ile büyücü kaydı başlat.",
        ),
        DemoStep(
            "Doğrulama",
            "QR + Yüz modundaysan lonca mührünü göster. İstersen Q > 3 ile Yalnızca Yüz moduna geç.",
            "verified",
        ),
        DemoStep(
            "Büyü Kitabı",
            "B ile Büyü Kitabı'nı aç. Sağ/sol oklarla büyü sayfalarını gez.",
            "spellbook_open",
            ("Q: Menü | E: Kayıt | B: Kitap | T: Trial", "Sağ/Sol Ok: Sayfa değiştir | Esc: Çıkış"),
        ),
        DemoStep(
            "Donma",
            "Avucunu açık tutarak Donma büyüsünü tetikle.",
            "spell:Donma",
        ),
        DemoStep(
            "Ateş",
            "Elini kontrollü yatay süpür, sonra avuç göstererek Ateş büyüsünü tetikle.",
            "spell:Ateş",
        ),
        DemoStep(
            "Kalkan",
            "İki açık elini göstererek Kalkan büyüsünü tetikle.",
            "spell:Kalkan",
        ),
        DemoStep(
            "Trial Mode",
            "T ile Mühürlü Kapı görevini başlat.",
            "trial_active",
        ),
        DemoStep(
            "Trial tamamlama",
            "Sırayla Donma -> Ateş -> Kalkan yaparak kapıyı aç.",
            "trial_completed",
        ),
        DemoStep(
            "Final",
            "Demo tamamlandı. VisionForge temel akışı gösterildi.",
        ),
    ]

    def __init__(self) -> None:
        self.state = "inactive"
        self.current_index = 0
        self.min_step_display_duration = 1.5
        self._step_started_at = time.monotonic()
        self._pending_auto_advance = False
        self._completion_notified = False

    def toggle(self) -> str:
        """G tuşu için rehberi başlatır veya kapatır."""
        if self.state == "inactive":
            self.start()
            return "started"

        self.reset()
        return "stopped"

    def start(self) -> None:
        """Demo rehberini ilk adımdan başlatır."""
        self.state = "active"
        self.current_index = 0
        self._mark_step_started()
        self._completion_notified = False

    def reset(self) -> None:
        """Demo rehberini kapatır ve ilk adıma döndürür."""
        self.state = "inactive"
        self.current_index = 0
        self._mark_step_started()
        self._completion_notified = False

    def next(self) -> str:
        """Manuel olarak sonraki adıma geçer."""
        if self.state == "inactive":
            return ""

        if self.current_index >= len(self.STEPS) - 1:
            self.state = "completed"
            return self._complete_once()

        self.current_index += 1
        self._mark_step_started()
        if self.current_index >= len(self.STEPS) - 1:
            self.state = "completed"
            return self._complete_once()
        return ""

    def previous(self) -> None:
        """Manuel olarak önceki adıma döner."""
        if self.state == "inactive":
            return

        self.state = "active"
        self._completion_notified = False
        self.current_index = max(0, self.current_index - 1)
        self._mark_step_started()

    def update(self, events: dict) -> str:
        """Uygulama olaylarına göre mevcut adımı gerekiyorsa ilerletir."""
        if self.state != "active":
            return ""

        step = self.STEPS[self.current_index]
        if not step.event_key:
            return ""

        if self._event_completed(step.event_key, events):
            self._pending_auto_advance = True

        if self._pending_auto_advance and time.monotonic() - self._step_started_at >= self.min_step_display_duration:
            return self.next()
        return ""

    def status(self) -> DemoGuideStatus:
        """Ekranda çizilecek mevcut demo durumunu döndürür."""
        step = self.STEPS[self.current_index]
        return DemoGuideStatus(
            state=self.state,
            current_step=self.current_index + 1,
            total_steps=len(self.STEPS),
            title=step.title,
            message=step.message,
            shortcut_hints=step.shortcut_hint or self._default_shortcut_hints(),
            step_completed=self._pending_auto_advance,
        )

    def _mark_step_started(self) -> None:
        """Yeni adım başladığında zaman ve tamamlanma beklemesini sıfırlar."""
        self._step_started_at = time.monotonic()
        self._pending_auto_advance = False

    def _default_shortcut_hints(self) -> tuple[str, ...]:
        """Panel altında gösterilecek kısa genel kısayolları döndürür."""
        return (
            "Q: Menü | E: Kayıt | B: Kitap | T: Trial | Esc: Çıkış",
            "N/P: Demo adımı | H: El çizimi | D: Debug sayfası",
        )

    def _event_completed(self, event_key: str, events: dict) -> bool:
        """Basit demo olaylarının tamamlanıp tamamlanmadığını döndürür."""
        if event_key == "verified":
            return events.get("verification_status") in {
                "Yüz tanındı",
                "Yüz + lonca mührü onaylandı",
            }
        if event_key == "spellbook_open":
            return bool(events.get("spellbook_open")) and int(events.get("spellbook_page", 0)) > 0
        if event_key.startswith("spell:"):
            return events.get("active_spell_name") == event_key.split(":", 1)[1]
        if event_key == "trial_active":
            return events.get("trial_state") in {"active", "completed"}
        if event_key == "trial_completed":
            return events.get("trial_state") == "completed"
        return False

    def _complete_once(self) -> str:
        """Tamamlanma olayını yalnızca bir kez döndürür."""
        if self._completion_notified:
            return ""
        self._completion_notified = True
        return "completed"

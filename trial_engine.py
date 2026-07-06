# Mühürlü Kapı görev modunun sıralı büyü ilerlemesini yönetir.

from dataclasses import dataclass, field


TRIAL_NAME = "Mühürlü Kapı"
TRIAL_SEQUENCE = ["Donma", "Ateş", "Kalkan"]


@dataclass
class TrialStatus:
    """Trial paneli ve debug ekranı için görev durumunu temsil eder."""

    name: str = TRIAL_NAME
    state: str = "idle"
    current_step: int = 0
    required_spell: str | None = TRIAL_SEQUENCE[0]
    completed_steps: list[str] = field(default_factory=list)
    message: str = "T ile Trial başlat"

    @property
    def completed_count(self) -> int:
        """Tamamlanan mühür sayısını döndürür."""
        return len(self.completed_steps)

    @property
    def total_steps(self) -> int:
        """Toplam mühür sayısını döndürür."""
        return len(TRIAL_SEQUENCE)

    @property
    def is_active(self) -> bool:
        """Görevin aktif olup olmadığını döndürür."""
        return self.state == "active"

    @property
    def is_completed(self) -> bool:
        """Görevin tamamlanıp tamamlanmadığını döndürür."""
        return self.state == "completed"


class TrialEngine:
    """Donma -> Ateş -> Kalkan sırasını izleyen basit görev motoru."""

    def __init__(self) -> None:
        self.state = "idle"
        self.current_step = 0
        self.completed_steps: list[str] = []
        self.message = "T ile Trial başlat"
        self._last_seen_spell: str | None = None

    def start_or_restart(self) -> TrialStatus:
        """Trial görevini başlatır veya baştan başlatır."""
        self.state = "active"
        self.current_step = 0
        self.completed_steps = []
        self.message = "Trial başladı"
        self._last_seen_spell = None
        return self.status()

    def update(
        self,
        active_spell_name: str | None = None,
        allowed_spells: list[str] | tuple[str, ...] | None = None,
    ) -> TrialStatus:
        """Aktif büyü olayını görev sırasına göre değerlendirir."""
        if self.state != "active":
            self._remember_spell(active_spell_name)
            return self.status()

        allowed_set = set(allowed_spells or [])
        required_spell = self.required_spell()
        if required_spell and required_spell not in allowed_set:
            self.message = f"{required_spell} kilitli: daha yüksek yetki gerekli"

        new_spell_event = self._consume_new_spell_event(active_spell_name)
        if not new_spell_event:
            return self.status()

        if new_spell_event != required_spell:
            self.message = "Yanlış büyü"
            return self.status()

        if required_spell not in allowed_set:
            self.message = f"{required_spell} kilitli: daha yüksek yetki gerekli"
            return self.status()

        self.completed_steps.append(required_spell)
        self.current_step += 1

        if self.current_step >= len(TRIAL_SEQUENCE):
            self.state = "completed"
            self.message = "Trial tamamlandı"
        else:
            self.message = f"{required_spell} mührü açıldı"

        return self.status()

    def required_spell(self) -> str | None:
        """Sıradaki gerekli büyüyü döndürür."""
        if self.current_step >= len(TRIAL_SEQUENCE):
            return None
        return TRIAL_SEQUENCE[self.current_step]

    def status(self) -> TrialStatus:
        """Güncel görev durumunu döndürür."""
        return TrialStatus(
            state=self.state,
            current_step=self.current_step,
            required_spell=self.required_spell(),
            completed_steps=self.completed_steps.copy(),
            message=self.message,
        )

    def _consume_new_spell_event(self, active_spell_name: str | None) -> str | None:
        """Aynı aktif büyünün birkaç kare boyunca tekrar işlenmesini engeller."""
        if active_spell_name is None:
            self._last_seen_spell = None
            return None

        if active_spell_name == self._last_seen_spell:
            return None

        self._last_seen_spell = active_spell_name
        return active_spell_name

    def _remember_spell(self, active_spell_name: str | None) -> None:
        """Idle/completed durumda aktif büyü tekrarlarını takip eder."""
        if active_spell_name is None:
            self._last_seen_spell = None
        else:
            self._last_seen_spell = active_spell_name

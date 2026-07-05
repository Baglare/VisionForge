# Lonca temalı kullanıcı profil verisini temsil eder ve dosyadan yükler.

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GuildProfile:
    """VisionForge içindeki lonca profili verisi."""

    username: str
    rank: str
    unlocked_spells: list[str]
    locked_spells: list[str]

    @classmethod
    def load_from_file(cls, file_path: str, username: str) -> "GuildProfile":
        """JSON profil dosyasından istenen kullanıcıyı yükler."""
        path = Path(file_path)
        data = json.loads(path.read_text(encoding="utf-8"))

        for profile in data.get("profiles", []):
            if profile.get("username") == username:
                return cls(
                    username=profile["username"],
                    rank=profile["rank"],
                    unlocked_spells=profile["unlocked_spells"],
                    locked_spells=profile["locked_spells"],
                )

        raise ValueError(f"Profil bulunamadı: {username}")


def load_default_profile(username: str = "baglare") -> GuildProfile:
    """Varsayılan profil dosyasından seçilen lonca profilini yükler."""
    profile_path = Path(__file__).resolve().parent / "data" / "profiles.json"
    return GuildProfile.load_from_file(str(profile_path), username=username)

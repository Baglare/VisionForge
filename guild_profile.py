# Lonca temalı kullanıcı profil verisini yükler, birleştirir ve kaydeder.

import json
import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_LOCKED_SPELLS = ["Ateş", "Kalkan", "Şimşek", "Alan Mührü", "Zaman Kırığı"]


@dataclass
class GuildProfile:
    """VisionForge içindeki lonca profili verisi."""

    username: str
    rank: str
    unlocked_spells: list[str]
    locked_spells: list[str]
    guild_seal_code: str | None = None
    face_label: str | None = None
    is_guest: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "GuildProfile":
        """JSON sözlüğünü profil nesnesine çevirir."""
        unlocked_spells = data.get("unlocked_spells", data.get("open_spells", []))
        return cls(
            username=str(data.get("username", "")),
            rank=str(data.get("rank", "")),
            unlocked_spells=list(unlocked_spells),
            locked_spells=list(data.get("locked_spells", [])),
            guild_seal_code=data.get("guild_seal_code"),
            face_label=data.get("face_label") or data.get("username"),
            is_guest=bool(data.get("is_guest", False)),
        )

    def to_dict(self) -> dict:
        """Profili JSON'a yazılabilir sözlüğe çevirir."""
        data = {
            "username": self.username,
            "rank": self.rank,
            "unlocked_spells": self.unlocked_spells,
            "locked_spells": self.locked_spells,
            "face_label": self.face_label or self.username,
        }
        if self.guild_seal_code:
            data["guild_seal_code"] = self.guild_seal_code
        if self.is_guest:
            data["is_guest"] = True
        return data

    @classmethod
    def load_from_file(cls, file_path: str, username: str) -> "GuildProfile":
        """JSON profil dosyasından istenen kullanıcıyı yükler."""
        profiles = load_profiles_from_file(Path(file_path))
        for profile in profiles:
            if profile.username == username:
                return profile

        raise ValueError(f"Profil bulunamadı: {username}")


def project_root() -> Path:
    """Proje kök klasörünü döndürür."""
    return Path(__file__).resolve().parent


def default_profiles_path() -> Path:
    """Demo profil dosyası yolunu döndürür."""
    return project_root() / "data" / "profiles.json"


def local_profiles_path() -> Path:
    """Yerel kullanıcı profil dosyası yolunu döndürür."""
    return project_root() / "data" / "local_profiles.json"


def guest_profile() -> GuildProfile:
    """Misafir profilini döndürür."""
    return GuildProfile(
        username="Misafir",
        rank="Misafir Büyücü",
        unlocked_spells=["Donma"],
        locked_spells=DEFAULT_LOCKED_SPELLS.copy(),
        face_label="guest",
        is_guest=True,
    )


def sanitize_username(username: str) -> str:
    """Kullanıcı adını dosya ve etiket için güvenli hale getirir."""
    cleaned = username.strip().lower()
    cleaned = re.sub(r"[^a-z0-9_]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        raise ValueError("Kullanıcı adı boş olamaz.")
    return cleaned


def display_username(username: str) -> str:
    """Boşlukları temizlenmiş ekranda gösterilecek kullanıcı adını döndürür."""
    cleaned = username.strip()
    if not cleaned:
        raise ValueError("Kullanıcı adı boş olamaz.")
    return cleaned


def load_profiles_from_file(path: Path) -> list[GuildProfile]:
    """Verilen JSON dosyasındaki profilleri okur."""
    if not path.exists():
        return []

    data = json.loads(path.read_text(encoding="utf-8"))
    return [GuildProfile.from_dict(profile) for profile in data.get("profiles", [])]


def load_all_profiles() -> list[GuildProfile]:
    """Demo, yerel ve Misafir profillerini birlikte döndürür."""
    profiles_by_key: dict[str, GuildProfile] = {"guest": guest_profile()}

    for profile in load_profiles_from_file(default_profiles_path()):
        profiles_by_key[profile.face_label or profile.username] = profile

    for profile in load_profiles_from_file(local_profiles_path()):
        profiles_by_key[profile.face_label or profile.username] = profile

    return list(profiles_by_key.values())


def load_default_profile(username: str = "baglare") -> GuildProfile:
    """Varsayılan profil dosyalarından seçilen lonca profilini yükler."""
    return find_profile(username) or guest_profile()


def find_profile(username: str) -> GuildProfile | None:
    """Kullanıcı adına göre profil bulur."""
    for profile in load_all_profiles():
        if profile.username == username or profile.face_label == username:
            return profile
    return None


def find_profile_by_face_label(face_label: str | None) -> GuildProfile | None:
    """Yüz tanıma etiketine göre profil bulur."""
    if not face_label:
        return None

    for profile in load_all_profiles():
        if profile.face_label == face_label or profile.username == face_label:
            return profile
    return None


def find_profile_by_seal_code(seal_code: str | None) -> GuildProfile | None:
    """Lonca mührü koduna göre profil bulur."""
    if not seal_code:
        return None

    for profile in load_all_profiles():
        if profile.guild_seal_code == seal_code:
            return profile
    return None


def build_local_profile(username: str, guild_seal_code: str) -> GuildProfile:
    """Yeni kayıt için varsayılan yerel profil oluşturur."""
    safe_name = sanitize_username(username)
    return GuildProfile(
        username=display_username(username),
        rank="C-Seviye Büyücü",
        unlocked_spells=["Donma"],
        locked_spells=DEFAULT_LOCKED_SPELLS.copy(),
        guild_seal_code=guild_seal_code,
        face_label=safe_name,
    )


def save_local_profile(profile: GuildProfile) -> None:
    """Yerel kullanıcı profilini local_profiles.json içine ekler veya günceller."""
    path = local_profiles_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    profiles = load_profiles_from_file(path)

    profile_key = profile.face_label or profile.username
    updated = False
    for index, existing_profile in enumerate(profiles):
        existing_key = existing_profile.face_label or existing_profile.username
        if existing_key == profile_key:
            profiles[index] = profile
            updated = True
            break

    if not updated:
        profiles.append(profile)

    payload = {"profiles": [item.to_dict() for item in profiles]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

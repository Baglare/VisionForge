# Lonca temalı kullanıcı profil verisini yükler, birleştirir ve kaydeder.

import json
import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_LOCKED_SPELLS = ["Ateş", "Kalkan", "Şimşek", "Alan Mührü", "Zaman Kırığı"]
BAGLARE_FACE_LABEL = "baglare"
BAGLARE_UNLOCKED_SPELLS = ["Donma", "Ateş", "Kalkan"]
BAGLARE_LOCKED_SPELLS = ["Şimşek", "Alan Mührü", "Zaman Kırığı"]
BAGLARE_GUILD_NAME = "VisionForge Loncası"
GUEST_GUILD_NAME = "Loncasız"
DEFAULT_GUILD_NAME = "Bağımsız Büyücüler"


@dataclass
class GuildProfile:
    """VisionForge içindeki lonca profili verisi."""

    username: str
    rank: str
    unlocked_spells: list[str]
    locked_spells: list[str]
    guild_name: str = DEFAULT_GUILD_NAME
    guild_seal_code: str | None = None
    face_label: str | None = None
    is_guest: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "GuildProfile":
        """JSON sözlüğünü profil nesnesine çevirir."""
        unlocked_spells = data.get("unlocked_spells", data.get("open_spells", []))
        username = str(data.get("username", ""))
        face_label = data.get("face_label") or username
        is_guest = bool(data.get("is_guest", False))
        return cls(
            username=username,
            rank=str(data.get("rank", "")),
            unlocked_spells=list(unlocked_spells),
            locked_spells=list(data.get("locked_spells", [])),
            guild_name=str(data.get("guild_name") or _default_guild_name(username, face_label, is_guest)),
            guild_seal_code=data.get("guild_seal_code"),
            face_label=face_label,
            is_guest=is_guest,
        )

    def to_dict(self) -> dict:
        """Profili JSON'a yazılabilir sözlüğe çevirir."""
        data = {
            "username": self.username,
            "rank": self.rank,
            "guild_name": self.guild_name,
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
        guild_name=GUEST_GUILD_NAME,
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


def normalize_profile(profile: GuildProfile) -> GuildProfile:
    """Özel demo profilleri ve boş açık büyü listelerini tek yerde düzeltir."""
    if _is_baglare_profile(profile):
        return GuildProfile(
            username="baglare",
            rank="S-Seviye Büyücü",
            unlocked_spells=BAGLARE_UNLOCKED_SPELLS.copy(),
            locked_spells=BAGLARE_LOCKED_SPELLS.copy(),
            guild_name=BAGLARE_GUILD_NAME,
            guild_seal_code=profile.guild_seal_code,
            face_label=BAGLARE_FACE_LABEL,
            is_guest=False,
        )

    unlocked_spells = profile.unlocked_spells or ["Donma"]
    locked_spells = [spell for spell in profile.locked_spells if spell not in unlocked_spells]
    guild_name = GUEST_GUILD_NAME if profile.is_guest else (profile.guild_name or DEFAULT_GUILD_NAME)
    return GuildProfile(
        username=profile.username,
        rank=profile.rank,
        unlocked_spells=unlocked_spells,
        locked_spells=locked_spells,
        guild_name=guild_name,
        guild_seal_code=profile.guild_seal_code,
        face_label=profile.face_label or profile.username,
        is_guest=profile.is_guest,
    )


def repair_local_profiles() -> None:
    """Yerel profillerde eski baglare yetkisi varsa dosyayı otomatik düzeltir."""
    path = local_profiles_path()
    if not path.exists():
        return

    data = json.loads(path.read_text(encoding="utf-8"))
    normalized_profiles = [
        normalize_profile(GuildProfile.from_dict(item))
        for item in data.get("profiles", [])
    ]
    normalized_payload = {"profiles": [profile.to_dict() for profile in normalized_profiles]}

    if data != normalized_payload:
        path.write_text(json.dumps(normalized_payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _is_baglare_profile(profile: GuildProfile) -> bool:
    """Profilin baglare demo kullanıcısına ait olup olmadığını döndürür."""
    return _profile_key(profile.username) == BAGLARE_FACE_LABEL or _profile_key(profile.face_label) == BAGLARE_FACE_LABEL


def _profile_key(value: str | None) -> str:
    """Karşılaştırma için güvenli profil anahtarı üretir."""
    if not value:
        return ""
    cleaned = value.strip().lower()
    cleaned = re.sub(r"[^a-z0-9_]+", "_", cleaned)
    return re.sub(r"_+", "_", cleaned).strip("_")


def _default_guild_name(username: str, face_label: str | None, is_guest: bool) -> str:
    """Eski profil kayıtları için güvenli varsayılan lonca adını döndürür."""
    if is_guest or _profile_key(username) in {"guest", "misafir"} or _profile_key(face_label) == "guest":
        return GUEST_GUILD_NAME
    if _profile_key(username) == BAGLARE_FACE_LABEL or _profile_key(face_label) == BAGLARE_FACE_LABEL:
        return BAGLARE_GUILD_NAME
    return DEFAULT_GUILD_NAME


def load_profiles_from_file(path: Path) -> list[GuildProfile]:
    """Verilen JSON dosyasındaki profilleri okur."""
    if not path.exists():
        return []

    data = json.loads(path.read_text(encoding="utf-8"))
    return [normalize_profile(GuildProfile.from_dict(profile)) for profile in data.get("profiles", [])]


def load_all_profiles() -> list[GuildProfile]:
    """Demo, yerel ve Misafir profillerini birlikte döndürür."""
    profiles_by_key: dict[str, GuildProfile] = {"guest": guest_profile()}

    for profile in load_profiles_from_file(default_profiles_path()):
        profiles_by_key[profile.face_label or profile.username] = profile

    repair_local_profiles()
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
    profile = GuildProfile(
        username="baglare" if safe_name == BAGLARE_FACE_LABEL else display_username(username),
        rank="S-Seviye Büyücü" if safe_name == BAGLARE_FACE_LABEL else "C-Seviye Büyücü",
        unlocked_spells=BAGLARE_UNLOCKED_SPELLS.copy() if safe_name == BAGLARE_FACE_LABEL else ["Donma"],
        locked_spells=BAGLARE_LOCKED_SPELLS.copy() if safe_name == BAGLARE_FACE_LABEL else DEFAULT_LOCKED_SPELLS.copy(),
        guild_name=BAGLARE_GUILD_NAME if safe_name == BAGLARE_FACE_LABEL else DEFAULT_GUILD_NAME,
        guild_seal_code=guild_seal_code,
        face_label=safe_name,
    )
    return normalize_profile(profile)


def save_local_profile(profile: GuildProfile) -> None:
    """Yerel kullanıcı profilini local_profiles.json içine ekler veya günceller."""
    profile = normalize_profile(profile)
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

from datetime import datetime, timezone
from typing import Dict, List, Optional

__LOCK_TOKEN__ = "YANKKJ-REVIVEM-GON-LOCK-v1"

STATUS_MAP = {0: "Offline", 1: "Online", 2: "Jogando", 3: "Criando"}
STATUS_COLOR = {0: 0x6E6E6E, 1: 0x22C55E, 2: 0x8B5CF6, 3: 0x10B981}

class EmbedClient:
    def __init__(self, config: dict, http):
        self.c = config
        self.http = http

    def _footer(self) -> Dict:
        return {"text": f"Gon Roblox Viewer | GitHub: {self.c['owner']['github_url']} | Discord: {self.c['owner']['discord']}"}

    def _account_age(self, created_iso: str) -> str:
        try:
            dt = datetime.fromisoformat(created_iso.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            days = max(0, (now - dt).days)
            years, rem = divmod(days, 365)
            months, _ = divmod(rem, 30)
            parts = []
            if years: parts.append(f"{years} ano{'s' if years != 1 else ''}")
            if months: parts.append(f"{months} mes{'es' if months != 1 else ''}")
            if not parts: parts.append(f"{days} dia{'s' if days != 1 else ''}")
            return " • " + " e ".join(parts)
        except Exception:
            return ""

    def _presence_color(self, presence: Optional[Dict]) -> int:
        t = (presence or {}).get("userPresenceType", 0)
        return STATUS_COLOR.get(t, 0x00D9FF)

    def initial(self, user: Dict, avatar_url: str, friends: int, followers: int, followings: int,
                presence: Optional[Dict], groups_count: int, description: str,
                game_name: Optional[str] = None, game_link: Optional[str] = None) -> Dict:
        friends = int(friends or 0); followers = int(followers or 0); followings = int(followings or 0)
        created_raw = user.get("created") or "N/A"
        created_txt = created_raw[:10] if created_raw != "N/A" else "N/A"
        age_txt = self._account_age(created_raw) if created_raw != "N/A" else ""
        status_type = (presence or {}).get("userPresenceType", 0)
        status = STATUS_MAP.get(status_type, "Offline")
        bio_text = (description or "*Sem descrição*").strip()[:350] or "*Sem descrição*"
        profile_url = f"https://www.roblox.com/users/{user['id']}/profile"
        is_verified = bool(user.get("hasVerifiedBadge", False))
        is_banned = bool(user.get("isBanned", False))
        name_line = f"{user.get('displayName','')}"
        if is_verified: name_line += " ✔"
        if is_banned: name_line += " ⛔"
        color = self._presence_color(presence)

        stats_text = f"ID: {user['id']}\nCriado em: {created_txt}{age_txt}"
        conex_text = f"Amigos: {friends}\nSeguidores: {followers}\nSeguindo: {followings}\nGrupos: {groups_count}"
        quick_links = " • ".join([f"[Ver Perfil]({profile_url})", f"[Ver Grupos](https://www.roblox.com/users/{user['id']}/groups)"])
        status_lines = [status]
        if status_type == 2 and game_name and game_link: status_lines.append(f"Jogo: [{game_name}]({game_link})")

        fields = [
            {"name": "📝 BIO", "value": bio_text, "inline": False},
            {"name": "📊 ESTATÍSTICAS", "value": stats_text, "inline": True},
            {"name": "🔗 CONEXÕES", "value": conex_text, "inline": True},
            {"name": "⚡ LINKS", "value": quick_links, "inline": False},
            {"name": "🟢 STATUS", "value": "\n".join(status_lines), "inline": False},
        ]

        return {
            "color": color,
            "author": {"name": f"{name_line} (@{user.get('name','')})", "url": profile_url, "icon_url": avatar_url or "https://static.rbxcdn.com/images/avatars/default.png"},
            "title": "🔍 MONITORAMENTO INICIADO",
            "description": "",
            "thumbnail": {"url": avatar_url or "https://static.rbxcdn.com/images/avatars/default.png"},
            "fields": fields,
            "footer": self._footer(),
            "timestamp": datetime.utcnow().isoformat()
        }

    def single(self, user: Dict, avatar_url: str, title: str, color: int, details: Dict) -> Dict:
        profile_url = f"https://www.roblox.com/users/{user['id']}/profile"
        fields = []
        for k, v in details.items():
            if isinstance(v, str) and v.startswith("http"):
                fields.append({"name": k, "value": f"[Clique aqui]({v})", "inline": False})
            else:
                text = str(v)
                fields.append({"name": k, "value": (f"`{text}`" if len(text) < 120 else text[:1024]), "inline": len(text) < 60})
        return {
            "title": title,
            "description": f"[Perfil]({profile_url})",
            "color": color,
            "thumbnail": {"url": avatar_url or "https://static.rbxcdn.com/images/avatars/default.png"},
            "fields": fields,
            "footer": self._footer(),
            "timestamp": datetime.utcnow().isoformat()
        }

    def batch(self, user: Dict, avatar_url: str, change_type: str, lines: List[str], totals: Optional[str] = None) -> Dict:
        titles = {"friend_add": ("➕ NOVOS AMIGOS", 0x22C55E),"friend_remove": ("➖ AMIGOS REMOVIDOS", 0xEF4444),"follower_add": ("➕ NOVOS SEGUIDORES", 0x22C55E),"follower_remove": ("➖ SEGUIDORES PERDIDOS", 0xEF4444),"following_add": ("➕ AGORA SEGUINDO", 0x22C55E),"following_remove": ("➖ DEIXOU DE SEGUIR", 0xEF4444)}
        title, color = titles.get(change_type, ("ℹ️ MUDANÇAS", 0x60A5FA))
        profile_url = f"https://www.roblox.com/users/{user['id']}/profile"
        fields = []
        if totals: fields.append({"name": "Resumo", "value": f"`{totals}`", "inline": False})
        if lines: fields.append({"name": "Detalhes", "value": "\n".join(lines)[:1024], "inline": False})
        return {"title": title,"description": f"[Perfil]({profile_url})","color": color,"thumbnail": {"url": avatar_url or "https://static.rbxcdn.com/images/avatars/default.png"},"fields": fields,"footer": self._footer(),"timestamp": datetime.utcnow().isoformat()}

    async def send(self, embed: Dict) -> bool:
        if self.c.get("silent_mode") or self._quiet_hours(): return True
        payload = {"username": "Gon","avatar_url": "https://i.pinimg.com/736x/45/2e/d0/452ed012937de83cbbf2343ece863eb1.jpg","embeds": [embed]}
        res = await self.http.post_json(self.c["webhook_url"], payload)
        return res is not None

    async def send_many(self, embeds: List[Dict]) -> bool:
        if self.c.get("silent_mode") or self._quiet_hours() or not embeds: return True
        ok = True
        for i in range(0, len(embeds), 10):
            payload = {"username": "Gon","avatar_url": "https://i.pinimg.com/736x/45/2e/d0/452ed012937de83cbbf2343ece863eb1.jpg","embeds": embeds[i:i+10]}
            res = await self.http.post_json(self.c["webhook_url"], payload)
            ok = ok and (res is not None)
        return ok

    def _quiet_hours(self) -> bool:
        q = self.c.get("quiet_hours", {})
        if not q.get("enabled", False): return False
        from datetime import datetime as _dt
        now = _dt.now().time()
        s = _dt.strptime(q["start"], "%H:%M").time()
        e = _dt.strptime(q["end"], "%H:%M").time()
        return (s <= now <= e) if s < e else (now >= s or now <= e)

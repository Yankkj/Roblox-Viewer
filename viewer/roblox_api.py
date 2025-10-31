from typing import Dict, List, Optional, Set
import asyncio, json, hashlib, time
from viewer.state import SimpleCache
from viewer.http import HTTPClient

__LOCK_TOKEN__ = "YANKKJ-REVIVEM-GON-LOCK-v1"

class RobloxAPI:
    def __init__(self, config: dict, http: HTTPClient):
        self.c = config
        self.http = http
        self.cache = SimpleCache(ttl_seconds=300, max_size=1000)
        self.base = "https://users.roblox.com"
        self.friends = "https://friends.roblox.com"
        self.games = "https://games.roblox.com"
        self.groups = "https://groups.roblox.com"
        self.presence = "https://presence.roblox.com"
        self.thumbs = "https://thumbnails.roblox.com"
        self.badges = "https://badges.roblox.com"
        self.avatar = "https://avatar.roblox.com"

    async def get_user_info(self, user_id: int) -> Optional[Dict]:
        key = f"user_{user_id}"
        if self.c["cache"]["profiles"]:
            cached = self.cache.get(key)
            if cached: return cached
        data = await self.http.get_json(f"{self.base}/v1/users/{user_id}")
        if data and self.c["cache"]["profiles"]:
            self.cache.set(key, data)
        return data

    async def get_avatar_urls_fresh(self, user_id: int) -> Dict[str, str]:
        head = await self.http.get_json(f"{self.thumbs}/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=Png&isCircular=false")
        head_url = head["data"][0].get("imageUrl") if head and head.get("data") else ""
        full = await self.http.get_json(f"{self.thumbs}/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false")
        full_url = full["data"][0].get("imageUrl") if full and full.get("data") else ""
        now_ms = int(time.time() * 1000)
        salt = hashlib.md5(f"{user_id}-{now_ms}".encode()).hexdigest()[:8]
        if head_url:
            sep = "&" if "?" in head_url else "?"
            head_url = f"{head_url}{sep}cb={now_ms}-{salt}"
        if full_url:
            sep = "&" if "?" in full_url else "?"
            full_url = f"{full_url}{sep}cb={now_ms}-{salt}"
        return {"head": head_url, "full": full_url}

    async def get_avatar_url(self, user_id: int) -> str:
        fresh = await self.get_avatar_urls_fresh(user_id)
        return fresh.get("head", "")

    async def get_avatar_signature(self, user_id: int) -> str:
        d = await self.http.get_json(f"{self.avatar}/v1/users/{user_id}/avatar")
        if not d: return ""
        assets = sorted([a.get("id") for a in d.get("assets", []) if a.get("id")])
        sig_obj = {"assets": assets, "colors": d.get("bodyColors", {}), "scales": d.get("scales", {}), "type": d.get("playerAvatarType", ""), "emotes": d.get("emotes", [])}
        return hashlib.sha256(json.dumps(sig_obj, sort_keys=True, default=str).encode()).hexdigest()

    async def get_user_presence(self, user_id: int) -> Optional[Dict]:
        sess = await self.http.ensure()
        try:
            async with sess.post(f"{self.presence}/v1/presence/users", json={"userIds": [user_id]}, timeout=10) as r:
                if r.status == 200:
                    d = await r.json()
                    if d.get("userPresences"): return d["userPresences"][0]
        except Exception:
            return None
        return None

    async def get_user_groups(self, user_id: int) -> List[Dict]:
        d = await self.http.get_json(f"{self.groups}/v1/users/{user_id}/groups/roles")
        return d.get("data", []) if d else []

    async def get_game_info(self, place_id: int) -> Optional[Dict]:
        d = await self.http.get_json(f"{self.games}/v1/games/multiget-place-details?placeIds={place_id}")
        if d and isinstance(d, list) and d: return d[0]
        return None

    async def friends_count(self, uid: int) -> int:
        d = await self.http.get_json(f"{self.friends}/v1/users/{uid}/friends/count")
        return d.get("count", 0) if d else 0

    async def followers_count(self, uid: int) -> int:
        d = await self.http.get_json(f"{self.friends}/v1/users/{uid}/followers/count")
        return d.get("count", 0) if d else 0

    async def followings_count(self, uid: int) -> int:
        d = await self.http.get_json(f"{self.friends}/v1/users/{uid}/followings/count")
        return d.get("count", 0) if d else 0

    async def friends_list(self, uid: int) -> Set[int]:
        s: Set[int] = set(); cursor = ""
        while True:
            url = f"{self.friends}/v1/users/{uid}/friends"
            if cursor: url += f"?cursor={cursor}"
            d = await self.http.get_json(url)
            if not d: break
            s.update([i["id"] for i in d.get("data", [])])
            cursor = d.get("nextPageCursor")
            if not cursor: break
        return s

    async def _paged(self, base: str, limit: int, sort: str) -> Set[int]:
        s: Set[int] = set(); cursor = ""; got = 0
        while got < limit:
            url = f"{base}&limit=100&sortOrder={sort}"
            if cursor: url += f"&cursor={cursor}"
            d = await self.http.get_json(url)
            if not d: break
            data = d.get("data", [])
            if not data: break
            s.update([i["id"] for i in data]); got += len(data)
            cursor = d.get("nextPageCursor")
            if not cursor: break
        return s

    async def followers_list(self, uid: int, limit: int, sort: str) -> Set[int]:
        return await self._paged(f"{self.friends}/v1/users/{uid}/followers?excludeBannedUsers=false", limit, sort)

    async def followings_list(self, uid: int, limit: int, sort: str) -> Set[int]:
        return await self._paged(f"{self.friends}/v1/users/{uid}/followings?excludeBannedUsers=false", limit, sort)

    async def user_badges_map(self, uid: int, limit: int, sort: str) -> Dict[int, str]:
        out: Dict[int, str] = {}; cursor = ""; got = 0
        while got < limit:
            url = f"{self.badges}/v1/users/{uid}/badges?sortOrder={sort}&limit=100"
            if cursor: url += f"&cursor={cursor}"
            d = await self.http.get_json(url)
            if not d: break
            data = d.get("data", [])
            if not data: break
            for b in data: out[b["id"]] = b.get("name", f"Badge {b['id']}")
            got += len(data)
            cursor = d.get("nextPageCursor")
            if not cursor: break
        return out

    async def users_info_batch(self, ids: List[int]) -> Dict[int, Dict]:
        if not ids: return {}
        sess = await self.http.ensure()
        out: Dict[int, Dict] = {}; remaining = list(ids)
        while remaining:
            batch = remaining[:100]; remaining = remaining[100:]
            try:
                async with sess.post(f"{self.base}/v1/users", json={"userIds": batch, "excludeBannedUsers": False}, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        for u in data.get("data", []): out[u["id"]] = u
                    elif r.status == 429:
                        retry = int(r.headers.get("Retry-After", 3))
                        await asyncio.sleep(retry); remaining = batch + remaining
            except Exception:
                pass
        return out

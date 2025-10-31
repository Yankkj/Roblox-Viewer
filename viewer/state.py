import json, hashlib, time
from pathlib import Path
from typing import Dict, Tuple, List, Any

class SimpleCache:
    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000):
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
        self.order: List[str] = []

    def get(self, key: str):
        item = self.cache.get(key)
        if not item: return None
        value, ts = item
        if time.time() - ts >= self.ttl:
            self.cache.pop(key, None)
            if key in self.order: self.order.remove(key)
            return None
        if key in self.order: self.order.remove(key)
        self.order.append(key)
        return value

    def set(self, key: str, value: Any):
        if key not in self.cache and len(self.cache) >= self.max_size:
            lru = self.order.pop(0)
            self.cache.pop(lru, None)
        self.cache[key] = (value, time.time())
        if key not in self.order: self.order.append(key)

    def clear_expired(self):
        now = time.time()
        for k in list(self.cache.keys()):
            _, ts = self.cache[k]
            if now - ts >= self.ttl:
                self.cache.pop(k, None)
                if k in self.order: self.order.remove(k)

class StateStore:
    def __init__(self, config: dict):
        self.config = config
        self.previous_states: Dict[int, dict] = {}
        self.cache = SimpleCache(ttl_seconds=300, max_size=1000)
        self.is_first_check: Dict[int, bool] = {}
        self._load_backup()

    def _hash(self, data: dict) -> str:
        return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()

    def _load_backup(self):
        p = Path("backup_states.json")
        hp = Path("backup_states.hash")
        loaded = False
        if p.exists() and self.config.get("backup_enabled", True):
            try:
                raw = json.loads(p.read_text(encoding="utf-8"))
                ok = not hp.exists() or self._hash(raw) == hp.read_text().strip()
                if ok:
                    for uid, st in raw.items():
                        for key in ("friends_list","followers_list","followings_list"):
                            if isinstance(st.get(key), list): st[key] = set(st[key])
                        self.previous_states[int(uid)] = st
                    loaded = True
            except Exception:
                pass
        for uid in self.config["user_ids"]:
            self.is_first_check[uid] = not loaded

    def save_backup(self):
        if not self.config.get("backup_enabled", True): return
        data = {}
        for uid, st in self.previous_states.items():
            c = dict(st)
            for key in ("friends_list","followers_list","followings_list"):
                if isinstance(c.get(key), set): c[key] = list(c[key])
            data[str(uid)] = c
        Path("backup_states.json").write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
        Path("backup_states.hash").write_text(self._hash(data), encoding="utf-8")

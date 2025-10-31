import json
from pathlib import Path

DEFAULTS = {
    "webhook_url": "SEU_WEBHOOK_URL_AQUI",
    "user_ids": [123456789],
    "check_interval": 30,
    "discord_user": "revivem",
    "roblox_user": "crucifixei",
    "silent_mode": False,
    "backup_enabled": True,
    "notifications": {"friends": True,"followers": True,"followings": True,"groups": True,"presence": True,"badges": True},
    "quiet_hours": {"enabled": False, "start": "23:00", "end": "07:00", "tz": "America/Sao_Paulo"},
    "cache": {"profiles": True, "avatars": True, "lists": False},
    "lists": {"window_limit": 200, "rotate_sort": True},
    "strategy": {"count_first": True, "full_refresh_every": 10},
    "badges": {"poll_every": 5, "window_limit": 500, "sort_order": "Desc"},
    "webhook": {"batch": True, "batch_max_items": 15, "multi_embed_per_request": True, "dedupe_per_cycle": True},
    "concurrency": {"total": 10, "per_host": 5},
    "owner": {"github": "Yankkj", "github_url": "https://github.com/Yankkj", "discord": "revivem", "lock_enabled": True}
}

def _merge(dst: dict, src: dict) -> dict:
    out = dict(dst)
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out

def _validate(cfg: dict) -> dict:
    if not isinstance(cfg.get("user_ids"), list) or not cfg["user_ids"]:
        raise ValueError("user_ids inválido")
    if cfg["check_interval"] < 10:
        cfg["check_interval"] = 10
    wl = int(cfg["lists"]["window_limit"])
    if wl < 50:
        cfg["lists"]["window_limit"] = 50
    pe = int(cfg["badges"]["poll_every"])
    if not 1 <= pe <= 60:
        cfg["badges"]["poll_every"] = 5
    return cfg

def load_config(path: str) -> dict:
    cfg = DEFAULTS.copy()
    p = Path(path)
    if p.exists():
        user = json.loads(p.read_text(encoding="utf-8"))
        cfg = _merge(cfg, user)
    else:
        p.write_text(json.dumps(cfg, indent=4, ensure_ascii=False), encoding="utf-8")
    return _validate(cfg)

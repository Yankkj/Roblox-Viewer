import hashlib, sys
from pathlib import Path

LOCK_TOKEN = "YANKKJ-REVIVEM-GON-LOCK-v1"

class LicenseGuard:
    def __init__(self, cfg: dict):
        self.cfg = cfg

    def _assert_owner(self):
        o = self.cfg.get("owner", {})
        return o.get("github") == "Yankkj" and str(o.get("github_url","")).startswith("https://github.com/Yankkj") and o.get("discord") == "revivem" and bool(o.get("lock_enabled", True))

    def _assert_tokens(self):
        try:
            from viewer import embeds, monitor, roblox_api
            return getattr(embeds, "__LOCK_TOKEN__", "") == LOCK_TOKEN and getattr(monitor, "__LOCK_TOKEN__", "") == LOCK_TOKEN and getattr(roblox_api, "__LOCK_TOKEN__", "") == LOCK_TOKEN
        except Exception:
            return False

    def verify_or_exit(self):
        if not self._assert_owner():
            print("Bloqueado: owner inválido."); sys.exit(2)
        if not self._assert_tokens():
            print("Bloqueado: tokens ausentes/alterados."); sys.exit(3)

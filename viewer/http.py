import aiohttp, asyncio, random
from typing import Optional

class HTTPClient:
    def __init__(self, config: dict):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.connector: Optional[aiohttp.TCPConnector] = None
        self.lock = asyncio.Lock()
        self.metrics = {"req": 0, "2xx": 0, "4xx": 0, "5xx": 0}

    async def ensure(self) -> aiohttp.ClientSession:
        async with self.lock:
            if self.session is None or self.session.closed:
                if self.connector and not self.connector.closed:
                    await self.connector.close()
                self.connector = aiohttp.TCPConnector(
                    limit=int(self.config["concurrency"]["total"]),
                    limit_per_host=int(self.config["concurrency"]["per_host"]),
                    keepalive_timeout=30,
                    enable_cleanup_closed=True
                )
                timeout = aiohttp.ClientTimeout(total=30, connect=10)
                self.session = aiohttp.ClientSession(
                    connector=self.connector,
                    timeout=timeout,
                    headers={"User-Agent": "GonRobloxViewer/3 (+github.com/Yankkj)"},
                )
        return self.session

    async def close(self):
        async with self.lock:
            if self.session and not self.session.closed:
                await self.session.close()
            self.session = None
            if self.connector and not self.connector.closed:
                await self.connector.close()
            self.connector = None

    async def _sleep_jitter(self, base: float):
        await asyncio.sleep(base + random.uniform(0, base * 0.5))

    async def get_json(self, url: str, max_retries: int = 3):
        sess = await self.ensure()
        for attempt in range(max_retries):
            self.metrics["req"] += 1
            try:
                async with sess.get(url) as r:
                    if 200 <= r.status < 300:
                        self.metrics["2xx"] += 1
                        return await r.json()
                    if r.status == 429:
                        retry = float(r.headers.get("Retry-After", 2 ** attempt))
                        await self._sleep_jitter(retry); continue
                    if 400 <= r.status < 500: self.metrics["4xx"] += 1
                    elif r.status >= 500: self.metrics["5xx"] += 1
                    if attempt < max_retries - 1:
                        await self._sleep_jitter(2 ** attempt)
            except Exception:
                if attempt < max_retries - 1:
                    await self._sleep_jitter(2 ** attempt)
        return None

    async def post_json(self, url: str, payload: dict, max_retries: int = 3):
        sess = await self.ensure()
        for attempt in range(max_retries):
            self.metrics["req"] += 1
            try:
                async with sess.post(url, json=payload) as r:
                    if r.status == 429:
                        retry = float(r.headers.get("Retry-After", 2 ** attempt))
                        await self._sleep_jitter(retry); continue
                    if 200 <= r.status < 300:
                        self.metrics["2xx"] += 1
                        return await (r.json() if r.content_type == "application/json" else asyncio.sleep(0))
                    if 400 <= r.status < 500: self.metrics["4xx"] += 1
                    elif r.status >= 500: self.metrics["5xx"] += 1
                    if attempt < max_retries - 1:
                        await self._sleep_jitter(2 ** attempt)
            except Exception:
                if attempt < max_retries - 1:
                    await self._sleep_jitter(2 ** attempt)
        return None

import asyncio
from collections import defaultdict
from typing import Dict, List
from viewer.roblox_api import RobloxAPI
from viewer.embeds import EmbedClient, STATUS_MAP

__LOCK_TOKEN__ = "YANKKJ-REVIVEM-GON-LOCK-v1"

class Monitor:
    def __init__(self, config: dict, api: RobloxAPI, embeds: EmbedClient, state):
        self.c = config
        self.api = api
        self.embeds = embeds
        self.state = state
        self.cycle = defaultdict(int)
        self.running = True
        self.sent_cache = {}

    async def start(self):
        print("=" * 50)
        print(" GON ROBLOX VIEWER - MONITORAMENTO ATIVO")
        print("=" * 50)
        print(f"👤 Monitorando {len(self.c['user_ids'])} usuário(s)")
        print(f"⏰ Intervalo: {self.c['check_interval']}s")
        print("=" * 50, "\n")
        while self.running:
            try:
                for uid in self.c["user_ids"]:
                    await self._monitor_user(uid)
                    await asyncio.sleep(0.2)
                self.state.cache.clear_expired()
                await asyncio.sleep(self.c["check_interval"])
            except KeyboardInterrupt:
                self.running = False
                break

    def _dedupe_key(self, uid: int, typ: str, payload_digest: str) -> str:
        return f"{uid}:{self.cycle[uid]}:{typ}:{payload_digest}"

    async def _monitor_user(self, uid: int):
        self.cycle[uid] += 1
        cyc = self.cycle[uid]
        rotate = self.c["lists"]["rotate_sort"] and (cyc % 2 == 0)
        sort = "Asc" if rotate else "Desc"
        window = int(self.c["lists"]["window_limit"])
        count_first = self.c["strategy"]["count_first"]
        full_refresh = (cyc % int(self.c["strategy"]["full_refresh_every"]) == 0)
        is_first = self.state.is_first_check.get(uid, True)

        (user, avatar, presence, groups, friends_count, followers_count, followings_count, avatar_sig) = await asyncio.gather(
            self.api.get_user_info(uid),
            self.api.get_avatar_url(uid),
            self.api.get_user_presence(uid),
            self.api.get_user_groups(uid),
            self.api.friends_count(uid),
            self.api.followers_count(uid),
            self.api.followings_count(uid),
            self.api.get_avatar_signature(uid),
        )
        if not user: return

        game_name, game_link = None, None
        if presence and presence.get("userPresenceType") == 2 and presence.get("placeId"):
            gi = await self.api.get_game_info(presence["placeId"])
            if gi: game_name = gi.get("name")
            game_link = f"https://www.roblox.com/games/{presence['placeId']}"

        prev = self.state.previous_states.get(uid, {})
        need_friends = is_first or not count_first or (friends_count != prev.get("friends_count")) or full_refresh
        need_followers = is_first or not count_first or (followers_count != prev.get("followers_count")) or full_refresh
        need_followings = is_first or not count_first or (followings_count != prev.get("followings_count")) or full_refresh

        tasks = []
        tasks.append(self.api.friends_list(uid) if need_friends else asyncio.sleep(0, result=prev.get("friends_list", set())))
        tasks.append(self.api.followers_list(uid, window, sort) if need_followers else asyncio.sleep(0, result=prev.get("followers_list", set())))
        tasks.append(self.api.followings_list(uid, window, sort) if need_followings else asyncio.sleep(0, result=prev.get("followings_list", set())))
        friends_set, followers_set, followings_set = await asyncio.gather(*tasks)

        badges_map = prev.get("badges", {})
        if self.c["notifications"].get("badges", True) and (is_first or cyc % int(self.c["badges"]["poll_every"]) == 0):
            badges_map = await self.api.user_badges_map(uid, int(self.c["badges"]["window_limit"]), self.c["badges"]["sort_order"])

        cur = {
            "friends_list": set(friends_set),
            "followers_list": set(followers_set),
            "followings_list": set(followings_set),
            "friends_count": friends_count if count_first else len(friends_set),
            "followers_count": followers_count if count_first else len(followers_set),
            "followings_count": followings_count if count_first else len(followings_set),
            "presence": presence or {},
            "groups": {g["group"]["id"]: {"name": g["group"]["name"], "role": g["role"]["name"], "rank": g["role"]["rank"]} for g in groups or []},
            "badges": badges_map,
            "display_name": user.get("displayName"),
            "username": user.get("name"),
            "description": user.get("description", ""),
            "avatar_url": avatar,
            "avatar_signature": avatar_sig,
            "is_banned": user.get("isBanned", False),
            "has_verified_badge": user.get("hasVerifiedBadge", False),
        }

        if is_first:
            emb = self.embeds.initial(user, avatar, cur["friends_count"], cur["followers_count"], cur["followings_count"], presence, len(groups or []), user.get("description", ""), game_name=game_name, game_link=game_link)
            await self.embeds.send(emb)
            self.state.previous_states[uid] = cur
            self.state.is_first_check[uid] = False
            self.state.save_backup()
            return

        embeds: List[dict] = []
        batches: Dict[str, List[int]] = {"friend_add": [], "friend_remove": [], "follower_add": [], "follower_remove": [], "following_add": [], "following_remove": []}

        if self.c["notifications"].get("friends", True):
            nf = cur["friends_list"] - prev.get("friends_list", set())
            rf = prev.get("friends_list", set()) - cur["friends_list"]
            if nf: batches["friend_add"] += list(nf)
            if rf: batches["friend_remove"] += list(rf)

        if self.c["notifications"].get("followers", True):
            na = cur["followers_list"] - prev.get("followers_list", set())
            ra = prev.get("followers_list", set()) - cur["followers_list"]
            if na: batches["follower_add"] += list(na)
            if ra: batches["follower_remove"] += list(ra)

        if self.c["notifications"].get("followings", True):
            ns = cur["followings_list"] - prev.get("followings_list", set())
            rs = prev.get("followings_list", set()) - cur["followings_list"]
            if ns: batches["following_add"] += list(ns)
            if rs: batches["following_remove"] += list(rs)

        if self.c["notifications"].get("groups", True):
            pg, cg = prev.get("groups", {}), cur["groups"]
            pset, cset = set(pg.keys()), set(cg.keys())
            for gid in cset - pset:
                g = cg[gid]
                embeds.append(self.embeds.single(user, avatar, "🟢 ENTROU EM GRUPO", 0x0099FF, {"Grupo": g["name"], "Cargo": g["role"], "Link": f"https://www.roblox.com/groups/{gid}"}))
            for gid in pset - cset:
                g = pg[gid]
                embeds.append(self.embeds.single(user, avatar, "🔴 SAIU DO GRUPO", 0xFF0000, {"Grupo": g["name"], "Cargo Anterior": g["role"]}))
            for gid in pset & cset:
                if pg[gid]["role"] != cg[gid]["role"]:
                    g = cg[gid]
                    embeds.append(self.embeds.single(user, avatar, "⚡ CARGO ALTERADO", 0xFFAA00, {"Grupo": g["name"], "Cargo Anterior": pg[gid]["role"], "Novo Cargo": g["role"], "Link": f"https://www.roblox.com/groups/{gid}"}))

        if self.c["notifications"].get("badges", True) and (is_first or cyc % int(self.c["badges"]["poll_every"]) == 0):
            nb = set(cur["badges"].keys()) - set(prev.get("badges", {}).keys())
            for bid in nb:
                embeds.append(self.embeds.single(user, avatar, "⭐ NOVO BADGE", 0xFFD700, {"Badge": cur["badges"][bid], "Badge ID": str(bid)}))

        if prev.get("avatar_signature") != cur.get("avatar_signature"):
            urls = await self.api.get_avatar_urls_fresh(uid)
            new_head = urls.get("head") or avatar
            new_full = urls.get("full") or new_head
            emb = self.embeds.single(user, new_head, "🖼️ FOTO ALTERADA", 0x9C27B0, {"Detalhes": "A skin foi alterada"})
            emb["image"] = {"url": new_full}
            embeds.append(emb)

        if self.c["notifications"].get("presence", True):
            pp, cp = prev.get("presence", {}), cur.get("presence", {})
            if cp.get("userPresenceType") != pp.get("userPresenceType"):
                embeds.append(self.embeds.single(user, avatar, "🔄 STATUS ALTERADO", 0xFFFF00, {"Status Anterior": STATUS_MAP.get(pp.get("userPresenceType", 0), "Desconhecido"), "Novo Status": STATUS_MAP.get(cp.get("userPresenceType", 0), "Desconhecido")}))
            prev_place = pp.get("placeId"); cur_place = cp.get("placeId")
            if cur_place and not prev_place:
                gi = await self.api.get_game_info(cur_place)
                embeds.append(self.embeds.single(user, avatar, "🎮 INGRESSOU EM JOGO", 0x9900FF, {"Jogo": (gi["name"] if gi else "Jogo Desconhecido"), "Place ID": str(cur_place), "Link do Jogo": f"https://www.roblox.com/games/{cur_place}"}))
            elif prev_place and not cur_place:
                embeds.append(self.embeds.single(user, avatar, "🏃 SAIU DO JOGO", 0x666666, {"Place ID Anterior": str(prev_place)}))
            elif prev_place and cur_place and prev_place != cur_place:
                gi = await self.api.get_game_info(cur_place)
                embeds.append(self.embeds.single(user, avatar, "🎮 INGRESSOU EM JOGO", 0x9900FF, {"Novo Jogo": (gi["name"] if gi else "Jogo Desconhecido"), "Place ID": str(cur_place), "Link do Jogo": f"https://www.roblox.com/games/{cur_place}"}))

        if self.c["webhook"]["batch"]:
            all_ids = set(); [all_ids.update(v) for v in batches.values()]
            users_map = await self.api.users_info_batch(list(all_ids))
            max_items = int(self.c["webhook"]["batch_max_items"])

            def make_lines(ids: List[int]) -> List[str]:
                lines = []
                for i in ids[:max_items]:
                    u = users_map.get(i, {"id": i, "name": "unknown", "displayName": "Desconhecido"})
                    lines.append(f"• **[{u['displayName']}](https://www.roblox.com/users/{u['id']}/profile)** (@{u['name']})")
                if len(ids) > max_items: lines.append(f"• e mais {len(ids) - max_items}…")
                return lines

            for typ in ("friend_add","friend_remove","follower_add","follower_remove","following_add","following_remove"):
                if batches[typ]:
                    lines = make_lines(batches[typ]); key = self._dedupe_key(uid, typ, str(lines))
                    if not self.sent_cache.get(key):
                        base_map = {"friend":"friends_count","follower":"followers_count","following":"followings_count"}
                        base = typ.split("_")[0]
                        prev_total = self.state.previous_states.get(uid, {}).get(base_map[base], 0)
                        now_total = cur[base_map[base]]
                        embeds.append(self.embeds.batch(user, avatar, typ, lines, f"{prev_total} → {now_total}"))
                        self.sent_cache[key] = True

        if embeds:
            if self.c["webhook"]["multi_embed_per_request"]:
                await self.embeds.send_many(embeds)
            else:
                for e in embeds: await self.embeds.send(e)

        self.state.previous_states[uid] = cur
        self.state.save_backup()

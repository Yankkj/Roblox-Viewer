import asyncio
from viewer.config import load_config
from viewer.http import HTTPClient
from viewer.state import StateStore
from viewer.roblox_api import RobloxAPI
from viewer.embeds import EmbedClient
from viewer.monitor import Monitor
from viewer.guard import LicenseGuard

logo = """
░██████╗░░█████╗░███╗░░██╗
██╔════╝░██╔══██╗████╗░██║
██║░░██╗░██║░░██║██╔██╗██║
██║░░╚██╗██║░░██║██║╚████║
╚██████╔╝╚█████╔╝██║░╚███║
░╚═════╝░░╚════╝░╚═╝░░╚══╝
    >> [Roblox Viewer developed by @revivem]
"""

async def main():
    print(logo)
    cfg = load_config("config.json")
    LicenseGuard(cfg).verify_or_exit()
    if cfg["webhook_url"] == "SEU_WEBHOOK_URL_AQUI":
        print("Configure webhook_url no config.json")
        input("Enter para sair...")
        return
    http = HTTPClient(cfg)
    state = StateStore(cfg)
    api = RobloxAPI(cfg, http)
    embeds = EmbedClient(cfg, http)
    monitor = Monitor(cfg, api, embeds, state)
    try:
        await monitor.start()
    except KeyboardInterrupt:
        print("\nEncerrado.")
    finally:
        await http.close()
        state.save_backup()

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from fastmcp import Client

URL = "https://mcp-server-earthquake.onrender.com/mcp"

async def main():
    async with Client(URL) as client:
        # 1) Tenta pingar
        try:
            await client.ping()
            print("[OK] Ping sucesso")
        except Exception as e:
            print("[ERRO] Ping falhou:", e)
            return

        # 2) Lista as tools disponíveis
        try:
            tools = await client.list_tools()
            print("\nTools disponíveis nesse servidor:")
            for t in tools:
                print(f"- {t.name}: {t.description}")
        except Exception as e:
            print("[ERRO] list_tools falhou:", e)

asyncio.run(main())

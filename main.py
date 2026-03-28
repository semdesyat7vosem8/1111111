import asyncio
import bot
from uvicorn import Config, Server

async def main():
    bot_task = asyncio.create_task(bot.run_bot())
    config = Config("server:app", host="0.0.0.0", port=3000, log_level="info")
    server = Server(config)
    server_task = asyncio.create_task(server.serve())
    await asyncio.gather(bot_task, server_task)

if __name__ == "__main__":
    asyncio.run(main())

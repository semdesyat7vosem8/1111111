import asyncio
import bot
import uvicorn

async def main():
    bot_task = asyncio.create_task(bot.run_bot())
    server_task = asyncio.create_task(
        uvicorn.run("server:app", host="0.0.0.0", port=3000, log_level="info")
    )
    await asyncio.gather(bot_task, server_task)

if __name__ == "__main__":
    asyncio.run(main())
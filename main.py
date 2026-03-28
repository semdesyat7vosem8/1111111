import asyncio
import bot
import uvicorn
from uvicorn import Config, Server

async def main():
    # Запускаем бота как отдельную задачу
    bot_task = asyncio.create_task(bot.run_bot())

    # Настраиваем Uvicorn сервер
    config = Config("server:app", host="0.0.0.0", port=3000, log_level="info")
    server = Server(config)

    # Запускаем сервер как асинхронную задачу
    server_task = asyncio.create_task(server.serve())

    # Ждём завершения обеих задач (бот и сервер)
    await asyncio.gather(bot_task, server_task)

if __name__ == "__main__":
    asyncio.run(main())

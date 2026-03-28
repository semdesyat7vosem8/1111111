import os
import discord
from discord.ext import commands
import aiohttp
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL_ID = 1433031537783341097
ADMIN_ROLE_ID = 1432275054149894227
SERVER_URL = "https://bot-1774698189-7271-neokokosik78.bothost.tech"

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# =================== ЛОГИ ===================
async def send_log(action_type, username, user_id, admin_id, reason="No reason set"):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    title = action_type.upper() + " LOG"
    avatar_url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png"

    description = (
        f"**Player:** {username} ({user_id})\n"
        f"🔗 **https://www.roblox.com/users/{user_id}/profile\n**"
        f"📄 **Administrator:** <@{admin_id}>\n"
        f"**Reason:** {reason}"
    )

    embed = discord.Embed(title=title, description=description, color=0xFF5555)
    embed.set_thumbnail(url=avatar_url)

    await channel.send(embed=embed)

# =================== Проверка ролей ===================
def has_admin_role(interaction):
    return any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles)

# =================== Roblox API ===================
async def get_roblox_user(username):
    url = "https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": False}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as res:
                data = await res.json()
                if data.get("data"):
                    return data["data"][0]
                return {"id": "Unknown", "name": username}
        except:
            return {"id": "Unknown", "name": username}

# =================== Отправка команды на сервер ===================
async def send_command(cmd_type, username, reason, days, admin_id):
    async with aiohttp.ClientSession() as session:
        await session.post(f"{SERVER_URL}/command", json={
            "type": cmd_type,
            "username": username,
            "reason": reason,
            "days": days,
            "adminId": admin_id
        })

# =================== Событие бота ===================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(e)

# =================== КОМАНДЫ ===================
@bot.tree.command(name="kick", description="Kick a player")
async def kick(interaction: discord.Interaction, username: str, reason: str = "No reason set"):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)
    await interaction.response.send_message("⏳ Processing...")
    user = await get_roblox_user(username)
    await send_command("kick", user["name"], reason, 0, interaction.user.id)
    await send_log("kick", user["name"], user["id"], interaction.user.id, reason)
    await interaction.edit_original_response(content=f"✅ Successfully Kicked {user['name']}")

@bot.tree.command(name="ban", description="Ban a player for X days")
async def ban(interaction: discord.Interaction, username: str, days: int, reason: str = "No reason set"):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)
    await interaction.response.send_message("⏳ Processing...")
    user = await get_roblox_user(username)
    await send_command("ban", user["name"], reason, days, interaction.user.id)
    await send_log("ban", user["name"], user["id"], interaction.user.id, reason)
    await interaction.edit_original_response(content=f"✅ Successfully Banned {user['name']}")

@bot.tree.command(name="permaban", description="Permanently ban a player")
async def permaban(interaction: discord.Interaction, username: str, reason: str = "No reason set"):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)
    await interaction.response.send_message("⏳ Processing...")
    user = await get_roblox_user(username)
    await send_command("permaban", user["name"], reason, 0, interaction.user.id)
    await send_log("permaban", user["name"], user["id"], interaction.user.id, reason)
    await interaction.edit_original_response(content=f"✅ Successfully Perma-banned {user['name']}")

@bot.tree.command(name="unban", description="Unban a player")
async def unban(interaction: discord.Interaction, username: str, reason: str = "No reason set"):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)
    await interaction.response.send_message("⏳ Processing...")
    user = await get_roblox_user(username)
    await send_command("unban", user["name"], "", 0, interaction.user.id)
    await send_log("unban", user["name"], user["id"], interaction.user.id, "Unbanned")
    await interaction.edit_original_response(content=f"✅ Successfully Unbanned {user['name']}")

# =================== BANLIST ===================
@bot.tree.command(name="banlist", description="Show list of banned players")
async def banlist(interaction: discord.Interaction):
    await interaction.response.send_message("⏳ Processing...")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SERVER_URL}/banlist") as res:
            data = await res.json()
    if not data:
        return await interaction.edit_original_response(content="No bans.")
    text = "\n".join(f"{b['username']} ({b['username']}) — {b['daysLeft']} day(s)" for b in data)
    await interaction.edit_original_response(content=f"```{text}```")

# =================== Запуск бота ===================
async def run_bot():
    await bot.start(BOT_TOKEN)

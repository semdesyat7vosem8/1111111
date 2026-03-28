import os
import discord
from discord.ext import commands
import aiohttp
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
SERVER_URL = "https://bot-1774698189-7271-neokokosik78.bothost.tech"
LOG_CHANNEL_ID = 1433031537783341097
ADMIN_ROLE_ID = 1432275054149894227

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Глобальная aiohttp сессия ---
session = None
async def get_session():
    global session
    if session is None or session.closed:
        session = aiohttp.ClientSession()
    return session

async def run_bot():
    await bot.start(BOT_TOKEN)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(e)

# --- Отправка команды на сервер ---
async def send_command(cmd_type, username, reason="", days=0, admin_id=0):
    s = await get_session()
    await s.post(f"{SERVER_URL}/command", json={
        "type": cmd_type,
        "username": username,
        "reason": reason,
        "days": days,
        "adminId": admin_id
    })

# --- Логирование в Discord ---
async def send_log(title, username, user_id, description):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel: return
    embed = discord.Embed(title=title, description=description, color=0xFFC0CB, timestamp=datetime.utcnow())
    await channel.send(content=f"{username} | {user_id}", embed=embed)

# --- Проверка роли администратора ---
def has_admin_role(interaction):
    return any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles)

# --- Slash-команды ---
@bot.tree.command(name="kick", description="Kick a player")
async def kick(interaction: discord.Interaction, username: str, reason: str = "No reason set"):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)
    await interaction.response.send_message("⏳ Processing...")
    await send_command("kick", username, reason, 0, interaction.user.id)
    await send_log("KICK LOG", username, "Unknown", f"Admin: <@{interaction.user.id}>\nReason: {reason}")
    await interaction.edit_original_response(content=f"✅ Successfully Kicked {username}.")

@bot.tree.command(name="ban", description="Ban a player for X days")
async def ban(interaction: discord.Interaction, username: str, days: int, reason: str = "No reason set"):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)
    await interaction.response.send_message("⏳ Processing...")
    await send_command("ban", username, reason, days, interaction.user.id)
    await send_log("BAN LOG", username, "Unknown", f"Admin: <@{interaction.user.id}>\nReason: {reason}\nDuration: {days} day(s)")
    await interaction.edit_original_response(content=f"✅ Successfully Banned {username}.")

@bot.tree.command(name="permaban", description="Permanently ban a player")
async def permaban(interaction: discord.Interaction, username: str, reason: str = "No reason set"):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)
    await interaction.response.send_message("⏳ Processing...")
    await send_command("permaban", username, reason, 0, interaction.user.id)
    await send_log("PERMABAN LOG", username, "Unknown", f"Admin: <@{interaction.user.id}>\nReason: {reason}")
    await interaction.edit_original_response(content=f"✅ Successfully Perma-banned {username}.")

@bot.tree.command(name="unban", description="Unban a player")
async def unban(interaction: discord.Interaction, username: str):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)
    await interaction.response.send_message("⏳ Processing...")
    await send_command("unban", username, "", 0, interaction.user.id)
    await send_log("UNBAN LOG", username, "Unknown", f"Admin: <@{interaction.user.id}>")
    await interaction.edit_original_response(content=f"✅ Successfully Unbanned {username}.")

@bot.tree.command(name="banlist", description="Show list of banned players")
async def banlist(interaction: discord.Interaction):
    await interaction.response.send_message("⏳ Processing...")
    s = await get_session()
    async with s.get(f"{SERVER_URL}/banlist") as res:
        data = await res.json()
    if not data:
        return await interaction.edit_original_response(content="No bans.")
    text = "\n".join(f"{b['username']} — {b['daysLeft']} day(s)" for b in data)
    await interaction.edit_original_response(content=f"```{text}```")

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
async def send_log(title, username, user_id, description, avatar):
    """Отправка логов в канал с эмбедами и портретом"""
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return
    embed = discord.Embed(title=title, description=description, color=0xFFC0CB)
    if avatar:
        embed.set_thumbnail(url=avatar)
    await channel.send(embed=embed)

# ===== Slash Commands =====

def profile(user_id):
    return f"https://www.roblox.com/users/{user_id}"

def has_admin_role(interaction):
    return any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles)

# --------------------- KICK ---------------------
@bot.tree.command(name="kick", description="Kick a player")
async def kick(interaction: discord.Interaction, username: str, reason: str = "No reason set"):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)
    await interaction.response.send_message("⏳ Processing...")

    user = await get_roblox_user(username)
    user_id = user["id"] if user else "Unknown"
    display_name = user["name"] if user else username
    avatar = await get_avatar(user_id) if user else None

    base = (
        f"**Player:** {display_name} ({user_id})\n"
        f"🔗 {profile(user_id)}\n\n"
        f"📄 **Administrator:** <@{interaction.user.id}>\n"
    )

    await send_command("kick", username, reason, 0, interaction.user.id)
    await send_log("KICK LOG", display_name, user_id, f"{base}\n**Reason:** {reason}", avatar)
    await interaction.edit_original_response(content=f"✅ Successfully Kicked {display_name}.")

# --------------------- BAN ---------------------
@bot.tree.command(name="ban", description="Ban a player for X days")
async def ban(interaction: discord.Interaction, username: str, days: int, reason: str = "No reason set"):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)
    await interaction.response.send_message("⏳ Processing...")

    user = await get_roblox_user(username)
    user_id = user["id"] if user else "Unknown"
    display_name = user["name"] if user else username
    avatar = await get_avatar(user_id) if user else None

    base = (
        f"**Player:** {display_name} ({user_id})\n\n"
        f"🔗 {profile(user_id)}\n\n"
        f"📄 **Administrator:** <@{interaction.user.id}>\n"
    )

    await send_command("ban", username, reason, days, interaction.user.id)
    await send_log(
        "BAN LOG",
        display_name,
        user_id,
        f"{base}\n**Duration:** {days} day(s)\n**Reason:** {reason}",
        avatar
    )
    await interaction.edit_original_response(content=f"✅ Successfully Banned {display_name}.")

# --------------------- PERMABAN ---------------------
@bot.tree.command(name="permaban", description="Permanently ban a player")
async def permaban(interaction: discord.Interaction, username: str, reason: str = "No reason set"):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)
    await interaction.response.send_message("⏳ Processing...")

    user = await get_roblox_user(username)
    user_id = user["id"] if user else "Unknown"
    display_name = user["name"] if user else username
    avatar = await get_avatar(user_id) if user else None

    base = (
        f"**Player:** {display_name} ({user_id})\n\n"
        f"🔗 {profile(user_id)}\n\n"
        f"📄 **Administrator:** <@{interaction.user.id}>\n"
    )

    await send_command("permaban", username, reason, 0, interaction.user.id)
    await send_log("PERMABAN LOG", display_name, user_id, f"{base}\n**Reason:** {reason}", avatar)
    await interaction.edit_original_response(content=f"✅ Successfully Perma-banned {display_name}.")

# --------------------- UNBAN ---------------------
@bot.tree.command(name="unban", description="Unban a player")
async def unban(interaction: discord.Interaction, username: str):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)
    await interaction.response.send_message("⏳ Processing...")

    user = await get_roblox_user(username)
    user_id = user["id"] if user else "Unknown"
    display_name = user["name"] if user else username
    avatar = await get_avatar(user_id) if user else None

    base = (
        f"**Player:** {display_name} ({user_id})\n\n"
        f"🔗 {profile(user_id)}\n\n"
        f"📄 **Administrator:** <@{interaction.user.id}>\n"
    )

    await send_command("unban", username, "", 0, interaction.user.id)
    await send_log("UNBAN LOG", display_name, user_id, f"{base}", avatar)
    await interaction.edit_original_response(content=f"✅ Successfully Unbanned {display_name}.")

# =================== BANLIST ===================
@bot.tree.command(name="banlist", description="Show list of banned players")
async def banlist(interaction: discord.Interaction):
    await interaction.response.send_message("⏳ Processing...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{SERVER_URL}/banlist", timeout=5) as res:
                if res.status != 200:
                    return await interaction.edit_original_response(content=f"Error: {res.status}")
                data = await res.json()
        except Exception as e:
            return await interaction.edit_original_response(content=f"Failed to fetch banlist: {e}")

    if not data:
        return await interaction.edit_original_response(content="No bans.")

    text_lines = []
    for b in data:
        user_id = b.get("userId", "Unknown")  # если сервер хранит UserId
        username = b["username"]
        days = b["daysLeft"]
        text_lines.append(f"{username} ({user_id}) — {days}")

    await interaction.edit_original_response(content="```" + "\n".join(text_lines) + "```")
# =================== Запуск бота ===================
async def run_bot():
    await bot.start(BOT_TOKEN)

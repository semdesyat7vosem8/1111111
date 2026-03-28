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

async def run_bot():
    await bot.start(BOT_TOKEN)

# ===== Roblox API =====
async def get_roblox_user(username):
    url = "https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": False}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as res:
                data = await res.json()
                return data["data"][0] if data.get("data") else None
    except:
        return None

async def get_avatar(user_id):
    url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                data = await res.json()
                return data["data"][0].get("imageUrl")
    except:
        return None

# ===== Send commands & logs =====
async def send_command(cmd_type, username, reason, days, admin_id):
    async with aiohttp.ClientSession() as session:
        await session.post(f"{SERVER_URL}/command", json={
            "type": cmd_type,
            "username": username,
            "reason": reason,
            "days": days,
            "adminId": admin_id
        })

async def send_log(title, username, user_id, description, avatar=None):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return
    embed = discord.Embed(title=title, description=description, color=0xFFC0CB)
    if avatar:
        embed.set_thumbnail(url=avatar)
    await channel.send(content=f"{username} | {user_id}", embed=embed)

def profile(user_id):
    return f"https://www.roblox.com/users/{user_id}"

def has_admin_role(interaction):
    return any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()

# ===== Universal player processing =====
async def process_player(interaction, cmd_type, username, reason="", days=0):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)

    await interaction.response.send_message("⏳ Processing...")
    user = await get_roblox_user(username)
    user_id = user["id"] if user else "Unknown"
    display_name = user["name"] if user else username
    avatar = await get_avatar(user_id) if user else None

    duration_text = f"{days} day(s)" if cmd_type == "ban" else ""
    base_text = f"**Player:** {display_name} ({user_id})\n🔗 {profile(user_id)}\n📄 Administrator: <@{interaction.user.id}>"
    if duration_text:
        base_text += f"\n⏱ Duration: {duration_text}"

    await send_command(cmd_type, username, reason, days, interaction.user.id)
    await send_log(f"{cmd_type.upper()} LOG", display_name, user_id, f"{base_text}\n\n**Reason:** {reason}", avatar)
    await interaction.edit_original_response(content=f"✅ Successfully {cmd_type}ed {display_name}.")

# ===== Commands =====
@bot.tree.command(name="kick", description="Kick a player")
async def kick(interaction, username: str, reason: str = "No reason set"):
    await process_player(interaction, "kick", username, reason)

@bot.tree.command(name="ban", description="Ban a player for X days")
async def ban(interaction, username: str, days: int, reason: str = "No reason set"):
    await process_player(interaction, "ban", username, reason, days)

@bot.tree.command(name="permaban", description="Permanently ban a player")
async def permaban(interaction, username: str, reason: str = "No reason set"):
    await process_player(interaction, "permaban", username, reason)

@bot.tree.command(name="unban", description="Unban a player")
async def unban(interaction, username: str):
    await process_player(interaction, "unban", username)

@bot.tree.command(name="banlist", description="Show list of banned players")
async def banlist(interaction):
    await interaction.response.send_message("⏳ Processing...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SERVER_URL}/banlist") as res:
                data = await res.json()
    except:
        return await interaction.edit_original_response(content="Error fetching banlist.")

    if not data:
        return await interaction.edit_original_response(content="No bans.")

    text = ""
    for b in data:
        days_text = b["daysLeft"] if b["daysLeft"] == "PERMA-BANNED" else f"{b['daysLeft']} day(s)"
        text += f"{b['username']} ({b['username']}) — {days_text}\n\n"
    await interaction.edit_original_response(content=f"```{text}```")

@bot.tree.command(name="unbanwave", description="Unban all temporary banned players")
async def unbanwave(interaction, reason: str = "Unban Wave"):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)

    await interaction.response.send_message("⏳ Processing unban wave...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SERVER_URL}/banlist") as res:
                bans_data = await res.json()
    except:
        return await interaction.edit_original_response(content="Error fetching banlist.")

    count = 0
    for b in bans_data:
        if b["daysLeft"] != "PERMA-BANNED":
            async with aiohttp.ClientSession() as session:
                await session.post(f"{SERVER_URL}/command", json={
                    "type": "unban",
                    "username": b["username"],
                    "reason": reason,
                    "days": 0,
                    "adminId": interaction.user.id
                })
            count += 1

    log_text = f"📄 Administrator: <@{interaction.user.id}>\n**Reason:** {reason}"
    await send_log("UNBANWAVE LOG", "ALL TEMPORARY BANS", "—", log_text)
    await interaction.edit_original_response(content=f"✅ Unban wave completed. {count} temporary bans removed.")

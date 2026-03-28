import os
import discord
from discord.ext import commands
import aiohttp
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
SERVER_URL = "bot-1774698189-7271-neokokosik78.bothost.tech"  # <--- вставь сюда свою ссылку
LOG_CHANNEL_ID = 1433031537783341097
ADMIN_ROLE_ID = 1432275054149894227

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

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

async def get_roblox_user(username):
    url = "https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": False}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as res:
                data = await res.json()
                return data["data"][0] if data.get("data") else None
        except:
            return None

async def get_avatar(user_id):
    url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as res:
                data = await res.json()
                return data["data"][0].get("imageUrl")
        except:
            return None

async def send_command(cmd_type, username, reason, days, admin_id):
    async with aiohttp.ClientSession() as session:
        await session.post(f"{SERVER_URL}/command", json={"type": cmd_type,"username": username,"reason": reason,"days": days,"adminId": admin_id})

async def send_log(title, username, user_id, description, avatar):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel: return
    embed = discord.Embed(title=title, description=description, color=0xFFC0CB, timestamp=datetime.utcnow())
    if avatar:
        embed.set_thumbnail(url=avatar)
    await channel.send(content=f"{username} | {user_id}", embed=embed)

def profile(user_id):
    return f"https://www.roblox.com/users/{user_id}/profile"

def has_admin_role(interaction):
    return any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles)

# ===== Slash Commands =====

@bot.tree.command(name="kick", description="Kick a player")
async def kick(interaction: discord.Interaction, username: str, reason: str = "No reason set"):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)
    await interaction.response.send_message("⏳ Processing...")
    user = await get_roblox_user(username)
    user_id = user["id"] if user else "Unknown"
    display_name = user["name"] if user else username
    avatar = await get_avatar(user_id) if user else None
    base = f"**Player:** {display_name} ({user_id})\n🔗 {profile(user_id) if user_id != 'Unknown' else 'Not found'}\n📄 **Administrator:** <@{interaction.user.id}>"
    await send_command("kick", username, reason, 0, interaction.user.id)
    await send_log("KICK LOG", display_name, user_id, f"{base}\n\n**Reason:** {reason}", avatar)
    await interaction.edit_original_response(content=f"✅ Successfully Kicked {display_name}.")

# 🔨 BAN
@bot.tree.command(name="ban", description="Ban a player for X days")
async def ban(interaction: discord.Interaction, username: str, days: int, reason: str = "No reason set"):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)
    await interaction.response.send_message("⏳ Processing...")
    user = await get_roblox_user(username)
    user_id = user["id"] if user else "Unknown"
    display_name = user["name"] if user else username
    avatar = await get_avatar(user_id) if user else None
    base = f"**Player:** {display_name} ({user_id})\n🔗 {profile(user_id) if user_id != 'Unknown' else 'Not found'}\n📄 **Administrator:** <@{interaction.user.id}>"
    await send_command("ban", username, reason, days, interaction.user.id)
    await send_log("BAN LOG", display_name, user_id, f"{base}\n\n**Duration:** {days} day(s)\n**Reason:** {reason}", avatar)
    await interaction.edit_original_response(content=f"✅ Successfully Banned {display_name}.")

# ☠️ PERMABAN
@bot.tree.command(name="permaban", description="Permanently ban a player")
async def permaban(interaction: discord.Interaction, username: str, reason: str = "No reason set"):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)
    await interaction.response.send_message("⏳ Processing...")
    user = await get_roblox_user(username)
    user_id = user["id"] if user else "Unknown"
    display_name = user["name"] if user else username
    avatar = await get_avatar(user_id) if user else None
    base = f"**Player:** {display_name} ({user_id})\n🔗 {profile(user_id) if user_id != 'Unknown' else 'Not found'}\n📄 **Administrator:** <@{interaction.user.id}>"
    await send_command("permaban", username, reason, 0, interaction.user.id)
    await send_log("PERMABAN LOG", display_name, user_id, f"{base}\n\n**Reason:** {reason}", avatar)
    await interaction.edit_original_response(content=f"✅ Successfully Perma-banned {display_name}.")

# 🔓 UNBAN
@bot.tree.command(name="unban", description="Unban a player")
async def unban(interaction: discord.Interaction, username: str):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)
    await interaction.response.send_message("⏳ Processing...")
    user = await get_roblox_user(username)
    user_id = user["id"] if user else "Unknown"
    display_name = user["name"] if user else username
    avatar = await get_avatar(user_id) if user else None
    base = f"**Player:** {display_name} ({user_id})\n🔗 {profile(user_id) if user_id != 'Unknown' else 'Not found'}\n📄 **Administrator:** <@{interaction.user.id}>"
    await send_command("unban", username, "", 0, interaction.user.id)
    await send_log("UNBAN LOG", display_name, user_id, base, avatar)
    await interaction.edit_original_response(content=f"✅ Successfully Unbanned {display_name}.")

# 📋 BANLIST
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

# 🔍 FIND
@bot.tree.command(name="find", description="Find Roblox profile by userId")
async def find(interaction: discord.Interaction, userid: str):
    await interaction.response.send_message(f"https://www.roblox.com/users/{userid}/profile")

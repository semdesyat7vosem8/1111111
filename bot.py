import os
import discord
from discord.ext import commands
import aiohttp

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
async def get_roblox_user(username: str):
    url = "https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": False}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.post(url, json=payload) as res:
                data = await res.json()
                return data["data"][0] if data.get("data") else None
    except Exception as e:
        print(f"Error fetching Roblox user {username}: {e}")
        return None


async def get_avatar(user_id):
    url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png"
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(url) as res:
                data = await res.json()
                return data["data"][0].get("imageUrl")
    except Exception as e:
        print(f"Error fetching avatar for {user_id}: {e}")
        return None


# ===== Отправка команд на сервер =====
async def send_command(cmd_type, username, reason, days, admin_id):
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.post(f"{SERVER_URL}/command", json={
                "type": cmd_type,
                "username": username,
                "reason": reason,
                "days": days,
                "adminId": admin_id
            }) as res:
                if res.status != 200:
                    print(f"Error sending command: {res.status}")
                else:
                    print(f"Command {cmd_type} sent for {username}")
    except Exception as e:
        print(f"Failed to send command: {e}")


# ===== Логи в Discord =====
async def send_log(title, username, user_id, description, avatar=None):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        print("ERROR: Log channel not found!")
        return
    embed = discord.Embed(title=title, description=description, color=0xFFC0CB)
    if avatar:
        embed.set_thumbnail(url=avatar)
    await channel.send(content=f"{username} | {user_id}", embed=embed)


def profile(user_id):
    return f"https://www.roblox.com/users/{user_id}"


def has_admin_role(interaction):
    return any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles)


# ===== Событие готовности =====
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(e)


# ===== Slash Commands =====
async def process_player(interaction, cmd_type, username, reason="", days=0):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)

    await interaction.response.send_message("⏳ Processing...")
    user = await get_roblox_user(username)
    user_id = user["id"] if user else "Unknown"
    display_name = user["name"] if user else username
    avatar = await get_avatar(user_id) if user else None

    # Duration только для команды ban
    if cmd_type == "ban":
        duration_text = f"{days} day(s)"
    else:
        duration_text = ""

    base_text = f"**Player:** {display_name} ({user_id})\n🔗 {profile(user_id)}\n📄 Administrator: <@{interaction.user.id}>"
    if duration_text:
        base_text += f"\n⏱ Duration: {duration_text}"

    await send_command(cmd_type, username, reason, days, interaction.user.id)
    await send_log(f"{cmd_type.upper()} LOG", display_name, user_id, f"{base_text}\n\n**Reason:** {reason}", avatar)
    await interaction.edit_original_response(content=f"✅ Successfully {cmd_type}ed {display_name}.")


@bot.tree.command(name="kick", description="Kick a player")
async def kick(interaction: discord.Interaction, username: str, reason: str = "No reason set"):
    await process_player(interaction, "kick", username, reason)


@bot.tree.command(name="ban", description="Ban a player for X days")
async def ban(interaction: discord.Interaction, username: str, days: int, reason: str = "No reason set"):
    await process_player(interaction, "ban", username, reason, days)


@bot.tree.command(name="permaban", description="Permanently ban a player")
async def permaban(interaction: discord.Interaction, username: str, reason: str = "No reason set"):
    await process_player(interaction, "permaban", username, reason)


@bot.tree.command(name="unban", description="Unban a player")
async def unban(interaction: discord.Interaction, username: str):
    await process_player(interaction, "unban", username)


# ===== Banlist =====
@bot.tree.command(name="banlist", description="Show list of banned players")
async def banlist(interaction: discord.Interaction):
    await interaction.response.send_message("⏳ Processing...")
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(f"{SERVER_URL}/banlist") as res:
                if res.status != 200:
                    return await interaction.edit_original_response(content="Error fetching banlist.")
                data = await res.json()
    except Exception as e:
        print(f"Failed to fetch banlist: {e}")
        return await interaction.edit_original_response(content="Error fetching banlist.")

    if not data:
        return await interaction.edit_original_response(content="No bans.")

    text = ""
    for b in data:
        if b["daysLeft"] == 0 or b["daysLeft"] is None:
            days_text = "PERMA-BANNED"
        else:
            days_text = f"{b['daysLeft']} day(s)"
        text += f"{b['username']} ({b['username']}) — {days_text}\n\n"
    await interaction.edit_original_response(content=f"```{text}```")

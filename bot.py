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


# ===== SEND COMMAND =====
async def send_command(cmd_type, username, reason, days, admin_id):
    async with aiohttp.ClientSession() as session:
        await session.post(f"{SERVER_URL}/command", json={
            "type": cmd_type,
            "username": username,
            "reason": reason,
            "days": days,
            "adminId": admin_id
        })


# ===== SEND LOG =====
async def send_log(title, username, user_id, description, avatar=None, color=0xFFC0CB):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return
    embed = discord.Embed(title=title, description=description, color=color)
    if avatar:
        embed.set_thumbnail(url=avatar)
    await channel.send(content=f"{username} | {user_id}", embed=embed)


def has_admin_role(interaction):
    return any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()


# ===== MAIN LOGIC =====
async def process_player(interaction, cmd_type, username, reason="", days=0):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)

    if not reason:
        return await interaction.response.send_message("❌ Reason is required!", ephemeral=True)

    await interaction.response.send_message("⏳ Processing...")

    user = await get_roblox_user(username)
    user_id = user["id"] if user else "Unknown"
    display_name = user["name"] if user else username
    avatar = await get_avatar(user_id) if user else None

    # ===== ЛОГ ФОРМАТ =====
    log_text = f"""**Player:** {display_name} ({user_id})

🔗 https://www.roblox.com/users/{user_id}

📄 **Administrator:** <@{interaction.user.id}>"""

    if cmd_type == "ban":
        log_text += f"\n\n**Duration:** {days} day(s)"

    log_text += f"\n\n**Reason:** {reason}"

    await send_command(cmd_type, username, reason, days, interaction.user.id)

    await send_log(
        f"{cmd_type.upper()} LOG",
        display_name,
        user_id,
        log_text,
        avatar
    )

    await interaction.edit_original_response(
        content=f"✅ Successfully {cmd_type}ed {display_name}"
        
        if cmd_type == "ban":
        content=f"✅ Successfully {cmd_type}ned {display_name}"
    )


# ===== COMMANDS =====
@bot.tree.command(name="kick", description="Kick a player")
async def kick(interaction: discord.Interaction, username: str, reason: str):
    await process_player(interaction, "kick", username, reason)


@bot.tree.command(name="ban", description="Ban a player")
async def ban(interaction: discord.Interaction, username: str, days: int, reason: str):
    await process_player(interaction, "ban", username, reason, days)


@bot.tree.command(name="permaban", description="Permanent ban")
async def permaban(interaction: discord.Interaction, username: str, reason: str):
    await process_player(interaction, "permaban", username, reason)


@bot.tree.command(name="unban", description="Unban player")
async def unban(interaction: discord.Interaction, username: str, reason: str):
    await process_player(interaction, "unban", username, reason)


# ===== BANLIST =====
@bot.tree.command(name="banlist", description="Show bans")
async def banlist(interaction: discord.Interaction):
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


# ===== UNBANWAVE =====
@bot.tree.command(name="unbanwave", description="Unban all temp-banned players")
async def unbanwave(interaction: discord.Interaction, reason: str):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("No permission", ephemeral=True)

    if not reason:
        return await interaction.response.send_message("❌ Reason is required!", ephemeral=True)

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

    # ===== ЗЕЛЁНЫЙ ЛОГ =====
    log_text = f"""📄 **Administrator:** <@{interaction.user.id}>

**Reason:** {reason}"""

    await send_log(
        "UNBANWAVE LOG",
        "UNBAN WAVE",
        "—",
        log_text,
        color=0x00FF00  # ЗЕЛЁНЫЙ
    )

    await interaction.edit_original_response(
        content=f"✅ Unban wave completed. Unbanned {count} players."
    )

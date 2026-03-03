import discord
from discord.ext import commands
from flask import Flask, request
import threading
import os

# ========================
# ENV ПЕРЕМЕННЫЕ
# ========================

TOKEN = os.getenv("TOKEN")

guild_env = os.getenv("GUILD_ID")
GUILD_ID = int(guild_env) if guild_env else None

roles_env = os.getenv("ALLOWED_ROLES")
ALLOWED_ROLE_IDS = list(map(int, roles_env.split(","))) if roles_env else []

print("TOKEN:", TOKEN)
print("GUILD_ID:", GUILD_ID)
print("ALLOWED_ROLES:", ALLOWED_ROLE_IDS)

# ========================
# DISCORD
# ========================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

DEPARTMENTS = {
    "Отдел кадров": {
        "channel_id": 1478104628796063927,
        "message_id": None,
        "staff": []
    },
    "Отдел СМИ": {
        "channel_id": 1478104654775717898,
        "message_id": None,
        "staff": []
    },
    "Отдел безопасности": {
        "channel_id": 1478104678482055249,
        "message_id": None,
        "staff": []
    }
}

@bot.event
async def on_ready():
    print(f"✅ Бот запущен как {bot.user}")

def has_access(member):
    return any(role.id in ALLOWED_ROLE_IDS for role in member.roles)

async def update_department_embed(department_name):
    department = DEPARTMENTS[department_name]
    channel = bot.get_channel(department["channel_id"])

    if not channel:
        print("❌ Канал не найден")
        return

    embed = discord.Embed(
        title=f"📋 Состав — {department_name}",
        color=0xf1c40f
    )

    embed.description = "\n".join(department["staff"]) if department["staff"] else "—"

    try:
        if department["message_id"] is None:
            msg = await channel.send(embed=embed)
            department["message_id"] = msg.id
        else:
            msg = await channel.fetch_message(department["message_id"])
            await msg.edit(embed=embed)
    except Exception as e:
        print("Ошибка обновления embed:", e)

# ========================
# FLASK
# ========================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

@app.route("/update", methods=["POST"])
def update():
    data = request.json

    try:
        user_id = int(data["sender_id"])
        department_name = data["department"]
        action = data["action"]
        target_id = int(data["target_id"])
    except:
        return {"status": "bad request"}

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return {"status": "guild not found"}

    member = guild.get_member(user_id)
    if not member or not has_access(member):
        return {"status": "no access"}

    if department_name not in DEPARTMENTS:
        return {"status": "unknown department"}

    mention = f"<@{target_id}>"
    department = DEPARTMENTS[department_name]

    if action == "add":
        if mention not in department["staff"]:
            department["staff"].append(mention)

    elif action == "remove":
        if mention in department["staff"]:
            department["staff"].remove(mention)

    bot.loop.create_task(update_department_embed(department_name))
    return {"status": "updated"}

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ========================
# ЗАПУСК
# ========================

threading.Thread(target=run_flask).start()

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ TOKEN НЕ НАЙДЕН!")
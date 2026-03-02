import discord
from discord.ext import commands
from flask import Flask, request
import threading
import os

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
ALLOWED_ROLE_IDS = list(map(int, os.getenv("ALLOWED_ROLES").split(",")))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

DEPARTMENTS = {
    "Отдел кадров": {
        "channel_id": 111111111111111111,
        "message_id": None,
        "staff": []
    },
    "Отдел СМИ": {
        "channel_id": 222222222222222222,
        "message_id": None,
        "staff": []
    },
    "Отдел безопасности": {
        "channel_id": 333333333333333333,
        "message_id": None,
        "staff": []
    }
}

@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")

def has_access(member):
    return any(role.id in ALLOWED_ROLE_IDS for role in member.roles)

async def update_department_embed(department_name):
    department = DEPARTMENTS[department_name]
    channel = bot.get_channel(department["channel_id"])

    embed = discord.Embed(
        title=f"📋 Состав — {department_name}",
        color=0xf1c40f
    )

    text = "\n".join(department["staff"]) if department["staff"] else "—"
    embed.description = text

    if department["message_id"] is None:
        msg = await channel.send(embed=embed)
        department["message_id"] = msg.id
    else:
        msg = await channel.fetch_message(department["message_id"])
        await msg.edit(embed=embed)

app = Flask(__name__)

@app.route("/update", methods=["POST"])
def update():
    data = request.json

    user_id = int(data["sender_id"])
    department_name = data["department"]
    action = data["action"]
    target_id = int(data["target_id"])

    guild = bot.get_guild(GUILD_ID)
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

    if action == "remove":
        if mention in department["staff"]:
            department["staff"].remove(mention)

    bot.loop.create_task(update_department_embed(department_name))
    return {"status": "updated"}

def run_flask():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_flask).start()
bot.run(TOKEN)
import discord
from discord.ext import commands
from flask import Flask, request
import threading
import os

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ALLOWED_ROLE_IDS = list(map(int, os.getenv("ALLOWED_ROLES").split(",")))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

staff_data = {}
message_id = None

@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")

def has_access(member):
    return any(role.id in ALLOWED_ROLE_IDS for role in member.roles)

async def update_embed():
    global message_id
    channel = bot.get_channel(CHANNEL_ID)

    embed = discord.Embed(
        title="📋 Состав организации",
        color=0xf1c40f
    )

    for department, members in staff_data.items():
        text = "\n".join(members) if members else "—"
        embed.add_field(name=department, value=text, inline=False)

    if message_id is None:
        msg = await channel.send(embed=embed)
        message_id = msg.id
    else:
        msg = await channel.fetch_message(message_id)
        await msg.edit(embed=embed)

app = Flask(__name__)

@app.route("/update", methods=["POST"])
def update():
    data = request.json

    user_id = int(data["sender_id"])
    department = data["department"]
    action = data["action"]
    target_id = int(data["target_id"])

    guild = bot.get_guild(GUILD_ID)
    member = guild.get_member(user_id)

    if not member or not has_access(member):
        return {"status": "no access"}

    mention = f"<@{target_id}>"

    if department not in staff_data:
        staff_data[department] = []

    if action == "add":
        if mention not in staff_data[department]:
            staff_data[department].append(mention)

    if action == "remove":
        if mention in staff_data[department]:
            staff_data[department].remove(mention)

    bot.loop.create_task(update_embed())
    return {"status": "updated"}

def run_flask():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_flask).start()
bot.run(TOKEN)
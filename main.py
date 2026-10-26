import random
import os, re, secrets
import discord
from mcrcon import MCRcon

NAME_OF_MC_SERVER = "TEST"
RCON_HOST = "127.0.0.1"
RCON_PORT = 25575
RCON_PASSWORD = ""
TOKEN = ""

def rcon(cmd: str) -> str:
    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as rc:
        return rc.command(cmd)



intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(client.user.display_name)

@tree.command(name="register", description="Register a user to the server. You will get a DM with the user's password.")
async def register(interaction: discord.Interaction, mc_name: str):
    password = random.randint(0, 2**32)
    response = rcon(f"authme register {mc_name} {password}")
    if not "success" in response.lower():
        await interaction.response.send_message("Something went wrong! Please contact the server moderators")
        print(mc_name, password)
        print(response)
    await interaction.user.send(f"{NAME_OF_MC_SERVER}\nusername: {mc_name}\ntemporary password: {password}")
    await interaction.response.send_message("Your account has been successfully created! I have DM'd you the password. Please make sure to change it when you get into the game with `/changepassword [old_password] [new_password]`\nYour new password can be anything as long as it does not contain a space.")

client.run(TOKEN)

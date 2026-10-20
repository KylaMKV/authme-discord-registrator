import os, re, secrets
import discord
from discord import app_commands
from mcrcon import MCRcon

NAME_OF_MC_SERVER = ""
RCON_HOST = "127.0.0.1"
RCON_PORT = 25575
RCON_PASSWORD = ""
TOKEN = ""
GUILD_ID = int(os.environ.get("GUILD_ID", 0))  # optional, for instant command sync

NAME_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")


def rcon(cmd: str) -> str:
    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as rc:
        return rc.command(cmd)


class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)  # shows up immediately
        else:
            await self.tree.sync()             # global sync can take a while


bot = Bot()


@bot.tree.command(name="register", description="Create your Minecraft account")
@app_commands.guild_only()
@app_commands.describe(mc_name="Your Minecraft username (case-sensitive)")
async def register(interaction: discord.Interaction, mc_name: str):
    await interaction.response.defer(ephemeral=True)

    if not NAME_RE.fullmatch(mc_name):
        return await interaction.followup.send(
            "Names must be 3-16 characters: letters, digits, or underscore.", ephemeral=True)

    password = secrets.token_urlsafe(12)

    try:
        # Called directly (no to_thread) so mcrcon runs on the main thread
        response = rcon(f"authme register {mc_name} {password}")
    except Exception as e:
        print("RCON error:", repr(e))
        return await interaction.followup.send(
            "I couldn't reach the Minecraft server. Ask moderators for help.", ephemeral=True)

    print("AuthMe replied:", response)  # check this once to confirm the success text

    if "success" not in response.lower():
        return await interaction.followup.send(
            "I was unable to register your account. Ask moderators for help.", ephemeral=True)

    try:
        await interaction.user.send(
            f"Your password for {NAME_OF_MC_SERVER}: `{password}`\n"
            f"Join with the name `{mc_name}`, run `/login {password}`, "
            f"then change it with `/changepassword {password} <new password>`.")
    except discord.Forbidden:
        try:
            rcon(f"authme unregister {mc_name}")  # undo so they can retry
        except Exception as e:
            print("Rollback failed:", repr(e))
        return await interaction.followup.send(
            "I couldn't DM you. Enable DMs from server members and run `/register` again.",
            ephemeral=True)

    await interaction.followup.send(
        "Your account was registered. Check your DMs for the temporary password, and "
        "change it with `/changepassword` once you log in.", ephemeral=True)

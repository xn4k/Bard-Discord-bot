from bardapi import BardAsync
import configparser
import discord
from discord.ext import commands

# logging
import datetime
# import ascii art
import pyfiglet
# import jokes
import pyjokes
# import reminder function
import asyncio
import time
from discord.ext import commands, tasks
from discord.ext.commands import Cog

config = configparser.ConfigParser()
config.read('config.ini')
BARD_TOKEN = config["TOKENS"]['bard_token']
bard = BardAsync(token=BARD_TOKEN)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, heartbeat_timeout=60)


@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="/help"))
    print(f"{bot.user.name} has connected to Discord!")
    invite_link = discord.utils.oauth_url(
        bot.user.id,
        permissions=discord.Permissions(administrator=True),
        scopes=("bot", "applications.commands")
    )
    print(f"Invite link: {invite_link}")


@bot.tree.command(name="reset", description="Reset chat context")
async def reset(interaction: discord.Interaction):
    await interaction.response.defer()
    global bard
    bard = BardAsync(token=BARD_TOKEN)
    await interaction.followup.send("Chat context successfully reset.")
    return


@bot.tree.command(name="chat", description="Chat with Milanobot")
async def chat(interaction: discord.Interaction, prompt: str, image: discord.Attachment = None):
    await interaction.response.defer()
    if image is not None:
        if not image.content_type.startswith('image/'):
            await interaction.response.send_message("File must be an image")
            return
        response = await bard.ask_about_image(prompt, await image.read())
        if len(response['content']) > 2000:
            embed = discord.Embed(title="Response", description=response['content'], color=0xf1c40f)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(response['content'])
            return
    response = await generate_response(prompt)
    if len(response['content']) > 2000:
        embed = discord.Embed(title="Response", description=response['content'], color=0xf1c40f)
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(response['content'])
    return


async def generate_response(prompt):
    response = await bard.get_answer(prompt)
    if not "Unable to get response." in response["content"]:
        config = read_config()
        if config.getboolean("SETTINGS", "use_images"):
            images = response.get("images", [])  # Use dict.get() to retrieve images or an empty list if not present
            if images:
                for image in images:
                    response["content"] += f"\n{image}"
                # Add the prompt and the response to the content
        response["content"] = f"**Your question:** {prompt}\n\n**Response from Milanobot:** {response['content']}"
        # log the interaction
        print("New input: " + prompt)
        log_interaction("User", prompt, response["content"])
        return response


@bot.tree.command(name="public", description="Bot will respond to all messages")
async def public(interaction: discord.Interaction):
    config = read_config()
    if config.getboolean("SETTINGS", "reply_all"):
        await interaction.response.send_message("Bot is already in public mode")
    else:
        config["SETTINGS"]["reply_all"] = "True"  # Update to string "True"
        await interaction.response.send_message("Bot will now respond to all messages")
    write_config(config)

    return


@bot.tree.command(name="private", description="Bot will only respond to /chat")
async def private(interaction: discord.Interaction):
    config = read_config()
    if config.getboolean("SETTINGS", "reply_all"):
        config["SETTINGS"]["reply_all"] = "False"  # Update to string "False"
        await interaction.response.send_message("Bot will now only respond to /chat")
    else:
        await interaction.response.send_message("Bot is already in private mode")
    write_config(config)
    return


@bot.event
async def on_message(message):
    config = read_config()
    if config.getboolean("SETTINGS", "reply_all"):
        if message.author == bot.user:
            return
        async with message.channel.typing():
            response = await generate_response(message.content)
            if len(response['content']) > 2000:
                embed = discord.Embed(title="Response", description=response['content'], color=0xf1c40f)
                await message.channel.send(embed=embed)
            else:
                await message.channel.send(response['content'])


@bot.tree.command(name="images", description="Toggle if bot should respond with images")
async def images(interaction: discord.Interaction):
    config = read_config()
    if config.getboolean("SETTINGS", "use_images"):
        config["SETTINGS"]["use_images"] = "False"
        await interaction.response.send_message("Bot will no longer respond with images")
    else:
        config["SETTINGS"]["use_images"] = "True"
        await interaction.response.send_message("Bot will now respond with images")
    write_config(config)
    return


@bot.tree.command(name="ascii", description="Generate ASCII art from text")
async def generate_ascii(interaction: discord.Interaction, text: str):
    ascii_text = pyfiglet.figlet_format(text)
    await interaction.response.send_message(f"```\n{ascii_text}\n```")


@bot.tree.command(name="author", description="Information about the author")
async def author_info(interaction: discord.Interaction):
    author_info_text = "Hello, my name is Mikhail aka xn4k, contact me on Discord: xn4k, if you have any questions."

    await interaction.response.send_message(author_info_text)
    return


@bot.tree.command(name="joke", description="Get a random joke")
async def get_joke(interaction: discord.Interaction):
    joke = pyjokes.get_joke()
    await interaction.response.send_message(joke)

# Add the convert function
def convert(time):
    pos = ['s', 'm', 'h', 'd']

    time_dict = {"s": 1, "m": 60, "h": 3600, "d": 3600 * 24}

    unit = time[-1]

    if unit not in pos:
        return -1
    try:
        val = int(time[:-1])
    except:
        return -2

    return val * time_dict[unit]


@bot.tree.command(name="remind", description="Set a reminder")
async def set_reminder(interaction: discord.Interaction, time: str, reminder_text: str):
    await interaction.response.defer()

    time_seconds = convert(time)
    if time_seconds == -1:
        await interaction.followup.send("Invalid time unit. Use 's', 'm', 'h', or 'd'.")
        return
    elif time_seconds == -2:
        await interaction.followup.send("Invalid time format. Use a valid number followed by 's', 'm', 'h', or 'd'.")
        return

    # Mention the user who set the reminder
    user_mention = interaction.user.mention  # Mention the user who set the reminder

    await interaction.followup.send(f"Okay, {user_mention}, I will remind you in {time}, with the following message: {reminder_text}")

    await asyncio.sleep(time_seconds)

    await interaction.followup.send(f"Reminder: {reminder_text}")


@bot.tree.command(name="help", description="Get all commands")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="Commands", description="All commands for the bot", color=0xFF66B2)
    embed.add_field(name="/chat", value="Chat with Bot", inline=False)
    embed.add_field(name="/reset", value="Reset chat context", inline=False)
    embed.add_field(name="/public", value="Set bot to respond to all messages", inline=False)
    embed.add_field(name="/private", value="Set bot to only respond to /chat", inline=False)
    embed.add_field(name="/images", value="Toggle if bot should respond with images", inline=False)
    embed.add_field(name="/ascii", value="Generate ASCII art from text", inline=False)
    embed.add_field(name="/author", value="Provide information about the author", inline=False)
    embed.add_field(name="/joke", value="Get a random joke", inline=False)
    embed.add_field(name="/remind", value="Set a reminder, use s, m, h or d, like: /remind 10 s Buy eggs", inline=False)

    # Send the embed to the channel where the command was invoked
    await interaction.channel.send(embed=embed)

    # Respond to the interaction to acknowledge the command
    await interaction.response.send_message("Help information:")


def read_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config


def write_config(config):
    with open("config.ini", "w") as configfile:
        config.write(configfile)


def log_interaction(author, message, response):
    print("Logging interaction...")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("interaction_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"Timestamp: {timestamp}\n")
        log_file.write(f"Author: {author}\n")
        log_file.write(f"Message: {message}\n")

        # Encode the response to utf-8 with 'replace' error handling and decode back to utf-8
        filtered_response = response.encode('utf-8', errors='replace').decode('utf-8')
        log_file.write(f"Response: {filtered_response}\n")

        log_file.write("=" * 50 + "\n")


bot.run(config["TOKENS"]['discord_bot_token'])

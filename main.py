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

config = configparser.ConfigParser()
config.read('config.ini')
BARD_TOKEN = config["TOKENS"]['bard_token']
bard = BardAsync(token=BARD_TOKEN)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, heartbeat_timeout=60)


class Reminder:
    def __init__(self, user_id, message, delay):
        self.user_id = user_id
        self.message = message
        self.delay = delay
        self.start_time = time.time()


active_reminders = []


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

    # Start the reminders loop
    check_reminders.start()


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


@bot.tree.command(name="remind", description="Set a reminder")
async def remind_command(interaction: discord.Interaction):
    await interaction.response.send_message("Usage: /remind <time> <message>")
    return


# Define the reminder command
@bot.command(name="remind")
async def remind(ctx, delay, *, message):
    user_id = ctx.author.id

    # Convert the time delay input to seconds
    if delay.endswith("seconds"):
        seconds = int(delay.split(" ")[0])
    elif delay.endswith("minutes"):
        seconds = int(delay.split(" ")[0]) * 60
    elif delay.endswith("hours"):
        seconds = int(delay.split(" ")[0]) * 3600
    elif delay.endswith("days"):
        seconds = int(delay.split(" ")[0]) * 86400
    else:
        await ctx.send("Invalid time format. Please use 'seconds', 'minutes', 'hours', or 'days'.")
        return

    reminder = Reminder(user_id, message, seconds)
    active_reminders.append(reminder)
    await ctx.send(f"Reminder set: '{message}' in {delay}.")


# Background task to check reminders
@tasks.loop(seconds=5)
async def check_reminders():
    now = time.time()
    reminders_to_remove = []

    for reminder in active_reminders:
        if now >= reminder.start_time + reminder.delay:
            user = bot.get_user(reminder.user_id)
            if user:
                await user.send(f"Reminder: {reminder.message}")
            reminders_to_remove.append(reminder)

    for reminder in reminders_to_remove:
        active_reminders.remove(reminder)


@bot.tree.command(name="help", description="Get all commands")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="Commands", description="All commands for the bot", color=0xf1c40f)
    embed.add_field(name="/chat", value="Chat with Bard", inline=False)
    embed.add_field(name="/reset", value="Reset chat context", inline=False)
    embed.add_field(name="/public", value="Set bot to respond to all messages", inline=False)
    embed.add_field(name="/private", value="Set bot to only respond to /chat", inline=False)
    embed.add_field(name="/images", value="Toggle if bot should respond with images", inline=False)
    embed.add_field(name="/ascii", value="Generate ASCII art from text", inline=False)
    embed.add_field(name="/author", value="Provide information about the author", inline=False)
    embed.add_field(name="/joke", value="Get a random joke", inline=False)
    embed.add_field(name="/remind", value="Set a reminder", inline=False)

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

import discord
from discord.ext import commands
import youtube_dl
import asyncio
import random
from PIL import Image

intents = discord.Intents.all()
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix='%', intents=intents)

bot.remove_command('help')

ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'force-ipv4': True,
    'preferredcodec': 'mp3',
    'cachedir': False,
    'extractor': 'youtube',
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdlopts)

queues = {}

async def play_queue(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client.is_playing():
        return

    if queues[ctx.guild.id]:
        song = queues[ctx.guild.id].pop(0)
        voice_client.play(discord.FFmpegPCMAudio(source=song['url'], **ffmpeg_options, executable="ffmpeg"),
                          after=lambda e: print('done', e))
        await ctx.send(f'**Now playing:** {song["title"]}')

        if queues[ctx.guild.id]:
            await play_queue(ctx)
    else:
        await voice_client.disconnect()

@bot.event
async def on_ready():
    statuses = ['Well, what can you do?', 'Yeah, I am...', '/help', 'What are you looking at?']
    while True:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=random.choice(statuses)))
        await asyncio.sleep(10)

@bot.command(description='Test command')
async def command(ctx):
    """
    Test command
    """
    await ctx.message.delete()
    await ctx.send('I am a robot')

blocked_words = ['gay', 'homosexual', 'n-word', 'little n-word', 'hohol', 'rusnya']  # List of blocked words

@bot.event
async def on_message(message):
    for word in blocked_words:
        if word in message.content.lower():
            await message.delete()
            await message.channel.send(f'{message.author.mention}, do not use such bad words. :smiling_face_with_tear:')
            break
    await bot.process_commands(message)

@bot.command()
async def help(ctx, description='List of all commands'):
    """All bot commands.
    Usage: /help
    """
    embed = discord.Embed(title="All Possible Commands", description="List of available bot commands:",
                          color=discord.Color.blue())

    for command in bot.commands:
        embed.add_field(name=command.name, value=command.help, inline=False)

    file_path = r"C:\Users\comp\Desktop\137077897\help.jpg"

    with Image.open(file_path) as img:
        img = img.resize((img.width * 2, img.height * 2))

        temp_file_path = r"C:\Users\comp\Desktop\137077897\help_resized.jpg"
        img.save(temp_file_path)

    resized_file = discord.File(temp_file_path, filename="help_resized.jpg")

    embed.set_image(url="attachment://help_resized.jpg")

    await ctx.reply(embed=embed, file=resized_file)

@bot.event  # random reactions
async def on_message(message):
    if random.random() < 0.1:
        emoji = random.choice(bot.emojis)
        try:
            await message.add_reaction(emoji)
        except discord.errors.HTTPException:
            pass
    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int, description='Delete messages'):
    """
    Deletes the specified number of messages from the current chat channel.
    Usage: /clear [amount]
    """
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f'{amount} messages deleted.')

@bot.command()
async def play(ctx, *, query):
    """
    Play music in the voice channel.
    Usage: /play [title]
    """
    try:
        voice_channel = ctx.author.voice.channel
    except AttributeError:
        return await ctx.send("No channel to connect. Make sure you are in a voice channel.")

    permissions = voice_channel.permissions_for(ctx.me)
    if not permissions.connect or not permissions.speak:
        await ctx.send("I don't have permission to connect or speak in this voice channel.")
        return

    voice_client = ctx.guild.voice_client
    if not voice_client:
        await voice_channel.connect(self_deaf=True)
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if ctx.guild.id not in queues:
        queues[ctx.guild.id] = []

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None,
                                      lambda: ytdl.extract_info(url=query, download=False, extra_info={'verbose': True}))

    title = data.get('title', 'Unknown title')

    if 'entries' in data:
        data = data['entries'][0]
        song = data.get('url', 'Unknown URL')
    else:
        song = data.get('url', 'Unknown URL')

    queues[ctx.guild.id].append({'title': title, 'url': song})

    position = len(queues[ctx.guild.id])

    await ctx.send(f'**Added to queue:** {title}. Queue position: {position}')

    if len(queues[ctx.guild.id]) == 1:
        await play_queue(ctx)
@bot.command()
async def skip(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Song skipped.")
    elif voice_client and voice_client.is_paused():
        voice_client.stop()
        await ctx.send("Song skipped.")
    else:
        await ctx.send("There is no active playback at the moment.")

@bot.command()
async def pause(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Song paused.")
    else:
        await ctx.send("Nothing is playing at the moment.")

@bot.command()
async def resume(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Resuming playback.")
    else:
        await ctx.send("The song is already playing or not paused.")

@bot.command()
async def stop(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client:
        await voice_client.disconnect()
        await ctx.send("Disconnecting from the voice channel.")
    else:
        await ctx.send("I am not in a voice channel.")

@bot.command(name="ban", usage="ban <@user> <reason=None>")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    """
    Ban a user on the server.
    Usage: /ban <@user> <reason=None>
    """
    server_name = ctx.guild.name
    
    await member.send(f"You are banned from the server {server_name}. If you want to appeal, contact the server administration.")
    await ctx.send(f"Member {member.mention} has been permanently banned from the server {server_name}.")
    await member.ban(reason=reason)

@bot.command(name="unban", usage="unban <user_id>")
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    """
    Unban a user on the server.
    Usage: /unban <user_id>
    """
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)

@bot.command()
async def knb(ctx, user_choice: str):
    """
    Rock, paper, scissors game.
    Usage: /knb [rock/scissors/paper]
    """
    choices = ['rock', 'scissors', 'paper']

    if user_choice.lower() not in choices:
        return await ctx.send("Invalid choice. Use: rock, scissors, or paper.")

    bot_choice = random.choice(choices)

    if user_choice.lower() == bot_choice:
        result = "It's a tie!"
    elif (user_choice.lower() == 'rock' and bot_choice == 'scissors') or \
         (user_choice.lower() == 'scissors' and bot_choice == 'paper') or \
         (user_choice.lower() == 'paper' and bot_choice == 'rock'):
        result = "You won!"
    else:
        result = "Bot won!"

    await ctx.send(f"Bot chose: {bot_choice}. Result: {result}")

@bot.command()
async def joke(ctx):
    """
    Random joke.
    Usage: /joke
    """
    jokes = [
        "Why do programmers communicate poorly? Because they have no life.",
        "What is a programmer's favorite drink? Java.",
        "What does a programmer say when in pain? try...except.",
        "Why do programmers love coffee? Because without it, they can't invoke Java.",
        "How does a programmer react to cold? if temperature < 0: print('Cold!')",
        "The only woman a guy listens to is the one in the GPS.",
    ]

    joke = random.choice(jokes)
    await ctx.reply(joke)

@bot.command()
async def guess_my_number(ctx):
    """
    Guess my number game.
    Usage: /guess_my_number
    """
    await ctx.send("Let's play 'Guess my number'. Choose a range to guess a number (e.g., 1-100):")

    def check_range(message):
        return message.author == ctx.author and message.channel == ctx.channel and '-' in message.content

    try:
        user_range = await bot.wait_for('message', check=check_range, timeout=30.0)
    except asyncio.TimeoutError:
        return await ctx.send("Time expired. The game is over.")

    range_start, range_end = map(int, user_range.content.split('-'))
    await ctx.send(f"Great, guess a number in the range from {range_start} to {range_end}.")

    lower_bound, upper_bound = range_start, range_end
    max_attempts = 10
    attempts_left = max_attempts

    await ctx.send(f"I have {max_attempts} attempts. Let's go!")

    while attempts_left > 0:
        guess = random.randint(lower_bound, upper_bound)
        await ctx.send(f"Is it {guess}? (Answer 'higher', 'lower', or 'guessed'):")

        def check_answer(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.lower() in ['higher', 'lower', 'guessed']

        try:
            user_answer = await bot.wait_for('message', check=check_answer, timeout=30.0)
        except asyncio.TimeoutError:
            return await ctx.send("Time expired. The game is over.")

        user_answer = user_answer.content.lower()

        if user_answer == 'higher':
            lower_bound = guess + 1
        elif user_answer == 'lower':
            upper_bound = guess - 1
        elif user_answer == 'guessed':
            return await ctx.send(f"Hooray! I guessed your number.")

        attempts_left -= 1
        await ctx.send(f"Attempts left: {attempts_left}")

    await ctx.send(f"Unfortunately, I lost. Attempts are over.")

bot.run('your token')  # Ensure to replace 'your token' with your actual bot token.




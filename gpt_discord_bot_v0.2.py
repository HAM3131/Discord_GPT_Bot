import os
import openai
import discord
import random
from discord.ext import commands
from dotenv import load_dotenv
from pydub import AudioSegment
import asyncio
from datetime import datetime, timedelta

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Set up OpenAI API
openai.api_key = OPENAI_API_KEY


async def fetch_gpt4_response(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003",  # Replace this with the desired GPT engine
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.5,
    )

    return response.choices[0].text.strip()


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author == bot.user:
        return

    # ping
    if message.content.startswith("ping"):
        await message.channel.send("pong")

    thresh = 0.01 #the probability from 0 to 1 that the bot responds
    
    # find the time of the detected message
    timezone_offset = timedelta(hours=-4)
    timestamp = message.created_at + timezone_offset
    formatted_timestamp = timestamp.strftime('%H:%M:%S')

    chance = random.random()
    respond = chance < thresh or (bot.user.mentioned_in(message) and message.channel.name != "general")
    print(f"{formatted_timestamp} - Message received. Chance = {chance}   Response = {respond}")


    if respond:
        directive = """---------------------------------
        Choose a random perspective to act from (a trait, opinion, occupation, nationality, time period, historical figure, etc.)
        Try to choose fun, interesting, or unique perspectives. If the perspective is mostly focused on a trait, use more than one trait. 
        Additionally, aim for a lengthy and entertaining responses. Change your dialect to suit the perspective you are using. 
        Respond to the statement above in the format on the following line.\n 
        [PERSPECTIVE]: [RESPONSE]\n
        Do not vary from this format at all."""
        prompt = "STATEMENT: " + message.content + "\n" + directive
        response = await fetch_gpt4_response(prompt)
        await message.reply(response)
        print("|-----------------------------------------------------------------------------")
        print(f"|Sent response: {response}")
        print("|-----------------------------------------------------------------------------")

@bot.command()
async def gpt(ctx, *, prompt):
    directive = "\n-----------------"
    prompt = prompt + directive
    print("|-----------------------------------------------------------------------------")
    print(f"|Received GPT-4 command: !gpt4 {prompt}")
    print("|------")
    response = await fetch_gpt4_response(prompt)
    await ctx.send(response)
    print(f"|Sent response: {response}")
    print("|-----------------------------------------------------------------------------")

# join vc
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("not in a voice channel!")

# leave vc
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("not in a voice channel!")

@bot.command()
async def listen(ctx):
    if ctx.voice_client:
        ctx.voice_client.start_recording(discord.sinks.WaveSink(), callback, ctx)
        await ctx.send("listening...")
    else:
        await ctx.send("not in a voice channel!")

async def callback(sink: discord.sinks, ctx):
    for user_id, audio in sink.audio_data.items():
        if user_id == ctx.author.id:
            audio: discord.sinks.core.AudioData = audio
            print(user_id)
            filepath = os.path.join("recordings", f"user_{user_id}.wav")
            with open(filepath, "wb") as f:
                f.write(audio.file.getvalue())

# stops recording
@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop_recording()
        await ctx.send("stopped recording")
    else:
        await ctx.send("not in a voice channel")

bot.run(DISCORD_TOKEN)

import os
import openai
import discord
import random
from discord.ext import commands
from dotenv import load_dotenv
from pydub import AudioSegment
import asyncio
from datetime import datetime, timedelta
import soundfile as sf
import numpy as np
from discord.opus import Decoder

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

# Class allowing the bot to record individual's voices
class CustomVoiceClient(discord.VoiceClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.audio_streams = {}
        self.decoders = {}
        self._nbytes = Decoder.CHANNELS * Decoder.SAMPLE_SIZE
        self.last_received_voice_data = datetime.utcnow()
        self.disconnect_timeout = 3 * 60  # 3 minutes in seconds
        self.context = None
        asyncio.ensure_future(self.auto_disconnect())

    def _get_user_decoder(self, user_id):
        if user_id not in self.decoders:
            self.decoders[user_id] = Decoder()
        return self.decoders[user_id]

    def _get_audio_stream(self, user_id):
        if user_id not in self.audio_streams:
            self.audio_streams[user_id] = []
        return self.audio_streams[user_id]

    async def on_voice_data(self, data):
        user_id = data.user_id
        decoder = self._get_user_decoder(user_id)
        pcm = decoder.decode(data.data)

        print(f"Received audio data for user {user_id}")

        audio_stream = self._get_audio_stream(user_id)
        audio_stream.append(pcm)
        self.last_received_voice_data = datetime.utcnow()

    async def save_audio_files(self):
        print("Saving audio files...")

        # Create a folder named 'recordings' if it doesn't exist
        folder = 'recordings'
        if not os.path.exists(folder):
            os.makedirs(folder)

        # Save audio files in the 'recordings' folder
        for user_id, audio_data in self.audio_streams.items():
            audio = np.frombuffer(b''.join(audio_data), dtype=np.int16)
            file_path = os.path.join(folder, f"user_{user_id}.wav")
            sf.write(file_path, audio, Decoder.SAMPLING_RATE, subtype='PCM_16')
    
    async def auto_disconnect(self):
        while True:
            await asyncio.sleep(10)  # Check every 10 seconds
            elapsed_time = (datetime.utcnow() - self.last_received_voice_data).total_seconds()
            if elapsed_time >= self.disconnect_timeout:
                if self.is_connected():
                    await self.disconnect()
                    await self.save_audio_files()
                    await self.context.send("Bot disconnected due to inactivity.")
                break



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
    thresh = 0.01 #the probability from 0 to 1 that the bot responds
    
    if message.author == bot.user:
        return
    
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

    await bot.process_commands(message)


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


@bot.command()
async def join(ctx):
    channel = ctx.author.voice.channel
    voice_client = ctx.guild.voice_client

    if voice_client and voice_client.is_connected():
        await ctx.send("The bot is already connected to a voice channel. Please use the `!stop` command before trying to connect to a different channel.")
    elif channel:
        voice_client = await channel.connect(timeout=10.0, reconnect=True, self_deaf=False, self_mute=False, cls=CustomVoiceClient)
        voice_client.context = ctx
    else:
        await ctx.send("You are not connected to a voice channel.")


@bot.command()
async def stop(ctx):
    voice_client = ctx.guild.voice_client

    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await voice_client.save_audio_files()
        await ctx.send("Recording stopped and audio files saved.")
    else:
        await ctx.send("The bot is not connected to a voice channel or not recording.")

bot.run(DISCORD_TOKEN)

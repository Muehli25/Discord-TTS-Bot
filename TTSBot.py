import discord

import uuid
import os
import queue
from SsmlVoiceGender import SsmlVoiceGender

from GoogleCloudTTSProvider import TTSProvider
from Timer import Timer

DATA_FOLDER = "data"
TIMEOUT = 1200


def delete_file(filename):
    try:
        os.remove(filename)
    except FileNotFoundError:
        print(f'File {filename} does not exists')


def clean_data_folder():
    file_list = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".mp3")]
    for f in file_list:
        delete_file(os.path.join(DATA_FOLDER, f))


class TTSBot(discord.Client):

    def __init__(self, language="en"):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)

        self.timer = None
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
        self.CurrentConnection = None
        self.language = language
        self.gender = SsmlVoiceGender.SSML_VOICE_GENDER_UNSPECIFIED
        self.queue = queue.Queue()
        self.play_next()
        self.TTSProvider = TTSProvider()
        self.current_text_channel = None

    async def call_bot(self, channel):
        self.CurrentConnection = await channel.connect()
        self.play_next()

    async def send_text_message(self, text):
        await self.current_text_channel.send(text)

    async def goodbye_bot(self):
        await self.send_text_message('Goodbye!')
        await self.CurrentConnection.disconnect()
        self.CurrentConnection = None
        self.queue = queue.Queue()
        clean_data_folder()
        self.stop_timeout()

    async def on_ready(self):
        print('Logged in as {0.user}'.format(client))

    def play_next(self):
        if self.CurrentConnection is not None \
                and not self.CurrentConnection.is_playing() \
                and not self.queue.empty():
            to_play = self.queue.get()
            self.CurrentConnection.play(discord.FFmpegPCMAudio(to_play, options="-loglevel panic"),
                                        after=lambda e: delete_file(filename=to_play))
        if self.CurrentConnection is not None:
            self.loop.call_later(0.5, self.play_next)

    def abort_playback(self):
        file = ""
        self.CurrentConnection.stop()
        while True:
            try:
                file = self.queue.get(block=False)
                delete_file(file)
            except queue.Empty:
                break
        self.queue = queue.Queue()
        clean_data_folder()

    def play(self, file):
        self.CurrentConnection.play(file)

    def start_timeout(self):
        if self.timer is None:
            self.timer = Timer(TIMEOUT, self.timeout_callback)

    def reset_timeout(self):
        if self.timer is not None:
            self.timer.cancel()
        self.timer = Timer(TIMEOUT, self.timeout_callback)

    def stop_timeout(self):
        if self.timer is not None:
            self.timer.cancel()

    async def timeout_callback(self):
        await self.goodbye_bot()

    async def on_message(self, message):
        if message.author == self.user:
            return

        elif message.content == '!male' \
                and self.CurrentConnection is not None \
                and self.CurrentConnection.is_connected():
            self.gender = SsmlVoiceGender.MALE
        
        elif message.content == '!female' \
                and self.CurrentConnection is not None \
                and self.CurrentConnection.is_connected():
            self.gender = SsmlVoiceGender.FEMALE
        
        elif message.content == '!neutral' \
                and self.CurrentConnection is not None \
                and self.CurrentConnection.is_connected():
            self.gender = SsmlVoiceGender.NEUTRAL

        elif message.content == "!call":
            self.current_text_channel = message.channel
            await self.send_text_message('Hello!')
            await self.call_bot(message.author.voice.channel)
            self.start_timeout()

        elif message.content == '!bye' \
                and self.CurrentConnection is not None \
                and self.CurrentConnection.is_connected():
            await self.goodbye_bot()

        elif message.content == "!abort":
            self.abort_playback()

        elif message.content.startswith("http"):
            # ignore links
            return

        else:
            if self.CurrentConnection is not None \
                    and self.CurrentConnection.is_connected() \
                    and len(message.content) > 0:
                # Cancel Time one new Message
                self.reset_timeout()
                lang = self.language
                text = user_input = message.content
                print(f"{message.author} says {message.content}.")
                if user_input[0] == "+":
                    divider = user_input.find(" ")
                    lang = user_input[1:divider]
                    text = user_input[(divider + 1):]
                # Create uuid as filename
                name = uuid.uuid1()
                # Play the requested text
                try:
                    filename = f'{DATA_FOLDER}/{name}.mp3'

                    self.TTSProvider.create_audio_file(filename, lang, text, self.gender)

                    self.queue.put(filename)
                except ValueError as e:
                    print(f"{message.author} says {message.content}.")
                    await self.send_text_message(f"Language not supported or no Text provided.")
                    if hasattr(e, 'message'):
                        print(e.message)
                    else:
                        print(e)


# Create new bot
client = TTSBot()
if os.getenv("LANG") is not None:
    client = TTSBot(os.environ['LANG'])
# run Bot with provided discord token
client.run(os.environ['TOKEN'])

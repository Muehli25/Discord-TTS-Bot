import discord

from gtts import gTTS
import uuid
import os
import queue
import time

DATA_FOLDER = "data"


def delete_file(filename):
    os.remove(filename)


def clean_data_folder():
    file_list = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".mp3")]
    for f in file_list:
        os.remove(os.path.join(DATA_FOLDER, f))


class TTSBot(discord.Client):

    def __init__(self, language="en"):
        super().__init__()
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
        self.CurrentConnection = None
        self.language = language
        self.queue = queue.Queue()
        self.play_next()

    async def call_bot(self, channel):
        self.CurrentConnection = await channel.connect()
        self.play_next()

    async def goodbye_bot(self):
        await self.CurrentConnection.disconnect()
        self.CurrentConnection = None
        self.queue = queue.Queue()
        clean_data_folder()

    async def on_ready(self):
        print('Logged in as {0.user}'.format(client))

    def play_next(self):
        if self.CurrentConnection is not None \
                and not self.CurrentConnection.is_playing() \
                and not self.queue.empty():
            to_play = self.queue.get()
            self.CurrentConnection.play(discord.FFmpegPCMAudio(to_play),
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

    async def countdown(self, number):
        if number < 0:
            return
        await self.say(str(number))
        time.sleep(1)
        await self.countdown(number - 1)

    async def say(self, message, language=None):
        if language is None:
            language = self.language
        # Create uuid as filename
        name = uuid.uuid1()
        # Play the requested text
        try:
            filename = f'{DATA_FOLDER}/{name}.mp3'
            tts = gTTS(message, lang=language)
            tts.save(filename)
            self.queue.put(filename)
        except ValueError:
            raise ValueError

    async def on_message(self, message):
        if message.author == self.user:
            return

        elif message.content == "!call":
            await message.channel.send('Hello!')
            await self.call_bot(message.author.voice.channel)

        elif message.content == '!bye' \
                and self.CurrentConnection is not None \
                and self.CurrentConnection.is_connected():
            await message.channel.send('Goodbye!')
            await self.goodbye_bot()

        elif message.content == "!abort":
            self.abort_playback()

        elif message.content.startswith("http"):
            # ignore links
            return

        elif message.content.startswith("!timer"):
            await self.countdown(int(message.content[7:]))

        else:
            if self.CurrentConnection is not None \
                    and self.CurrentConnection.is_connected():
                lang = self.language
                text = user_input = message.content
                if user_input[0] == "+":
                    divider = user_input.find(" ")
                    lang = user_input[1:divider]
                    text = user_input[(divider + 1):]
                try:
                    await self.say(text, lang)
                except ValueError:
                    await message.channel.send(f"Language not supported or no Text provided.")


# Create new bot
client = TTSBot()
if os.getenv("LANG") is not None:
    client = TTSBot(os.environ['LANG'])
# run Bot with provided discord token
client.run(os.environ['TOKEN'])

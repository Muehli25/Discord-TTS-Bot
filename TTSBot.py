import discord

from gtts import gTTS
import uuid
import os

SAY_COMMAND = "!say"
DATA_FOLDER = "data"


class TTSBot(discord.Client):
    def __init__(self):
        super().__init__()
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
        self.CurrentConnection = None
        self.queue = []

    async def on_ready(self):
        print('Logged in as {0.user}'.format(client))

    async def join_channel(self, channel):
        self.CurrentConnection = await channel.connect()
        self.play_next()

    async def disconnect_channel(self):
        await self.CurrentConnection.disconnect()
        self.CurrentConnection = None

    def delete_file(self, filename):
        os.remove(filename)

    def play_next(self):
        if self.CurrentConnection is not None and not self.CurrentConnection.is_playing() and len(self.queue) > 0:
            to_play = self.queue.pop()
            self.CurrentConnection.play(discord.FFmpegPCMAudio(to_play),
                                        after=lambda e: self.delete_file(filename=to_play))
        if self.CurrentConnection is not None:
            self.loop.call_later(0.5, self.play_next)

    def abort_playback(self):
        self.CurrentConnection.stop()
        self.queue = []

    def play(self, file):
        self.CurrentConnection.play(file)

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith('!bye') and self.CurrentConnection is not None \
                and self.CurrentConnection.is_connected():
            await message.channel.send('Goodbye!')
            await self.disconnect_channel()

        if message.content.startswith("!lang"):
            await message.channel.send('Visit: {}'.format("https://sites.google.com/site/opti365/translate_codes"))

        if message.content.startswith("!abort"):
            self.abort_playback()

        if message.content.startswith(SAY_COMMAND):
            # if already connected ignore this
            if self.CurrentConnection is None:
                await self.join_channel(message.author.voice.channel)

            if self.CurrentConnection.channel != message.author.voice.channel:
                await self.disconnect_channel()
                await self.join_channel(message.author.voice.channel)

            # Create uuid as filename
            name = uuid.uuid1()
            # Get user input
            user_input = message.content[len(SAY_COMMAND):]
            if len(user_input) == 0 or (user_input[0] == ":" and user_input.find(" ") == -1):
                await message.channel.send('No text provided.')
            else:
                # Check for language tag,
                if user_input[0] == ":":
                    divider = user_input.find(" ")
                    lang = user_input[1:divider]
                    text = user_input[(divider + 1):]
                else:
                    lang = 'de'
                    text = user_input[1:]
                # Play the requested text
                try:
                    print(f"Create mp3 for text: {text} in {lang}")
                    filename = f'{DATA_FOLDER}/{name}.mp3'
                    tts = gTTS(text, lang=lang)
                    tts.save(filename)
                    self.queue.append(filename)
                    # self.play(discord.FFmpegPCMAudio(filename))
                except ValueError:
                    await message.channel.send(f"Language {lang} not supported.")


# Create new bot
client = TTSBot()
# run Bot with provided discord token
client.run(os.environ['TOKEN'])

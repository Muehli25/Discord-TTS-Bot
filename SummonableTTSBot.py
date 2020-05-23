import discord

from gtts import gTTS
import uuid
import os

from discord_token import TOKEN


class SummonableTTSBot(discord.Client):

    def __init__(self):
        super().__init__()
        self.CurrentConnection = None
        self.queue = []
        self.play_next()

    async def call_bot(self, channel):
        self.CurrentConnection = await channel.connect()

    async def goodbye_bot(self):
        await self.CurrentConnection.disconnect()
        self.CurrentConnection = None

    async def on_ready(self):
        print('Logged in as {0.user}'.format(client))

    def delete_file(self, filename):
        os.remove(filename)

    def play_next(self):
        if self.CurrentConnection is not None and not self.CurrentConnection.is_playing() and len(self.queue) > 0:
            to_play = self.queue.pop()
            self.CurrentConnection.play(discord.FFmpegPCMAudio(to_play),
                                        after=lambda e: self.delete_file(filename=to_play))
        self.loop.call_soon(self.play_next)

    def abort_playback(self):
        self.CurrentConnection.stop()
        self.queue = []

    def play(self, file):
        self.CurrentConnection.play(file)

    async def on_message(self, message):
        if message.author == self.user:
            return

        elif message.content == "!call":
            await message.channel.send('Hello!')
            await self.call_bot(message.author.voice.channel)

        elif message.content == '!bye' and self.CurrentConnection is not None \
                and self.CurrentConnection.is_connected():
            await message.channel.send('Goodbye!')
            await self.goodbye_bot()

        elif message.content == "!abort":
            self.abort_playback()

        else:
            lang = "de"
            user_input = message.content
            if user_input[0] == "+":
                divider = user_input.find(" ")
                lang = user_input[1:divider]
                text = user_input[(divider + 1):]
            else:
                text = user_input
            # Create uuid as filename
            name = uuid.uuid1()
            # Play the requested text
            try:
                filename = f'data/{name}.mp3'
                tts = gTTS(text, lang=lang)
                tts.save(filename)
                self.queue.append(filename)
            except ValueError:
                await message.channel.send(f"Language not supported or no Text provided.")


# Create new bot
client = SummonableTTSBot()
# run Bot with provided discord token
client.run(TOKEN)

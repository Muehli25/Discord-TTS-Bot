import discord

from gtts import gTTS
import uuid

from token import TOKEN


class TTSBot(discord.Client):
    CurrentVoiceChannel = None

    async def on_ready(self):
        print('We have logged in as {0.user}'.format(client))

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith(
                '!bye') and self.CurrentVoiceChannel is not None and self.CurrentVoiceChannel.is_connected():
            await self.CurrentVoiceChannel.disconnect()
            self.CurrentVoiceChannel = None

        if message.content.startswith("!say"):
            # if already connected ignore this
            if self.CurrentVoiceChannel is None:
                channel = message.author.voice.channel
                self.CurrentVoiceChannel = await channel.connect()
            name = uuid.uuid1()
            input = message.content[4:]
            if len(input) == 0:
                await message.channel.send('No text provided.')
            else:
                if input[0] == ":":
                    lang = input[1:3]
                    text = input[4:]
                else:
                    lang = 'en'
                    text = input
                self.parse_text_to_audio(name, text, lang)
                filename = 'data/{}.mp3'.format(name)
                self.CurrentVoiceChannel.play(discord.FFmpegPCMAudio(filename))

    def parse_text_to_audio(self, name, text, lang):
        print("Create mp3 for text: {} in {}".format(text,lang))
        tts = gTTS(text, lang=lang)
        tts.save('data/{}.mp3'.format(name))


client = TTSBot()
client.run(TOKEN)

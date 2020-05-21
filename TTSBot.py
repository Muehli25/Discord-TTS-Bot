import discord

from gtts import gTTS
import uuid

from discord_token import TOKEN


class TTSBot(discord.Client):
    CurrentVoiceChannel = None

    async def on_ready(self):
        print('Logged in as {0.user}'.format(client))

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith(
                '!bye') and self.CurrentVoiceChannel is not None and self.CurrentVoiceChannel.is_connected():
            await message.channel.send('Goodbye!')
            await self.CurrentVoiceChannel.disconnect()
            self.CurrentVoiceChannel = None

        if message.content.startswith("!say"):
            # if already connected ignore this
            if self.CurrentVoiceChannel is None:
                channel = message.author.voice.channel
                self.CurrentVoiceChannel = await channel.connect()
            # Create uuid as filename
            name = uuid.uuid1()
            # Get user input
            user_input = message.content[4:]
            if len(user_input) == 0:
                await message.channel.send('No text provided.')
            else:
                # Check for language tag,
                if user_input[0] == ":":
                    lang = user_input[1:3]
                    text = user_input[4:]
                else:
                    lang = 'en'
                    text = user_input[1:]
                # Play the requested text
                filename = 'data/{}.mp3'.format(name)
                self.parse_text_to_audio(filename, text, lang)
                self.CurrentVoiceChannel.play(discord.FFmpegPCMAudio(filename))

    @staticmethod
    def parse_text_to_audio(filename, text, lang):
        print("Create mp3 for text: {} in {}".format(text, lang))
        tts = gTTS(text, lang=lang)
        tts.save(filename)


# Create new bot
client = TTSBot()
# run Bot with provided discord token
client.run(TOKEN)

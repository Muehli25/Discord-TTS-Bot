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
            if len(user_input) == 0 or (user_input[0] == ":" and user_input.find(" ") == -1):
                await message.channel.send('No text provided.')
            else:
                # Check for language tag,
                if user_input[0] == ":":
                    divider = user_input.find(" ")
                    lang = user_input[1:divider]
                    text = user_input[(divider + 1):]
                else:
                    lang = 'en'
                    text = user_input[1:]
                # Play the requested text
                try:
                    print("Create mp3 for text: {} in {}".format(text, lang))
                    filename = 'data/{}.mp3'.format(name)
                    tts = gTTS(text, lang=lang)
                    tts.save(filename)
                    self.CurrentVoiceChannel.play(discord.FFmpegPCMAudio(filename))
                except ValueError:
                    await message.channel.send("Language {} not supported.".format(lang))


# Create new bot
client = TTSBot()
# run Bot with provided discord token
client.run(TOKEN)

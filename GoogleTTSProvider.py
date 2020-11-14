from gtts import gTTS


class GoogleTTSProvider:

    def create_audio_file(self, filename, language, text):
        tts = gTTS(text, lang=language)
        tts.save(filename)
        return

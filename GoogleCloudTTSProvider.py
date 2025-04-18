from google.cloud import texttospeech

class TTSProvider:
    def __init__(self):
        self.cloudTTSClient = texttospeech.TextToSpeechClient()

    def create_audio_file(self, filename, language, text, gender):
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language,
            ssml_gender=gender
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        response = self.cloudTTSClient.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        with open(filename, "wb") as out:
            out.write(response.audio_content)
        return
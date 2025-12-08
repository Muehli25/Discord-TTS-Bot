import unittest
from unittest.mock import MagicMock, patch
import os

# Set dummy credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/dev/null'

from GoogleCloudTTSProvider import TTSProvider
from google.cloud import texttospeech

class TestGoogleCloudTTSProvider(unittest.TestCase):
    def test_create_audio_file(self):
        # We need to ensure that the mock is applied BEFORE TTSProvider is instantiated
        # AND we need to be careful about how we patch it.
        # Since `GoogleCloudTTSProvider` imports `texttospeech` from `google.cloud`,
        # and then calls `texttospeech.TextToSpeechClient()`.

        # We should patch `google.cloud.texttospeech.TextToSpeechClient` globally.
        with patch('google.cloud.texttospeech.TextToSpeechClient') as MockClient:
            # Setup mock
            mock_client_instance = MockClient.return_value
            mock_response = MagicMock()
            mock_response.audio_content = b'fake_audio_content'
            mock_client_instance.synthesize_speech.return_value = mock_response

            provider = TTSProvider()
            filename = 'test_audio.mp3'
            text = 'Hello world'
            language = 'en-US'
            gender = texttospeech.SsmlVoiceGender.NEUTRAL

            # Run
            with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
                provider.create_audio_file(filename, language, text, gender)

                # Verify
                mock_client_instance.synthesize_speech.assert_called_once()
                args, kwargs = mock_client_instance.synthesize_speech.call_args
                input_arg = kwargs.get('input')
                voice_arg = kwargs.get('voice')
                audio_config_arg = kwargs.get('audio_config')

                self.assertEqual(input_arg.text, text)
                self.assertEqual(voice_arg.language_code, language)
                self.assertEqual(voice_arg.ssml_gender, gender)
                self.assertEqual(audio_config_arg.audio_encoding, texttospeech.AudioEncoding.MP3)

                mock_file.assert_called_once_with(filename, "wb")
                mock_file().write.assert_called_once_with(b'fake_audio_content')

if __name__ == '__main__':
    unittest.main()

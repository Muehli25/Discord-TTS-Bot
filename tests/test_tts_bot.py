import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys

# Mock discord before importing TTSBot
# We need to mock discord.Client and discord.Intents
sys_modules_patch = patch.dict('sys.modules', {'discord': MagicMock()})
sys_modules_patch.start()

import discord
# Setup mocks for discord objects
discord.Intents.default = MagicMock()
discord.Client = MagicMock

# IMPORTANT: We must also mock GoogleCloudTTSProvider BEFORE importing TTSBot
# because TTSBot imports it.
# However, TTSBot imports it as: `from GoogleCloudTTSProvider import TTSProvider`
# So we need to mock `GoogleCloudTTSProvider` in sys.modules so that import returns our mock.

mock_provider_module = MagicMock()
mock_provider_class = MagicMock()
mock_provider_module.TTSProvider = mock_provider_class

# Patch GoogleCloudTTSProvider module
sys_modules_patch_provider = patch.dict('sys.modules', {'GoogleCloudTTSProvider': mock_provider_module})
sys_modules_patch_provider.start()

# Now we can import TTSBot
from TTSBot import TTSBot

class TestTTSBotAsync(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Setup common mocks
        # Since we mocked the module, TTSBot.TTSProvider should be our mock_provider_class

        self.patcher_timer = patch('TTSBot.Timer')
        self.MockTimer = self.patcher_timer.start()
        # Ensure Timer returns a NEW mock each time it is instantiated
        self.MockTimer.side_effect = lambda *args, **kwargs: MagicMock()

        self.patcher_ffmpeg = patch('discord.FFmpegPCMAudio')
        self.MockFFmpeg = self.patcher_ffmpeg.start()

        self.patcher_os_path_exists = patch('os.path.exists', return_value=True)
        self.patcher_os_path_exists.start()

        # Create bot instance
        self.bot = TTSBot()
        self.bot.loop = MagicMock()
        self.bot.user = MagicMock()
        self.bot.user.id = 12345

        # Manually set loop for call_later
        self.bot.loop.call_later = MagicMock()

    def tearDown(self):
        self.patcher_timer.stop()
        self.patcher_ffmpeg.stop()
        self.patcher_os_path_exists.stop()

    def test_init(self):
        self.assertEqual(self.bot.language, "en")
        self.assertIsNone(self.bot.CurrentConnection)
        self.assertTrue(self.bot.queue.empty())
        pass

    async def test_call_bot(self):
        channel = AsyncMock()
        connection = MagicMock()
        channel.connect.return_value = connection

        await self.bot.call_bot(channel)

        channel.connect.assert_called_once()
        self.assertEqual(self.bot.CurrentConnection, connection)

    async def test_on_message_ignore_self(self):
        message = MagicMock()
        message.author = self.bot.user

        await self.bot.on_message(message)

        # Should do nothing
        self.assertIsNone(self.bot.current_text_channel)

    async def test_on_message_call(self):
        message = MagicMock()
        message.content = "!call"
        message.author.voice.channel = AsyncMock()
        message.channel = AsyncMock()

        # We need to mock call_bot as it's an async method on the bot
        with patch.object(self.bot, 'call_bot', new_callable=AsyncMock) as mock_call_bot:
            with patch.object(self.bot, 'send_text_message', new_callable=AsyncMock) as mock_send_msg:
                with patch.object(self.bot, 'start_timeout') as mock_start_timeout:
                     await self.bot.on_message(message)

                     self.assertEqual(self.bot.current_text_channel, message.channel)
                     mock_send_msg.assert_called_with('Hello!')
                     mock_call_bot.assert_called_with(message.author.voice.channel)
                     mock_start_timeout.assert_called_once()

    async def test_on_message_bye(self):
        message = MagicMock()
        message.content = "!bye"

        # Setup connection
        self.bot.CurrentConnection = MagicMock()
        self.bot.CurrentConnection.is_connected.return_value = True

        with patch.object(self.bot, 'goodbye_bot', new_callable=AsyncMock) as mock_goodbye:
            await self.bot.on_message(message)
            mock_goodbye.assert_called_once()

    async def test_on_message_abort(self):
        message = MagicMock()
        message.content = "!abort"

        with patch.object(self.bot, 'abort_playback') as mock_abort:
            await self.bot.on_message(message)
            mock_abort.assert_called_once()

    async def test_on_message_tts(self):
        message = MagicMock()
        message.content = "Hello there"
        message.author = MagicMock()
        message.author.name = "User"

        # Setup connection
        self.bot.CurrentConnection = MagicMock()
        self.bot.CurrentConnection.is_connected.return_value = True

        with patch.object(self.bot, 'reset_timeout') as mock_reset_timeout:
             with patch('uuid.uuid1', return_value='test_uuid'):
                with patch('builtins.print'): # Suppress print
                    await self.bot.on_message(message)

                    mock_reset_timeout.assert_called_once()
                    self.bot.TTSProvider.create_audio_file.assert_called()

                    # Verify queue
                    self.assertFalse(self.bot.queue.empty())
                    item = self.bot.queue.get()
                    self.assertEqual(item, 'data/test_uuid.mp3')

    async def test_on_message_change_gender(self):
        message = MagicMock()
        # Setup connection
        self.bot.CurrentConnection = MagicMock()
        self.bot.CurrentConnection.is_connected.return_value = True

        from google.cloud import texttospeech

        # Test !male
        message.content = "!male"
        await self.bot.on_message(message)
        self.assertEqual(self.bot.gender, texttospeech.SsmlVoiceGender.MALE)

        # Test !female
        message.content = "!female"
        await self.bot.on_message(message)
        self.assertEqual(self.bot.gender, texttospeech.SsmlVoiceGender.FEMALE)

        # Test !neutral
        message.content = "!neutral"
        await self.bot.on_message(message)
        self.assertEqual(self.bot.gender, texttospeech.SsmlVoiceGender.NEUTRAL)

    def test_play_next(self):
        self.bot.CurrentConnection = MagicMock()
        self.bot.CurrentConnection.is_playing.return_value = False
        self.bot.queue.put("test_file.mp3")

        self.bot.play_next()

        self.bot.CurrentConnection.play.assert_called_once()
        # Check if call_later was called to schedule next check
        self.bot.loop.call_later.assert_called_with(0.5, self.bot.play_next)

    def test_abort_playback(self):
        self.bot.CurrentConnection = MagicMock()
        self.bot.queue.put("file1.mp3")
        self.bot.queue.put("file2.mp3")

        with patch('TTSBot.clean_data_folder') as mock_clean:
            with patch('TTSBot.delete_file') as mock_delete:
                self.bot.abort_playback()

                self.bot.CurrentConnection.stop.assert_called_once()
                self.assertTrue(self.bot.queue.empty())
                self.assertEqual(mock_delete.call_count, 2)
                mock_clean.assert_called_once()

    def test_timeout_logic(self):
        # start_timeout
        self.bot.start_timeout()
        self.MockTimer.assert_called_with(1200, self.bot.timeout_callback)
        self.assertIsNotNone(self.bot.timer)

        # Reset mock calls count to avoid confusion
        self.bot.timer.cancel.reset_mock()

        # reset_timeout
        # We need to ensure bot.timer is set (it is from start_timeout)
        old_timer = self.bot.timer
        self.bot.reset_timeout()

        old_timer.cancel.assert_called_once()
        # self.MockTimer is called twice now (once in start_timeout, once in reset_timeout)
        self.assertEqual(self.MockTimer.call_count, 2)

        # stop_timeout
        timer_instance = self.bot.timer
        # stop_timeout calls cancel() on the current timer
        # The current timer is the one created in reset_timeout
        timer_instance.cancel.reset_mock()
        self.bot.stop_timeout()
        timer_instance.cancel.assert_called_once()

    async def test_goodbye_bot(self):
        self.bot.current_text_channel = AsyncMock()
        self.bot.CurrentConnection = AsyncMock()
        # Make sure disconnect is a coroutine or something awaitable if it's awaited in code
        self.bot.CurrentConnection.disconnect.return_value = None

        connection = self.bot.CurrentConnection

        with patch('TTSBot.clean_data_folder') as mock_clean:
            with patch.object(self.bot, 'stop_timeout') as mock_stop_timeout:
                await self.bot.goodbye_bot()

                self.bot.current_text_channel.send.assert_called_with('Goodbye!')
                connection.disconnect.assert_called_once()
                self.assertIsNone(self.bot.CurrentConnection)
                self.assertTrue(self.bot.queue.empty())
                mock_clean.assert_called_once()
                mock_stop_timeout.assert_called_once()

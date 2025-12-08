import unittest
import asyncio
from unittest.mock import MagicMock
from Timer import Timer

class TestTimer(unittest.TestCase):
    def test_timer_callback(self):
        callback = MagicMock()
        async def async_callback():
            callback()

        # We need to run the timer in an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        timer = Timer(0.1, async_callback)

        loop.run_until_complete(asyncio.sleep(0.2))

        callback.assert_called_once()
        loop.close()

    def test_timer_cancel(self):
        callback = MagicMock()
        async def async_callback():
            callback()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        timer = Timer(0.2, async_callback)
        loop.run_until_complete(asyncio.sleep(0.1))
        timer.cancel()
        loop.run_until_complete(asyncio.sleep(0.2))

        callback.assert_not_called()
        loop.close()

if __name__ == '__main__':
    unittest.main()

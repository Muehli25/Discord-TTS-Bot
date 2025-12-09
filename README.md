# Discord-TTS-Bot

## TTSBot

Simple Text-to-Speech Bot that uses Google TTS or Google Cloud TTS

### Usage

Add your token as an ENV Variable called `TOKEN`

#### Commands

| Command  | Description |
| ------------- | ------------- |
| !call  | Summon the bot to your current voice channel |
| !bye  | Dismiss the bot from the current channel |
| !abort | Abort current playback (useful for long texts) |
| +en text | Read the next text in the specified language, in this case english. |

#### Languages

Using the CloudTTS nearly all ISO 639-1 languages can be used.

With the environmental variable `LANG`, the default language can be set.

### Docker

```
docker build -t ttsbot .

docker run -e TOKEN="YOUR-TOKEN" ttsbot
```

### Google Cloud TTS

```
docker build -t ttsbot .

docker run -e TOKEN="YOUR-TOKEN" -e GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"  ttsbot
```

### Running Tests

To run the tests, you need to install the development dependencies:

```bash
pip install -r requirements.txt
pip install coverage pytest pytest-asyncio
```

Then you can run the tests using `pytest`:

```bash
pytest
```

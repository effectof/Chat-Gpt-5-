import os
import openai
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if TELEGRAM_TOKEN is None:
    raise ValueError("TELEGRAM_TOKEN не установлен в переменных окружения")

if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY не установлен в переменных окружения")

openai.api_key = OPENAI_API_KEY

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_text(message: types.Message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": message.text}],
            temperature=0.7
        )
        answer = response.choices[0].message["content"]
        await message.reply(answer)
    except Exception as e:
        await message.reply(f"Ошибка: {e}")

@dp.message_handler(content_types=types.ContentType.VOICE)
async def handle_voice(message: types.Message):
    try:
        file = await bot.get_file(message.voice.file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file.file_path}"

        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as resp:
                voice_bytes = await resp.read()

        temp_path = f"/tmp/voice_{message.message_id}.ogg"
        with open(temp_path, "wb") as f:
            f.write(voice_bytes)

        with open(temp_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)

        recognized_text = transcript["text"]

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": recognized_text}],
            temperature=0.7
        )
        answer = response.choices[0].message["content"]

        await message.reply(f"🗣 Вы сказали: {recognized_text}\n\n💬 Ответ: {answer}")

    except Exception as e:
        await message.reply(f"Ошибка при обработке голосового: {e}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

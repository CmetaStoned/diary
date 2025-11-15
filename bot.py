import asyncio
import traceback
from aiogram import Bot, Dispatcher, F
from aiogram.types import ReplyKeyboardRemove, Message
from datetime import datetime, timedelta
from scripts.code10 import load_env_with_password
from scripts.code20 import encrypt_and_store_entry

TOKEN = "8321721543:AAE6aeMspggYYyuD8jcFPnLP-MD4ahnlJYM"

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}

# Храним пароль и время последнего ввода
user_passwords = {}

@dp.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    now = datetime.now()

    # Если у пользователя уже есть запись и мы ждём пароль
    if user_id in user_data and "entry" in user_data[user_id]:
        entry = user_data[user_id]["entry"]
        timestamp = user_data[user_id]["timestamp"]

        # Проверяем, есть ли сохранённый пароль и не прошло ли 3 часа
        if user_id in user_passwords and now - user_passwords[user_id]["time"] < timedelta(hours=3):
            password = user_passwords[user_id]["password"]
        else:
            # Сохраняем новый пароль
            password = message.text
            user_passwords[user_id] = {"password": password, "time": now}

        env = load_env_with_password(password)
        encrypt_and_store_entry(timestamp, entry, env)

        # Удаляем сообщение пользователя
        await message.delete()

        # Удаляем сообщение "Контроль"
        control_msg_id = user_data[user_id].get("control_msg_id")
        if control_msg_id:
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=control_msg_id)
            except Exception as e:
                print(f"Не удалось удалить сообщение 'Контроль': {e}")

        # Отправляем финальное сообщение
        await message.answer(f"Запись сохранена: <b>{timestamp}</b>", reply_markup=ReplyKeyboardRemove())

        # Чистим данные
        user_data.pop(user_id)

    else:
        entry = message.text
        timestamp = now.strftime("%d.%m.%Y %H:%M")

        # Удаляем сообщение пользователя
        await message.delete()

        # Проверяем, есть ли свежий пароль
        if user_id in user_passwords and now - user_passwords[user_id]["time"] < timedelta(hours=3):
            password = user_passwords[user_id]["password"]
            env = load_env_with_password(password)
            encrypt_and_store_entry(timestamp, entry, env)

            await message.answer(f"Запись сохранена: <b>{timestamp}</b>", reply_markup=ReplyKeyboardRemove())
        else:
            # Отправляем "Контроль" и сохраняем его ID
            control_msg = await message.answer("Контроль")
            user_data[user_id] = {
                "entry": entry,
                "timestamp": timestamp,
                "control_msg_id": control_msg.message_id
            }

async def main():
    try:
        print("Бот запущен")
        await dp.start_polling(bot)
    except Exception as e:
        print("Ошибка при завершении работы:")
        traceback.print_exc()
    finally:
        await bot.session.close()
        print("Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Остановка по Ctrl+C")
    except Exception as e:
        print("Глобальная ошибка:")
        traceback.print_exc()

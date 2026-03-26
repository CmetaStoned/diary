import os
import asyncio
import traceback
from aiohttp import web  # Добавили импорт для веб-заглушки
from aiogram import Bot, Dispatcher, F
from aiogram.types import ReplyKeyboardRemove, Message
from datetime import datetime, timedelta
from scripts.code10 import load_env_with_password
from scripts.code20 import encrypt_and_store_entry

# Достаем токен из переменных окружения сервера
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Токен не найден! Укажи BOT_TOKEN в переменных окружения.")

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}
user_passwords = {}


async def handle_ping(request):
    return web.Response(text="Бот дневника работает 24/7!")



@dp.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    now = datetime.now()

    # Если ждём пароль
    if user_id in user_data and "entry" in user_data[user_id]:
        entry = user_data[user_id]["entry"]
        timestamp = user_data[user_id]["timestamp"]

        if user_id in user_passwords and now - user_passwords[user_id]["time"] < timedelta(hours=3):
            password = user_passwords[user_id]["password"]
        else:
            password = message.text
            user_passwords[user_id] = {"password": password, "time": now}

        # ЗАЩИТА ОТ КРИВОГО ПАРОЛЯ
        try:
            env = load_env_with_password(str(password))
            encrypt_and_store_entry(timestamp, entry, env)
        except Exception as e:
            print(f"Ошибка расшифровки: {e}")
            user_passwords.pop(user_id, None) # Удаляем неверный пароль из памяти
            await message.answer("Неверный пароль")
            user_data.pop(user_id, None)
            return

        await message.delete()

        control_msg_id = user_data[user_id].get("control_msg_id")
        if control_msg_id:
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=control_msg_id)
            except Exception:
                pass

        await message.answer(f"Запись сохранена: <b>{timestamp}</b>", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
        user_data.pop(user_id)

    else:
        entry = message.text
        timestamp = now.strftime("%d.%m.%Y %H:%M")
        await message.delete()

        if user_id in user_passwords and now - user_passwords[user_id]["time"] < timedelta(hours=3):
            password = user_passwords[user_id]["password"]
            
            # ТУТ ТОЖЕ ЗАЩИТА ДЛЯ СОХРАНЕННОГО ПАРОЛЯ
            try:
                env = load_env_with_password(password)
                encrypt_and_store_entry(timestamp, str(entry), env)
                print(f'Добавлена запись: [{timestamp}]')
                await message.answer(f"Запись сохранена: <b>{timestamp}</b>", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
            except Exception as e:
                print(f"Ошибка кэша: {e}")
                user_passwords.pop(user_id, None)
                await message.answer("❌ Сохраненный пароль слетел. Отправь запись заново.")
        else:
            control_msg = await message.answer("Контроль")
            user_data[user_id] = {
                "entry": entry,
                "timestamp": timestamp,
                "control_msg_id": control_msg.message_id
            }

async def main():
    # --- НАСТРОЙКА И ЗАПУСК ВЕБ-ЗАГЛУШКИ ---
    app = web.Application()
    app.router.add_get('/', handle_ping)
    
    # Render передает свой порт, если его нет — используем 10000
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Веб-заглушка запущена на порту {port}")
    # --- КОНЕЦ НАСТРОЙКИ ---

    try:
        print("Бот запущен")
        await dp.start_polling(bot)
    except Exception:
        print("Ошибка при завершении работы:")
        traceback.print_exc()
    finally:
        await bot.session.close()
        await runner.cleanup()  # Важно: закрываем веб-сервер при выключении бота
        print("Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Остановка по Ctrl+C")
    except Exception:
        print("Глобальная ошибка:")
        traceback.print_exc()
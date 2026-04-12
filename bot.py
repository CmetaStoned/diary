import os
import asyncio
import traceback
from zoneinfo import ZoneInfo
from aiohttp import web  
from aiogram import Bot, Dispatcher, F
from aiogram.types import ReplyKeyboardRemove, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from scripts.code10 import load_env_with_password
from scripts.code20 import encrypt_and_store_entry
import base64
from io import BytesIO


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Токен не найден! Укажи BOT_TOKEN в переменных окружения.")

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()


user_data = {}
user_passwords = {}

class RemainderStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_time = State()


async def handle_ping(request):
    return web.Response(text="Бот дневника работает 24/7!")


async def send_reminder(bot: Bot, chat_id: int, text: str):
    await bot.send_message(chat_id, f"Напоминание: {text}")


@dp.message(Command('remind'))
async def cmd_remind(message: Message, state: FSMContext):
    remind_question = await message.answer('Напоминание?')
    await state.set_state(RemainderStates.waiting_for_text)
    await state.update_data(remind_quest = remind_question.message_id)

@dp.message(RemainderStates.waiting_for_text)
async def process_text(message:Message, state:FSMContext):
    data = await state.get_data()
    await bot.delete_message(chat_id=message.chat.id,
    message_id= data.get("remind_quest"))
    await message.delete()
    await state.update_data(remind_text=message.text)
    await message.answer('Через сколько минут напомнить?')
    await state.set_state(RemainderStates.waiting_for_time)

@dp.message(RemainderStates.waiting_for_time)
async def process_time(message:Message, state:FSMContext):
    minutes = int(message.text)
    data = await state.get_data()
    text = data.get("remind_text")

    run_time = datetime.now(ZoneInfo("Asia/Jerusalem")) + timedelta(minutes=minutes)

    scheduler.add_job(
        send_reminder,
        trigger='date',
        run_date=run_time,
        kwargs={"bot": bot, "chat_id": message.chat.id, "text": text}
    )

    await message.answer("Напомню!")
    await state.clear()

@dp.message(F.text | F.photo)
async def handle_message(message: Message):
    user_id = message.from_user.id
    now = datetime.now(ZoneInfo("Asia/Jerusalem"))

    # ЕСЛИ ЖДЕМ ПАРОЛЬ
    if user_id in user_data and "entry" in user_data[user_id]:
        entry = user_data[user_id]["entry"]
        timestamp = user_data[user_id]["timestamp"]
        img = user_data[user_id].get("img")  
        if user_id in user_passwords and now - user_passwords[user_id]["time"] < timedelta(hours=3):
            password = user_passwords[user_id]["password"]
        else:
            password = message.text
            user_passwords[user_id] = {"password": password, "time": now}

        try:
            env = load_env_with_password(str(password))
            
            safe_entry = str(entry) if entry else ""
            encrypt_and_store_entry(timestamp, safe_entry, img, env) 
        except Exception as e:
            print(f"Ошибка расшифровки: {e}")
            user_passwords.pop(user_id, None)
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

    # ЕСЛИ ЭТО НОВАЯ ЗАПИСЬ
    else:
        entry = message.text if message.text else message.caption 
        img = None  
        if message.photo:
            img1 = message.photo[-1]
            file_in_memory = BytesIO()
            file_info = await bot.get_file(img1.file_id)
            await bot.download_file(file_info.file_path, file_in_memory)
            image_bytes = file_in_memory.getvalue()
            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            img = f"data:image/jpeg;base64,{base64_string}"
            
        timestamp = now.strftime("%d.%m.%Y %H:%M")
        await message.delete()

        if user_id in user_passwords and now - user_passwords[user_id]["time"] < timedelta(hours=3):
            password = user_passwords[user_id]["password"]
            
            try:
                env = load_env_with_password(password)
                safe_entry = str(entry) if entry else ""
                encrypt_and_store_entry(timestamp, safe_entry, img, env)
                print(f'Добавлена запись: [{timestamp}]')
                await message.answer(f"Запись сохранена: <b>{timestamp}</b>", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
            except Exception as e:
                print(f"Ошибка кэша: {e}")
                user_passwords.pop(user_id, None)
                await message.answer("Сохраненный пароль слетел. Отправь запись заново.")
        else:
            control_msg = await message.answer("Введи пароль для сохранения:")
            user_data[user_id] = {
                "entry": str(entry) if entry else "",  
                "timestamp": timestamp,
                "img": img,  
                "control_msg_id": control_msg.message_id
            }

async def main():
    # НАСТРОЙКА И ЗАПУСК ЗАГЛУШКИ ДЛЯ ХОСТА 
    app = web.Application()
    app.router.add_get('/', handle_ping)
    
    # Render передает свой порт, если его нет — используем 10000
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Веб-заглушка запущена на порту {port}")
    # КОНЕЦ НАСТРОЙКИ 

    scheduler.start()

    try:
        print("Бот запущен")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception:
        print("Ошибка при завершении работы:")
        traceback.print_exc()
    finally:
        await bot.session.close()
        await runner.cleanup()  # закрываем веб-сервер при выключении бота
        print("Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Остановка по Ctrl+C")
    except Exception:
        print("Глобальная ошибка:")
        traceback.print_exc()
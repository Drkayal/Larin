import random
import time
import requests
import config
from ZeMusic import app

from pyrogram.enums import ChatAction, ParseMode
from pyrogram import filters


async def log_gpt_usage(user_id: int, chat_id: int, question: str, success: bool):
    """تسجيل استخدام وظيفة GPT"""
    try:
        if config.DATABASE_TYPE == "postgresql":
            from ZeMusic.core.postgres import execute_query
            await execute_query(
                "INSERT INTO activity_logs (user_id, chat_id, activity_type, details, created_at) "
                "VALUES ($1, $2, $3, $4, NOW())",
                user_id,
                chat_id,
                "gpt_usage",
                f"Question: {question[:50]}... | Success: {success}"
            )
        else:
            # MongoDB fallback
            from ZeMusic.misc import mongodb
            await mongodb.activity_logs.insert_one({
                "user_id": user_id,
                "chat_id": chat_id,
                "activity_type": "gpt_usage",
                "details": f"Question: {question[:50]}... | Success: {success}",
                "created_at": "now"
            })
    except Exception as e:
        print(f"خطأ في تسجيل استخدام GPT: {e}")

@app.on_message(filters.command(["رون"],""))
async def chat_gpt(bot, message):
    try:
        start_time = time.time()
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        if len(message.command) < 2:
            await message.reply_text(
                "⟡ استخدم الأمر هكذا :\n\n ⟡ رون + سؤالك"
            )
        else:
            a = message.text.split(' ', 1)[1]
            response = requests.get(f'https://chatgpt.apinepdev.workers.dev/?question={a}')

            try:
                # Check if "results" key is present in the JSON response
                if "answer" in response.json():
                    x = response.json()["answer"]
                    end_time = time.time()
                    telegram_ping = str(round((end_time - start_time) * 1000, 3)) + " ms"
                    await message.reply_text(
                        f" {x} ",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    
                    # تسجيل الاستخدام الناجح
                    await log_gpt_usage(message.from_user.id, message.chat.id, a, True)
                else:
                    await message.reply_text("لم يتم العثور على النتائج في الاستجابة.")
                    # تسجيل الاستخدام الفاشل
                    await log_gpt_usage(message.from_user.id, message.chat.id, a, False)
            except KeyError:
                # Handle any other KeyError that might occur
                await message.reply_text("حدث خطأ أثناء الوصول إلى الاستجابة.")
                # تسجيل الاستخدام الفاشل
                await log_gpt_usage(message.from_user.id, message.chat.id, a, False)
    except Exception as e:
        await message.reply_text(f"**á´‡Ê€Ê€á´Ê€: {e} ")
        # تسجيل الاستخدام الفاشل
        if len(message.command) >= 2:
            question = message.text.split(' ', 1)[1]
            await log_gpt_usage(message.from_user.id, message.chat.id, question, False)

from pyrogram import filters, Client
from ZeMusic import app
import asyncio
import config
from pyrogram.types import VideoChatEnded, Message
from pytgcalls import PyTgCalls
# from pytgcalls.types.stream import MediaStream
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from ZeMusic.core.call import Mody
from ZeMusic.utils.database import *
from pytgcalls.exceptions import (NoActiveGroupCall,TelegramServerError,AlreadyJoinedError)


async def log_call_participants_check(chat_id: int, user_id: int, participants_count: int):
    """تسجيل فحص المشاركين في المكالمة"""
    try:
        if config.DATABASE_TYPE == "postgresql":
            from ZeMusic.core.postgres import execute_query
            await execute_query(
                "INSERT INTO activity_logs (user_id, chat_id, activity_type, details, created_at) "
                "VALUES ($1, $2, $3, $4, NOW())",
                user_id,
                chat_id,
                "call_participants_check",
                f"Checked call participants: {participants_count} users"
            )
        else:
            # MongoDB fallback
            from ZeMusic.misc import mongodb
            await mongodb.activity_logs.insert_one({
                "user_id": user_id,
                "chat_id": chat_id,
                "activity_type": "call_participants_check",
                "details": f"Checked call participants: {participants_count} users",
                "created_at": "now"
            })
    except Exception as e:
        print(f"خطأ في تسجيل فحص المشاركين في المكالمة: {e}")

@app.on_message(filters.regex("^(مين في الكول|من في الكول|من بالمكالمه|من بالمكالمة|من في المكالمه|من في المكالمة|الصاعدين)$"))
async def strcall(client, message):
    assistant = await group_assistant(Mody,message.chat.id)
    try:
        await assistant.join_group_call(message.chat.id, AudioPiped("./ZeMusic/assets/call.mp3"))
        text="<b>الموجودين في المكالمه 🚶🏻 :</b>\n\n"
        participants = await assistant.get_participants(message.chat.id)
        k =0
        for participant in participants:
            info = participant
            if info.muted == False:
                mut="يتحدث 🗣 "
            else:
                mut="ساكت 🔕 "
            user = await client.get_users(participant.user_id)
            k +=1
            text +=f"{k} - {user.mention} : {mut}\n"
        text += f"\n<b>عددهم :</b> {len(participants)}"    
        await message.reply(f"{text}")
        
        # تسجيل النشاط
        await log_call_participants_check(message.chat.id, message.from_user.id, len(participants))
        
        await asyncio.sleep(7)
        await assistant.leave_group_call(message.chat.id)
    except NoActiveGroupCall:
        await message.reply(f"المكالمه ليست مفتوح")
    except TelegramServerError:
        await message.reply(f"ابعت الامر تاني في مشكله في سيرفر التليجرام")
    except AlreadyJoinedError:
        text="<b>الموجودين في المكالمه 🚶🏻 :</b>\n\n"
        participants = await assistant.get_participants(message.chat.id)
        k =0
        for participant in participants:
            info = participant
            if info.muted == False:
                mut="يتحدث 🗣"
            else:
                mut="ساكت 🔕 "
            user = await client.get_users(participant.user_id)
            k +=1
            text +=f"{k} - {user.mention} : {mut}\n"
        text += f"\n<b>عددهم :</b> {len(participants)}"    
        await message.reply(f"{text}")
        
        # تسجيل النشاط
        await log_call_participants_check(message.chat.id, message.from_user.id, len(participants))

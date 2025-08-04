from pyrogram import filters
from pyrogram.types import Message

import config
from ZeMusic import app
from ZeMusic.utils.database import get_loop, set_loop
from ZeMusic.utils.decorators import AdminRightsCheck
from ZeMusic.utils.inline import close_markup
from config import BANNED_USERS


async def log_loop_change(chat_id: int, admin_id: int, old_value: int, new_value: int):
    """تسجيل تغييرات إعدادات التكرار في قاعدة البيانات"""
    try:
        if config.DATABASE_TYPE == "postgresql":
            from ZeMusic.core.postgres import execute_query
            await execute_query(
                "INSERT INTO activity_logs (user_id, chat_id, activity_type, details, created_at) "
                "VALUES ($1, $2, $3, $4, NOW())",
                admin_id,
                chat_id,
                "loop_setting_changed",
                f"Loop changed from {old_value} to {new_value}"
            )
        else:
            # MongoDB fallback
            from ZeMusic.misc import mongodb
            await mongodb.activity_logs.insert_one({
                "user_id": admin_id,
                "chat_id": chat_id,
                "activity_type": "loop_setting_changed",
                "details": f"Loop changed from {old_value} to {new_value}",
                "created_at": "now"
            })
    except Exception as e:
        print(f"خطأ في تسجيل تغيير إعدادات التكرار: {e}")


@app.on_message(filters.command(["loop", "cloop", "تكرار", "التكرار"],"") & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def admins(cli, message: Message, _, chat_id):
    usage = _["admin_17"]
    if len(message.command) != 2:
        return await message.reply_text(usage)
    state = message.text.split(None, 1)[1].strip()
    if state.isnumeric():
        state = int(state)
        if 1 <= state <= 10:
            got = await get_loop(chat_id)
            if got != 0:
                state = got + state
            if int(state) > 10:
                state = 10
            old_loop = await get_loop(chat_id)
            await set_loop(chat_id, state)
            
            # تسجيل تغيير الإعدادات
            await log_loop_change(chat_id, message.from_user.id, old_loop, state)
            
            return await message.reply_text(
                text=_["admin_18"].format(state, message.from_user.mention),
                reply_markup=close_markup(_),
            )
        else:
            return await message.reply_text(_["admin_17"])
    elif state.lower() == "enable" or state == "تفعيل":
        old_loop = await get_loop(chat_id)
        await set_loop(chat_id, 10)
        
        # تسجيل تغيير الإعدادات
        await log_loop_change(chat_id, message.from_user.id, old_loop, 10)
        
        return await message.reply_text(
            text=_["admin_18"].format(state, message.from_user.mention),
            reply_markup=close_markup(_),
        )
    elif state.lower() == "disable" or state == "تعطيل":
        old_loop = await get_loop(chat_id)
        await set_loop(chat_id, 0)
        
        # تسجيل تغيير الإعدادات
        await log_loop_change(chat_id, message.from_user.id, old_loop, 0)
        
        return await message.reply_text(
            _["admin_19"].format(message.from_user.mention),
            reply_markup=close_markup(_),
        )
    else:
        return await message.reply_text(usage)

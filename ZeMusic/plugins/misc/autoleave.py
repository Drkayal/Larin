import asyncio
from datetime import datetime

from pyrogram.enums import ChatType

import config
from ZeMusic import app
from ZeMusic.core.call import Mody, autoend
from ZeMusic.utils.database import get_client, is_active_chat, is_autoend


async def get_auto_leave_setting():
    """جلب إعداد المغادرة التلقائية من قاعدة البيانات"""
    try:
        if config.DATABASE_TYPE == "postgresql":
            from ZeMusic.core.postgres import fetch_value
            status = await fetch_value(
                "SELECT value FROM system_settings WHERE key = 'auto_leaving_assistant'"
            )
            return status == 'true' if status else config.AUTO_LEAVING_ASSISTANT
        else:
            # MongoDB fallback
            from ZeMusic.misc import mongodb
            result = await mongodb.settings.find_one({"key": "auto_leaving_assistant"})
            return result.get("value", config.AUTO_LEAVING_ASSISTANT) if result else config.AUTO_LEAVING_ASSISTANT
    except:
        return config.AUTO_LEAVING_ASSISTANT


async def set_auto_leave_setting(status: bool):
    """حفظ إعداد المغادرة التلقائية في قاعدة البيانات"""
    try:
        if config.DATABASE_TYPE == "postgresql":
            from ZeMusic.core.postgres import execute_query
            await execute_query(
                "INSERT INTO system_settings (key, value) VALUES ($1, $2) "
                "ON CONFLICT (key) DO UPDATE SET value = $2",
                "auto_leaving_assistant", 
                "true" if status else "false"
            )
        else:
            # MongoDB fallback
            from ZeMusic.misc import mongodb
            await mongodb.settings.update_one(
                {"key": "auto_leaving_assistant"},
                {"$set": {"value": status}},
                upsert=True
            )
    except Exception as e:
        print(f"خطأ في حفظ إعداد المغادرة التلقائية: {e}")


async def auto_leave():
    while not await asyncio.sleep(1500):
        # التحقق من إعداد المغادرة التلقائية من قاعدة البيانات
        auto_leave_enabled = await get_auto_leave_setting()
        if auto_leave_enabled:
            from ZeMusic.core.userbot import assistants

            for num in assistants:
                client = await get_client(num)
                left = 0
                try:
                    async for i in client.get_dialogs():
                        if i.chat.type in [
                            ChatType.SUPERGROUP,
                            ChatType.GROUP,
                            ChatType.CHANNEL,
                        ]:
                            if (
                                i.chat.id != config.LOGGER_ID
                                and i.chat.id != -1001426097254
                                and i.chat.id != -1001583360745
                            ):
                                if left == 20:
                                    continue
                                if not await is_active_chat(i.chat.id):
                                    try:
                                        await client.leave_chat(i.chat.id)
                                        left += 1
                                    except:
                                        continue
                except:
                    pass


# أمر للتحكم في المغادرة التلقائية
from pyrogram import filters
from pyrogram.types import Message
from ZeMusic.misc import SUDOERS
from ZeMusic.utils.decorators.language import language


@app.on_message(filters.command(["autoleave", "مغادرة_تلقائية", "المغادرة_التلقائية"]) & SUDOERS)
@language
async def toggle_auto_leave(client, message: Message, _):
    """تفعيل/تعطيل المغادرة التلقائية للمساعدين"""
    if len(message.command) != 2:
        current_status = await get_auto_leave_setting()
        status_text = "مفعلة" if current_status else "معطلة"
        return await message.reply_text(
            f"🔄 **حالة المغادرة التلقائية:** {status_text}\n\n"
            f"**الاستخدام:**\n"
            f"├ `/autoleave تفعيل` - لتفعيل المغادرة التلقائية\n"
            f"└ `/autoleave تعطيل` - لتعطيل المغادرة التلقائية"
        )
    
    state = message.text.split(None, 1)[1].strip().lower()
    
    if state in ["تفعيل", "enable", "on", "true"]:
        await set_auto_leave_setting(True)
        await message.reply_text(
            "✅ **تم تفعيل المغادرة التلقائية بنجاح!**\n\n"
            "🤖 **المساعدين سيغادرون المجموعات غير النشطة تلقائياً كل 25 دقيقة.**\n"
            "💾 **الإعداد محفوظ في قاعدة البيانات.**"
        )
    elif state in ["تعطيل", "disable", "off", "false"]:
        await set_auto_leave_setting(False)
        await message.reply_text(
            "❌ **تم تعطيل المغادرة التلقائية بنجاح!**\n\n"
            "🤖 **المساعدين لن يغادروا المجموعات تلقائياً.**\n"
            "💾 **الإعداد محفوظ في قاعدة البيانات.**"
        )
    else:
        await message.reply_text(
            "❌ **خيار غير صحيح!**\n\n"
            "**الاستخدام:**\n"
            "├ `/autoleave تفعيل` - لتفعيل المغادرة التلقائية\n"
            "└ `/autoleave تعطيل` - لتعطيل المغادرة التلقائية"
        )


asyncio.create_task(auto_leave())

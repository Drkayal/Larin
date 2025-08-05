import asyncio
import importlib

# Apply compatibility patch before importing pytgcalls
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ntgcalls_patch

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from ZeMusic import LOGGER, app, userbot
from ZeMusic.core.call import Mody
from ZeMusic.misc import sudo
from ZeMusic.plugins import ALL_MODULES
from ZeMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS

# إضافة دعم PostgreSQL
if config.DATABASE_TYPE == "postgresql":
    from ZeMusic.core.postgres import init_postgres, close_postgres
    from ZeMusic.database.setup import setup_database
    from ZeMusic.database.migrations import run_migrations


async def init():
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error("Assistant client variables not defined, exiting...")
        exit()
    
    # إعداد قاعدة البيانات
    if config.DATABASE_TYPE == "postgresql":
        LOGGER(__name__).info("إعداد قاعدة بيانات PostgreSQL...")
        
        # إعداد قاعدة البيانات
        if not await setup_database():
            LOGGER(__name__).error("فشل في إعداد قاعدة البيانات، توقف البوت...")
            exit()
        
        # تشغيل التحديثات
        if not await run_migrations():
            LOGGER(__name__).warning("تحذير: فشل في تطبيق بعض تحديثات قاعدة البيانات")
        
        LOGGER(__name__).info("تم إعداد PostgreSQL بنجاح ✅")
    
    await sudo()
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass
    await app.start()
    for all_module in ALL_MODULES:
        importlib.import_module("ZeMusic.plugins" + all_module)
    LOGGER("ZeMusic.plugins").info("تنزيل معلومات السورس...")
    await userbot.start()
    await Mody.start()
    try:
        await Mody.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
    except NoActiveGroupCall:
        LOGGER("ZeMusic").warning(
            "No active group call found. Bot will continue without initial stream..."
        )
    except:
        pass
    await Mody.decorators()
    LOGGER("ZeMusic").info(
        "جاري تشغيل البوت\nتم التنصيب على سورس الملك بنجاح\nقناة السورس https://t.me/EF_19"
    )
    await idle()
    await app.stop()
    await userbot.stop()
    
    # إغلاق اتصال PostgreSQL
    if config.DATABASE_TYPE == "postgresql":
        await close_postgres()
    
    LOGGER("ZeMusic").info("Stopping Ze Music Bot...")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())

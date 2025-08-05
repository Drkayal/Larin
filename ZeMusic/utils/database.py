import random
from typing import Dict, List, Union

from ZeMusic import userbot
from ZeMusic.core.mongo import mongodb

# إضافة دعم PostgreSQL
import config
if config.DATABASE_TYPE == "postgresql":
    from ZeMusic.database.dal import (
        user_dal, chat_dal, chat_settings_dal, 
        auth_dal, ban_dal
    )

authdb = mongodb.adminauth
authuserdb = mongodb.authuser
autoenddb = mongodb.autoend
assdb = mongodb.assistants
blacklist_chatdb = mongodb.blacklistChat
blockeddb = mongodb.blockedusers
chatsdb = mongodb.chats
channeldb = mongodb.cplaymode
countdb = mongodb.upcount
gbansdb = mongodb.gban
langdb = mongodb.language
onoffdb = mongodb.onoffper
playmodedb = mongodb.playmode
playtypedb = mongodb.playtypedb
skipdb = mongodb.skipmode
sudoersdb = mongodb.sudoers
usersdb = mongodb.tgusersdb

#########
ders1db = mongodb.dere1
dersdb = mongodb.dere

# Shifting to memory [mongo sucks often]
active = []
activevideo = []
assistantdict = {}
autoend = {}
count = {}
channelconnect = {}
langm = {}
loop = {}
maintenance = []
nonadmin = {}
pause = {}
playmode = {}
playtype = {}
skipmode = {}


wedb = mongodb.we
lfdb = mongodb.lf


###############&&&&&&&&&&&&############

async def is_loge_enabled(chat_id):
    settings = await lfdb.find_one({"name": "search", "chat_id": chat_id})
    if settings:
        return settings.get("enabled", False)
    return False

async def enable_loge(chat_id):
    await lfdb.update_one({"name": "search", "chat_id": chat_id}, {"$set": {"enabled": True}}, upsert=True)

async def disable_loge(chat_id):
    await lfdb.update_one({"name": "search", "chat_id": chat_id}, {"$set": {"enabled": False}}, upsert=True)

###############&&&&&&&&&&&&############

async def is_welcome_enabled(chat_id):
    settings = await wedb.find_one({"name": "search", "chat_id": chat_id})
    if settings:
        return settings.get("enabled", False)
    return False

async def enable_welcome(chat_id):
    await wedb.update_one({"name": "search", "chat_id": chat_id}, {"$set": {"enabled": True}}, upsert=True)

async def disable_welcome(chat_id):
    await wedb.update_one({"name": "search", "chat_id": chat_id}, {"$set": {"enabled": False}}, upsert=True)
    
#####################################################
async def is_search_enabled1():
    settings = await ders1db.find_one({"name": "search"})
    if settings:
        return settings.get("enabled", False)
    return False

async def enable_search1():
    await ders1db.update_one({"name": "search"}, {"$set": {"enabled": True}}, upsert=True)

async def disable_search1():
    await ders1db.update_one({"name": "search"}, {"$set": {"enabled": False}}, upsert=True)


async def is_search_enabled(chat_id):
    """التحقق من تفعيل البحث في المجموعة"""
    try:
        if config.DATABASE_TYPE == "postgresql":
            from ZeMusic.core.postgres import get_postgres_connection
            async with get_postgres_connection() as conn:
                result = await conn.fetchval(
                    "SELECT search_enabled FROM chat_settings WHERE chat_id = $1",
                    chat_id
                )
                return result if result is not None else True  # افتراضياً مفعل
        else:
            # MongoDB fallback
            settings = await dersdb.find_one({"name": "search", "chat_id": chat_id})
            if settings:
                return settings.get("enabled", False)
            return True  # افتراضياً مفعل
    except Exception as e:
        print(f"خطأ في is_search_enabled: {e}")
        return True  # في حالة الخطأ، نسمح بالبحث

async def enable_search(chat_id):
    """تفعيل البحث في المجموعة"""
    try:
        if config.DATABASE_TYPE == "postgresql":
            from ZeMusic.core.postgres import get_postgres_connection
            async with get_postgres_connection() as conn:
                # التأكد من وجود المجموعة في جدول chats أولاً
                await conn.execute(
                    """INSERT INTO chats (chat_id, chat_type) 
                       VALUES ($1, 'group') 
                       ON CONFLICT (chat_id) DO NOTHING""",
                    chat_id
                )
                # ثم إضافة/تحديث إعدادات البحث
                await conn.execute(
                    """INSERT INTO chat_settings (chat_id, search_enabled) 
                       VALUES ($1, TRUE) 
                       ON CONFLICT (chat_id) 
                       DO UPDATE SET search_enabled = TRUE""",
                    chat_id
                )
        else:
            # MongoDB fallback
            await dersdb.update_one({"name": "search", "chat_id": chat_id}, {"$set": {"enabled": True}}, upsert=True)
    except Exception as e:
        print(f"خطأ في enable_search: {e}")

async def disable_search(chat_id):
    """تعطيل البحث في المجموعة"""
    try:
        if config.DATABASE_TYPE == "postgresql":
            from ZeMusic.core.postgres import get_postgres_connection
            async with get_postgres_connection() as conn:
                # التأكد من وجود المجموعة في جدول chats أولاً
                await conn.execute(
                    """INSERT INTO chats (chat_id, chat_type) 
                       VALUES ($1, 'group') 
                       ON CONFLICT (chat_id) DO NOTHING""",
                    chat_id
                )
                # ثم إضافة/تحديث إعدادات البحث
                await conn.execute(
                    """INSERT INTO chat_settings (chat_id, search_enabled) 
                       VALUES ($1, FALSE) 
                       ON CONFLICT (chat_id) 
                       DO UPDATE SET search_enabled = FALSE""",
                    chat_id
                )
        else:
            # MongoDB fallback
            await dersdb.update_one({"name": "search", "chat_id": chat_id}, {"$set": {"enabled": False}}, upsert=True)
    except Exception as e:
        print(f"خطأ في disable_search: {e}")

########################################################


async def get_assistant_number(chat_id: int) -> str:
    assistant = assistantdict.get(chat_id)
    return assistant


async def get_client(assistant: int):
    if int(assistant) == 1:
        return userbot.one
    elif int(assistant) == 2:
        return userbot.two
    elif int(assistant) == 3:
        return userbot.three
    elif int(assistant) == 4:
        return userbot.four
    elif int(assistant) == 5:
        return userbot.five


async def set_assistant_new(chat_id, number):
    number = int(number)
    await assdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"assistant": number}},
        upsert=True,
    )


async def set_assistant(chat_id):
    from ZeMusic.core.userbot import assistants

    ran_assistant = random.choice(assistants)
    assistantdict[chat_id] = ran_assistant
    await assdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"assistant": ran_assistant}},
        upsert=True,
    )
    userbot = await get_client(ran_assistant)
    return userbot


async def get_assistant(chat_id: int) -> str:
    from ZeMusic.core.userbot import assistants

    assistant = assistantdict.get(chat_id)
    if not assistant:
        dbassistant = await assdb.find_one({"chat_id": chat_id})
        if not dbassistant:
            userbot = await set_assistant(chat_id)
            return userbot
        else:
            got_assis = dbassistant["assistant"]
            if got_assis in assistants:
                assistantdict[chat_id] = got_assis
                userbot = await get_client(got_assis)
                return userbot
            else:
                userbot = await set_assistant(chat_id)
                return userbot
    else:
        if assistant in assistants:
            userbot = await get_client(assistant)
            return userbot
        else:
            userbot = await set_assistant(chat_id)
            return userbot


async def set_calls_assistant(chat_id):
    from ZeMusic.core.userbot import assistants

    ran_assistant = random.choice(assistants)
    assistantdict[chat_id] = ran_assistant
    await assdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"assistant": ran_assistant}},
        upsert=True,
    )
    return ran_assistant


async def group_assistant(self, chat_id: int) -> int:
    from ZeMusic.core.userbot import assistants

    assistant = assistantdict.get(chat_id)
    if not assistant:
        dbassistant = await assdb.find_one({"chat_id": chat_id})
        if not dbassistant:
            assis = await set_calls_assistant(chat_id)
        else:
            assis = dbassistant["assistant"]
            if assis in assistants:
                assistantdict[chat_id] = assis
                assis = assis
            else:
                assis = await set_calls_assistant(chat_id)
    else:
        if assistant in assistants:
            assis = assistant
        else:
            assis = await set_calls_assistant(chat_id)
    if int(assis) == 1:
        return self.one
    elif int(assis) == 2:
        return self.two
    elif int(assis) == 3:
        return self.three
    elif int(assis) == 4:
        return self.four
    elif int(assis) == 5:
        return self.five


async def is_skipmode(chat_id: int) -> bool:
    mode = skipmode.get(chat_id)
    if not mode:
        user = await skipdb.find_one({"chat_id": chat_id})
        if not user:
            skipmode[chat_id] = True
            return True
        skipmode[chat_id] = False
        return False
    return mode


async def skip_on(chat_id: int):
    skipmode[chat_id] = True
    user = await skipdb.find_one({"chat_id": chat_id})
    if user:
        return await skipdb.delete_one({"chat_id": chat_id})


async def skip_off(chat_id: int):
    skipmode[chat_id] = False
    user = await skipdb.find_one({"chat_id": chat_id})
    if not user:
        return await skipdb.insert_one({"chat_id": chat_id})


async def get_upvote_count(chat_id: int) -> int:
    if config.DATABASE_TYPE == "postgresql":
        return await chat_settings_dal.get_upvote_count(chat_id)
    
    mode = count.get(chat_id)
    if not mode:
        mode = await countdb.find_one({"chat_id": chat_id})
        if not mode:
            return 5
        count[chat_id] = mode["mode"]
        return mode["mode"]
    return mode


async def set_upvotes(chat_id: int, mode: int):
    if config.DATABASE_TYPE == "postgresql":
        return await chat_settings_dal.set_upvotes(chat_id, mode)
    
    count[chat_id] = mode
    await countdb.update_one(
        {"chat_id": chat_id}, {"$set": {"mode": mode}}, upsert=True
    )


async def is_autoend() -> bool:
    chat_id = 1234
    user = await autoenddb.find_one({"chat_id": chat_id})
    if not user:
        return False
    return True


async def autoend_on():
    chat_id = 1234
    await autoenddb.insert_one({"chat_id": chat_id})


async def autoend_off():
    chat_id = 1234
    await autoenddb.delete_one({"chat_id": chat_id})


async def get_loop(chat_id: int) -> int:
    lop = loop.get(chat_id)
    if not lop:
        return 0
    return lop


async def set_loop(chat_id: int, mode: int):
    loop[chat_id] = mode


async def get_cmode(chat_id: int) -> int:
    mode = channelconnect.get(chat_id)
    if not mode:
        mode = await channeldb.find_one({"chat_id": chat_id})
        if not mode:
            return None
        channelconnect[chat_id] = mode["mode"]
        return mode["mode"]
    return mode


async def set_cmode(chat_id: int, mode: int):
    channelconnect[chat_id] = mode
    await channeldb.update_one(
        {"chat_id": chat_id}, {"$set": {"mode": mode}}, upsert=True
    )


async def get_playtype(chat_id: int) -> str:
    if config.DATABASE_TYPE == "postgresql":
        return await chat_settings_dal.get_playtype(chat_id)
    
    mode = playtype.get(chat_id)
    if not mode:
        mode = await playtypedb.find_one({"chat_id": chat_id})
        if not mode:
            playtype[chat_id] = "Everyone"
            return "Everyone"
        playtype[chat_id] = mode["mode"]
        return mode["mode"]
    return mode


async def set_playtype(chat_id: int, mode: str):
    if config.DATABASE_TYPE == "postgresql":
        return await chat_settings_dal.set_playtype(chat_id, mode)
    
    playtype[chat_id] = mode
    await playtypedb.update_one(
        {"chat_id": chat_id}, {"$set": {"mode": mode}}, upsert=True
    )


async def get_playmode(chat_id: int) -> str:
    if config.DATABASE_TYPE == "postgresql":
        return await chat_settings_dal.get_playmode(chat_id)
    
    mode = playmode.get(chat_id)
    if not mode:
        mode = await playmodedb.find_one({"chat_id": chat_id})
        if not mode:
            playmode[chat_id] = "Direct"
            return "Direct"
        playmode[chat_id] = mode["mode"]
        return mode["mode"]
    return mode


async def set_playmode(chat_id: int, mode: str):
    if config.DATABASE_TYPE == "postgresql":
        return await chat_settings_dal.set_playmode(chat_id, mode)
    
    playmode[chat_id] = mode
    await playmodedb.update_one(
        {"chat_id": chat_id}, {"$set": {"mode": mode}}, upsert=True
    )


async def get_lang(chat_id: int) -> str:
    if config.DATABASE_TYPE == "postgresql":
        return await chat_settings_dal.get_lang(chat_id)
    
    mode = langm.get(chat_id)
    if not mode:
        lang = await langdb.find_one({"chat_id": chat_id})
        if not lang:
            langm[chat_id] = "en"
            return "en"
        langm[chat_id] = lang["lang"]
        return lang["lang"]
    return mode


async def set_lang(chat_id: int, lang: str):
    if config.DATABASE_TYPE == "postgresql":
        return await chat_settings_dal.set_lang(chat_id, lang)
    
    langm[chat_id] = lang
    await langdb.update_one({"chat_id": chat_id}, {"$set": {"lang": lang}}, upsert=True)


async def is_music_playing(chat_id: int) -> bool:
    mode = pause.get(chat_id)
    if not mode:
        return False
    return mode


async def music_on(chat_id: int):
    pause[chat_id] = True


async def music_off(chat_id: int):
    pause[chat_id] = False


async def get_active_chats() -> list:
    return active


async def is_active_chat(chat_id: int) -> bool:
    if chat_id not in active:
        return False
    else:
        return True


async def add_active_chat(chat_id: int):
    if chat_id not in active:
        active.append(chat_id)


async def remove_active_chat(chat_id: int):
    if chat_id in active:
        active.remove(chat_id)


async def get_active_video_chats() -> list:
    return activevideo


async def is_active_video_chat(chat_id: int) -> bool:
    if chat_id not in activevideo:
        return False
    else:
        return True


async def add_active_video_chat(chat_id: int):
    if chat_id not in activevideo:
        activevideo.append(chat_id)


async def remove_active_video_chat(chat_id: int):
    if chat_id in activevideo:
        activevideo.remove(chat_id)


async def check_nonadmin_chat(chat_id: int) -> bool:
    user = await authdb.find_one({"chat_id": chat_id})
    if not user:
        return False
    return True


async def is_nonadmin_chat(chat_id: int) -> bool:
    mode = nonadmin.get(chat_id)
    if not mode:
        user = await authdb.find_one({"chat_id": chat_id})
        if not user:
            nonadmin[chat_id] = False
            return False
        nonadmin[chat_id] = True
        return True
    return mode


async def add_nonadmin_chat(chat_id: int):
    nonadmin[chat_id] = True
    is_admin = await check_nonadmin_chat(chat_id)
    if is_admin:
        return
    return await authdb.insert_one({"chat_id": chat_id})


async def remove_nonadmin_chat(chat_id: int):
    nonadmin[chat_id] = False
    is_admin = await check_nonadmin_chat(chat_id)
    if not is_admin:
        return
    return await authdb.delete_one({"chat_id": chat_id})


async def is_on_off(on_off: int) -> bool:
    onoff = await onoffdb.find_one({"on_off": on_off})
    if not onoff:
        return False
    return True


async def add_on(on_off: int):
    is_on = await is_on_off(on_off)
    if is_on:
        return
    return await onoffdb.insert_one({"on_off": on_off})


async def add_off(on_off: int):
    is_off = await is_on_off(on_off)
    if not is_off:
        return
    return await onoffdb.delete_one({"on_off": on_off})


async def is_maintenance():
    if not maintenance:
        get = await onoffdb.find_one({"on_off": 1})
        if not get:
            maintenance.clear()
            maintenance.append(2)
            return True
        else:
            maintenance.clear()
            maintenance.append(1)
            return False
    else:
        if 1 in maintenance:
            return False
        else:
            return True


async def maintenance_off():
    maintenance.clear()
    maintenance.append(2)
    is_off = await is_on_off(1)
    if not is_off:
        return
    return await onoffdb.delete_one({"on_off": 1})


async def maintenance_on():
    maintenance.clear()
    maintenance.append(1)
    is_on = await is_on_off(1)
    if is_on:
        return
    return await onoffdb.insert_one({"on_off": 1})


async def is_served_user(user_id: int) -> bool:
    if config.DATABASE_TYPE == "postgresql":
        return await user_dal.is_served_user(user_id)
    
    user = await usersdb.find_one({"user_id": user_id})
    if not user:
        return False
    return True


async def get_served_users() -> list:
    if config.DATABASE_TYPE == "postgresql":
        return await user_dal.get_served_users()
    
    users_list = []
    async for user in usersdb.find({"user_id": {"$gt": 0}}):
        users_list.append(user)
    return users_list


async def add_served_user(user_id: int):
    if config.DATABASE_TYPE == "postgresql":
        return await user_dal.add_served_user(user_id)
    
    is_served = await is_served_user(user_id)
    if is_served:
        return
    return await usersdb.insert_one({"user_id": user_id})


async def get_served_chats() -> list:
    if config.DATABASE_TYPE == "postgresql":
        return await chat_dal.get_served_chats()
    
    chats_list = []
    async for chat in chatsdb.find({"chat_id": {"$lt": 0}}):
        chats_list.append(chat)
    return chats_list


async def is_served_chat(chat_id: int) -> bool:
    if config.DATABASE_TYPE == "postgresql":
        return await chat_dal.is_served_chat(chat_id)
    
    chat = await chatsdb.find_one({"chat_id": chat_id})
    if not chat:
        return False
    return True


async def add_served_chat(chat_id: int):
    if config.DATABASE_TYPE == "postgresql":
        return await chat_dal.add_served_chat(chat_id)
    
    is_served = await is_served_chat(chat_id)
    if is_served:
        return
    return await chatsdb.insert_one({"chat_id": chat_id})


async def blacklisted_chats() -> list:
    if config.DATABASE_TYPE == "postgresql":
        return await ban_dal.blacklisted_chats()
    
    chats_list = []
    async for chat in blacklist_chatdb.find({"chat_id": {"$lt": 0}}):
        chats_list.append(chat["chat_id"])
    return chats_list


async def blacklist_chat(chat_id: int) -> bool:
    if config.DATABASE_TYPE == "postgresql":
        return await ban_dal.blacklist_chat(chat_id)
    
    if not await blacklist_chatdb.find_one({"chat_id": chat_id}):
        await blacklist_chatdb.insert_one({"chat_id": chat_id})
        return True
    return False


async def whitelist_chat(chat_id: int) -> bool:
    if config.DATABASE_TYPE == "postgresql":
        return await ban_dal.whitelist_chat(chat_id)
    
    if await blacklist_chatdb.find_one({"chat_id": chat_id}):
        await blacklist_chatdb.delete_one({"chat_id": chat_id})
        return True
    return False


async def _get_authusers(chat_id: int) -> Dict[str, int]:
    _notes = await authuserdb.find_one({"chat_id": chat_id})
    if not _notes:
        return {}
    return _notes["notes"]


async def get_authuser_names(chat_id: int) -> List[str]:
    if config.DATABASE_TYPE == "postgresql":
        return await auth_dal.get_authuser_names(chat_id)
    
    _notes = []
    for note in await _get_authusers(chat_id):
        _notes.append(note)
    return _notes


async def get_authuser(chat_id: int, name: str) -> Union[bool, dict]:
    if config.DATABASE_TYPE == "postgresql":
        return await auth_dal.get_authuser(chat_id, name)
    
    name = name
    _notes = await _get_authusers(chat_id)
    if name in _notes:
        return _notes[name]
    else:
        return False


async def save_authuser(chat_id: int, name: str, note: dict):
    if config.DATABASE_TYPE == "postgresql":
        return await auth_dal.save_authuser(chat_id, name, note)
    
    name = name
    _notes = await _get_authusers(chat_id)
    _notes[name] = note

    await authuserdb.update_one(
        {"chat_id": chat_id}, {"$set": {"notes": _notes}}, upsert=True
    )


async def delete_authuser(chat_id: int, name: str) -> bool:
    if config.DATABASE_TYPE == "postgresql":
        return await auth_dal.delete_authuser(chat_id, name)
    
    notesd = await _get_authusers(chat_id)
    name = name
    if name in notesd:
        del notesd[name]
        await authuserdb.update_one(
            {"chat_id": chat_id},
            {"$set": {"notes": notesd}},
            upsert=True,
        )
        return True
    return False


async def get_gbanned() -> list:
    if config.DATABASE_TYPE == "postgresql":
        return await ban_dal.get_gbanned()
    
    results = []
    async for user in gbansdb.find({"user_id": {"$gt": 0}}):
        user_id = user["user_id"]
        results.append(user_id)
    return results


async def is_gbanned_user(user_id: int) -> bool:
    if config.DATABASE_TYPE == "postgresql":
        return await ban_dal.is_gbanned_user(user_id)
    
    user = await gbansdb.find_one({"user_id": user_id})
    if not user:
        return False
    return True


async def add_gban_user(user_id: int):
    if config.DATABASE_TYPE == "postgresql":
        return await ban_dal.add_gban_user(user_id)
    
    is_gbanned = await is_gbanned_user(user_id)
    if is_gbanned:
        return
    return await gbansdb.insert_one({"user_id": user_id})


async def remove_gban_user(user_id: int):
    if config.DATABASE_TYPE == "postgresql":
        return await ban_dal.remove_gban_user(user_id)
    
    is_gbanned = await is_gbanned_user(user_id)
    if not is_gbanned:
        return
    return await gbansdb.delete_one({"user_id": user_id})


async def get_sudoers() -> list:
    if config.DATABASE_TYPE == "postgresql":
        return await auth_dal.get_sudoers()
    
    sudoers = await sudoersdb.find_one({"sudo": "sudo"})
    if not sudoers:
        return []
    return sudoers["sudoers"]


async def add_sudo(user_id: int) -> bool:
    if config.DATABASE_TYPE == "postgresql":
        return await auth_dal.add_sudo(user_id)
    
    sudoers = await get_sudoers()
    sudoers.append(user_id)
    await sudoersdb.update_one(
        {"sudo": "sudo"}, {"$set": {"sudoers": sudoers}}, upsert=True
    )
    return True


async def remove_sudo(user_id: int) -> bool:
    if config.DATABASE_TYPE == "postgresql":
        return await auth_dal.remove_sudo(user_id)
    
    sudoers = await get_sudoers()
    sudoers.remove(user_id)
    await sudoersdb.update_one(
        {"sudo": "sudo"}, {"$set": {"sudoers": sudoers}}, upsert=True
    )
    return True


async def get_banned_users() -> list:
    if config.DATABASE_TYPE == "postgresql":
        return await ban_dal.get_banned_users()
    
    results = []
    async for user in blockeddb.find({"user_id": {"$gt": 0}}):
        user_id = user["user_id"]
        results.append(user_id)
    return results


async def get_banned_count() -> int:
    if config.DATABASE_TYPE == "postgresql":
        return await ban_dal.get_banned_count()
    
    users = blockeddb.find({"user_id": {"$gt": 0}})
    users = await users.to_list(length=100000)
    return len(users)


async def is_banned_user(user_id: int) -> bool:
    if config.DATABASE_TYPE == "postgresql":
        return await ban_dal.is_banned_user(user_id)
    
    user = await blockeddb.find_one({"user_id": user_id})
    if not user:
        return False
    return True


async def add_banned_user(user_id: int):
    if config.DATABASE_TYPE == "postgresql":
        return await ban_dal.add_banned_user(user_id)
    
    is_gbanned = await is_banned_user(user_id)
    if is_gbanned:
        return
    return await blockeddb.insert_one({"user_id": user_id})


async def remove_banned_user(user_id: int):
    if config.DATABASE_TYPE == "postgresql":
        return await ban_dal.remove_banned_user(user_id)
    
    is_gbanned = await is_banned_user(user_id)
    if not is_gbanned:
        return
    return await blockeddb.delete_one({"user_id": user_id})


# ============================================
# نظام التخزين المؤقت المتقدم
# ============================================

import asyncio
import os
import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import cachetools
from ZeMusic.logging import LOGGER

# إضافة استيراد download_dal
if config.DATABASE_TYPE == "postgresql":
    from ZeMusic.database.dal import download_dal

class CacheManager:
    """
    مدير التخزين المؤقت المتقدم للبوت
    يدعم التخزين في الذاكرة وقاعدة البيانات
    """
    
    def __init__(self):
        # تخزين مؤقت في الذاكرة لمدة أسبوع (بدون حدود)
        self.memory_cache = cachetools.TTLCache(
            maxsize=config.CACHE_MAX_SIZE,
            ttl=config.CACHE_EXPIRATION_HOURS * 3600
        )
        
        # تخزين مؤقت للبحث السريع
        self.search_cache = cachetools.TTLCache(
            maxsize=config.CACHE_MAX_SIZE // 2,
            ttl=3600  # ساعة واحدة للبحث
        )
        
        # إحصائيات التخزين المؤقت
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        }
        
    def _generate_cache_key(self, prefix: str, identifier: str) -> str:
        """إنشاء مفتاح تخزين مؤقت فريد"""
        return f"{prefix}:{hashlib.md5(identifier.encode()).hexdigest()}"
    
    async def get_cached_audio(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        جلب الملف الصوتي من التخزين المؤقت
        """
        self.cache_stats['total_requests'] += 1
        cache_key = self._generate_cache_key("audio", video_id)
        
        # البحث في الذاكرة أولاً
        if cache_key in self.memory_cache:
            self.cache_stats['hits'] += 1
            LOGGER(__name__).info(f"Cache hit in memory for video: {video_id}")
            return self.memory_cache[cache_key]
        
        # البحث في قاعدة البيانات
        if config.DATABASE_TYPE == "postgresql":
            try:
                result = await download_dal.get_cached_audio(video_id)
                if result:
                    # حفظ في الذاكرة للمرات القادمة
                    self.memory_cache[cache_key] = result
                    self.cache_stats['hits'] += 1
                    LOGGER(__name__).info(f"Cache hit in database for video: {video_id}")
                    return result
            except Exception as e:
                LOGGER(__name__).error(f"خطأ في جلب التخزين المؤقت من قاعدة البيانات: {e}")
        
        self.cache_stats['misses'] += 1
        LOGGER(__name__).info(f"Cache miss for video: {video_id}")
        return None
    
    async def save_audio_cache(self, video_info: Dict[str, Any]) -> bool:
        """
        حفظ الملف الصوتي في التخزين المؤقت
        """
        try:
            video_id = video_info.get('video_id')
            if not video_id:
                return False
            
            cache_key = self._generate_cache_key("audio", video_id)
            
            # حفظ في الذاكرة
            self.memory_cache[cache_key] = video_info
            
            # حفظ في قاعدة البيانات
            if config.DATABASE_TYPE == "postgresql":
                success = await download_dal.save_audio_cache(video_info)
                if success:
                    LOGGER(__name__).info(f"Audio cached successfully: {video_id}")
                    return True
            
            return True
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في حفظ التخزين المؤقت: {e}")
            return False
    
    async def get_search_results(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        جلب نتائج البحث من التخزين المؤقت
        """
        if not config.ENABLE_SEARCH_CACHE:
            return None
            
        cache_key = self._generate_cache_key("search", query.lower())
        
        # البحث في الذاكرة
        if cache_key in self.search_cache:
            LOGGER(__name__).info(f"Search cache hit for query: {query}")
            return self.search_cache[cache_key]
        
        # البحث في قاعدة البيانات
        if config.DATABASE_TYPE == "postgresql":
            try:
                results = await download_dal.get_search_history(query, limit=5)
                if results:
                    self.search_cache[cache_key] = results
                    return results
            except Exception as e:
                LOGGER(__name__).error(f"خطأ في جلب تاريخ البحث: {e}")
        
        return None
    
    async def save_search_results(self, query: str, results: List[Dict[str, Any]]) -> bool:
        """
        حفظ نتائج البحث في التخزين المؤقت
        """
        try:
            if not config.ENABLE_SEARCH_CACHE:
                return False
                
            cache_key = self._generate_cache_key("search", query.lower())
            self.search_cache[cache_key] = results
            
            LOGGER(__name__).info(f"Search results cached for query: {query}")
            return True
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في حفظ نتائج البحث: {e}")
            return False
    
    async def cleanup_expired_cache(self) -> Dict[str, int]:
        """
        تنظيف التخزين المؤقت المنتهي الصلاحية
        """
        cleanup_stats = {
            'memory_cleaned': 0,
            'database_cleaned': 0,
            'total_cleaned': 0
        }
        
        try:
            # تنظيف الذاكرة (تلقائي مع TTLCache)
            initial_memory_size = len(self.memory_cache)
            self.memory_cache.expire()
            cleanup_stats['memory_cleaned'] = initial_memory_size - len(self.memory_cache)
            
            initial_search_size = len(self.search_cache)
            self.search_cache.expire()
            cleanup_stats['memory_cleaned'] += initial_search_size - len(self.search_cache)
            
            # تنظيف قاعدة البيانات
            if config.DATABASE_TYPE == "postgresql":
                try:
                    # تنظيف الملفات القديمة (أكثر من أسبوع بدون استخدام)
                    days_old = config.CACHE_EXPIRATION_HOURS // 24
                    cleaned_count = await download_dal.cleanup_old_cache(days_old)
                    cleanup_stats['database_cleaned'] = cleaned_count
                except Exception as e:
                    LOGGER(__name__).error(f"خطأ في تنظيف قاعدة البيانات: {e}")
            
            cleanup_stats['total_cleaned'] = (
                cleanup_stats['memory_cleaned'] + 
                cleanup_stats['database_cleaned']
            )
            
            if cleanup_stats['total_cleaned'] > 0:
                LOGGER(__name__).info(f"Cache cleanup completed: {cleanup_stats}")
            
            return cleanup_stats
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تنظيف التخزين المؤقت: {e}")
            return cleanup_stats
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        جلب إحصائيات التخزين المؤقت
        """
        hit_ratio = 0
        if self.cache_stats['total_requests'] > 0:
            hit_ratio = (self.cache_stats['hits'] / self.cache_stats['total_requests']) * 100
        
        return {
            'memory_cache_size': len(self.memory_cache),
            'search_cache_size': len(self.search_cache),
            'total_requests': self.cache_stats['total_requests'],
            'cache_hits': self.cache_stats['hits'],
            'cache_misses': self.cache_stats['misses'],
            'hit_ratio_percent': round(hit_ratio, 2),
            'max_memory_size': config.CACHE_MAX_SIZE,
            'cache_expiration_hours': config.CACHE_EXPIRATION_HOURS
        }
    
    async def clear_all_cache(self) -> bool:
        """
        مسح جميع التخزين المؤقت (للطوارئ فقط)
        """
        try:
            # مسح الذاكرة
            self.memory_cache.clear()
            self.search_cache.clear()
            
            # إعادة تعيين الإحصائيات
            self.cache_stats = {
                'hits': 0,
                'misses': 0,
                'total_requests': 0
            }
            
            LOGGER(__name__).warning("تم مسح جميع التخزين المؤقت")
            return True
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في مسح التخزين المؤقت: {e}")
            return False

# إنشاء مثيل عام لمدير التخزين المؤقت
cache_manager = CacheManager()


# ============================================
# نظام إدارة الملفات المتقدم
# ============================================

import shutil
import subprocess
import aiofiles
import aiofiles.os
from pathlib import Path

class FileManager:
    """
    مدير الملفات المتقدم للبوت
    يدير إنشاء المجلدات وتحسين الصوت وحذف الملفات
    """
    
    def __init__(self):
        self.base_downloads_dir = Path(config.DOWNLOADS_DIR)
        self.temp_dir = self.base_downloads_dir / "temp"
        self.optimized_dir = self.base_downloads_dir / "optimized"
        self._initialized = False
    
    async def _ensure_initialized(self):
        """التأكد من تهيئة المجلدات"""
        if not self._initialized:
            await self._create_base_directories()
            self._initialized = True
    
    async def _create_base_directories(self):
        """إنشاء المجلدات الأساسية"""
        try:
            for directory in [self.base_downloads_dir, self.temp_dir, self.optimized_dir]:
                await aiofiles.os.makedirs(directory, exist_ok=True)
            LOGGER(__name__).info("تم إنشاء المجلدات الأساسية بنجاح")
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إنشاء المجلدات الأساسية: {e}")
    
    async def create_user_directory(self, user_id: int) -> Path:
        """
        إنشاء مجلد خاص للمستخدم
        """
        await self._ensure_initialized()
        try:
            user_dir = self.base_downloads_dir / str(user_id)
            await aiofiles.os.makedirs(user_dir, exist_ok=True)
            
            # إنشاء مجلدات فرعية للمستخدم
            for subdir in ["audio", "temp", "thumbnails"]:
                await aiofiles.os.makedirs(user_dir / subdir, exist_ok=True)
            
            LOGGER(__name__).info(f"تم إنشاء مجلد المستخدم: {user_id}")
            return user_dir
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إنشاء مجلد المستخدم {user_id}: {e}")
            return self.base_downloads_dir
    
    async def optimize_audio_quality(self, input_file: str, output_file: str = None, 
                                   target_quality: str = None) -> str:
        """
        تحسين جودة الصوت باستخدام FFmpeg
        """
        try:
            if not target_quality:
                target_quality = config.AUDIO_QUALITY
            
            if not output_file:
                input_path = Path(input_file)
                output_file = str(input_path.parent / f"{input_path.stem}_optimized{input_path.suffix}")
            
            # التحقق من وجود FFmpeg
            if not shutil.which('ffmpeg'):
                LOGGER(__name__).warning("FFmpeg غير متوفر، سيتم إرجاع الملف الأصلي")
                return input_file
            
            # أوامر FFmpeg للتحسين (بدون حدود على الحجم)
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', input_file,
                '-c:a', config.FFMPEG_AUDIO_CODEC,
                '-b:a', f"{target_quality}k",
                '-ac', str(config.FFMPEG_AUDIO_CHANNELS),
                '-ar', str(config.FFMPEG_SAMPLE_RATE),
                '-avoid_negative_ts', 'make_zero',
                '-map_metadata', '0',
                '-id3v2_version', '3',
                '-write_id3v1', '1',
                '-y',  # الكتابة فوق الملف الموجود
                output_file
            ]
            
            # تشغيل FFmpeg في الخلفية
            process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE
            )
            
            _, stderr = await process.communicate()
            
            if process.returncode == 0:
                # التحقق من حجم الملف المحسن
                input_size = (await aiofiles.os.stat(input_file)).st_size
                output_size = (await aiofiles.os.stat(output_file)).st_size
                
                # حذف الملف الأصلي فقط إذا كان التحسين ناجحاً
                try:
                    await aiofiles.os.remove(input_file)
                except:
                    pass
                
                LOGGER(__name__).info(
                    f"تم تحسين الصوت: {input_size//1024}KB -> {output_size//1024}KB"
                )
                return output_file
            else:
                error_msg = stderr.decode() if stderr else "خطأ غير معروف"
                LOGGER(__name__).error(f"خطأ في FFmpeg: {error_msg}")
                return input_file
                
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تحسين جودة الصوت: {e}")
            return input_file
    
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        جلب معلومات الملف
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {}
            
            stat = await aiofiles.os.stat(file_path)
            
            return {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size': stat.st_size,
                'file_size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created_time': datetime.fromtimestamp(stat.st_ctime),
                'modified_time': datetime.fromtimestamp(stat.st_mtime),
                'file_extension': file_path.suffix,
                'is_audio': file_path.suffix.lower() in ['.mp3', '.m4a', '.wav', '.flac', '.ogg']
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في جلب معلومات الملف: {e}")
            return {}
    
    async def cleanup_user_files(self, user_id: int, max_age_hours: int = None) -> Dict[str, int]:
        """
        تنظيف ملفات المستخدم القديمة
        """
        cleanup_stats = {
            'files_deleted': 0,
            'space_freed_mb': 0,
            'directories_cleaned': 0
        }
        
        try:
            if not max_age_hours:
                max_age_hours = config.CLEANUP_INTERVAL_HOURS
            
            user_dir = self.base_downloads_dir / str(user_id)
            if not user_dir.exists():
                return cleanup_stats
            
            cutoff_time = time.time() - (max_age_hours * 3600)
            
            # تنظيف الملفات القديمة
            for file_path in user_dir.rglob("*"):
                if file_path.is_file():
                    try:
                        stat = await aiofiles.os.stat(file_path)
                        if stat.st_mtime < cutoff_time:
                            file_size = stat.st_size
                            await aiofiles.os.remove(file_path)
                            cleanup_stats['files_deleted'] += 1
                            cleanup_stats['space_freed_mb'] += file_size / (1024 * 1024)
                    except Exception as e:
                        LOGGER(__name__).warning(f"خطأ في حذف الملف {file_path}: {e}")
            
            # تنظيف المجلدات الفارغة
            for dir_path in user_dir.rglob("*"):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    try:
                        await aiofiles.os.rmdir(dir_path)
                        cleanup_stats['directories_cleaned'] += 1
                    except Exception as e:
                        LOGGER(__name__).warning(f"خطأ في حذف المجلد {dir_path}: {e}")
            
            if cleanup_stats['files_deleted'] > 0:
                LOGGER(__name__).info(
                    f"تنظيف ملفات المستخدم {user_id}: "
                    f"{cleanup_stats['files_deleted']} ملف، "
                    f"{cleanup_stats['space_freed_mb']:.2f} MB"
                )
            
            return cleanup_stats
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تنظيف ملفات المستخدم {user_id}: {e}")
            return cleanup_stats
    
    async def cleanup_all_temp_files(self) -> Dict[str, int]:
        """
        تنظيف جميع الملفات المؤقتة
        """
        await self._ensure_initialized()
        cleanup_stats = {
            'temp_files_deleted': 0,
            'temp_space_freed_mb': 0,
            'old_files_deleted': 0,
            'old_space_freed_mb': 0
        }
        
        try:
            # تنظيف مجلد temp
            if self.temp_dir.exists():
                for file_path in self.temp_dir.rglob("*"):
                    if file_path.is_file():
                        try:
                            stat = await aiofiles.os.stat(file_path)
                            file_size = stat.st_size
                            await aiofiles.os.remove(file_path)
                            cleanup_stats['temp_files_deleted'] += 1
                            cleanup_stats['temp_space_freed_mb'] += file_size / (1024 * 1024)
                        except Exception as e:
                            LOGGER(__name__).warning(f"خطأ في حذف الملف المؤقت {file_path}: {e}")
            
            # تنظيف الملفات القديمة من جميع مجلدات المستخدمين
            cutoff_time = time.time() - (config.CLEANUP_INTERVAL_HOURS * 3600)
            
            for user_dir in self.base_downloads_dir.iterdir():
                if user_dir.is_dir() and user_dir.name.isdigit():
                    for file_path in user_dir.rglob("*"):
                        if file_path.is_file():
                            try:
                                stat = await aiofiles.os.stat(file_path)
                                if stat.st_mtime < cutoff_time:
                                    file_size = stat.st_size
                                    await aiofiles.os.remove(file_path)
                                    cleanup_stats['old_files_deleted'] += 1
                                    cleanup_stats['old_space_freed_mb'] += file_size / (1024 * 1024)
                            except Exception as e:
                                LOGGER(__name__).warning(f"خطأ في حذف الملف القديم {file_path}: {e}")
            
            total_files = cleanup_stats['temp_files_deleted'] + cleanup_stats['old_files_deleted']
            total_space = cleanup_stats['temp_space_freed_mb'] + cleanup_stats['old_space_freed_mb']
            
            if total_files > 0:
                LOGGER(__name__).info(f"تنظيف عام: {total_files} ملف، {total_space:.2f} MB")
            
            return cleanup_stats
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في التنظيف العام: {e}")
            return cleanup_stats
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        جلب إحصائيات التخزين
        """
        try:
            stats = {
                'total_users': 0,
                'total_files': 0,
                'total_size_mb': 0,
                'temp_files': 0,
                'temp_size_mb': 0,
                'user_stats': {}
            }
            
            # إحصائيات المجلد المؤقت
            if self.temp_dir.exists():
                for file_path in self.temp_dir.rglob("*"):
                    if file_path.is_file():
                        try:
                            stat = await aiofiles.os.stat(file_path)
                            stats['temp_files'] += 1
                            stats['temp_size_mb'] += stat.st_size / (1024 * 1024)
                        except:
                            pass
            
            # إحصائيات مجلدات المستخدمين
            for user_dir in self.base_downloads_dir.iterdir():
                if user_dir.is_dir() and user_dir.name.isdigit():
                    user_id = user_dir.name
                    user_files = 0
                    user_size = 0
                    
                    for file_path in user_dir.rglob("*"):
                        if file_path.is_file():
                            try:
                                stat = await aiofiles.os.stat(file_path)
                                user_files += 1
                                user_size += stat.st_size / (1024 * 1024)
                            except:
                                pass
                    
                    if user_files > 0:
                        stats['user_stats'][user_id] = {
                            'files': user_files,
                            'size_mb': round(user_size, 2)
                        }
                        stats['total_users'] += 1
                        stats['total_files'] += user_files
                        stats['total_size_mb'] += user_size
            
            stats['total_size_mb'] = round(stats['total_size_mb'], 2)
            stats['temp_size_mb'] = round(stats['temp_size_mb'], 2)
            
            return stats
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في جلب إحصائيات التخزين: {e}")
            return {}
    
    async def safe_delete_file(self, file_path: str) -> bool:
        """
        حذف آمن للملف
        """
        try:
            file_path = Path(file_path)
            if file_path.exists():
                await aiofiles.os.remove(file_path)
                LOGGER(__name__).info(f"تم حذف الملف: {file_path.name}")
                return True
            return False
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في حذف الملف {file_path}: {e}")
            return False
    
    async def move_file(self, source: str, destination: str) -> bool:
        """
        نقل الملف من مكان لآخر
        """
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            # إنشاء مجلد الوجهة إذا لم يكن موجوداً
            await aiofiles.os.makedirs(dest_path.parent, exist_ok=True)
            
            # نقل الملف
            shutil.move(str(source_path), str(dest_path))
            
            LOGGER(__name__).info(f"تم نقل الملف من {source_path.name} إلى {dest_path}")
            return True
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في نقل الملف: {e}")
            return False

# إنشاء مثيل عام لمدير الملفات
file_manager = FileManager()


# ============================================
# وظائف مساعدة للتخزين المؤقت وإدارة الملفات
# ============================================

async def get_cached_audio_info(video_id: str) -> Optional[Dict[str, Any]]:
    """
    دالة مساعدة للحصول على معلومات الملف الصوتي من التخزين المؤقت
    """
    return await cache_manager.get_cached_audio(video_id)

async def save_audio_to_cache(video_info: Dict[str, Any]) -> bool:
    """
    دالة مساعدة لحفظ معلومات الملف الصوتي في التخزين المؤقت
    """
    return await cache_manager.save_audio_cache(video_info)

async def get_search_cache(query: str) -> Optional[List[Dict[str, Any]]]:
    """
    دالة مساعدة للحصول على نتائج البحث من التخزين المؤقت
    """
    return await cache_manager.get_search_results(query)

async def save_search_to_cache(query: str, results: List[Dict[str, Any]]) -> bool:
    """
    دالة مساعدة لحفظ نتائج البحث في التخزين المؤقت
    """
    return await cache_manager.save_search_results(query, results)

async def create_user_download_dir(user_id: int) -> Path:
    """
    دالة مساعدة لإنشاء مجلد تحميل للمستخدم
    """
    return await file_manager.create_user_directory(user_id)

async def optimize_audio_file(input_file: str, target_quality: str = None) -> str:
    """
    دالة مساعدة لتحسين جودة الملف الصوتي
    """
    return await file_manager.optimize_audio_quality(input_file, target_quality=target_quality)

async def cleanup_user_downloads(user_id: int) -> Dict[str, int]:
    """
    دالة مساعدة لتنظيف تحميلات المستخدم
    """
    return await file_manager.cleanup_user_files(user_id)

async def get_file_details(file_path: str) -> Dict[str, Any]:
    """
    دالة مساعدة لجلب تفاصيل الملف
    """
    return await file_manager.get_file_info(file_path)

async def cleanup_system_cache() -> Dict[str, int]:
    """
    دالة مساعدة لتنظيف التخزين المؤقت للنظام
    """
    cache_stats = await cache_manager.cleanup_expired_cache()
    file_stats = await file_manager.cleanup_all_temp_files()
    
    return {
        'cache_cleaned': cache_stats.get('total_cleaned', 0),
        'files_cleaned': file_stats.get('temp_files_deleted', 0) + file_stats.get('old_files_deleted', 0),
        'space_freed_mb': file_stats.get('temp_space_freed_mb', 0) + file_stats.get('old_space_freed_mb', 0)
    }

def get_system_cache_stats() -> Dict[str, Any]:
    """
    دالة مساعدة لجلب إحصائيات التخزين المؤقت
    """
    return cache_manager.get_cache_stats()

async def get_system_storage_stats() -> Dict[str, Any]:
    """
    دالة مساعدة لجلب إحصائيات التخزين
    """
    return await file_manager.get_storage_stats()


# ============================================
# مهام التنظيف الدورية
# ============================================

async def periodic_cleanup_task():
    """
    مهمة تنظيف دورية تعمل في الخلفية
    """
    while True:
        try:
            # انتظار فترة التنظيف (بدون حدود)
            await asyncio.sleep(config.CLEANUP_INTERVAL_HOURS * 3600)
            
            # تنظيف النظام
            cleanup_stats = await cleanup_system_cache()
            
            if cleanup_stats['files_cleaned'] > 0 or cleanup_stats['cache_cleaned'] > 0:
                LOGGER(__name__).info(
                    f"تنظيف دوري مكتمل: "
                    f"ملفات محذوفة: {cleanup_stats['files_cleaned']}, "
                    f"تخزين مؤقت محذوف: {cleanup_stats['cache_cleaned']}, "
                    f"مساحة محررة: {cleanup_stats['space_freed_mb']:.2f} MB"
                )
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في المهمة الدورية للتنظيف: {e}")
            # انتظار قبل المحاولة مرة أخرى
            await asyncio.sleep(3600)  # ساعة واحدة

# بدء المهمة الدورية
async def start_cleanup_task():
    """
    بدء مهمة التنظيف الدورية
    """
    try:
        asyncio.create_task(periodic_cleanup_task())
        LOGGER(__name__).info("تم بدء مهمة التنظيف الدورية")
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في بدء مهمة التنظيف الدورية: {e}")

# المهمة ستبدأ عند الحاجة وليس عند الاستيراد

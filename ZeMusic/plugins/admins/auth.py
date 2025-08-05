from pyrogram import filters
from pyrogram.types import Message

import config
from ZeMusic import app
from ZeMusic.utils import extract_user, int_to_alpha
from ZeMusic.utils.database import (
    delete_authuser,
    get_authuser,
    get_authuser_names,
    save_authuser,
)
from ZeMusic.utils.decorators import AdminActual, language
from ZeMusic.utils.inline import close_markup
from config import BANNED_USERS, adminlist


async def log_admin_action(chat_id: int, admin_id: int, action_type: str, target_user_id: int, details: str):
    """تسجيل إجراءات المشرفين في قاعدة البيانات"""
    try:
        if config.DATABASE_TYPE == "postgresql":
            from ZeMusic.core.postgres import execute_query
            await execute_query(
                "INSERT INTO activity_logs (user_id, chat_id, activity_type, details, created_at) "
                "VALUES ($1, $2, $3, $4, NOW())",
                admin_id,
                chat_id,
                action_type,
                f"Target: {target_user_id} - {details}"
            )
        else:
            # MongoDB fallback
            from ZeMusic.misc import mongodb
            await mongodb.activity_logs.insert_one({
                "user_id": admin_id,
                "chat_id": chat_id,
                "activity_type": action_type,
                "details": f"Target: {target_user_id} - {details}",
                "created_at": "now"
            })
    except Exception as e:
        print(f"خطأ في تسجيل إجراء المشرف: {e}")


async def backup_auth_users(chat_id: int):
    """حفظ احتياطي لقائمة المشرفين المخولين"""
    try:
        auth_users = await get_authuser_names(chat_id)
        
        if config.DATABASE_TYPE == "postgresql":
            from ZeMusic.core.postgres import execute_query
            await execute_query(
                "INSERT INTO settings_backup (chat_id, settings_data, created_at) "
                "VALUES ($1, $2, NOW()) "
                "ON CONFLICT (chat_id) DO UPDATE SET settings_data = $2, created_at = NOW()",
                chat_id,
                f"auth_users: {str(auth_users)}"
            )
        else:
            # MongoDB fallback
            from ZeMusic.misc import mongodb
            await mongodb.settings_backup.update_one(
                {"chat_id": chat_id},
                {"$set": {
                    "auth_users": auth_users,
                    "backup_time": "now"
                }},
                upsert=True
            )
    except Exception as e:
        print(f"خطأ في حفظ قائمة المشرفين المخولين: {e}")


@app.on_message(filters.command(("رفع ادمن"),"") & filters.group & ~BANNED_USERS)
@AdminActual
async def auth(client, message: Message, _):
    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text(_["general_1"])
        user = message.text.split(None, 2)[2]
        if "@" in user:
            user = user.replace("@", "")
        else:
            return await message.reply_text(_["general_1"])
        
        user = await app.get_users(user)
        user_id = message.from_user.id
        token = await int_to_alpha(user.id)
        from_user_name = message.from_user.first_name
        from_user_id = message.from_user.id
        _check = await get_authuser_names(message.chat.id)
        count = len(_check)
        if int(count) == 50:
            return await message.reply_text(_["auth_1"])
        if token not in _check:
            assis = {
                "auth_user_id": user.id,
                "auth_name": user.first_name,
                "admin_id": from_user_id,
                "admin_name": from_user_name,
            }
            get = adminlist.get(message.chat.id)
            if get:
                if user.id not in get:
                    get.append(user.id)
            await save_authuser(message.chat.id, token, assis)
            
            # تسجيل الإجراء وحفظ احتياطي
            await log_admin_action(
                message.chat.id,
                message.from_user.id,
                "auth_user_added",
                user.id,
                f"Added {user.first_name} as authorized user"
            )
            await backup_auth_users(message.chat.id)
            
            return await message.reply_text(_["auth_2"].format(user.mention))
        else:
            await message.reply_text(_["auth_3"].format(user.mention))
        return

    user = await extract_user(message)
    from_user_id = message.from_user.id
    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name
    token = await int_to_alpha(user_id)
    from_user_name = message.from_user.first_name
    _check = await get_authuser_names(message.chat.id)
    count = 0
    for smex in _check:
        count += 1
    if int(count) == 50:
        return await message.reply_text(_["auth_1"])
    if token not in _check:
        assis = {
            "auth_user_id": user_id,
            "auth_name": user_name,
            "admin_id": from_user_id,
            "admin_name": from_user_name,
        }
        get = adminlist.get(message.chat.id)
        if get:
            if user_id not in get:
                get.append(user_id)
        await save_authuser(message.chat.id, token, assis)
        
        # تسجيل الإجراء وحفظ احتياطي
        await log_admin_action(
            message.chat.id,
            message.from_user.id,
            "auth_user_added",
            user_id,
            f"Added {user_name} as authorized user"
        )
        await backup_auth_users(message.chat.id)
        
        return await message.reply_text(_["auth_2"].format(user.mention))
    else:
        await message.reply_text(_["auth_3"].format(user.mention))

                                                           
@app.on_message(filters.command(["تنزيل ادمن"],"") & filters.group & ~BANNED_USERS)
@AdminActual
async def unauthusers(client, message: Message, _):
    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text(_["general_1"])
        user = message.text.split(None, 2)[2]
        if "@" in user:
            user = user.replace("@", "")
        else:
            return await message.reply_text(_["general_1"])
            
        user = await app.get_users(user)
        token = await int_to_alpha(user.id)
        deleted = await delete_authuser(message.chat.id, token)
        get = adminlist.get(message.chat.id)
        if get:
            if user.id in get:
                get.remove(user.id)
        if deleted:
            # تسجيل الإجراء وحفظ احتياطي
            await log_admin_action(
                message.chat.id,
                message.from_user.id,
                "auth_user_removed",
                user.id,
                f"Removed {user.first_name} from authorized users"
            )
            await backup_auth_users(message.chat.id)
            
            return await message.reply_text(_["auth_4"].format(user.mention))
        else:
            return await message.reply_text(_["auth_5"].format(user.mention))

    user = await extract_user(message)
    user_id = message.reply_to_message.from_user.id
    token = await int_to_alpha(user_id)
    deleted = await delete_authuser(message.chat.id, token)
    get = adminlist.get(message.chat.id)
    if get:
        if user_id in get:
            get.remove(user_id)
    if deleted:
        # تسجيل الإجراء وحفظ احتياطي
        await log_admin_action(
            message.chat.id,
            message.from_user.id,
            "auth_user_removed",
            user_id,
            f"Removed authorized user (ID: {user_id})"
        )
        await backup_auth_users(message.chat.id)
        
        return await message.reply_text(_["auth_4"].format(user.mention))
    else:
        return await message.reply_text(_["auth_5"].format(user.mention))


@app.on_message(
    filters.command(["الادمنيه", "الادمن"]) & filters.group & ~BANNED_USERS
)
@language
async def authusers(client, message: Message, _):
    _wtf = await get_authuser_names(message.chat.id)
    if not _wtf:
        return await message.reply_text(_["setting_4"])
    else:
        j = 0
        mystic = await message.reply_text(_["auth_6"])
        text = _["auth_7"].format(message.chat.title)
        for umm in _wtf:
            _umm = await get_authuser(message.chat.id, umm)
            user_id = _umm["auth_user_id"]
            try:
                user = await app.get_users(user_id)
                user = user.mention
                j += 1
            except:
                continue
            text += f"{j} - {user}\n"
        await mystic.edit_text(text, reply_markup=close_markup(_))


@app.on_message(
    filters.command(["admin_logs", "سجل_المشرفين", "activity_logs"]) & filters.group & ~BANNED_USERS
)
@AdminActual
async def admin_activity_logs(client, message: Message, _):
    """عرض سجل أنشطة المشرفين في المحادثة"""
    try:
        logs_text = "📊 **سجل أنشطة المشرفين:**\n\n"
        
        if config.DATABASE_TYPE == "postgresql":
            from ZeMusic.core.postgres import fetch_all
            logs = await fetch_all(
                "SELECT user_id, activity_type, details, created_at "
                "FROM activity_logs WHERE chat_id = $1 "
                "ORDER BY created_at DESC LIMIT 10",
                message.chat.id
            )
            
            if logs:
                for i, log in enumerate(logs, 1):
                    try:
                        user = await app.get_users(log['user_id'])
                        user_name = user.first_name
                    except:
                        user_name = f"المستخدم {log['user_id']}"
                    
                    logs_text += f"{i}. **{user_name}**\n"
                    logs_text += f"   └ {log['details']}\n"
                    logs_text += f"   └ {log['created_at']}\n\n"
            else:
                logs_text += "لا توجد أنشطة مسجلة حتى الآن."
        else:
            # MongoDB fallback
            from ZeMusic.misc import mongodb
            logs = await mongodb.activity_logs.find(
                {"chat_id": message.chat.id}
            ).sort("created_at", -1).limit(10).to_list(10)
            
            if logs:
                for i, log in enumerate(logs, 1):
                    try:
                        user = await app.get_users(log['user_id'])
                        user_name = user.first_name
                    except:
                        user_name = f"المستخدم {log['user_id']}"
                    
                    logs_text += f"{i}. **{user_name}**\n"
                    logs_text += f"   └ {log['details']}\n"
                    logs_text += f"   └ {log.get('created_at', 'غير محدد')}\n\n"
            else:
                logs_text += "لا توجد أنشطة مسجلة حتى الآن."
        
        await message.reply_text(logs_text)
        
    except Exception as e:
        await message.reply_text(
            f"❌ **خطأ في جلب سجل الأنشطة:**\n\n"
            f"```\n{str(e)}\n```"
        )

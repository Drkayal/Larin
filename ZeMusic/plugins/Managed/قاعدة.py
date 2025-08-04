import requests
import random
import os
import re
import asyncio
import time
import config
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserAlreadyParticipant
from ZeMusic.utils.database import add_served_chat
from ZeMusic import app


async def log_chat_interaction(chat_id: int, user_id: int, interaction_type: str):
    """تسجيل تفاعلات المحادثات في قاعدة البيانات"""
    try:
        if config.DATABASE_TYPE == "postgresql":
            from ZeMusic.core.postgres import execute_query
            await execute_query(
                "INSERT INTO activity_logs (user_id, chat_id, activity_type, details, created_at) "
                "VALUES ($1, $2, $3, $4, NOW())",
                user_id,
                chat_id,
                "chat_interaction",
                f"Interaction type: {interaction_type}"
            )
        else:
            # MongoDB fallback
            from ZeMusic.misc import mongodb
            await mongodb.activity_logs.insert_one({
                "user_id": user_id,
                "chat_id": chat_id,
                "activity_type": "chat_interaction",
                "details": f"Interaction type: {interaction_type}",
                "created_at": "now"
            })
    except Exception as e:
        print(f"خطأ في تسجيل تفاعل المحادثة: {e}")


@app.on_message(filters.command(["ا", "هلا", "سلام", "المالك", "بخير", "وانت", "بوت"],"") & filters.group)
async def bot_check(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # إضافة المحادثة للقائمة المخدومة
    await add_served_chat(chat_id)
    
    # تسجيل التفاعل
    await log_chat_interaction(chat_id, user_id, f"greeting_command: {message.text}")


@app.on_message(filters.command(["chat_stats", "إحصائيات_المحادثة"]) & filters.group)
async def chat_statistics(client, message):
    """عرض إحصائيات المحادثة"""
    try:
        chat_id = message.chat.id
        stats_text = "📊 **إحصائيات المحادثة:**\n\n"
        
        if config.DATABASE_TYPE == "postgresql":
            from ZeMusic.core.postgres import fetch_all, fetch_value
            
            # عدد التفاعلات
            interaction_count = await fetch_value(
                "SELECT COUNT(*) FROM activity_logs WHERE chat_id = $1 AND activity_type = 'chat_interaction'",
                chat_id
            )
            
            # آخر التفاعلات
            recent_interactions = await fetch_all(
                "SELECT user_id, details, created_at FROM activity_logs "
                "WHERE chat_id = $1 AND activity_type = 'chat_interaction' "
                "ORDER BY created_at DESC LIMIT 5",
                chat_id
            )
            
            stats_text += f"🔢 **إجمالي التفاعلات:** {interaction_count or 0}\n\n"
            
            if recent_interactions:
                stats_text += "📝 **آخر التفاعلات:**\n"
                for i, interaction in enumerate(recent_interactions, 1):
                    try:
                        user = await client.get_users(interaction['user_id'])
                        user_name = user.first_name
                    except:
                        user_name = f"المستخدم {interaction['user_id']}"
                    
                    stats_text += f"{i}. **{user_name}**\n"
                    stats_text += f"   └ {interaction['details']}\n"
                    stats_text += f"   └ {interaction['created_at']}\n\n"
        else:
            # MongoDB fallback
            from ZeMusic.misc import mongodb
            interaction_count = await mongodb.activity_logs.count_documents({
                "chat_id": chat_id,
                "activity_type": "chat_interaction"
            })
            
            stats_text += f"🔢 **إجمالي التفاعلات:** {interaction_count}\n\n"
            stats_text += "💡 **للمزيد من الإحصائيات:** قم بتفعيل PostgreSQL"
        
        await message.reply_text(stats_text)
        
    except Exception as e:
        await message.reply_text(
            f"❌ **خطأ في جلب إحصائيات المحادثة:**\n\n"
            f"```\n{str(e)}\n```"
        )

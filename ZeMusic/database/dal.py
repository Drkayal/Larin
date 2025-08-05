"""
Data Access Layer (DAL) for PostgreSQL
طبقة الوصول للبيانات لـ PostgreSQL
"""

import asyncio
from typing import Dict, List, Union, Optional, Any
from datetime import datetime

import config
from ZeMusic.core.postgres import execute_query, fetch_all, fetch_one, fetch_value
from ZeMusic.models import (
    User, Chat, ChatSettings, AuthorizedUser, SudoUser,
    BannedUser, GBannedUser, BlacklistedChat, ActiveChat,
    PlayQueue, Assistant, SystemSetting, BotStats, ActivityLog
)
from ZeMusic.logging import LOGGER

class BaseDAL:
    """
    طبقة الوصول الأساسية للبيانات
    """
    
    def __init__(self):
        self.is_postgresql = config.DATABASE_TYPE == "postgresql"
    
    async def _execute(self, query: str, *args) -> str:
        """تنفيذ استعلام"""
        if self.is_postgresql:
            return await execute_query(query, *args)
        return None
    
    async def _fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """جلب جميع النتائج"""
        if self.is_postgresql:
            return await fetch_all(query, *args)
        return []
    
    async def _fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """جلب سطر واحد"""
        if self.is_postgresql:
            return await fetch_one(query, *args)
        return None
    
    async def _fetch_value(self, query: str, *args) -> Any:
        """جلب قيمة واحدة"""
        if self.is_postgresql:
            return await fetch_value(query, *args)
        return None

class UserDAL(BaseDAL):
    """
    طبقة الوصول لبيانات المستخدمين
    """
    
    async def add_served_user(self, user_id: int) -> bool:
        """إضافة مستخدم مخدوم"""
        try:
            if not self.is_postgresql:
                return True
            
            await self._execute(
                """
                INSERT INTO users (user_id, is_active) 
                VALUES ($1, $2) 
                ON CONFLICT (user_id) DO UPDATE SET 
                    last_activity = CURRENT_TIMESTAMP,
                    is_active = $2
                """,
                user_id, True
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إضافة المستخدم {user_id}: {e}")
            return False
    
    async def is_served_user(self, user_id: int) -> bool:
        """فحص وجود المستخدم"""
        try:
            if not self.is_postgresql:
                return True
            
            result = await self._fetch_value(
                "SELECT EXISTS(SELECT 1 FROM users WHERE user_id = $1 AND is_active = TRUE)",
                user_id
            )
            return bool(result)
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في فحص المستخدم {user_id}: {e}")
            return False
    
    async def get_served_users(self) -> List[int]:
        """جلب جميع المستخدمين المخدومين"""
        try:
            if not self.is_postgresql:
                return []
            
            rows = await self._fetch_all(
                "SELECT user_id FROM users WHERE is_active = TRUE ORDER BY joined_at DESC"
            )
            return [row['user_id'] for row in rows]
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في جلب المستخدمين: {e}")
            return []
    
    async def update_user_info(self, user_id: int, first_name: str = None, 
                              last_name: str = None, username: str = None) -> bool:
        """تحديث معلومات المستخدم"""
        try:
            if not self.is_postgresql:
                return True
            
            update_fields = []
            values = []
            param_count = 1
            
            if first_name is not None:
                update_fields.append(f"first_name = ${param_count}")
                values.append(first_name)
                param_count += 1
            
            if last_name is not None:
                update_fields.append(f"last_name = ${param_count}")
                values.append(last_name)
                param_count += 1
            
            if username is not None:
                update_fields.append(f"username = ${param_count}")
                values.append(username)
                param_count += 1
            
            if not update_fields:
                return True
            
            update_fields.append(f"last_activity = CURRENT_TIMESTAMP")
            values.append(user_id)
            
            query = f"""
                UPDATE users 
                SET {', '.join(update_fields)}
                WHERE user_id = ${param_count}
            """
            
            await self._execute(query, *values)
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تحديث المستخدم {user_id}: {e}")
            return False

class ChatDAL(BaseDAL):
    """
    طبقة الوصول لبيانات المحادثات
    """
    
    async def add_served_chat(self, chat_id: int, chat_type: str = "group", 
                             title: str = None) -> bool:
        """إضافة محادثة مخدومة"""
        try:
            if not self.is_postgresql:
                return True
            
            await self._execute(
                """
                INSERT INTO chats (chat_id, chat_type, title, is_active) 
                VALUES ($1, $2, $3, $4) 
                ON CONFLICT (chat_id) DO UPDATE SET 
                    last_activity = CURRENT_TIMESTAMP,
                    is_active = $4,
                    title = COALESCE($3, chats.title)
                """,
                chat_id, chat_type, title, True
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إضافة المحادثة {chat_id}: {e}")
            return False
    
    async def is_served_chat(self, chat_id: int) -> bool:
        """فحص وجود المحادثة"""
        try:
            if not self.is_postgresql:
                return True
            
            result = await self._fetch_value(
                "SELECT EXISTS(SELECT 1 FROM chats WHERE chat_id = $1 AND is_active = TRUE)",
                chat_id
            )
            return bool(result)
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في فحص المحادثة {chat_id}: {e}")
            return False
    
    async def get_served_chats(self) -> List[int]:
        """جلب جميع المحادثات المخدومة"""
        try:
            if not self.is_postgresql:
                return []
            
            rows = await self._fetch_all(
                "SELECT chat_id FROM chats WHERE is_active = TRUE ORDER BY joined_at DESC"
            )
            return [row['chat_id'] for row in rows]
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في جلب المحادثات: {e}")
            return []

class ChatSettingsDAL(BaseDAL):
    """
    طبقة الوصول لإعدادات المحادثات
    """
    
    async def get_lang(self, chat_id: int) -> str:
        """جلب لغة المحادثة"""
        try:
            if not self.is_postgresql:
                return "ar"
            
            result = await self._fetch_value(
                """
                SELECT language FROM chat_settings 
                WHERE chat_id = $1
                """,
                chat_id
            )
            return result or "ar"
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في جلب اللغة للمحادثة {chat_id}: {e}")
            return "ar"
    
    async def set_lang(self, chat_id: int, lang: str) -> bool:
        """تعيين لغة المحادثة"""
        try:
            if not self.is_postgresql:
                return True
            
            await self._execute(
                """
                INSERT INTO chat_settings (chat_id, language) 
                VALUES ($1, $2) 
                ON CONFLICT (chat_id) DO UPDATE SET 
                    language = $2,
                    updated_at = CURRENT_TIMESTAMP
                """,
                chat_id, lang
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تعيين اللغة للمحادثة {chat_id}: {e}")
            return False
    
    async def get_playmode(self, chat_id: int) -> str:
        """جلب وضع التشغيل"""
        try:
            if not self.is_postgresql:
                return "everyone"
            
            result = await self._fetch_value(
                "SELECT play_mode FROM chat_settings WHERE chat_id = $1",
                chat_id
            )
            return result or "everyone"
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في جلب وضع التشغيل للمحادثة {chat_id}: {e}")
            return "everyone"
    
    async def set_playmode(self, chat_id: int, mode: str) -> bool:
        """تعيين وضع التشغيل"""
        try:
            if not self.is_postgresql:
                return True
            
            await self._execute(
                """
                INSERT INTO chat_settings (chat_id, play_mode) 
                VALUES ($1, $2) 
                ON CONFLICT (chat_id) DO UPDATE SET 
                    play_mode = $2,
                    updated_at = CURRENT_TIMESTAMP
                """,
                chat_id, mode
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تعيين وضع التشغيل للمحادثة {chat_id}: {e}")
            return False
    
    async def get_playtype(self, chat_id: int) -> str:
        """جلب نوع التشغيل"""
        try:
            if not self.is_postgresql:
                return "music"
            
            result = await self._fetch_value(
                "SELECT play_type FROM chat_settings WHERE chat_id = $1",
                chat_id
            )
            return result or "music"
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في جلب نوع التشغيل للمحادثة {chat_id}: {e}")
            return "music"
    
    async def set_playtype(self, chat_id: int, play_type: str) -> bool:
        """تعيين نوع التشغيل"""
        try:
            if not self.is_postgresql:
                return True
            
            await self._execute(
                """
                INSERT INTO chat_settings (chat_id, play_type) 
                VALUES ($1, $2) 
                ON CONFLICT (chat_id) DO UPDATE SET 
                    play_type = $2,
                    updated_at = CURRENT_TIMESTAMP
                """,
                chat_id, play_type
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تعيين نوع التشغيل للمحادثة {chat_id}: {e}")
            return False
    
    async def get_upvote_count(self, chat_id: int) -> int:
        """جلب عدد الأصوات المطلوبة"""
        try:
            if not self.is_postgresql:
                return 5
            
            result = await self._fetch_value(
                "SELECT upvote_count FROM chat_settings WHERE chat_id = $1",
                chat_id
            )
            return result or 5
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في جلب عدد الأصوات للمحادثة {chat_id}: {e}")
            return 5
    
    async def set_upvotes(self, chat_id: int, count: int) -> bool:
        """تعيين عدد الأصوات المطلوبة"""
        try:
            if not self.is_postgresql:
                return True
            
            await self._execute(
                """
                INSERT INTO chat_settings (chat_id, upvote_count) 
                VALUES ($1, $2) 
                ON CONFLICT (chat_id) DO UPDATE SET 
                    upvote_count = $2,
                    updated_at = CURRENT_TIMESTAMP
                """,
                chat_id, count
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تعيين عدد الأصوات للمحادثة {chat_id}: {e}")
            return False

class AuthDAL(BaseDAL):
    """
    طبقة الوصول لبيانات الصلاحيات والمطورين
    """
    
    async def get_authuser_names(self, chat_id: int) -> List[str]:
        """جلب أسماء المستخدمين المصرح لهم"""
        try:
            if not self.is_postgresql:
                return []
            
            rows = await self._fetch_all(
                "SELECT user_name FROM authorized_users WHERE chat_id = $1",
                chat_id
            )
            return [row['user_name'] for row in rows]
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في جلب أسماء المصرح لهم في {chat_id}: {e}")
            return []
    
    async def get_authuser(self, chat_id: int, name: str) -> Union[bool, dict]:
        """جلب بيانات مستخدم مصرح"""
        try:
            if not self.is_postgresql:
                return False
            
            row = await self._fetch_one(
                "SELECT * FROM authorized_users WHERE chat_id = $1 AND user_name = $2",
                chat_id, name
            )
            return dict(row) if row else False
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في جلب المستخدم المصرح {name} في {chat_id}: {e}")
            return False
    
    async def save_authuser(self, chat_id: int, name: str, note: dict) -> bool:
        """حفظ مستخدم مصرح"""
        try:
            if not self.is_postgresql:
                return True
            
            import json
            await self._execute(
                """
                INSERT INTO authorized_users (chat_id, user_id, user_name, notes) 
                VALUES ($1, $2, $3, $4) 
                ON CONFLICT (chat_id, user_id) DO UPDATE SET 
                    user_name = $3,
                    notes = $4,
                    updated_at = CURRENT_TIMESTAMP
                """,
                chat_id, note.get('user_id', 0), name, json.dumps(note)
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في حفظ المستخدم المصرح {name} في {chat_id}: {e}")
            return False
    
    async def delete_authuser(self, chat_id: int, name: str) -> bool:
        """حذف مستخدم مصرح"""
        try:
            if not self.is_postgresql:
                return True
            
            result = await self._execute(
                "DELETE FROM authorized_users WHERE chat_id = $1 AND user_name = $2",
                chat_id, name
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في حذف المستخدم المصرح {name} من {chat_id}: {e}")
            return False
    
    async def get_sudoers(self) -> List[int]:
        """جلب جميع المطورين"""
        try:
            if not self.is_postgresql:
                return []
            
            rows = await self._fetch_all(
                "SELECT user_id FROM sudo_users WHERE is_active = TRUE"
            )
            return [row['user_id'] for row in rows]
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في جلب المطورين: {e}")
            return []
    
    async def add_sudo(self, user_id: int) -> bool:
        """إضافة مطور"""
        try:
            if not self.is_postgresql:
                return True
            
            await self._execute(
                """
                INSERT INTO sudo_users (user_id, is_active) 
                VALUES ($1, $2) 
                ON CONFLICT (user_id) DO UPDATE SET 
                    is_active = $2,
                    updated_at = CURRENT_TIMESTAMP
                """,
                user_id, True
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إضافة المطور {user_id}: {e}")
            return False
    
    async def remove_sudo(self, user_id: int) -> bool:
        """حذف مطور"""
        try:
            if not self.is_postgresql:
                return True
            
            await self._execute(
                "UPDATE sudo_users SET is_active = FALSE WHERE user_id = $1",
                user_id
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في حذف المطور {user_id}: {e}")
            return False

class BanDAL(BaseDAL):
    """
    طبقة الوصول لبيانات الحظر
    """
    
    async def get_banned_users(self) -> List[int]:
        """جلب جميع المستخدمين المحظورين محلياً"""
        try:
            if not self.is_postgresql:
                return []
            
            rows = await self._fetch_all(
                "SELECT user_id FROM banned_users WHERE is_active = TRUE"
            )
            return [row['user_id'] for row in rows]
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في جلب المحظورين محلياً: {e}")
            return []
    
    async def get_banned_count(self) -> int:
        """جلب عدد المحظورين محلياً"""
        try:
            if not self.is_postgresql:
                return 0
            
            result = await self._fetch_value(
                "SELECT COUNT(*) FROM banned_users WHERE is_active = TRUE"
            )
            return result or 0
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في جلب عدد المحظورين: {e}")
            return 0
    
    async def is_banned_user(self, user_id: int) -> bool:
        """فحص حظر المستخدم محلياً"""
        try:
            if not self.is_postgresql:
                return False
            
            result = await self._fetch_value(
                "SELECT EXISTS(SELECT 1 FROM banned_users WHERE user_id = $1 AND is_active = TRUE)",
                user_id
            )
            return bool(result)
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في فحص حظر المستخدم {user_id}: {e}")
            return False
    
    async def add_banned_user(self, user_id: int) -> bool:
        """إضافة مستخدم محظور محلياً"""
        try:
            if not self.is_postgresql:
                return True
            
            await self._execute(
                """
                INSERT INTO banned_users (user_id, is_active) 
                VALUES ($1, $2) 
                ON CONFLICT (user_id) DO UPDATE SET 
                    is_active = $2,
                    updated_at = CURRENT_TIMESTAMP
                """,
                user_id, True
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في حظر المستخدم {user_id}: {e}")
            return False
    
    async def remove_banned_user(self, user_id: int) -> bool:
        """إزالة حظر المستخدم محلياً"""
        try:
            if not self.is_postgresql:
                return True
            
            await self._execute(
                "UPDATE banned_users SET is_active = FALSE WHERE user_id = $1",
                user_id
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إزالة حظر المستخدم {user_id}: {e}")
            return False
    
    async def get_gbanned(self) -> List[int]:
        """جلب جميع المستخدمين المحظورين عامياً"""
        try:
            if not self.is_postgresql:
                return []
            
            rows = await self._fetch_all(
                "SELECT user_id FROM gbanned_users WHERE is_active = TRUE"
            )
            return [row['user_id'] for row in rows]
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في جلب المحظورين عامياً: {e}")
            return []
    
    async def is_gbanned_user(self, user_id: int) -> bool:
        """فحص الحظر العام للمستخدم"""
        try:
            if not self.is_postgresql:
                return False
            
            result = await self._fetch_value(
                "SELECT EXISTS(SELECT 1 FROM gbanned_users WHERE user_id = $1 AND is_active = TRUE)",
                user_id
            )
            return bool(result)
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في فحص الحظر العام للمستخدم {user_id}: {e}")
            return False
    
    async def add_gban_user(self, user_id: int) -> bool:
        """إضافة حظر عام للمستخدم"""
        try:
            if not self.is_postgresql:
                return True
            
            await self._execute(
                """
                INSERT INTO gbanned_users (user_id, is_active) 
                VALUES ($1, $2) 
                ON CONFLICT (user_id) DO UPDATE SET 
                    is_active = $2,
                    updated_at = CURRENT_TIMESTAMP
                """,
                user_id, True
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في الحظر العام للمستخدم {user_id}: {e}")
            return False
    
    async def remove_gban_user(self, user_id: int) -> bool:
        """إزالة الحظر العام للمستخدم"""
        try:
            if not self.is_postgresql:
                return True
            
            await self._execute(
                "UPDATE gbanned_users SET is_active = FALSE WHERE user_id = $1",
                user_id
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إزالة الحظر العام للمستخدم {user_id}: {e}")
            return False
    
    async def blacklisted_chats(self) -> List[int]:
        """جلب المحادثات المحظورة"""
        try:
            if not self.is_postgresql:
                return []
            
            rows = await self._fetch_all(
                "SELECT chat_id FROM blacklisted_chats WHERE is_active = TRUE"
            )
            return [row['chat_id'] for row in rows]
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في جلب المحادثات المحظورة: {e}")
            return []
    
    async def blacklist_chat(self, chat_id: int) -> bool:
        """إضافة محادثة للقائمة السوداء"""
        try:
            if not self.is_postgresql:
                return True
            
            await self._execute(
                """
                INSERT INTO blacklisted_chats (chat_id, is_active) 
                VALUES ($1, $2) 
                ON CONFLICT (chat_id) DO UPDATE SET 
                    is_active = $2,
                    updated_at = CURRENT_TIMESTAMP
                """,
                chat_id, True
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في حظر المحادثة {chat_id}: {e}")
            return False
    
    async def whitelist_chat(self, chat_id: int) -> bool:
        """إزالة محادثة من القائمة السوداء"""
        try:
            if not self.is_postgresql:
                return True
            
            await self._execute(
                "UPDATE blacklisted_chats SET is_active = FALSE WHERE chat_id = $1",
                chat_id
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إزالة حظر المحادثة {chat_id}: {e}")
            return False

class DownloadDAL(BaseDAL):
    """
    طبقة الوصول لبيانات التحميل والتخزين المؤقت
    """
    
    async def get_cached_audio(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        جلب معلومات الملف الصوتي من التخزين المؤقت
        """
        query = """
        SELECT video_id, title, uploader, duration, file_path, file_size, 
               audio_quality, file_format, thumbnail_url, view_count, 
               like_count, upload_date, download_count, last_accessed, 
               is_available, metadata
        FROM audio_cache 
        WHERE video_id = $1 AND is_available = TRUE
        """
        result = await self._fetch_one(query, video_id)
        
        if result:
            # تحديث آخر وصول
            await self.update_last_accessed(video_id)
            
        return result
    
    async def save_audio_cache(self, video_info: Dict[str, Any]) -> bool:
        """
        حفظ معلومات الملف الصوتي في التخزين المؤقت
        """
        query = """
        INSERT INTO audio_cache (
            video_id, title, uploader, duration, file_path, file_size,
            audio_quality, file_format, thumbnail_url, view_count,
            like_count, upload_date, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        ON CONFLICT (video_id) 
        DO UPDATE SET
            title = EXCLUDED.title,
            file_path = EXCLUDED.file_path,
            file_size = EXCLUDED.file_size,
            download_count = audio_cache.download_count + 1,
            last_accessed = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        """
        
        try:
            await self._execute(
                query,
                video_info.get('video_id'),
                video_info.get('title'),
                video_info.get('uploader'),
                video_info.get('duration', 0),
                video_info.get('file_path'),
                video_info.get('file_size', 0),
                video_info.get('audio_quality', '320'),
                video_info.get('file_format', 'mp3'),
                video_info.get('thumbnail_url'),
                video_info.get('view_count', 0),
                video_info.get('like_count', 0),
                video_info.get('upload_date'),
                video_info.get('metadata', {})
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في حفظ التخزين المؤقت: {e}")
            return False
    
    async def update_last_accessed(self, video_id: str) -> bool:
        """
        تحديث آخر وقت وصول للملف
        """
        query = """
        UPDATE audio_cache 
        SET last_accessed = CURRENT_TIMESTAMP 
        WHERE video_id = $1
        """
        try:
            await self._execute(query, video_id)
            return True
        except:
            return False
    
    async def get_search_history(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        جلب تاريخ البحث للاستعلام المحدد
        """
        search_query = """
        SELECT DISTINCT sh.video_id, sh.query, ac.title, ac.uploader, 
               sh.created_at, ac.download_count
        FROM search_history sh
        LEFT JOIN audio_cache ac ON sh.video_id = ac.video_id
        WHERE sh.query ILIKE $1 AND sh.success = TRUE
        ORDER BY sh.created_at DESC, ac.download_count DESC NULLS LAST
        LIMIT $2
        """
        return await self._fetch_all(search_query, f"%{query}%", limit)
    
    async def log_search(self, user_id: int, chat_id: int, query: str, 
                        video_id: str = None, result_count: int = 0,
                        response_time_ms: int = 0, was_cached: bool = False,
                        success: bool = True, error_message: str = None) -> bool:
        """
        تسجيل عملية البحث
        """
        insert_query = """
        INSERT INTO search_history (
            user_id, chat_id, query, video_id, result_count, 
            response_time_ms, was_cached, success, error_message
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        
        try:
            await self._execute(
                insert_query, user_id, chat_id, query, video_id,
                result_count, response_time_ms, was_cached, success, error_message
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تسجيل البحث: {e}")
            return False
    
    async def log_download(self, user_id: int, chat_id: int, video_id: str,
                          audio_title: str, file_size: int = 0,
                          download_time_seconds: int = 0, audio_quality: str = '320',
                          was_cached: bool = False, success: bool = True,
                          error_code: str = None, error_message: str = None) -> bool:
        """
        تسجيل عملية التحميل
        """
        insert_query = """
        INSERT INTO download_stats (
            user_id, chat_id, video_id, audio_title, file_size,
            download_time_seconds, audio_quality, was_cached, 
            success, error_code, error_message
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """
        
        try:
            await self._execute(
                insert_query, user_id, chat_id, video_id, audio_title,
                file_size, download_time_seconds, audio_quality, was_cached,
                success, error_code, error_message
            )
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تسجيل التحميل: {e}")
            return False
    
    async def get_popular_content(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        جلب المحتوى الأكثر شعبية
        """
        query = """
        SELECT video_id, title, uploader, download_count, 
               unique_users_count, trending_score, last_downloaded
        FROM popular_content
        ORDER BY trending_score DESC, download_count DESC
        LIMIT $1
        """
        return await self._fetch_all(query, limit)
    
    async def update_popular_content(self, video_id: str, title: str, 
                                   uploader: str = None) -> bool:
        """
        تحديث إحصائيات المحتوى الشعبي
        """
        query = """
        INSERT INTO popular_content (video_id, title, uploader, download_count, unique_users_count)
        VALUES ($1, $2, $3, 1, 1)
        ON CONFLICT (video_id)
        DO UPDATE SET
            download_count = popular_content.download_count + 1,
            last_downloaded = CURRENT_TIMESTAMP,
            trending_score = (popular_content.download_count + 1) * 
                           (EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - popular_content.created_at)) / 86400.0 + 1),
            updated_at = CURRENT_TIMESTAMP
        """
        
        try:
            await self._execute(query, video_id, title, uploader)
            return True
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تحديث المحتوى الشعبي: {e}")
            return False
    
    async def cleanup_old_cache(self, days_old: int = 7) -> int:
        """
        تنظيف الملفات القديمة من التخزين المؤقت
        """
        query = """
        DELETE FROM audio_cache 
        WHERE last_accessed < CURRENT_TIMESTAMP - INTERVAL '%s days'
        AND download_count < 5
        """
        
        try:
            result = await self._execute(query % days_old)
            return int(result.split()[-1]) if result else 0
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تنظيف التخزين المؤقت: {e}")
            return 0
    
    async def get_download_stats_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        جلب ملخص إحصائيات التحميل
        """
        query = """
        SELECT 
            COUNT(*) as total_downloads,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT video_id) as unique_videos,
            AVG(download_time_seconds) as avg_download_time,
            SUM(file_size) as total_size_bytes,
            COUNT(CASE WHEN was_cached THEN 1 END) as cached_downloads,
            COUNT(CASE WHEN success THEN 1 END) as successful_downloads
        FROM download_stats
        WHERE download_date >= CURRENT_TIMESTAMP - INTERVAL '%s days'
        """
        
        result = await self._fetch_one(query % days)
        return result or {}


# إنشاء instances عامة
user_dal = UserDAL()
chat_dal = ChatDAL()
chat_settings_dal = ChatSettingsDAL()
auth_dal = AuthDAL()
ban_dal = BanDAL()
download_dal = DownloadDAL()
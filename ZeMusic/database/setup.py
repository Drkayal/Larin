"""
Database Setup Script
سكريبت إعداد قاعدة البيانات
"""

import asyncio
import os
import subprocess
from typing import Optional

import config
from ZeMusic.core.postgres import postgres_db, fetch_value, execute_query
from ZeMusic.logging import LOGGER

async def create_database_if_not_exists():
    """
    إنشاء قاعدة البيانات إذا لم تكن موجودة
    """
    if config.DATABASE_TYPE != "postgresql":
        return True
    
    try:
        # الاتصال بقاعدة postgres الافتراضية للتحقق من وجود قاعدة البيانات
        import asyncpg
        
        # إنشاء URI للاتصال بقاعدة postgres
        postgres_uri = config.POSTGRES_URI.replace(f"/{config.POSTGRES_DB}", "/postgres")
        
        conn = await asyncpg.connect(postgres_uri)
        
        # التحقق من وجود قاعدة البيانات
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", 
            config.POSTGRES_DB
        )
        
        if not exists:
            LOGGER(__name__).info(f"إنشاء قاعدة البيانات: {config.POSTGRES_DB}")
            await conn.execute(f'CREATE DATABASE "{config.POSTGRES_DB}"')
            LOGGER(__name__).info("تم إنشاء قاعدة البيانات بنجاح")
        else:
            LOGGER(__name__).info("قاعدة البيانات موجودة بالفعل")
        
        await conn.close()
        return True
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في إنشاء قاعدة البيانات: {e}")
        return False

async def execute_sql_file(file_path: str) -> bool:
    """
    تنفيذ ملف SQL
    """
    try:
        if not os.path.exists(file_path):
            LOGGER(__name__).error(f"ملف SQL غير موجود: {file_path}")
            return False

        if config.DATABASE_TYPE != "postgresql":
            return True

        host = config.POSTGRES_HOST
        port = str(config.POSTGRES_PORT)
        user = config.POSTGRES_USER
        db = config.POSTGRES_DB
        password = config.POSTGRES_PASSWORD or ""

        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password

        cmd = [
            "psql",
            "-h", host,
            "-p", port,
            "-U", user,
            "-d", db,
            "-v", "ON_ERROR_STOP=1",
            "-f", file_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            LOGGER(__name__).error(f"خطأ في تنفيذ ملف SQL: {result.stderr.strip()}")
            return False

        if result.stdout:
            LOGGER(__name__).info(result.stdout.strip())

        LOGGER(__name__).info(f"تم تنفيذ ملف SQL بنجاح: {file_path}")
        return True

    except Exception as e:
        LOGGER(__name__).error(f"خطأ في تنفيذ ملف SQL: {e}")
        return False

async def create_tables() -> bool:
    """
    إنشاء جميع الجداول
    """
    try:
        schema_file = os.path.join(os.getcwd(), "database_schema.sql")
        success = await execute_sql_file(schema_file)
        
        # إنشاء جداول التحميل المتقدم
        if success:
            success = await create_download_tables()
            
        return success
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في إنشاء الجداول: {e}")
        return False

async def create_download_tables() -> bool:
    """
    إنشاء جداول نظام التحميل المتقدم
    """
    try:
        from ZeMusic.models.downloads import (
            AudioCache, SearchHistory, DownloadStats, 
            CacheMetrics, PopularContent
        )
        
        # إنشاء جداول التحميل
        models = [
            AudioCache(),
            SearchHistory(),
            DownloadStats(),
            CacheMetrics(),
            PopularContent()
        ]
        
        for model in models:
            try:
                await execute_query(model.create_sql)
                LOGGER(__name__).info(f"تم إنشاء جدول {model.table_name} بنجاح")
            except Exception as e:
                LOGGER(__name__).error(f"خطأ في إنشاء جدول {model.table_name}: {e}")
                return False
        
        LOGGER(__name__).info("تم إنشاء جميع جداول التحميل بنجاح")
        return True
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في إنشاء جداول التحميل: {e}")
        return False

async def insert_initial_data() -> bool:
    """
    إدراج البيانات الأولية
    """
    try:
        # إعدادات النظام الأولية
        initial_settings = [
            ('maintenance_mode', 'false', 'boolean', 'وضع الصيانة للبوت'),
            ('auto_end_enabled', 'true', 'boolean', 'تفعيل الإنهاء التلقائي'),
            ('global_search_enabled', 'true', 'boolean', 'تفعيل البحث العام'),
            ('max_queue_size', '50', 'integer', 'الحد الأقصى لقائمة الانتظار'),
            ('default_language', 'ar', 'string', 'اللغة الافتراضية'),
            ('bot_version', '2.0.0', 'string', 'إصدار البوت'),
            ('last_backup', '', 'string', 'آخر نسخة احتياطية'),
        ]
        
        for key, value, type_, desc in initial_settings:
            try:
                await execute_query(
                    """
                    INSERT INTO system_settings (setting_key, setting_value, setting_type, description) 
                    VALUES ($1, $2, $3, $4) 
                    ON CONFLICT (setting_key) DO NOTHING
                    """,
                    key, value, type_, desc
                )
            except Exception as e:
                LOGGER(__name__).warning(f"تحذير في إدراج الإعداد {key}: {e}")
        
        # إحصائيات اليوم الحالي
        try:
            from datetime import date
            today = date.today()
            await execute_query(
                """
                INSERT INTO bot_stats (stat_date) 
                VALUES ($1) 
                ON CONFLICT (stat_date) DO NOTHING
                """,
                today
            )
        except Exception as e:
            LOGGER(__name__).warning(f"تحذير في إدراج إحصائيات اليوم: {e}")
        
        # إضافة المطور الرئيسي
        try:
            await execute_query(
                """
                INSERT INTO users (user_id, first_name, is_active) 
                VALUES ($1, $2, $3) 
                ON CONFLICT (user_id) DO NOTHING
                """,
                config.OWNER_ID, "المطور الرئيسي", True
            )
            
            await execute_query(
                """
                INSERT INTO sudo_users (user_id, is_active) 
                VALUES ($1, $2) 
                ON CONFLICT (user_id) DO NOTHING
                """,
                config.OWNER_ID, True
            )
        except Exception as e:
            LOGGER(__name__).warning(f"تحذير في إضافة المطور الرئيسي: {e}")
        
        LOGGER(__name__).info("تم إدراج البيانات الأولية بنجاح")
        return True
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في إدراج البيانات الأولية: {e}")
        return False

async def verify_database() -> bool:
    """
    التحقق من سلامة قاعدة البيانات
    """
    try:
        # التحقق من وجود الجداول الأساسية
        required_tables = [
            'users', 'chats', 'chat_settings', 'authorized_users',
            'sudo_users', 'banned_users', 'gbanned_users', 'blacklisted_chats',
            'active_chats', 'play_queue', 'assistants', 'system_settings',
            'bot_stats', 'activity_logs'
        ]
        
        for table in required_tables:
            exists = await fetch_value(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                )
                """,
                table
            )
            
            if not exists:
                LOGGER(__name__).error(f"الجدول المطلوب غير موجود: {table}")
                return False
        
        # اختبار إدراج وحذف سجل تجريبي
        test_key = "test_connection_" + str(int(asyncio.get_event_loop().time()))
        
        await execute_query(
            "INSERT INTO system_settings (setting_key, setting_value) VALUES ($1, $2)",
            test_key, "test"
        )
        
        result = await fetch_value(
            "SELECT setting_value FROM system_settings WHERE setting_key = $1",
            test_key
        )
        
        if result != "test":
            LOGGER(__name__).error("فشل في اختبار الكتابة والقراءة")
            return False
        
        await execute_query(
            "DELETE FROM system_settings WHERE setting_key = $1",
            test_key
        )
        
        LOGGER(__name__).info("تم التحقق من سلامة قاعدة البيانات بنجاح")
        return True
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في التحقق من قاعدة البيانات: {e}")
        return False

async def setup_database() -> bool:
    """
    إعداد قاعدة البيانات الكامل
    """
    if config.DATABASE_TYPE != "postgresql":
        LOGGER(__name__).info("تم تخطي إعداد PostgreSQL - النوع المحدد: " + config.DATABASE_TYPE)
        return True
    
    try:
        LOGGER(__name__).info("بدء إعداد قاعدة البيانات...")
        
        # 1. إنشاء قاعدة البيانات إذا لم تكن موجودة
        if not await create_database_if_not_exists():
            return False
        
        # 2. الاتصال بقاعدة البيانات
        if not await postgres_db.connect():
            return False
        
        # 3. إنشاء الجداول
        if not await create_tables():
            return False
        
        # 4. إدراج البيانات الأولية
        if not await insert_initial_data():
            return False
        
        # 5. التحقق من سلامة قاعدة البيانات
        if not await verify_database():
            return False
        
        LOGGER(__name__).info("تم إعداد قاعدة البيانات بنجاح! ✅")
        return True
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في إعداد قاعدة البيانات: {e}")
        return False

async def drop_database() -> bool:
    """
    حذف قاعدة البيانات (خطر!)
    """
    if config.DATABASE_TYPE != "postgresql":
        return True
    
    try:
        LOGGER(__name__).warning("تحذير: سيتم حذف قاعدة البيانات!")
        
        import asyncpg
        postgres_uri = config.POSTGRES_URI.replace(f"/{config.POSTGRES_DB}", "/postgres")
        conn = await asyncpg.connect(postgres_uri)
        
        # قطع جميع الاتصالات النشطة
        await conn.execute(
            """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = $1 AND pid <> pg_backend_pid()
            """,
            config.POSTGRES_DB
        )
        
        # حذف قاعدة البيانات
        await conn.execute(f'DROP DATABASE IF EXISTS "{config.POSTGRES_DB}"')
        await conn.close()
        
        LOGGER(__name__).info("تم حذف قاعدة البيانات")
        return True
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في حذف قاعدة البيانات: {e}")
        return False

async def reset_database() -> bool:
    """
    إعادة تعيين قاعدة البيانات (حذف وإعادة إنشاء)
    """
    LOGGER(__name__).info("بدء إعادة تعيين قاعدة البيانات...")
    
    # حذف قاعدة البيانات
    if not await drop_database():
        return False
    
    # إعادة إنشاء قاعدة البيانات
    if not await setup_database():
        return False
    
    LOGGER(__name__).info("تم إعادة تعيين قاعدة البيانات بنجاح! ✅")
    return True

# دالة مساعدة للتشغيل من سطر الأوامر
async def main():
    """
    دالة رئيسية للتشغيل المباشر
    """
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "setup":
            success = await setup_database()
        elif command == "drop":
            success = await drop_database()
        elif command == "reset":
            success = await reset_database()
        else:
            print("الأوامر المتاحة: setup, drop, reset")
            return
        
        if success:
            print("تم تنفيذ الأمر بنجاح ✅")
        else:
            print("فشل في تنفيذ الأمر ❌")
    else:
        # الإعداد الافتراضي
        success = await setup_database()
        if success:
            print("تم إعداد قاعدة البيانات بنجاح ✅")
        else:
            print("فشل في إعداد قاعدة البيانات ❌")

if __name__ == "__main__":
    asyncio.run(main())
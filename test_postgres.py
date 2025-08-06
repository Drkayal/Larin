#!/usr/bin/env python3
"""
اختبار إعدادات PostgreSQL
"""

import asyncio
import asyncpg
import sys

async def test_postgres_connection():
    """اختبار الاتصال بقاعدة البيانات"""
    
    # إعدادات قاعدة البيانات
    POSTGRES_HOST = "localhost"
    POSTGRES_PORT = 5432
    POSTGRES_DB = "postgres"  # قاعدة البيانات الافتراضية
    POSTGRES_USER = "postgres"
    POSTGRES_PASSWORD = "your_password_here"  # استبدل بكلمة المرور الخاصة بك
    
    try:
        # إنشاء URI الاتصال
        uri = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        
        print("🔍 اختبار الاتصال بقاعدة البيانات...")
        
        # الاتصال بقاعدة البيانات
        conn = await asyncpg.connect(uri)
        
        # اختبار استعلام بسيط
        version = await conn.fetchval('SELECT version()')
        print(f"✅ تم الاتصال بنجاح!")
        print(f"📊 إصدار PostgreSQL: {version}")
        
        # التحقق من وجود قاعدة البيانات zemusic_bot
        databases = await conn.fetch('SELECT datname FROM pg_database')
        db_names = [row['datname'] for row in databases]
        
        if 'zemusic_bot' in db_names:
            print("✅ قاعدة البيانات zemusic_bot موجودة")
        else:
            print("⚠️ قاعدة البيانات zemusic_bot غير موجودة - سيتم إنشاؤها تلقائياً")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")
        return False

async def create_test_database():
    """إنشاء قاعدة بيانات اختبار"""
    
    POSTGRES_HOST = "localhost"
    POSTGRES_PORT = 5432
    POSTGRES_DB = "postgres"
    POSTGRES_USER = "postgres"
    POSTGRES_PASSWORD = "your_password_here"
    
    try:
        # الاتصال بقاعدة postgres الافتراضية
        uri = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        conn = await asyncpg.connect(uri)
        
        # إنشاء قاعدة البيانات zemusic_bot
        await conn.execute('CREATE DATABASE zemusic_bot')
        print("✅ تم إنشاء قاعدة البيانات zemusic_bot")
        
        await conn.close()
        return True
        
    except Exception as e:
        if "already exists" in str(e).lower():
            print("ℹ️ قاعدة البيانات zemusic_bot موجودة بالفعل")
            return True
        else:
            print(f"❌ خطأ في إنشاء قاعدة البيانات: {e}")
            return False

async def main():
    """الدالة الرئيسية"""
    print("🚀 بدء اختبار إعدادات PostgreSQL...")
    
    # اختبار الاتصال
    if await test_postgres_connection():
        print("\n📋 الإعدادات المطلوبة لـ config.py:")
        print("""
DATABASE_TYPE = "postgresql"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_DB = "zemusic_bot"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "your_password_here"  # استبدل بكلمة المرور الخاصة بك
        """)
        
        print("\n📋 الإعدادات المطلوبة لـ .env:")
        print("""
DATABASE_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=zemusic_bot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
        """)
        
        # إنشاء قاعدة البيانات
        await create_test_database()
        
        print("\n✅ تم إعداد PostgreSQL بنجاح!")
        print("🎵 يمكنك الآن تشغيل البوت!")
        
    else:
        print("\n❌ فشل في الاتصال بقاعدة البيانات")
        print("🔧 تأكد من:")
        print("   1. تثبيت PostgreSQL")
        print("   2. تشغيل خدمة PostgreSQL")
        print("   3. إعداد كلمة مرور للمستخدم postgres")
        print("   4. صحة الإعدادات في config.py")

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
نظام إنشاء حساب قاعدة البيانات تلقائياً
Auto Database Account Creation
"""

import os
import subprocess
import asyncio
import asyncpg
from typing import Dict, Optional

async def check_database_exists() -> bool:
    """التحقق من وجود قاعدة البيانات"""
    try:
        # محاولة الاتصال بقاعدة البيانات الحالية
        db_name = os.getenv("POSTGRES_DB", "zemusic_bot")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "")
        
        if password:
            uri = f"postgresql://{user}:{password}@localhost:5432/{db_name}"
        else:
            uri = f"postgresql://{user}@localhost:5432/{db_name}"
        
        conn = await asyncpg.connect(uri)
        await conn.close()
        return True
        
    except:
        return False

async def create_postgresql_user() -> Dict[str, str]:
    """إنشاء مستخدم PostgreSQL تلقائياً"""
    try:
        # توليد اسم مستخدم فريد
        import uuid
        import socket
        hostname = socket.gethostname().replace('-', '_').replace('.', '_')
        unique_id = str(uuid.uuid4())[:8]
        db_user = f"{hostname}_{unique_id}_user"
        
        # توليد كلمة مرور قوية
        import secrets
        import string
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        
        # إنشاء المستخدم
        create_user_cmd = f'sudo -u postgres psql -c "CREATE USER \\"{db_user}\\" WITH PASSWORD \'{password}\';"'
        result = subprocess.run(create_user_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            # إذا فشل، استخدم المستخدم الافتراضي
            db_user = "postgres"
            password = ""
        
        return {
            "user": db_user,
            "password": password
        }
        
    except Exception as e:
        print(f"خطأ في إنشاء المستخدم: {e}")
        return {"user": "postgres", "password": ""}

async def create_database_account() -> Dict[str, str]:
    """إنشاء حساب قاعدة البيانات الكامل"""
    try:
        # 1. إنشاء المستخدم
        user_info = await create_postgresql_user()
        
        # 2. إنشاء قاعدة البيانات
        db_name = f"{user_info['user']}_db"
        create_db_cmd = f'sudo -u postgres psql -c "CREATE DATABASE \\"{db_name}\\" OWNER \\"{user_info[\"user\"]}\\";"'
        result = subprocess.run(create_db_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            # إذا فشل، استخدم اسم افتراضي
            db_name = "zemusic_bot"
        
        # 3. إعطاء الصلاحيات
        if user_info['user'] != "postgres":
            grant_cmd = f'sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE \\"{db_name}\\" TO \\"{user_info[\"user\"]}\\";"'
            subprocess.run(grant_cmd, shell=True, capture_output=True, text=True)
        
        return {
            "DATABASE_TYPE": "postgresql",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": db_name,
            "POSTGRES_USER": user_info['user'],
            "POSTGRES_PASSWORD": user_info['password']
        }
        
    except Exception as e:
        print(f"خطأ في إنشاء حساب قاعدة البيانات: {e}")
        return {
            "DATABASE_TYPE": "postgresql",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "zemusic_bot",
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": ""
        }

def update_config_file(db_config: Dict[str, str]):
    """تحديث ملف config.py بالإعدادات الجديدة"""
    try:
        # قراءة config.py
        with open('config.py', 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # تحديث الإعدادات
        for key, value in db_config.items():
            if key == "POSTGRES_PASSWORD":
                # تحديث كلمة المرور
                config_content = config_content.replace(
                    'POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD", "")',
                    f'POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD", "{value}")'
                )
            elif key == "POSTGRES_DB":
                # تحديث اسم قاعدة البيانات
                config_content = config_content.replace(
                    'POSTGRES_DB = getenv("POSTGRES_DB", "zemusic_bot")',
                    f'POSTGRES_DB = getenv("POSTGRES_DB", "{value}")'
                )
            elif key == "POSTGRES_USER":
                # تحديث اسم المستخدم
                config_content = config_content.replace(
                    'POSTGRES_USER = getenv("POSTGRES_USER", "postgres")',
                    f'POSTGRES_USER = getenv("POSTGRES_USER", "{value}")'
                )
        
        # كتابة التحديثات
        with open('config.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print("✅ تم تحديث config.py بالإعدادات الجديدة")
        
    except Exception as e:
        print(f"❌ خطأ في تحديث config.py: {e}")

async def auto_setup_database():
    """إعداد قاعدة البيانات التلقائي الكامل"""
    print("🔍 التحقق من وجود قاعدة البيانات...")
    
    # التحقق من وجود قاعدة البيانات
    if await check_database_exists():
        print("✅ قاعدة البيانات موجودة بالفعل - لا حاجة لإنشاء حساب جديد")
        return None
    
    print("🚀 قاعدة البيانات غير موجودة - بدء إنشاء حساب قاعدة البيانات تلقائياً...")
    
    # 1. إنشاء حساب قاعدة البيانات
    db_config = await create_database_account()
    
    # 2. عرض المعلومات
    print("📋 معلومات حساب قاعدة البيانات الجديد:")
    for key, value in db_config.items():
        if key == "POSTGRES_PASSWORD":
            print(f"   {key} = {'***' if value else '(فارغ)'}")
        else:
            print(f"   {key} = {value}")
    
    # 3. تحديث config.py
    update_config_file(db_config)
    
    # 4. تحديث متغيرات البيئة
    for key, value in db_config.items():
        os.environ[key] = str(value)
    
    print("✅ تم إنشاء وإعداد قاعدة البيانات تلقائياً!")
    return db_config

# تشغيل الإعداد عند استيراد الوحدة
if __name__ == "__main__":
    asyncio.run(auto_setup_database())
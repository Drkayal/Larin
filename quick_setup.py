#!/usr/bin/env python3
"""
سكريبت سريع لإعداد PostgreSQL لجميع البوتات
Quick PostgreSQL Setup for Multiple Bots
"""

import os
import subprocess
import sys

def run_command(command):
    """تشغيل أمر في النظام"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def quick_setup():
    """إعداد سريع لـ PostgreSQL"""
    print("🚀 بدء الإعداد السريع لـ PostgreSQL...")
    
    # كلمة مرور موحدة
    password = "zemusic123"
    
    # 1. تثبيت PostgreSQL
    print("📦 تثبيت PostgreSQL...")
    success, stdout, stderr = run_command("sudo apt update && sudo apt install postgresql postgresql-contrib -y")
    if success:
        print("✅ تم تثبيت PostgreSQL")
    else:
        print("❌ فشل في تثبيت PostgreSQL")
        return False
    
    # 2. بدء تشغيل PostgreSQL
    print("⚡ بدء تشغيل PostgreSQL...")
    success, stdout, stderr = run_command("sudo service postgresql start")
    if success:
        print("✅ تم بدء تشغيل PostgreSQL")
    else:
        print("❌ فشل في بدء تشغيل PostgreSQL")
        return False
    
    # 3. إعداد كلمة مرور
    print("🔐 إعداد كلمة مرور...")
    success, stdout, stderr = run_command(f'sudo -u postgres psql -c "ALTER USER postgres PASSWORD \'{password}\';"')
    if success:
        print("✅ تم إعداد كلمة المرور")
    else:
        print("❌ فشل في إعداد كلمة المرور")
        return False
    
    # 4. إنشاء قواعد البيانات
    databases = ["zemusic_bot", "bot2_db", "bot3_db"]
    for db in databases:
        print(f"📊 إنشاء قاعدة البيانات: {db}")
        success, stdout, stderr = run_command(f'sudo -u postgres psql -c "CREATE DATABASE \\"{db}\\" OWNER postgres;"')
        if success:
            print(f"✅ تم إنشاء قاعدة البيانات: {db}")
        else:
            if "already exists" in stderr.lower():
                print(f"ℹ️ قاعدة البيانات {db} موجودة بالفعل")
            else:
                print(f"❌ فشل في إنشاء قاعدة البيانات {db}")
    
    # 5. إنشاء ملف .env
    print("📝 إنشاء ملف .env...")
    env_content = f"""# PostgreSQL Database Configuration
DATABASE_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=zemusic_bot
POSTGRES_USER=postgres
POSTGRES_PASSWORD={password}

# Bot Configuration
API_ID=20036317
API_HASH=986cb4ba434870a62fe96da3b5f6d411
BOT_TOKEN=your_bot_token_here
OWNER_ID=your_owner_id_here
STRING_SESSION=your_string_session_here
LOGGER_ID=your_logger_id_here
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ تم إنشاء ملف .env")
    
    # 6. تحديث config.py
    print("⚙️ تحديث config.py...")
    config_content = f'''
# PostgreSQL Database Configuration
DATABASE_TYPE = "postgresql"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_DB = "zemusic_bot"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "{password}"

# Build PostgreSQL URI
POSTGRES_URI = f"postgresql://{{POSTGRES_USER}}:{{POSTGRES_PASSWORD}}@{{POSTGRES_HOST}}:{{POSTGRES_PORT}}/{{POSTGRES_DB}}"
'''
    
    # إضافة الإعدادات إلى config.py
    try:
        with open('config.py', 'a', encoding='utf-8') as f:
            f.write(config_content)
        print("✅ تم تحديث config.py")
    except:
        print("⚠️ لم يتم تحديث config.py - سيتم إنشاؤه تلقائياً")
    
    print("\n🎉 تم الإعداد السريع بنجاح!")
    print(f"🔑 كلمة مرور PostgreSQL: {password}")
    print("📋 الإعدادات المطلوبة:")
    print(f"   DATABASE_TYPE = 'postgresql'")
    print(f"   POSTGRES_HOST = 'localhost'")
    print(f"   POSTGRES_PORT = 5432")
    print(f"   POSTGRES_DB = 'zemusic_bot'")
    print(f"   POSTGRES_USER = 'postgres'")
    print(f"   POSTGRES_PASSWORD = '{password}'")
    print("\n🚀 يمكنك الآن تشغيل البوت: python3 -m ZeMusic")
    
    return True

if __name__ == "__main__":
    quick_setup()
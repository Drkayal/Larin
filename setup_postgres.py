#!/usr/bin/env python3
"""
إعداد سريع لـ PostgreSQL
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

def setup_postgres():
    """إعداد PostgreSQL"""
    print("🚀 بدء إعداد PostgreSQL...")
    
    # 1. تثبيت PostgreSQL
    print("📦 تثبيت PostgreSQL...")
    success, stdout, stderr = run_command("sudo apt update && sudo apt install postgresql postgresql-contrib -y")
    if success:
        print("✅ تم تثبيت PostgreSQL بنجاح")
    else:
        print("❌ فشل في تثبيت PostgreSQL")
        print(f"خطأ: {stderr}")
        return False
    
    # 2. بدء تشغيل PostgreSQL
    print("⚡ بدء تشغيل PostgreSQL...")
    success, stdout, stderr = run_command("sudo service postgresql start")
    if success:
        print("✅ تم بدء تشغيل PostgreSQL")
    else:
        print("❌ فشل في بدء تشغيل PostgreSQL")
        return False
    
    # 3. إعداد كلمة مرور للمستخدم postgres
    print("🔐 إعداد كلمة مرور للمستخدم postgres...")
    password = "zemusic123"  # كلمة مرور بسيطة للاختبار
    success, stdout, stderr = run_command(f'sudo -u postgres psql -c "ALTER USER postgres PASSWORD \'{password}\';"')
    if success:
        print("✅ تم إعداد كلمة المرور")
    else:
        print("❌ فشل في إعداد كلمة المرور")
        return False
    
    # 4. إنشاء ملف .env
    print("📝 إنشاء ملف .env...")
    env_content = f"""# PostgreSQL Database Configuration
DATABASE_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=zemusic_bot
POSTGRES_USER=postgres
POSTGRES_PASSWORD={password}

# Other Bot Settings
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
    
    # 5. تحديث config.py
    print("⚙️ تحديث config.py...")
    config_content = f'''# Database Configuration
DATABASE_TYPE = "postgresql"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_DB = "zemusic_bot"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "{password}"

# Build PostgreSQL URI
POSTGRES_URI = f"postgresql://{{POSTGRES_USER}}:{{POSTGRES_PASSWORD}}@{{POSTGRES_HOST}}:{{POSTGRES_PORT}}/{{POSTGRES_DB}}"
'''
    
    # قراءة config.py الحالي
    try:
        with open('config.py', 'r', encoding='utf-8') as f:
            current_config = f.read()
        
        # إضافة إعدادات PostgreSQL إذا لم تكن موجودة
        if 'DATABASE_TYPE' not in current_config:
            with open('config.py', 'a', encoding='utf-8') as f:
                f.write('\n\n# PostgreSQL Database Configuration\n')
                f.write(config_content)
            print("✅ تم إضافة إعدادات PostgreSQL إلى config.py")
        else:
            print("ℹ️ إعدادات PostgreSQL موجودة بالفعل في config.py")
            
    except FileNotFoundError:
        print("⚠️ ملف config.py غير موجود - سيتم إنشاؤه تلقائياً عند تشغيل البوت")
    
    print("\n🎉 تم إعداد PostgreSQL بنجاح!")
    print(f"📋 كلمة مرور PostgreSQL: {password}")
    print("🔧 تأكد من تحديث باقي الإعدادات في ملف .env")
    print("🚀 يمكنك الآن تشغيل البوت باستخدام: python3 -m ZeMusic")
    
    return True

if __name__ == "__main__":
    setup_postgres()
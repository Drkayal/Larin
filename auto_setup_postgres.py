#!/usr/bin/env python3
"""
سكريبت تلقائي لإعداد PostgreSQL لجميع البوتات
Auto PostgreSQL Setup for Multiple Bots
"""

import os
import subprocess
import sys
import json
from pathlib import Path

class AutoPostgresSetup:
    def __init__(self):
        self.postgres_password = "zemusic123"  # كلمة مرور موحدة لجميع البوتات
        self.bots_config = {
            "zemusic_bot": {
                "db_name": "zemusic_bot",
                "description": "ZeMusic Bot Database"
            },
            "bot2": {
                "db_name": "bot2_db",
                "description": "Bot 2 Database"
            },
            "bot3": {
                "db_name": "bot3_db", 
                "description": "Bot 3 Database"
            }
            # يمكنك إضافة المزيد من البوتات هنا
        }
    
    def run_command(self, command, capture_output=True):
        """تشغيل أمر في النظام"""
        try:
            result = subprocess.run(command, shell=True, capture_output=capture_output, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def install_postgresql(self):
        """تثبيت PostgreSQL"""
        print("📦 تثبيت PostgreSQL...")
        
        commands = [
            "sudo apt update",
            "sudo apt install postgresql postgresql-contrib -y",
            "sudo service postgresql start",
            "sudo systemctl enable postgresql"
        ]
        
        for cmd in commands:
            success, stdout, stderr = self.run_command(cmd)
            if not success:
                print(f"❌ فشل في تنفيذ: {cmd}")
                print(f"خطأ: {stderr}")
                return False
        
        print("✅ تم تثبيت وتشغيل PostgreSQL بنجاح")
        return True
    
    def setup_postgres_user(self):
        """إعداد المستخدم postgres"""
        print("🔐 إعداد كلمة مرور للمستخدم postgres...")
        
        cmd = f'sudo -u postgres psql -c "ALTER USER postgres PASSWORD \'{self.postgres_password}\';"'
        success, stdout, stderr = self.run_command(cmd)
        
        if success:
            print("✅ تم إعداد كلمة مرور للمستخدم postgres")
            return True
        else:
            print(f"❌ فشل في إعداد كلمة المرور: {stderr}")
            return False
    
    def create_databases(self):
        """إنشاء قواعد البيانات لجميع البوتات"""
        print("🗄️ إنشاء قواعد البيانات...")
        
        for bot_name, config in self.bots_config.items():
            db_name = config['db_name']
            description = config['description']
            
            print(f"📊 إنشاء قاعدة البيانات: {db_name}")
            
            # إنشاء قاعدة البيانات
            create_cmd = f'sudo -u postgres psql -c "CREATE DATABASE \\"{db_name}\\" OWNER postgres;"'
            success, stdout, stderr = self.run_command(create_cmd)
            
            if success:
                print(f"✅ تم إنشاء قاعدة البيانات: {db_name}")
            else:
                if "already exists" in stderr.lower():
                    print(f"ℹ️ قاعدة البيانات {db_name} موجودة بالفعل")
                else:
                    print(f"❌ فشل في إنشاء قاعدة البيانات {db_name}: {stderr}")
        
        return True
    
    def create_env_template(self, bot_name, db_name):
        """إنشاء ملف .env template للبوت"""
        env_content = f"""# PostgreSQL Database Configuration
DATABASE_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB={db_name}
POSTGRES_USER=postgres
POSTGRES_PASSWORD={self.postgres_password}

# Bot Configuration
API_ID=20036317
API_HASH=986cb4ba434870a62fe96da3b5f6d411
BOT_TOKEN=your_bot_token_here
OWNER_ID=your_owner_id_here
STRING_SESSION=your_string_session_here
LOGGER_ID=your_logger_id_here

# Additional Settings
MONGO_DB_URI=your_mongo_uri_here
"""
        
        # إنشاء مجلد البوت إذا لم يكن موجوداً
        bot_dir = Path(f"./{bot_name}")
        bot_dir.mkdir(exist_ok=True)
        
        # حفظ ملف .env
        env_file = bot_dir / ".env"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print(f"✅ تم إنشاء ملف .env للبوت: {bot_name}")
        return env_file
    
    def create_config_template(self, bot_name, db_name):
        """إنشاء ملف config.py template للبوت"""
        config_content = f'''# -*- coding: utf-8 -*-
"""
Config file for {bot_name}
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_TYPE = "postgresql"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_DB = "{db_name}"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "{self.postgres_password}"

# Build PostgreSQL URI
POSTGRES_URI = f"postgresql://{{POSTGRES_USER}}:{{POSTGRES_PASSWORD}}@{{POSTGRES_HOST}}:{{POSTGRES_PORT}}/{{POSTGRES_DB}}"

# Bot Configuration
API_ID = int(os.getenv("API_ID", "20036317"))
API_HASH = os.getenv("API_HASH", "986cb4ba434870a62fe96da3b5f6d411")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
STRING_SESSION = os.getenv("STRING_SESSION", "")
LOGGER_ID = int(os.getenv("LOGGER_ID", "0"))

# Additional Settings
MONGO_DB_URI = os.getenv("MONGO_DB_URI", "")
'''
        
        # إنشاء مجلد البوت إذا لم يكن موجوداً
        bot_dir = Path(f"./{bot_name}")
        bot_dir.mkdir(exist_ok=True)
        
        # حفظ ملف config.py
        config_file = bot_dir / "config.py"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✅ تم إنشاء ملف config.py للبوت: {bot_name}")
        return config_file
    
    def create_startup_script(self, bot_name):
        """إنشاء سكريبت تشغيل للبوت"""
        script_content = f'''#!/bin/bash
# Startup script for {bot_name}

echo "🚀 بدء تشغيل {bot_name}..."

# تفعيل البيئة الافتراضية (إذا كانت موجودة)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# التحقق من PostgreSQL
echo "🗄️ التحقق من PostgreSQL..."
if ! sudo service postgresql status > /dev/null 2>&1; then
    echo "⚡ بدء تشغيل PostgreSQL..."
    sudo service postgresql start
fi

# تشغيل البوت
echo "🎵 تشغيل {bot_name}..."
cd {bot_name}
python3 -m ZeMusic
'''
        
        # حفظ سكريبت التشغيل
        script_file = Path(f"start_{bot_name}.sh")
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # جعل السكريبت قابل للتنفيذ
        os.chmod(script_file, 0o755)
        
        print(f"✅ تم إنشاء سكريبت التشغيل: start_{bot_name}.sh")
        return script_file
    
    def create_database_schema(self, bot_name, db_name):
        """إنشاء ملف schema للبوت"""
        schema_content = f'''-- Database Schema for {bot_name}
-- {self.bots_config[bot_name]['description']}

-- إنشاء قاعدة البيانات
-- CREATE DATABASE {db_name};

-- الاتصال بقاعدة البيانات
-- \\c {db_name};

-- جدول المستخدمين
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    username VARCHAR(255),
    language_code VARCHAR(10) DEFAULT 'ar',
    is_bot BOOLEAN DEFAULT FALSE,
    is_premium BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- جدول المحادثات
CREATE TABLE IF NOT EXISTS chats (
    chat_id BIGINT PRIMARY KEY,
    chat_type VARCHAR(20) NOT NULL,
    title VARCHAR(255),
    username VARCHAR(255),
    description TEXT,
    member_count INTEGER DEFAULT 0,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- جدول إعدادات المحادثات
CREATE TABLE IF NOT EXISTS chat_settings (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    language VARCHAR(10) DEFAULT 'ar',
    play_mode VARCHAR(20) DEFAULT 'everyone',
    play_type VARCHAR(20) DEFAULT 'music',
    auto_end BOOLEAN DEFAULT FALSE,
    skip_mode BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chat_id)
);

-- جدول المستخدمين المصرح لهم
CREATE TABLE IF NOT EXISTS authorized_users (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    user_name VARCHAR(255) NOT NULL,
    authorized_by BIGINT REFERENCES users(user_id),
    authorized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chat_id, user_id)
);

-- جدول المطورين
CREATE TABLE IF NOT EXISTS sudo_users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    added_by BIGINT REFERENCES users(user_id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id)
);

-- جدول المستخدمين المحظورين
CREATE TABLE IF NOT EXISTS banned_users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    banned_by BIGINT REFERENCES users(user_id),
    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id)
);

-- جدول المستخدمين المحظورين عالمياً
CREATE TABLE IF NOT EXISTS gbanned_users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    banned_by BIGINT REFERENCES users(user_id),
    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id)
);

-- جدول المحادثات المحظورة
CREATE TABLE IF NOT EXISTS blacklisted_chats (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    banned_by BIGINT REFERENCES users(user_id),
    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(chat_id)
);

-- جدول المحادثات النشطة
CREATE TABLE IF NOT EXISTS active_chats (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    is_video BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(chat_id)
);

-- جدول قائمة التشغيل
CREATE TABLE IF NOT EXISTS play_queue (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    duration INTEGER NOT NULL,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_played BOOLEAN DEFAULT FALSE,
    UNIQUE(chat_id, position)
);

-- إنشاء الفهارس
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_activity ON users(last_activity);
CREATE INDEX IF NOT EXISTS idx_chats_type ON chats(chat_type);
CREATE INDEX IF NOT EXISTS idx_chats_activity ON chats(last_activity);
CREATE INDEX IF NOT EXISTS idx_queue_chat ON play_queue(chat_id);
CREATE INDEX IF NOT EXISTS idx_queue_position ON play_queue(chat_id, position);
CREATE INDEX IF NOT EXISTS idx_active_chats_video ON active_chats(is_video);
'''
        
        # حفظ ملف schema
        schema_file = Path(f"{bot_name}/database_schema.sql")
        schema_file.parent.mkdir(exist_ok=True)
        
        with open(schema_file, 'w', encoding='utf-8') as f:
            f.write(schema_content)
        
        print(f"✅ تم إنشاء ملف schema للبوت: {bot_name}")
        return schema_file
    
    def setup_all_bots(self):
        """إعداد جميع البوتات"""
        print("🚀 بدء إعداد PostgreSQL لجميع البوتات...")
        
        # 1. تثبيت PostgreSQL
        if not self.install_postgresql():
            return False
        
        # 2. إعداد المستخدم postgres
        if not self.setup_postgres_user():
            return False
        
        # 3. إنشاء قواعد البيانات
        if not self.create_databases():
            return False
        
        # 4. إنشاء ملفات لكل بوت
        for bot_name, config in self.bots_config.items():
            print(f"\n📁 إعداد البوت: {bot_name}")
            
            db_name = config['db_name']
            
            # إنشاء ملف .env
            self.create_env_template(bot_name, db_name)
            
            # إنشاء ملف config.py
            self.create_config_template(bot_name, db_name)
            
            # إنشاء سكريبت التشغيل
            self.create_startup_script(bot_name)
            
            # إنشاء ملف schema
            self.create_database_schema(bot_name, db_name)
        
        # 5. إنشاء ملف README
        self.create_readme()
        
        print("\n🎉 تم إعداد جميع البوتات بنجاح!")
        print(f"🔑 كلمة مرور PostgreSQL: {self.postgres_password}")
        print("\n📋 كيفية التشغيل:")
        for bot_name in self.bots_config.keys():
            print(f"   ./start_{bot_name}.sh")
        
        return True
    
    def create_readme(self):
        """إنشاء ملف README"""
        readme_content = f"""# Auto PostgreSQL Setup for Multiple Bots

## 📋 الإعدادات المطلوبة

### كلمة مرور PostgreSQL:
```
{self.postgres_password}
```

## 🚀 كيفية التشغيل

### تشغيل البوتات:
```bash
# تشغيل ZeMusic Bot
./start_zemusic_bot.sh

# تشغيل Bot 2
./start_bot2.sh

# تشغيل Bot 3
./start_bot3.sh
```

## 📁 هيكل المجلدات

```
.
├── zemusic_bot/
│   ├── .env
│   ├── config.py
│   └── database_schema.sql
├── bot2/
│   ├── .env
│   ├── config.py
│   └── database_schema.sql
├── bot3/
│   ├── .env
│   ├── config.py
│   └── database_schema.sql
├── start_zemusic_bot.sh
├── start_bot2.sh
└── start_bot3.sh
```

## 🔧 الإعدادات

### PostgreSQL:
- Host: localhost
- Port: 5432
- User: postgres
- Password: {self.postgres_password}

### قواعد البيانات:
"""
        
        for bot_name, config in self.bots_config.items():
            readme_content += f"- {config['db_name']} ({config['description']})\n"
        
        readme_content += """
## ⚠️ ملاحظات مهمة

1. تأكد من تحديث BOT_TOKEN في ملف .env لكل بوت
2. تأكد من تحديث OWNER_ID في ملف .env لكل بوت
3. تأكد من تحديث STRING_SESSION في ملف .env لكل بوت
4. تأكد من تحديث LOGGER_ID في ملف .env لكل بوت

## 🛠️ إضافة بوت جديد

1. أضف البوت إلى `bots_config` في `auto_setup_postgres.py`
2. شغل السكريبت مرة أخرى
3. سيتم إنشاء جميع الملفات تلقائياً
"""
        
        with open("README_POSTGRES_SETUP.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print("✅ تم إنشاء ملف README_POSTGRES_SETUP.md")

def main():
    """الدالة الرئيسية"""
    setup = AutoPostgresSetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--add-bot":
        # إضافة بوت جديد
        if len(sys.argv) < 4:
            print("❌ الاستخدام: python3 auto_setup_postgres.py --add-bot <bot_name> <db_name>")
            return
        
        bot_name = sys.argv[2]
        db_name = sys.argv[3]
        
        setup.bots_config[bot_name] = {
            "db_name": db_name,
            "description": f"{bot_name} Database"
        }
        
        print(f"✅ تم إضافة البوت: {bot_name}")
        print("🔧 شغل السكريبت مرة أخرى لتطبيق التغييرات")
        return
    
    # إعداد جميع البوتات
    setup.setup_all_bots()

if __name__ == "__main__":
    main()
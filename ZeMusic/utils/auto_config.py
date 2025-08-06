#!/usr/bin/env python3
"""
نظام اكتشاف تلقائي لإعدادات PostgreSQL
Auto PostgreSQL Configuration Detection
"""

import os
import subprocess
import socket
import psutil
from typing import Dict, Optional

def detect_postgresql_installation() -> bool:
    """اكتشاف تثبيت PostgreSQL"""
    try:
        # التحقق من وجود psql
        result = subprocess.run(['which', 'psql'], capture_output=True, text=True)
        if result.returncode == 0:
            return True
        
        # التحقق من وجود خدمة PostgreSQL
        result = subprocess.run(['systemctl', 'status', 'postgresql'], capture_output=True, text=True)
        if result.returncode == 0:
            return True
        
        return False
    except:
        return False

def detect_postgresql_port() -> int:
    """اكتشاف منفذ PostgreSQL"""
    try:
        # محاولة الاتصال بالمنافذ الشائعة
        common_ports = [5432, 5433, 5434]
        
        for port in common_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                return port
        
        # إذا لم نجد، نستخدم المنفذ الافتراضي
        return 5432
    except:
        return 5432

def detect_postgresql_user() -> str:
    """اكتشاف مستخدم PostgreSQL"""
    try:
        # التحقق من وجود مستخدم postgres
        result = subprocess.run(['id', 'postgres'], capture_output=True, text=True)
        if result.returncode == 0:
            return "postgres"
        
        # التحقق من مستخدمين آخرين
        users = ['postgres', 'pgsql', 'postgresql']
        for user in users:
            result = subprocess.run(['id', user], capture_output=True, text=True)
            if result.returncode == 0:
                return user
        
        return "postgres"
    except:
        return "postgres"

def generate_database_name() -> str:
    """توليد اسم قاعدة بيانات فريد"""
    import uuid
    import socket
    
    # استخدام اسم الجهاز + معرف فريد
    hostname = socket.gethostname().replace('-', '_').replace('.', '_')
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{hostname}_{unique_id}_bot"

def detect_postgresql_password() -> Optional[str]:
    """اكتشاف كلمة مرور PostgreSQL"""
    try:
        # محاولة الاتصال بدون كلمة مرور
        result = subprocess.run(
            ['sudo', '-u', 'postgres', 'psql', '-c', 'SELECT 1;'],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            return ""  # لا توجد كلمة مرور
        
        # محاولة كلمات مرور شائعة
        common_passwords = ['', 'postgres', 'admin', 'password', '123456']
        
        for password in common_passwords:
            try:
                if password:
                    cmd = f'PGPASSWORD={password} psql -h localhost -U postgres -c "SELECT 1;"'
                else:
                    cmd = 'sudo -u postgres psql -c "SELECT 1;"'
                
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    return password
            except:
                continue
        
        return None
    except:
        return None

def auto_configure_postgresql() -> Dict[str, any]:
    """التكوين التلقائي لـ PostgreSQL"""
    config = {}
    
    # 1. اكتشاف التثبيت
    if not detect_postgresql_installation():
        print("⚠️ PostgreSQL غير مثبت - سيتم تثبيته تلقائياً")
        # هنا يمكن إضافة تثبيت تلقائي
    
    # 2. إعدادات افتراضية
    config['DATABASE_TYPE'] = "postgresql"
    config['POSTGRES_HOST'] = "localhost"
    config['POSTGRES_PORT'] = detect_postgresql_port()
    config['POSTGRES_USER'] = detect_postgresql_user()
    
    # 3. توليد اسم قاعدة بيانات فريد
    config['POSTGRES_DB'] = generate_database_name()
    
    # 4. اكتشاف كلمة المرور
    password = detect_postgresql_password()
    config['POSTGRES_PASSWORD'] = password if password is not None else ""
    
    # 5. بناء URI
    if config['POSTGRES_PASSWORD']:
        config['POSTGRES_URI'] = f"postgresql://{config['POSTGRES_USER']}:{config['POSTGRES_PASSWORD']}@{config['POSTGRES_HOST']}:{config['POSTGRES_PORT']}/{config['POSTGRES_DB']}"
    else:
        config['POSTGRES_URI'] = f"postgresql://{config['POSTGRES_USER']}@{config['POSTGRES_HOST']}:{config['POSTGRES_PORT']}/{config['POSTGRES_DB']}"
    
    return config

def apply_auto_config():
    """تطبيق التكوين التلقائي"""
    config = auto_configure_postgresql()
    
    print("🔍 اكتشاف إعدادات PostgreSQL تلقائياً...")
    print(f"   DATABASE_TYPE = {config['DATABASE_TYPE']}")
    print(f"   POSTGRES_HOST = {config['POSTGRES_HOST']}")
    print(f"   POSTGRES_PORT = {config['POSTGRES_PORT']}")
    print(f"   POSTGRES_DB = {config['POSTGRES_DB']}")
    print(f"   POSTGRES_USER = {config['POSTGRES_USER']}")
    print(f"   POSTGRES_PASSWORD = {'***' if config['POSTGRES_PASSWORD'] else '(فارغ)'}")
    
    # تحديث متغيرات البيئة
    for key, value in config.items():
        os.environ[key] = str(value)
    
    return config

# تطبيق التكوين عند استيراد الوحدة
AUTO_CONFIG = apply_auto_config()
"""
Database Backup and Restore
نظام النسخ الاحتياطي واستعادة قاعدة البيانات
"""

import os
import asyncio
import gzip
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

import config
from ZeMusic.core.postgres import fetch_all, execute_query
from ZeMusic.logging import LOGGER

async def backup_database(backup_path: Optional[str] = None) -> str:
    """
    إنشاء نسخة احتياطية من قاعدة البيانات
    """
    if config.DATABASE_TYPE != "postgresql":
        LOGGER(__name__).info("تم تخطي النسخ الاحتياطي - قاعدة البيانات ليست PostgreSQL")
        return ""
    
    try:
        # إنشاء اسم الملف
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not backup_path:
            backup_dir = os.path.join(os.getcwd(), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, f"zemusic_backup_{timestamp}.json.gz")
        
        LOGGER(__name__).info(f"بدء إنشاء نسخة احتياطية: {backup_path}")
        
        # جلب بيانات جميع الجداول
        backup_data = {
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "database_type": config.DATABASE_TYPE,
                "bot_version": "2.0.0",
                "backup_version": "1.0"
            },
            "tables": {}
        }
        
        # قائمة الجداول للنسخ الاحتياطي
        tables = [
            "users", "chats", "chat_settings", "authorized_users",
            "sudo_users", "banned_users", "gbanned_users", "blacklisted_chats",
            "active_chats", "play_queue", "assistants", "system_settings",
            "bot_stats", "activity_logs"
        ]
        
        for table in tables:
            try:
                rows = await fetch_all(f"SELECT * FROM {table}")
                backup_data["tables"][table] = []
                
                for row in rows:
                    # تحويل التواريخ إلى نص
                    clean_row = {}
                    for key, value in row.items():
                        if isinstance(value, datetime):
                            clean_row[key] = value.isoformat()
                        elif hasattr(value, 'date'):  # date objects
                            clean_row[key] = value.isoformat()
                        else:
                            clean_row[key] = value
                    backup_data["tables"][table].append(clean_row)
                
                LOGGER(__name__).info(f"تم نسخ جدول {table}: {len(rows)} سجل")
                
            except Exception as e:
                LOGGER(__name__).warning(f"تحذير في نسخ جدول {table}: {e}")
                backup_data["tables"][table] = []
        
        # حفظ النسخة الاحتياطية مضغوطة
        json_data = json.dumps(backup_data, ensure_ascii=False, indent=2)
        
        with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
            f.write(json_data)
        
        # تحديث آخر نسخة احتياطية في الإعدادات
        try:
            await execute_query(
                """
                INSERT INTO system_settings (setting_key, setting_value, setting_type, description) 
                VALUES ('last_backup', $1, 'string', 'آخر نسخة احتياطية') 
                ON CONFLICT (setting_key) DO UPDATE SET 
                    setting_value = EXCLUDED.setting_value,
                    updated_at = CURRENT_TIMESTAMP
                """,
                datetime.utcnow().isoformat()
            )
        except:
            pass
        
        file_size = os.path.getsize(backup_path) / (1024 * 1024)  # MB
        LOGGER(__name__).info(f"تم إنشاء النسخة الاحتياطية بنجاح: {backup_path} ({file_size:.2f} MB)")
        
        return backup_path
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
        return ""

async def restore_database(backup_path: str, confirm: bool = False) -> bool:
    """
    استعادة قاعدة البيانات من نسخة احتياطية
    """
    if config.DATABASE_TYPE != "postgresql":
        LOGGER(__name__).info("تم تخطي الاستعادة - قاعدة البيانات ليست PostgreSQL")
        return True
    
    if not confirm:
        LOGGER(__name__).error("يجب تأكيد الاستعادة بتمرير confirm=True")
        return False
    
    try:
        if not os.path.exists(backup_path):
            LOGGER(__name__).error(f"ملف النسخة الاحتياطية غير موجود: {backup_path}")
            return False
        
        LOGGER(__name__).warning(f"بدء استعادة قاعدة البيانات من: {backup_path}")
        
        # قراءة النسخة الاحتياطية
        with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # التحقق من صحة النسخة الاحتياطية
        if "metadata" not in backup_data or "tables" not in backup_data:
            LOGGER(__name__).error("ملف النسخة الاحتياطية غير صالح")
            return False
        
        metadata = backup_data["metadata"]
        LOGGER(__name__).info(f"استعادة نسخة احتياطية من: {metadata.get('created_at', 'غير معروف')}")
        
        # حذف البيانات الحالية (خطر!)
        tables = list(backup_data["tables"].keys())
        for table in reversed(tables):  # ترتيب عكسي لتجنب مشاكل المفاتيح الخارجية
            try:
                await execute_query(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                LOGGER(__name__).info(f"تم تفريغ جدول {table}")
            except Exception as e:
                LOGGER(__name__).warning(f"تحذير في تفريغ جدول {table}: {e}")
        
        # استعادة البيانات
        for table, rows in backup_data["tables"].items():
            if not rows:
                continue
            
            try:
                # الحصول على أعمدة الجدول
                columns = list(rows[0].keys())
                
                # إنشاء استعلام INSERT
                placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])
                query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
                
                # إدراج البيانات
                for row in rows:
                    values = []
                    for col in columns:
                        value = row[col]
                        
                        # تحويل التواريخ من نص
                        if col in ['created_at', 'updated_at', 'joined_at', 'last_activity', 
                                  'authorized_at', 'banned_at', 'blacklisted_at', 'added_at', 
                                  'started_at', 'assigned_at'] and isinstance(value, str):
                            try:
                                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            except:
                                value = datetime.utcnow()
                        elif col == 'stat_date' and isinstance(value, str):
                            try:
                                value = datetime.fromisoformat(value).date()
                            except:
                                value = datetime.utcnow().date()
                        
                        values.append(value)
                    
                    await execute_query(query, *values)
                
                LOGGER(__name__).info(f"تم استعادة جدول {table}: {len(rows)} سجل")
                
            except Exception as e:
                LOGGER(__name__).error(f"خطأ في استعادة جدول {table}: {e}")
                return False
        
        LOGGER(__name__).info("تم استعادة قاعدة البيانات بنجاح! ✅")
        return True
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في استعادة قاعدة البيانات: {e}")
        return False

async def list_backups(backup_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    قائمة النسخ الاحتياطية المتاحة
    """
    if not backup_dir:
        backup_dir = os.path.join(os.getcwd(), "backups")
    
    if not os.path.exists(backup_dir):
        return []
    
    backups = []
    
    for filename in os.listdir(backup_dir):
        if filename.startswith("zemusic_backup_") and filename.endswith(".json.gz"):
            filepath = os.path.join(backup_dir, filename)
            
            try:
                # قراءة metadata
                with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                    metadata = data.get("metadata", {})
                
                file_stats = os.stat(filepath)
                
                backups.append({
                    "filename": filename,
                    "filepath": filepath,
                    "created_at": metadata.get("created_at", "غير معروف"),
                    "file_size": file_stats.st_size,
                    "file_size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                    "bot_version": metadata.get("bot_version", "غير معروف"),
                    "backup_version": metadata.get("backup_version", "1.0")
                })
                
            except Exception as e:
                LOGGER(__name__).warning(f"خطأ في قراءة النسخة الاحتياطية {filename}: {e}")
    
    # ترتيب حسب التاريخ (الأحدث أولاً)
    backups.sort(key=lambda x: x["created_at"], reverse=True)
    
    return backups

async def cleanup_old_backups(backup_dir: Optional[str] = None, keep_count: int = 5) -> int:
    """
    تنظيف النسخ الاحتياطية القديمة
    """
    backups = await list_backups(backup_dir)
    
    if len(backups) <= keep_count:
        return 0
    
    deleted_count = 0
    
    # حذف النسخ الزائدة
    for backup in backups[keep_count:]:
        try:
            os.remove(backup["filepath"])
            LOGGER(__name__).info(f"تم حذف النسخة الاحتياطية القديمة: {backup['filename']}")
            deleted_count += 1
        except Exception as e:
            LOGGER(__name__).warning(f"خطأ في حذف النسخة الاحتياطية {backup['filename']}: {e}")
    
    return deleted_count

async def auto_backup() -> bool:
    """
    نسخة احتياطية تلقائية
    """
    try:
        # إنشاء نسخة احتياطية
        backup_path = await backup_database()
        
        if not backup_path:
            return False
        
        # تنظيف النسخ القديمة
        deleted = await cleanup_old_backups(keep_count=7)  # الاحتفاظ بـ 7 نسخ
        
        if deleted > 0:
            LOGGER(__name__).info(f"تم حذف {deleted} نسخة احتياطية قديمة")
        
        return True
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في النسخ الاحتياطي التلقائي: {e}")
        return False

# للتشغيل المباشر
async def main():
    """دالة رئيسية للتشغيل المباشر"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "backup":
            backup_path = await backup_database()
            print(f"تم إنشاء النسخة الاحتياطية: {backup_path}" if backup_path else "فشل في إنشاء النسخة الاحتياطية")
        
        elif command == "restore" and len(sys.argv) > 2:
            backup_path = sys.argv[2]
            print("تحذير: سيتم حذف جميع البيانات الحالية!")
            confirm = input("هل أنت متأكد؟ (yes/no): ").lower() == "yes"
            
            if confirm:
                success = await restore_database(backup_path, confirm=True)
                print("تم استعادة قاعدة البيانات بنجاح ✅" if success else "فشل في استعادة قاعدة البيانات ❌")
            else:
                print("تم إلغاء الاستعادة")
        
        elif command == "list":
            backups = await list_backups()
            if backups:
                print(f"النسخ الاحتياطية المتاحة ({len(backups)}):")
                for backup in backups:
                    print(f"  - {backup['filename']} ({backup['file_size_mb']} MB) - {backup['created_at']}")
            else:
                print("لا توجد نسخ احتياطية")
        
        elif command == "cleanup":
            deleted = await cleanup_old_backups()
            print(f"تم حذف {deleted} نسخة احتياطية قديمة")
        
        elif command == "auto":
            success = await auto_backup()
            print("تم النسخ الاحتياطي التلقائي بنجاح ✅" if success else "فشل في النسخ الاحتياطي التلقائي ❌")
        
        else:
            print("الأوامر المتاحة: backup, restore <file>, list, cleanup, auto")
    else:
        print("الأوامر المتاحة: backup, restore <file>, list, cleanup, auto")

if __name__ == "__main__":
    asyncio.run(main())
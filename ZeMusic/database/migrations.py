"""
Database Migrations
نظام إدارة تحديثات قاعدة البيانات
"""

import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any

import config
from ZeMusic.core.postgres import execute_query, fetch_all, fetch_value
from ZeMusic.logging import LOGGER

class Migration:
    """
    فئة التحديث
    """
    
    def __init__(self, version: str, description: str, up_sql: str, down_sql: str = ""):
        self.version = version
        self.description = description
        self.up_sql = up_sql
        self.down_sql = down_sql
        self.created_at = datetime.utcnow()
    
    async def apply(self) -> bool:
        """تطبيق التحديث"""
        try:
            await execute_query(self.up_sql)
            await self._record_migration()
            LOGGER(__name__).info(f"تم تطبيق التحديث: {self.version} - {self.description}")
            return True
        except Exception as e:
            LOGGER(__name__).error(f"فشل في تطبيق التحديث {self.version}: {e}")
            return False
    
    async def rollback(self) -> bool:
        """التراجع عن التحديث"""
        if not self.down_sql:
            LOGGER(__name__).warning(f"لا يوجد سكريبت تراجع للتحديث: {self.version}")
            return False
        
        try:
            await execute_query(self.down_sql)
            await self._remove_migration_record()
            LOGGER(__name__).info(f"تم التراجع عن التحديث: {self.version}")
            return True
        except Exception as e:
            LOGGER(__name__).error(f"فشل في التراجع عن التحديث {self.version}: {e}")
            return False
    
    async def _record_migration(self):
        """تسجيل التحديث في قاعدة البيانات"""
        await execute_query(
            """
            INSERT INTO system_settings (setting_key, setting_value, setting_type, description) 
            VALUES ($1, $2, 'string', $3) 
            ON CONFLICT (setting_key) DO UPDATE SET 
                setting_value = EXCLUDED.setting_value,
                description = EXCLUDED.description,
                updated_at = CURRENT_TIMESTAMP
            """,
            f"migration_{self.version}",
            self.created_at.isoformat(),
            f"Migration: {self.description}"
        )
    
    async def _remove_migration_record(self):
        """حذف سجل التحديث"""
        await execute_query(
            "DELETE FROM system_settings WHERE setting_key = $1",
            f"migration_{self.version}"
        )

class MigrationManager:
    """
    مدير التحديثات
    """
    
    def __init__(self):
        self.migrations: List[Migration] = []
    
    def add_migration(self, migration: Migration):
        """إضافة تحديث"""
        self.migrations.append(migration)
    
    async def get_applied_migrations(self) -> List[str]:
        """الحصول على التحديثات المطبقة"""
        try:
            results = await fetch_all(
                "SELECT setting_key FROM system_settings WHERE setting_key LIKE 'migration_%'"
            )
            return [row['setting_key'].replace('migration_', '') for row in results]
        except:
            return []
    
    async def get_pending_migrations(self) -> List[Migration]:
        """الحصول على التحديثات المعلقة"""
        applied = await self.get_applied_migrations()
        return [m for m in self.migrations if m.version not in applied]
    
    async def run_migrations(self) -> bool:
        """تشغيل جميع التحديثات المعلقة"""
        if config.DATABASE_TYPE != "postgresql":
            return True
        
        try:
            pending = await self.get_pending_migrations()
            
            if not pending:
                LOGGER(__name__).info("لا توجد تحديثات معلقة")
                return True
            
            LOGGER(__name__).info(f"تشغيل {len(pending)} تحديث معلق...")
            
            for migration in sorted(pending, key=lambda m: m.version):
                if not await migration.apply():
                    return False
            
            LOGGER(__name__).info("تم تطبيق جميع التحديثات بنجاح")
            return True
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تشغيل التحديثات: {e}")
            return False
    
    async def rollback_migration(self, version: str) -> bool:
        """التراجع عن تحديث محدد"""
        migration = next((m for m in self.migrations if m.version == version), None)
        
        if not migration:
            LOGGER(__name__).error(f"التحديث غير موجود: {version}")
            return False
        
        applied = await self.get_applied_migrations()
        if version not in applied:
            LOGGER(__name__).warning(f"التحديث غير مطبق: {version}")
            return True
        
        return await migration.rollback()

# إنشاء مدير التحديثات العام
migration_manager = MigrationManager()

# التحديثات المتاحة
def register_migrations():
    """تسجيل جميع التحديثات"""
    
    # التحديث 1.0.0: إضافة فهارس إضافية
    migration_manager.add_migration(Migration(
        version="1.0.0",
        description="إضافة فهارس إضافية للأداء",
        up_sql="""
            CREATE INDEX IF NOT EXISTS idx_users_joined_at ON users(joined_at);
            CREATE INDEX IF NOT EXISTS idx_chats_joined_at ON chats(joined_at);
            CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at);
        """,
        down_sql="""
            DROP INDEX IF EXISTS idx_users_joined_at;
            DROP INDEX IF EXISTS idx_chats_joined_at;
            DROP INDEX IF EXISTS idx_activity_logs_created_at;
        """
    ))
    
    # التحديث 1.1.0: إضافة جدول الإشعارات
    migration_manager.add_migration(Migration(
        version="1.1.0",
        description="إضافة جدول الإشعارات",
        up_sql="""
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
            CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
        """,
        down_sql="""
            DROP TABLE IF EXISTS notifications;
        """
    ))
    
    # التحديث 1.2.0: تحسين جدول play_queue
    migration_manager.add_migration(Migration(
        version="1.2.0", 
        description="تحسين جدول قائمة الانتظار",
        up_sql="""
            ALTER TABLE play_queue ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 0;
            ALTER TABLE play_queue ADD COLUMN IF NOT EXISTS duration INTEGER DEFAULT 0;
            CREATE INDEX IF NOT EXISTS idx_play_queue_priority ON play_queue(chat_id, priority, position);
        """,
        down_sql="""
            DROP INDEX IF EXISTS idx_play_queue_priority;
            ALTER TABLE play_queue DROP COLUMN IF EXISTS priority;
            ALTER TABLE play_queue DROP COLUMN IF EXISTS duration;
        """
    ))

# وظائف المساعدة
async def run_migrations() -> bool:
    """تشغيل جميع التحديثات"""
    register_migrations()
    return await migration_manager.run_migrations()

async def create_migration(version: str, description: str, up_sql: str, down_sql: str = "") -> bool:
    """إنشاء تحديث جديد"""
    migration = Migration(version, description, up_sql, down_sql)
    migration_manager.add_migration(migration)
    
    # تطبيق التحديث فوراً
    return await migration.apply()

async def rollback_migration(version: str) -> bool:
    """التراجع عن تحديث"""
    register_migrations()
    return await migration_manager.rollback_migration(version)

async def get_migration_status() -> Dict[str, Any]:
    """الحصول على حالة التحديثات"""
    register_migrations()
    
    applied = await migration_manager.get_applied_migrations()
    pending = await migration_manager.get_pending_migrations()
    
    return {
        "total_migrations": len(migration_manager.migrations),
        "applied_count": len(applied),
        "pending_count": len(pending),
        "applied_versions": applied,
        "pending_versions": [m.version for m in pending]
    }

# للتشغيل المباشر
async def main():
    """دالة رئيسية للتشغيل المباشر"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "run":
            success = await run_migrations()
            print("تم تطبيق التحديثات بنجاح ✅" if success else "فشل في تطبيق التحديثات ❌")
        
        elif command == "status":
            status = await get_migration_status()
            print(f"إجمالي التحديثات: {status['total_migrations']}")
            print(f"المطبقة: {status['applied_count']}")
            print(f"المعلقة: {status['pending_count']}")
            
        elif command == "rollback" and len(sys.argv) > 2:
            version = sys.argv[2]
            success = await rollback_migration(version)
            print(f"تم التراجع عن التحديث {version} ✅" if success else f"فشل في التراجع عن التحديث {version} ❌")
            
        else:
            print("الأوامر المتاحة: run, status, rollback <version>")
    else:
        print("الأوامر المتاحة: run, status, rollback <version>")

if __name__ == "__main__":
    asyncio.run(main())
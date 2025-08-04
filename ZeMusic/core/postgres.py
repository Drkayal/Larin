import asyncio
import logging
from typing import Optional, Any, Dict, List
import asyncpg
from asyncpg import Pool, Connection
from contextlib import asynccontextmanager

import config
from ZeMusic.logging import LOGGER

# Global connection pool
_connection_pool: Optional[Pool] = None

class PostgreSQLConnection:
    """
    PostgreSQL Connection Manager
    إدارة الاتصالات مع قاعدة بيانات PostgreSQL
    """
    
    def __init__(self):
        self.pool: Optional[Pool] = None
        self.is_connected = False
        
    async def connect(self) -> bool:
        """
        إنشاء pool الاتصالات مع PostgreSQL
        """
        global _connection_pool
        
        try:
            LOGGER(__name__).info("يتم الاتصال بقاعدة بيانات PostgreSQL...")
            
            # إعداد pool الاتصالات
            self.pool = await asyncpg.create_pool(
                config.POSTGRES_URI,
                min_size=5,  # الحد الأدنى للاتصالات
                max_size=20,  # الحد الأقصى للاتصالات
                max_queries=50000,  # الحد الأقصى للاستعلامات لكل اتصال
                max_inactive_connection_lifetime=300.0,  # 5 دقائق
                timeout=30.0,  # مهلة الاتصال
                command_timeout=60.0,  # مهلة الأوامر
                server_settings={
                    'application_name': 'ZeMusic_Bot',
                    'timezone': 'UTC'
                }
            )
            
            _connection_pool = self.pool
            self.is_connected = True
            
            # اختبار الاتصال
            async with self.pool.acquire() as conn:
                version = await conn.fetchval('SELECT version()')
                LOGGER(__name__).info(f"تم الاتصال بنجاح - PostgreSQL: {version}")
                
            return True
            
        except Exception as e:
            LOGGER(__name__).error(f"فشل في الاتصال بقاعدة البيانات: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """
        قطع الاتصال وإغلاق pool
        """
        global _connection_pool
        
        if self.pool:
            try:
                await self.pool.close()
                LOGGER(__name__).info("تم قطع الاتصال بقاعدة البيانات")
            except Exception as e:
                LOGGER(__name__).error(f"خطأ في قطع الاتصال: {e}")
            finally:
                self.pool = None
                _connection_pool = None
                self.is_connected = False
    
    @asynccontextmanager
    async def get_connection(self):
        """
        الحصول على اتصال من pool
        """
        if not self.pool:
            raise ConnectionError("لم يتم إنشاء pool الاتصالات")
            
        conn = None
        try:
            conn = await self.pool.acquire()
            yield conn
        finally:
            if conn:
                await self.pool.release(conn)
    
    async def execute(self, query: str, *args) -> str:
        """
        تنفيذ استعلام بدون إرجاع نتائج
        """
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """
        تنفيذ استعلام وإرجاع جميع النتائج
        """
        async with self.get_connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """
        تنفيذ استعلام وإرجاع سطر واحد
        """
        async with self.get_connection() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetchval(self, query: str, *args) -> Any:
        """
        تنفيذ استعلام وإرجاع قيمة واحدة
        """
        async with self.get_connection() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute_many(self, query: str, args_list: List[tuple]) -> None:
        """
        تنفيذ استعلام متعدد
        """
        async with self.get_connection() as conn:
            await conn.executemany(query, args_list)
    
    async def transaction(self):
        """
        بدء معاملة قاعدة البيانات
        """
        if not self.pool:
            raise ConnectionError("لم يتم إنشاء pool الاتصالات")
            
        conn = await self.pool.acquire()
        return conn.transaction()

# إنشاء instance عامة
postgres_db = PostgreSQLConnection()

# وظائف مساعدة سريعة
async def get_pool() -> Optional[Pool]:
    """الحصول على pool الاتصالات"""
    global _connection_pool
    return _connection_pool

async def execute_query(query: str, *args) -> str:
    """تنفيذ استعلام سريع"""
    return await postgres_db.execute(query, *args)

async def fetch_all(query: str, *args) -> List[Dict[str, Any]]:
    """جلب جميع النتائج"""
    return await postgres_db.fetch(query, *args)

async def fetch_one(query: str, *args) -> Optional[Dict[str, Any]]:
    """جلب سطر واحد"""
    return await postgres_db.fetchrow(query, *args)

async def fetch_value(query: str, *args) -> Any:
    """جلب قيمة واحدة"""
    return await postgres_db.fetchval(query, *args)

async def init_postgres():
    """
    تهيئة اتصال PostgreSQL
    """
    if config.DATABASE_TYPE == "postgresql":
        success = await postgres_db.connect()
        if success:
            LOGGER(__name__).info("تم تهيئة PostgreSQL بنجاح")
            return True
        else:
            LOGGER(__name__).error("فشل في تهيئة PostgreSQL")
            return False
    return True

async def close_postgres():
    """
    إغلاق اتصال PostgreSQL
    """
    if postgres_db.is_connected:
        await postgres_db.disconnect()
        LOGGER(__name__).info("تم إغلاق اتصال PostgreSQL")

# معلومات الاتصال
def get_connection_info() -> Dict[str, Any]:
    """
    الحصول على معلومات الاتصال
    """
    return {
        "database_type": config.DATABASE_TYPE,
        "is_connected": postgres_db.is_connected,
        "host": config.POSTGRES_HOST if config.DATABASE_TYPE == "postgresql" else None,
        "port": config.POSTGRES_PORT if config.DATABASE_TYPE == "postgresql" else None,
        "database": config.POSTGRES_DB if config.DATABASE_TYPE == "postgresql" else None,
        "pool_size": postgres_db.pool.get_size() if postgres_db.pool else 0,
        "pool_max_size": postgres_db.pool.get_max_size() if postgres_db.pool else 0,
    }

# اختبار الاتصال
async def test_connection() -> bool:
    """
    اختبار اتصال قاعدة البيانات
    """
    try:
        if config.DATABASE_TYPE == "postgresql":
            result = await fetch_value("SELECT 1")
            return result == 1
        return True
    except Exception as e:
        LOGGER(__name__).error(f"فشل اختبار الاتصال: {e}")
        return False
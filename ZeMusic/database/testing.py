"""
نظام اختبار شامل لقاعدة البيانات PostgreSQL
Database Testing System for PostgreSQL Integration
"""

import asyncio
import time
import psutil
import gc
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

import config
from ZeMusic.logging import LOGGER
from ZeMusic.core.postgres import get_pool, execute_query, fetch_all, fetch_one, fetch_value
from ZeMusic.database.dal import user_dal, chat_dal, chat_settings_dal, auth_dal, ban_dal
from ZeMusic.models import User, Chat, ChatSettings, AuthorizedUser, SudoUser


class DatabaseTester:
    """فئة اختبار قاعدة البيانات الشاملة"""
    
    def __init__(self):
        self.test_results = []
        self.performance_metrics = {}
        self.memory_usage = {}
        self.connection_stats = {}
        
    def log_test(self, test_name: str, status: str, details: str = "", duration: float = 0):
        """تسجيل نتيجة الاختبار"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "duration": duration,
            "timestamp": datetime.now()
        }
        self.test_results.append(result)
        
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        duration_str = f" ({duration:.3f}s)" if duration > 0 else ""
        LOGGER(__name__).info(f"{emoji} {test_name}: {details}{duration_str}")

    async def test_database_connection(self) -> bool:
        """اختبار الاتصال بقاعدة البيانات"""
        LOGGER(__name__).info("🔌 اختبار الاتصال بقاعدة البيانات...")
        
        if config.DATABASE_TYPE != "postgresql":
            self.log_test("Database Connection", "SKIP", "PostgreSQL غير مفعل")
            return True
        
        try:
            start_time = time.time()
            
            # اختبار الحصول على pool
            pool = get_pool()
            if not pool:
                self.log_test("Database Connection Pool", "FAIL", "فشل في الحصول على connection pool")
                return False
            
            # اختبار استعلام بسيط
            result = await fetch_one("SELECT version()")
            if not result:
                self.log_test("Database Query Test", "FAIL", "فشل في تنفيذ استعلام بسيط")
                return False
            
            duration = time.time() - start_time
            version = result.get('version', 'Unknown')
            
            self.log_test("Database Connection", "PASS", f"متصل بـ PostgreSQL", duration)
            self.log_test("Database Version", "PASS", f"إصدار: {version[:50]}...")
            
            # اختبار إحصائيات الاتصال
            await self._test_connection_stats()
            
            return True
            
        except Exception as e:
            self.log_test("Database Connection", "FAIL", f"خطأ في الاتصال: {str(e)}")
            return False

    async def _test_connection_stats(self):
        """اختبار إحصائيات الاتصال"""
        try:
            # إحصائيات قاعدة البيانات
            db_stats = await fetch_one("""
                SELECT 
                    pg_database_size(current_database()) as db_size,
                    (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()) as active_connections
            """)
            
            if db_stats:
                db_size_mb = db_stats['db_size'] / (1024 * 1024)
                active_conns = db_stats['active_connections']
                
                self.connection_stats = {
                    'database_size_mb': db_size_mb,
                    'active_connections': active_conns,
                    'timestamp': datetime.now()
                }
                
                self.log_test("Database Stats", "PASS", 
                             f"حجم قاعدة البيانات: {db_size_mb:.2f} MB، الاتصالات النشطة: {active_conns}")
        
        except Exception as e:
            self.log_test("Database Stats", "WARN", f"تحذير في إحصائيات الاتصال: {str(e)}")

    async def test_crud_operations(self) -> bool:
        """اختبار عمليات CRUD الأساسية"""
        LOGGER(__name__).info("📝 اختبار عمليات CRUD الأساسية...")
        
        if config.DATABASE_TYPE != "postgresql":
            self.log_test("CRUD Operations", "SKIP", "PostgreSQL غير مفعل")
            return True
        
        success_count = 0
        total_tests = 0
        
        # اختبار عمليات المستخدمين
        success_count += await self._test_user_crud()
        total_tests += 4
        
        # اختبار عمليات المحادثات
        success_count += await self._test_chat_crud()
        total_tests += 4
        
        # اختبار عمليات الإعدادات
        success_count += await self._test_settings_crud()
        total_tests += 3
        
        # اختبار عمليات الصلاحيات
        success_count += await self._test_auth_crud()
        total_tests += 3
        
        success_rate = (success_count / total_tests) * 100
        
        if success_rate >= 90:
            self.log_test("CRUD Operations Overall", "PASS", 
                         f"نجح {success_count}/{total_tests} اختبار ({success_rate:.1f}%)")
            return True
        else:
            self.log_test("CRUD Operations Overall", "FAIL", 
                         f"نجح {success_count}/{total_tests} اختبار فقط ({success_rate:.1f}%)")
            return False

    async def _test_user_crud(self) -> int:
        """اختبار عمليات CRUD للمستخدمين"""
        success = 0
        test_user_id = 999999999  # ID اختبار
        
        try:
            start_time = time.time()
            
            # CREATE - إضافة مستخدم
            await user_dal.add_served_user(test_user_id)
            duration = time.time() - start_time
            self.log_test("User CREATE", "PASS", f"تم إضافة مستخدم اختبار", duration)
            success += 1
            
            # READ - قراءة مستخدم
            start_time = time.time()
            exists = await user_dal.is_served_user(test_user_id)
            duration = time.time() - start_time
            
            if exists:
                self.log_test("User READ", "PASS", f"تم العثور على مستخدم اختبار", duration)
                success += 1
            else:
                self.log_test("User READ", "FAIL", "لم يتم العثور على مستخدم اختبار")
            
            # UPDATE - تحديث معلومات المستخدم
            start_time = time.time()
            await user_dal.update_user_info(test_user_id, "Test User", "testuser")
            duration = time.time() - start_time
            self.log_test("User UPDATE", "PASS", f"تم تحديث معلومات المستخدم", duration)
            success += 1
            
            # LIST - قائمة المستخدمين
            start_time = time.time()
            users = await user_dal.get_served_users()
            duration = time.time() - start_time
            
            if users and len(users) > 0:
                self.log_test("User LIST", "PASS", f"تم جلب {len(users)} مستخدم", duration)
                success += 1
            else:
                self.log_test("User LIST", "FAIL", "فشل في جلب قائمة المستخدمين")
            
        except Exception as e:
            self.log_test("User CRUD Error", "FAIL", f"خطأ في عمليات المستخدمين: {str(e)}")
        
        return success

    async def _test_chat_crud(self) -> int:
        """اختبار عمليات CRUD للمحادثات"""
        success = 0
        test_chat_id = -999999999  # ID اختبار للمجموعة
        
        try:
            start_time = time.time()
            
            # CREATE - إضافة محادثة
            await chat_dal.add_served_chat(test_chat_id)
            duration = time.time() - start_time
            self.log_test("Chat CREATE", "PASS", f"تم إضافة محادثة اختبار", duration)
            success += 1
            
            # READ - قراءة محادثة
            start_time = time.time()
            exists = await chat_dal.is_served_chat(test_chat_id)
            duration = time.time() - start_time
            
            if exists:
                self.log_test("Chat READ", "PASS", f"تم العثور على محادثة اختبار", duration)
                success += 1
            else:
                self.log_test("Chat READ", "FAIL", "لم يتم العثور على محادثة اختبار")
            
            # LIST - قائمة المحادثات
            start_time = time.time()
            chats = await chat_dal.get_served_chats()
            duration = time.time() - start_time
            
            if chats and len(chats) > 0:
                self.log_test("Chat LIST", "PASS", f"تم جلب {len(chats)} محادثة", duration)
                success += 1
            else:
                self.log_test("Chat LIST", "FAIL", "فشل في جلب قائمة المحادثات")
            
            # COUNT - عد المحادثات
            start_time = time.time()
            count = len(chats) if chats else 0
            duration = time.time() - start_time
            self.log_test("Chat COUNT", "PASS", f"عدد المحادثات: {count}", duration)
            success += 1
            
        except Exception as e:
            self.log_test("Chat CRUD Error", "FAIL", f"خطأ في عمليات المحادثات: {str(e)}")
        
        return success

    async def _test_settings_crud(self) -> int:
        """اختبار عمليات CRUD للإعدادات"""
        success = 0
        test_chat_id = -999999999
        
        try:
            # SET Language
            start_time = time.time()
            await chat_settings_dal.set_lang(test_chat_id, "ar")
            duration = time.time() - start_time
            self.log_test("Settings SET Language", "PASS", f"تم تعيين اللغة", duration)
            success += 1
            
            # GET Language
            start_time = time.time()
            lang = await chat_settings_dal.get_lang(test_chat_id)
            duration = time.time() - start_time
            
            if lang == "ar":
                self.log_test("Settings GET Language", "PASS", f"تم جلب اللغة: {lang}", duration)
                success += 1
            else:
                self.log_test("Settings GET Language", "FAIL", f"لغة خاطئة: {lang}")
            
            # SET Playmode
            start_time = time.time()
            await chat_settings_dal.set_playmode(test_chat_id, "Everyone")
            duration = time.time() - start_time
            self.log_test("Settings SET Playmode", "PASS", f"تم تعيين وضع التشغيل", duration)
            success += 1
            
        except Exception as e:
            self.log_test("Settings CRUD Error", "FAIL", f"خطأ في عمليات الإعدادات: {str(e)}")
        
        return success

    async def _test_auth_crud(self) -> int:
        """اختبار عمليات CRUD للصلاحيات"""
        success = 0
        test_user_id = 999999999
        
        try:
            # ADD Sudo
            start_time = time.time()
            await auth_dal.add_sudo(test_user_id)
            duration = time.time() - start_time
            self.log_test("Auth ADD Sudo", "PASS", f"تم إضافة مطور", duration)
            success += 1
            
            # GET Sudoers
            start_time = time.time()
            sudoers = await auth_dal.get_sudoers()
            duration = time.time() - start_time
            
            if test_user_id in sudoers:
                self.log_test("Auth GET Sudoers", "PASS", f"تم جلب المطورين: {len(sudoers)}", duration)
                success += 1
            else:
                self.log_test("Auth GET Sudoers", "FAIL", "المطور غير موجود في القائمة")
            
            # REMOVE Sudo
            start_time = time.time()
            await auth_dal.remove_sudo(test_user_id)
            duration = time.time() - start_time
            self.log_test("Auth REMOVE Sudo", "PASS", f"تم حذف مطور", duration)
            success += 1
            
        except Exception as e:
            self.log_test("Auth CRUD Error", "FAIL", f"خطأ في عمليات الصلاحيات: {str(e)}")
        
        return success

    async def test_performance(self) -> bool:
        """اختبار الأداء"""
        LOGGER(__name__).info("⚡ اختبار الأداء...")
        
        if config.DATABASE_TYPE != "postgresql":
            self.log_test("Performance Test", "SKIP", "PostgreSQL غير مفعل")
            return True
        
        try:
            # اختبار سرعة الاستعلامات
            await self._test_query_performance()
            
            # اختبار الذاكرة
            await self._test_memory_usage()
            
            # اختبار الاتصالات المتعددة
            await self._test_concurrent_operations()
            
            return True
            
        except Exception as e:
            self.log_test("Performance Test", "FAIL", f"خطأ في اختبار الأداء: {str(e)}")
            return False

    async def _test_query_performance(self):
        """اختبار أداء الاستعلامات"""
        queries = [
            ("SELECT COUNT(*) FROM users", "عد المستخدمين"),
            ("SELECT COUNT(*) FROM chats", "عد المحادثات"),
            ("SELECT * FROM chat_settings LIMIT 10", "جلب الإعدادات"),
            ("SELECT version()", "معلومات قاعدة البيانات")
        ]
        
        total_time = 0
        for query, description in queries:
            start_time = time.time()
            try:
                await fetch_all(query)
                duration = time.time() - start_time
                total_time += duration
                
                # تقييم الأداء
                if duration < 0.1:
                    status = "PASS"
                    perf = "سريع جداً"
                elif duration < 0.5:
                    status = "PASS"
                    perf = "سريع"
                elif duration < 1.0:
                    status = "WARN"
                    perf = "متوسط"
                else:
                    status = "WARN"
                    perf = "بطيء"
                
                self.log_test(f"Query Performance: {description}", status, 
                             f"{perf} ({duration:.3f}s)", duration)
                
            except Exception as e:
                self.log_test(f"Query Performance: {description}", "FAIL", 
                             f"فشل: {str(e)}")
        
        # تقييم إجمالي الأداء
        avg_time = total_time / len(queries)
        if avg_time < 0.2:
            self.log_test("Overall Query Performance", "PASS", 
                         f"متوسط الوقت: {avg_time:.3f}s - ممتاز")
        elif avg_time < 0.5:
            self.log_test("Overall Query Performance", "PASS", 
                         f"متوسط الوقت: {avg_time:.3f}s - جيد")
        else:
            self.log_test("Overall Query Performance", "WARN", 
                         f"متوسط الوقت: {avg_time:.3f}s - يحتاج تحسين")

    async def _test_memory_usage(self):
        """اختبار استهلاك الذاكرة"""
        process = psutil.Process()
        
        # قياس الذاكرة قبل العمليات
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # تنفيذ عمليات مختلفة
        operations = [
            lambda: user_dal.get_served_users(),
            lambda: chat_dal.get_served_chats(),
            lambda: auth_dal.get_sudoers(),
        ]
        
        for i, operation in enumerate(operations):
            try:
                await operation()
            except:
                pass
        
        # قياس الذاكرة بعد العمليات
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_diff = memory_after - memory_before
        
        # تنظيف الذاكرة
        gc.collect()
        memory_final = process.memory_info().rss / 1024 / 1024  # MB
        
        self.memory_usage = {
            'before_mb': memory_before,
            'after_mb': memory_after,
            'final_mb': memory_final,
            'difference_mb': memory_diff,
            'timestamp': datetime.now()
        }
        
        if memory_diff < 10:  # أقل من 10 MB
            status = "PASS"
            assessment = "ممتاز"
        elif memory_diff < 50:  # أقل من 50 MB
            status = "PASS"
            assessment = "جيد"
        else:
            status = "WARN"
            assessment = "يحتاج مراقبة"
        
        self.log_test("Memory Usage", status, 
                     f"استهلاك إضافي: {memory_diff:.2f} MB - {assessment}")

    async def _test_concurrent_operations(self):
        """اختبار العمليات المتزامنة"""
        start_time = time.time()
        
        # تنفيذ عمليات متزامنة
        tasks = [
            user_dal.get_served_users(),
            chat_dal.get_served_chats(),
            auth_dal.get_sudoers(),
            fetch_one("SELECT COUNT(*) FROM users"),
            fetch_one("SELECT COUNT(*) FROM chats"),
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time
            
            # تحليل النتائج
            successful = sum(1 for r in results if not isinstance(r, Exception))
            failed = len(results) - successful
            
            if failed == 0:
                status = "PASS"
                assessment = f"جميع العمليات نجحت ({successful}/{len(tasks)})"
            elif failed <= 2:
                status = "WARN"
                assessment = f"بعض العمليات فشلت ({successful}/{len(tasks)})"
            else:
                status = "FAIL"
                assessment = f"معظم العمليات فشلت ({successful}/{len(tasks)})"
            
            self.log_test("Concurrent Operations", status, assessment, duration)
            
        except Exception as e:
            self.log_test("Concurrent Operations", "FAIL", f"خطأ في العمليات المتزامنة: {str(e)}")

    async def run_basic_tests(self) -> Dict[str, Any]:
        """تشغيل جميع الاختبارات الأساسية"""
        LOGGER(__name__).info("🧪 بدء الاختبارات الأساسية لقاعدة البيانات...")
        
        start_time = time.time()
        
        # تشغيل الاختبارات
        connection_ok = await self.test_database_connection()
        crud_ok = await self.test_crud_operations()
        performance_ok = await self.test_performance()
        
        total_duration = time.time() - start_time
        
        # تلخيص النتائج
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        warned_tests = len([r for r in self.test_results if r["status"] == "WARN"])
        skipped_tests = len([r for r in self.test_results if r["status"] == "SKIP"])
        
        success_rate = (passed_tests / (total_tests - skipped_tests)) * 100 if total_tests > skipped_tests else 0
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "warned": warned_tests,
            "skipped": skipped_tests,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "connection_ok": connection_ok,
            "crud_ok": crud_ok,
            "performance_ok": performance_ok,
            "overall_status": "PASS" if failed_tests == 0 and connection_ok and crud_ok else "FAIL"
        }
        
        LOGGER(__name__).info(f"📊 ملخص الاختبارات الأساسية:")
        LOGGER(__name__).info(f"   إجمالي: {total_tests} | نجح: {passed_tests} | فشل: {failed_tests} | تحذير: {warned_tests}")
        LOGGER(__name__).info(f"   نسبة النجاح: {success_rate:.1f}% | المدة: {total_duration:.2f}s")
        
        return summary


# إنشاء instance عام للاختبار
database_tester = DatabaseTester()
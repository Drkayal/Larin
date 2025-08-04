"""
أمر اختبار قاعدة البيانات للمطورين
Database Testing Command for Developers
"""

import asyncio
from pyrogram import filters
from pyrogram.types import Message

import config
from ZeMusic import app
from ZeMusic.misc import SUDOERS
from ZeMusic.utils.decorators.language import language
from ZeMusic.database import database_tester, advanced_tester


@app.on_message(filters.command(["testdb", "اختبار_قاعدة_البيانات"]) & SUDOERS)
@language
async def test_database_command(client, message: Message, _):
    """أمر اختبار قاعدة البيانات الشامل"""
    
    if config.DATABASE_TYPE != "postgresql":
        return await message.reply_text(
            "❌ **خطأ:** PostgreSQL غير مفعل!\n"
            "يجب تعيين `DATABASE_TYPE=postgresql` لتشغيل الاختبارات."
        )
    
    # رسالة البداية
    test_msg = await message.reply_text(
        "🧪 **بدء اختبار قاعدة البيانات الشامل...**\n\n"
        "⏳ جاري تشغيل الاختبارات الأساسية..."
    )
    
    try:
        # تشغيل الاختبارات الأساسية
        basic_results = await database_tester.run_basic_tests()
        
        # تحديث الرسالة
        await test_msg.edit_text(
            "🧪 **اختبار قاعدة البيانات الشامل**\n\n"
            "✅ **الاختبارات الأساسية مكتملة:**\n"
            f"├ إجمالي: {basic_results['total_tests']}\n"
            f"├ نجح: {basic_results['passed']}\n"
            f"├ فشل: {basic_results['failed']}\n"
            f"├ تحذير: {basic_results['warned']}\n"
            f"└ نسبة النجاح: {basic_results['success_rate']:.1f}%\n\n"
            "⏳ جاري تشغيل الاختبارات المتقدمة..."
        )
        
        # تشغيل الاختبارات المتقدمة
        advanced_results = await advanced_tester.run_advanced_tests()
        
        # النتائج النهائية
        total_tests = basic_results['total_tests'] + advanced_results['total_tests']
        total_passed = basic_results['passed'] + advanced_results['passed']
        total_failed = basic_results['failed'] + advanced_results['failed']
        total_warned = basic_results['warned'] + advanced_results['warned']
        total_skipped = basic_results['skipped'] + advanced_results['skipped']
        
        overall_success_rate = (total_passed / (total_tests - total_skipped)) * 100 if total_tests > total_skipped else 0
        
        # تحديد حالة النظام
        if total_failed == 0 and overall_success_rate >= 95:
            status_emoji = "🟢"
            status_text = "ممتاز"
        elif total_failed <= 2 and overall_success_rate >= 85:
            status_emoji = "🟡"
            status_text = "جيد"
        else:
            status_emoji = "🔴"
            status_text = "يحتاج انتباه"
        
        # الرسالة النهائية
        final_message = (
            f"🧪 **تقرير اختبار قاعدة البيانات الشامل**\n\n"
            f"{status_emoji} **حالة النظام: {status_text}**\n\n"
            f"📊 **الملخص الإجمالي:**\n"
            f"├ إجمالي الاختبارات: {total_tests}\n"
            f"├ ✅ نجح: {total_passed}\n"
            f"├ ❌ فشل: {total_failed}\n"
            f"├ ⚠️ تحذير: {total_warned}\n"
            f"├ ⏭️ تم تخطي: {total_skipped}\n"
            f"└ 📈 نسبة النجاح: {overall_success_rate:.1f}%\n\n"
            f"🔧 **الاختبارات الأساسية:**\n"
            f"├ اتصال قاعدة البيانات: {'✅' if basic_results['connection_ok'] else '❌'}\n"
            f"├ عمليات CRUD: {'✅' if basic_results['crud_ok'] else '❌'}\n"
            f"├ الأداء: {'✅' if basic_results['performance_ok'] else '❌'}\n"
            f"└ المدة: {basic_results['total_duration']:.2f}s\n\n"
            f"🚀 **الاختبارات المتقدمة:**\n"
            f"├ محاكاة الأوامر: {'✅' if advanced_results['commands_ok'] else '❌'}\n"
            f"├ اختبار الحمولة: {'✅' if advanced_results['load_ok'] else '❌'}\n"
            f"├ الاستقرار: {'✅' if advanced_results['stability_ok'] else '❌'}\n"
            f"└ المدة: {advanced_results['total_duration']:.2f}s\n\n"
        )
        
        # إضافة تفاصيل إضافية إذا كان هناك مشاكل
        if total_failed > 0:
            final_message += (
                f"⚠️ **تفاصيل الأخطاء:**\n"
                f"يرجى مراجعة سجلات النظام للحصول على تفاصيل أكثر.\n\n"
            )
        
        # إضافة توصيات
        if overall_success_rate >= 95:
            final_message += "🎉 **النظام يعمل بشكل مثالي!**"
        elif overall_success_rate >= 85:
            final_message += "👍 **النظام يعمل بشكل جيد مع بعض التحذيرات.**"
        else:
            final_message += "⚠️ **يُنصح بمراجعة إعدادات قاعدة البيانات.**"
        
        await test_msg.edit_text(final_message)
        
    except Exception as e:
        await test_msg.edit_text(
            f"❌ **خطأ في تشغيل الاختبارات:**\n\n"
            f"```\n{str(e)}\n```\n\n"
            f"يرجى التحقق من إعدادات قاعدة البيانات والمحاولة مرة أخرى."
        )


@app.on_message(filters.command(["testdb_basic", "اختبار_أساسي"]) & SUDOERS)
@language
async def test_database_basic_command(client, message: Message, _):
    """أمر اختبار قاعدة البيانات الأساسي فقط"""
    
    if config.DATABASE_TYPE != "postgresql":
        return await message.reply_text(
            "❌ **خطأ:** PostgreSQL غير مفعل!\n"
            "يجب تعيين `DATABASE_TYPE=postgresql` لتشغيل الاختبارات."
        )
    
    test_msg = await message.reply_text("🧪 **جاري تشغيل الاختبارات الأساسية...**")
    
    try:
        # تشغيل الاختبارات الأساسية فقط
        results = await database_tester.run_basic_tests()
        
        # تحديد الحالة
        if results['failed'] == 0:
            status_emoji = "✅"
            status_text = "نجح"
        else:
            status_emoji = "❌"
            status_text = "فشل"
        
        final_message = (
            f"🧪 **نتائج الاختبارات الأساسية**\n\n"
            f"{status_emoji} **الحالة: {status_text}**\n\n"
            f"📊 **التفاصيل:**\n"
            f"├ إجمالي: {results['total_tests']}\n"
            f"├ نجح: {results['passed']}\n"
            f"├ فشل: {results['failed']}\n"
            f"├ تحذير: {results['warned']}\n"
            f"├ تم تخطي: {results['skipped']}\n"
            f"└ نسبة النجاح: {results['success_rate']:.1f}%\n\n"
            f"🔧 **اختبارات فرعية:**\n"
            f"├ الاتصال: {'✅' if results['connection_ok'] else '❌'}\n"
            f"├ CRUD: {'✅' if results['crud_ok'] else '❌'}\n"
            f"└ الأداء: {'✅' if results['performance_ok'] else '❌'}\n\n"
            f"⏱️ **المدة الإجمالية:** {results['total_duration']:.2f}s"
        )
        
        await test_msg.edit_text(final_message)
        
    except Exception as e:
        await test_msg.edit_text(
            f"❌ **خطأ في الاختبارات الأساسية:**\n\n"
            f"```\n{str(e)}\n```"
        )


@app.on_message(filters.command(["testdb_advanced", "اختبار_متقدم"]) & SUDOERS)
@language
async def test_database_advanced_command(client, message: Message, _):
    """أمر اختبار قاعدة البيانات المتقدم فقط"""
    
    if config.DATABASE_TYPE != "postgresql":
        return await message.reply_text(
            "❌ **خطأ:** PostgreSQL غير مفعل!\n"
            "يجب تعيين `DATABASE_TYPE=postgresql` لتشغيل الاختبارات."
        )
    
    test_msg = await message.reply_text("🚀 **جاري تشغيل الاختبارات المتقدمة...**")
    
    try:
        # تشغيل الاختبارات المتقدمة فقط
        results = await advanced_tester.run_advanced_tests()
        
        # تحديد الحالة
        if results['failed'] == 0:
            status_emoji = "✅"
            status_text = "نجح"
        else:
            status_emoji = "❌"
            status_text = "فشل"
        
        final_message = (
            f"🚀 **نتائج الاختبارات المتقدمة**\n\n"
            f"{status_emoji} **الحالة: {status_text}**\n\n"
            f"📊 **التفاصيل:**\n"
            f"├ إجمالي: {results['total_tests']}\n"
            f"├ نجح: {results['passed']}\n"
            f"├ فشل: {results['failed']}\n"
            f"├ تحذير: {results['warned']}\n"
            f"├ تم تخطي: {results['skipped']}\n"
            f"└ نسبة النجاح: {results['success_rate']:.1f}%\n\n"
            f"🔧 **اختبارات فرعية:**\n"
            f"├ محاكاة الأوامر: {'✅' if results['commands_ok'] else '❌'}\n"
            f"├ اختبار الحمولة: {'✅' if results['load_ok'] else '❌'}\n"
            f"└ الاستقرار: {'✅' if results['stability_ok'] else '❌'}\n\n"
            f"⏱️ **المدة الإجمالية:** {results['total_duration']:.2f}s"
        )
        
        await test_msg.edit_text(final_message)
        
    except Exception as e:
        await test_msg.edit_text(
            f"❌ **خطأ في الاختبارات المتقدمة:**\n\n"
            f"```\n{str(e)}\n```"
        )


@app.on_message(filters.command(["dbstatus", "حالة_قاعدة_البيانات"]) & SUDOERS)
@language
async def database_status_command(client, message: Message, _):
    """أمر فحص حالة قاعدة البيانات السريع"""
    
    status_msg = await message.reply_text("🔍 **جاري فحص حالة قاعدة البيانات...**")
    
    try:
        if config.DATABASE_TYPE == "postgresql":
            # فحص PostgreSQL
            from ZeMusic.core.postgres import get_pool, fetch_one
            
            pool = get_pool()
            if not pool:
                await status_msg.edit_text("❌ **PostgreSQL:** غير متصل")
                return
            
            # معلومات قاعدة البيانات
            db_info = await fetch_one("SELECT version(), current_database(), current_user")
            db_stats = await fetch_one("""
                SELECT 
                    pg_database_size(current_database()) as size,
                    (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()) as connections
            """)
            
            # إحصائيات الجداول
            table_stats = await fetch_one("""
                SELECT 
                    COUNT(*) as table_count
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            db_size_mb = db_stats['size'] / (1024 * 1024) if db_stats else 0
            
            message_text = (
                f"🟢 **PostgreSQL متصل ويعمل بشكل طبيعي**\n\n"
                f"📋 **معلومات قاعدة البيانات:**\n"
                f"├ الاسم: `{db_info['current_database']}`\n"
                f"├ المستخدم: `{db_info['current_user']}`\n"
                f"├ الإصدار: `{db_info['version'][:50]}...`\n"
                f"├ الحجم: `{db_size_mb:.2f} MB`\n"
                f"├ الاتصالات النشطة: `{db_stats['connections']}`\n"
                f"└ عدد الجداول: `{table_stats['table_count']}`\n\n"
                f"✅ **النظام جاهز لتشغيل الاختبارات الشاملة**"
            )
            
        else:
            # MongoDB
            message_text = (
                f"🟡 **MongoDB نشط (وضع التوافق)**\n\n"
                f"📋 **معلومات:**\n"
                f"├ النوع: MongoDB\n"
                f"├ الحالة: متصل\n"
                f"└ وضع PostgreSQL: غير مفعل\n\n"
                f"💡 **لتشغيل الاختبارات الشاملة:**\n"
                f"يجب تفعيل PostgreSQL بتعيين `DATABASE_TYPE=postgresql`"
            )
        
        await status_msg.edit_text(message_text)
        
    except Exception as e:
        await status_msg.edit_text(
            f"❌ **خطأ في فحص حالة قاعدة البيانات:**\n\n"
            f"```\n{str(e)}\n```\n\n"
            f"يرجى التحقق من إعدادات قاعدة البيانات."
        )
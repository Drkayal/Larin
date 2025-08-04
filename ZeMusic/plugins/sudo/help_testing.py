"""
مساعدة أوامر اختبار قاعدة البيانات للمطورين
Database Testing Commands Help for Developers
"""

from pyrogram import filters
from pyrogram.types import Message

from ZeMusic import app
from ZeMusic.misc import SUDOERS
from ZeMusic.utils.decorators.language import language


@app.on_message(filters.command(["testhelp", "مساعدة_الاختبار"]) & SUDOERS)
@language
async def test_help_command(client, message: Message, _):
    """أمر مساعدة اختبار قاعدة البيانات"""
    
    help_text = """
🧪 **دليل أوامر اختبار قاعدة البيانات**

📋 **الأوامر المتاحة:**

🔍 **أوامر الحالة:**
├ `/dbstatus` أو `/حالة_قاعدة_البيانات`
└ فحص سريع لحالة قاعدة البيانات الحالية

🧪 **أوامر الاختبار الأساسية:**
├ `/testdb_basic` أو `/اختبار_أساسي`
└ اختبار الوظائف الأساسية فقط (اتصال، CRUD، أداء)

🚀 **أوامر الاختبار المتقدمة:**
├ `/testdb_advanced` أو `/اختبار_متقدم`
└ اختبار الحمولة العالية والاستقرار

🔬 **الاختبار الشامل:**
├ `/testdb` أو `/اختبار_قاعدة_البيانات`
└ تشغيل جميع الاختبارات (أساسية + متقدمة)

📊 **ما يتم اختباره:**

🔧 **الاختبارات الأساسية:**
├ ✅ اتصال قاعدة البيانات
├ ✅ عمليات CRUD (إنشاء، قراءة، تحديث، حذف)
├ ✅ أداء الاستعلامات
├ ✅ استهلاك الذاكرة
└ ✅ العمليات المتزامنة

🚀 **الاختبارات المتقدمة:**
├ ✅ محاكاة أوامر البوت
├ ✅ اختبار الحمولة العالية (100+ عملية)
├ ✅ اختبار الأداء المستمر
├ ✅ اختبار تسريب الذاكرة
├ ✅ استقرار الاتصالات
└ ✅ التعافي من الأخطاء

⚙️ **متطلبات التشغيل:**
├ يجب تعيين `DATABASE_TYPE=postgresql`
├ قاعدة بيانات PostgreSQL نشطة
└ صلاحيات مطور (sudo)

🎯 **تفسير النتائج:**

🟢 **ممتاز (95%+):**
└ النظام يعمل بشكل مثالي

🟡 **جيد (85-94%):**
└ النظام يعمل مع بعض التحذيرات البسيطة

🔴 **يحتاج انتباه (<85%):**
└ يُنصح بمراجعة إعدادات قاعدة البيانات

💡 **نصائح:**
├ استخدم `/dbstatus` للفحص السريع
├ ابدأ بـ `/testdb_basic` قبل الاختبار الشامل
├ راجع السجلات للحصول على تفاصيل الأخطاء
└ قم بتشغيل الاختبارات دورياً للتأكد من الاستقرار

📞 **للدعم:**
إذا واجهت مشاكل، تحقق من:
├ إعدادات PostgreSQL في config.py
├ اتصال قاعدة البيانات
└ سجلات النظام للأخطاء التفصيلية
"""
    
    await message.reply_text(help_text)


@app.on_message(filters.command(["testcommands", "أوامر_الاختبار"]) & SUDOERS)
@language  
async def test_commands_list(client, message: Message, _):
    """قائمة سريعة بأوامر الاختبار"""
    
    commands_text = """
⚡ **أوامر الاختبار السريعة**

🔍 `/dbstatus` - فحص الحالة
🧪 `/testdb_basic` - اختبار أساسي  
🚀 `/testdb_advanced` - اختبار متقدم
🔬 `/testdb` - اختبار شامل
❓ `/testhelp` - المساعدة التفصيلية

💡 **للمساعدة الكاملة:** `/testhelp`
"""
    
    await message.reply_text(commands_text)
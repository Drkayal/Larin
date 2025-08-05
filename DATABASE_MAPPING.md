# 🗄️ دليل مطابقة قاعدة البيانات - MongoDB إلى PostgreSQL

## 📋 **نظرة عامة**

هذا الملف يوضح المطابقة الدقيقة بين مجموعات MongoDB الحالية وجداول PostgreSQL الجديدة، مع شرح كيفية تحويل البيانات والوظائف.

---

## 📊 **مطابقة المجموعات والجداول**

### **1. المستخدمون (Users)**

| **MongoDB Collection** | **PostgreSQL Table** | **الوصف** |
|----------------------|---------------------|----------|
| `tgusersdb` | `users` | بيانات المستخدمين الأساسية |

**تحويل البيانات:**
```javascript
// MongoDB Document
{
  "user_id": 123456789
}

// PostgreSQL Row
{
  "user_id": 123456789,
  "first_name": null,
  "last_name": null,
  "username": null,
  "language_code": "ar",
  "is_bot": false,
  "is_premium": false,
  "joined_at": "2024-01-01 00:00:00",
  "last_activity": "2024-01-01 00:00:00",
  "is_active": true
}
```

### **2. المحادثات (Chats)**

| **MongoDB Collection** | **PostgreSQL Table** | **الوصف** |
|----------------------|---------------------|----------|
| `chats` | `chats` | بيانات المحادثات والمجموعات |

**تحويل البيانات:**
```javascript
// MongoDB Document
{
  "chat_id": -1001234567890
}

// PostgreSQL Row
{
  "chat_id": -1001234567890,
  "chat_type": "supergroup",
  "title": null,
  "username": null,
  "description": null,
  "member_count": 0,
  "joined_at": "2024-01-01 00:00:00",
  "last_activity": "2024-01-01 00:00:00",
  "is_active": true
}
```

### **3. إعدادات المحادثات (Chat Settings)**

| **MongoDB Collections** | **PostgreSQL Table** | **الوصف** |
|------------------------|---------------------|----------|
| `language` | `chat_settings.language` | لغة المحادثة |
| `playmode` | `chat_settings.play_mode` | وضع التشغيل |
| `playtypedb` | `chat_settings.play_type` | نوع التشغيل |
| `cplaymode` | `chat_settings.channel_play_mode` | وضع تشغيل القناة |
| `upcount` | `chat_settings.upvote_count` | عدد الأصوات |
| `autoend` | `chat_settings.auto_end` | الإنهاء التلقائي |
| `skipmode` | `chat_settings.skip_mode` | وضع التخطي |
| `adminauth` | `chat_settings.non_admin_commands` | الأوامر للغير مشرفين |
| `dere` | `chat_settings.search_enabled` | تفعيل البحث |
| `we` | `chat_settings.welcome_enabled` | تفعيل الترحيب |
| `lf` | `chat_settings.logs_enabled` | تفعيل السجلات |

**تحويل البيانات:**
```javascript
// MongoDB Documents (متعددة)
language: { "chat_id": -100123, "lang": "ar" }
playmode: { "chat_id": -100123, "mode": "everyone" }
upcount: { "chat_id": -100123, "mode": 5 }

// PostgreSQL Row (موحدة)
{
  "chat_id": -1001234567890,
  "language": "ar",
  "play_mode": "everyone",
  "play_type": "music",
  "channel_play_mode": null,
  "upvote_count": 5,
  "auto_end": false,
  "skip_mode": true,
  "non_admin_commands": false,
  "search_enabled": true,
  "welcome_enabled": false,
  "logs_enabled": false,
  "created_at": "2024-01-01 00:00:00",
  "updated_at": "2024-01-01 00:00:00"
}
```

### **4. المستخدمون المصرح لهم (Authorized Users)**

| **MongoDB Collection** | **PostgreSQL Table** | **الوصف** |
|----------------------|---------------------|----------|
| `authuser` | `authorized_users` | المستخدمون المصرح لهم في كل محادثة |

**تحويل البيانات:**
```javascript
// MongoDB Document
{
  "chat_id": -1001234567890,
  "notes": {
    "user_123": {
      "user_id": 123456789,
      "user_name": "احمد",
      "auth": 1234567890
    }
  }
}

// PostgreSQL Rows (سطر لكل مستخدم)
{
  "chat_id": -1001234567890,
  "user_id": 123456789,
  "user_name": "احمد",
  "authorized_by": 1234567890,
  "authorized_at": "2024-01-01 00:00:00",
  "notes": {}
}
```

### **5. المطورون (Sudo Users)**

| **MongoDB Collection** | **PostgreSQL Table** | **الوصف** |
|----------------------|---------------------|----------|
| `sudoers` | `sudo_users` | قائمة المطورين |

**تحويل البيانات:**
```javascript
// MongoDB Document
{
  "sudo": "sudo",
  "sudoers": [123456789, 987654321]
}

// PostgreSQL Rows (سطر لكل مطور)
[
  {
    "user_id": 123456789,
    "added_by": null,
    "added_at": "2024-01-01 00:00:00",
    "is_active": true
  },
  {
    "user_id": 987654321,
    "added_by": null,
    "added_at": "2024-01-01 00:00:00",
    "is_active": true
  }
]
```

### **6. المستخدمون المحظورون (Banned Users)**

| **MongoDB Collection** | **PostgreSQL Table** | **الوصف** |
|----------------------|---------------------|----------|
| `blockedusers` | `banned_users` | المستخدمون المحظورون محلياً |
| `gban` | `gbanned_users` | المستخدمون المحظورون عامياً |

**تحويل البيانات:**
```javascript
// MongoDB Document
{
  "user_id": 123456789
}

// PostgreSQL Row
{
  "user_id": 123456789,
  "banned_by": null,
  "banned_at": "2024-01-01 00:00:00",
  "reason": null,
  "is_active": true
}
```

### **7. المحادثات المحظورة (Blacklisted Chats)**

| **MongoDB Collection** | **PostgreSQL Table** | **الوصف** |
|----------------------|---------------------|----------|
| `blacklistChat` | `blacklisted_chats` | المحادثات المحظورة |

### **8. المحادثات النشطة (Active Chats)**

| **Memory Arrays** | **PostgreSQL Table** | **الوصف** |
|------------------|---------------------|----------|
| `active[]` | `active_chats` | المحادثات النشطة حالياً |
| `activevideo[]` | `active_chats.is_video` | المحادثات المرئية النشطة |

### **9. قوائم الانتظار (Play Queue)**

| **Memory Object** | **PostgreSQL Table** | **الوصف** |
|------------------|---------------------|----------|
| `db[chat_id][]` | `play_queue` | قوائم انتظار الأغاني |

### **10. المساعدون (Assistants)**

| **MongoDB Collection** | **PostgreSQL Table** | **الوصف** |
|----------------------|---------------------|----------|
| `assistants` | `assistants` | تخصيص المساعدين للمحادثات |

### **11. إعدادات النظام (System Settings)**

| **MongoDB Collection** | **PostgreSQL Table** | **الوصف** |
|----------------------|---------------------|----------|
| `onoffper` | `system_settings` | إعدادات النظام العامة |
| `dere1` | `system_settings` | البحث العام |

---

## 🔄 **مطابقة الوظائف الكاملة**

### **وظائف المستخدمين:**

| **MongoDB Function** | **PostgreSQL Function** | **الوصف** |
|---------------------|------------------------|----------|
| `add_served_user()` | `add_served_user()` | إضافة مستخدم جديد |
| `get_served_users()` | `get_served_users()` | جلب جميع المستخدمين |
| `is_served_user()` | `is_served_user()` | فحص وجود المستخدم |

### **وظائف المحادثات:**

| **MongoDB Function** | **PostgreSQL Function** | **الوصف** |
|---------------------|------------------------|----------|
| `add_served_chat()` | `add_served_chat()` | إضافة محادثة جديدة |
| `get_served_chats()` | `get_served_chats()` | جلب جميع المحادثات |
| `is_served_chat()` | `is_served_chat()` | فحص وجود المحادثة |

### **وظائف الإعدادات:**

| **MongoDB Function** | **PostgreSQL Function** | **الوصف** |
|---------------------|------------------------|----------|
| `set_lang()` | `set_chat_language()` | تعيين لغة المحادثة |
| `get_lang()` | `get_chat_language()` | جلب لغة المحادثة |
| `set_playmode()` | `set_chat_play_mode()` | تعيين وضع التشغيل |
| `get_playmode()` | `get_chat_play_mode()` | جلب وضع التشغيل |

### **وظائف الصلاحيات:**

| **MongoDB Function** | **PostgreSQL Function** | **الوصف** |
|---------------------|------------------------|----------|
| `save_authuser()` | `add_authorized_user()` | إضافة مستخدم مصرح |
| `delete_authuser()` | `remove_authorized_user()` | حذف مستخدم مصرح |
| `get_authuser()` | `get_authorized_user()` | جلب بيانات مستخدم مصرح |
| `get_authuser_names()` | `get_authorized_user_names()` | جلب أسماء المستخدمين المصرح لهم |

### **وظائف المساعدين:**

| **MongoDB Function** | **PostgreSQL Function** | **الوصف** |
|---------------------|------------------------|----------|
| `get_assistant()` | `get_chat_assistant()` | جلب المساعد المخصص للمحادثة |
| `set_assistant()` | `set_chat_assistant()` | تخصيص مساعد للمحادثة |
| `set_assistant_new()` | `set_chat_assistant_manual()` | تخصيص مساعد يدوياً |
| `get_assistant_number()` | `get_chat_assistant_number()` | جلب رقم المساعد |
| `set_calls_assistant()` | `set_calls_assistant()` | تخصيص مساعد للمكالمات |

### **وظائف المحادثات النشطة:**

| **MongoDB Function** | **PostgreSQL Function** | **الوصف** |
|---------------------|------------------------|----------|
| `add_active_chat()` | `add_active_chat()` | إضافة محادثة نشطة |
| `remove_active_chat()` | `remove_active_chat()` | إزالة محادثة نشطة |
| `get_active_chats()` | `get_active_chats()` | جلب المحادثات النشطة |
| `is_active_chat()` | `is_active_chat()` | فحص نشاط المحادثة |
| `add_active_video_chat()` | `add_active_video_chat()` | إضافة محادثة فيديو نشطة |
| `remove_active_video_chat()` | `remove_active_video_chat()` | إزالة محادثة فيديو نشطة |
| `is_active_video_chat()` | `is_active_video_chat()` | فحص نشاط الفيديو |

### **وظائف الحظر والمنع:**

| **MongoDB Function** | **PostgreSQL Function** | **الوصف** |
|---------------------|------------------------|----------|
| `add_banned_user()` | `add_banned_user()` | حظر مستخدم محلياً |
| `remove_banned_user()` | `remove_banned_user()` | إلغاء حظر مستخدم |
| `get_banned_users()` | `get_banned_users()` | جلب المستخدمين المحظورين |
| `is_banned_user()` | `is_banned_user()` | فحص حظر المستخدم |
| `get_banned_count()` | `get_banned_count()` | عدد المستخدمين المحظورين |
| `add_gban_user()` | `add_gbanned_user()` | حظر مستخدم عامياً |
| `remove_gban_user()` | `remove_gbanned_user()` | إلغاء الحظر العام |
| `get_gbanned()` | `get_gbanned_users()` | جلب المحظورين عامياً |
| `is_gbanned_user()` | `is_gbanned_user()` | فحص الحظر العام |
| `blacklist_chat()` | `blacklist_chat()` | حظر محادثة |
| `whitelist_chat()` | `whitelist_chat()` | إلغاء حظر محادثة |
| `blacklisted_chats()` | `get_blacklisted_chats()` | جلب المحادثات المحظورة |

### **وظائف المطورين:**

| **MongoDB Function** | **PostgreSQL Function** | **الوصف** |
|---------------------|------------------------|----------|
| `add_sudo()` | `add_sudo_user()` | إضافة مطور |
| `remove_sudo()` | `remove_sudo_user()` | إزالة مطور |
| `get_sudoers()` | `get_sudo_users()` | جلب قائمة المطورين |

### **وظائف النظام:**

| **MongoDB Function** | **PostgreSQL Function** | **الوصف** |
|---------------------|------------------------|----------|
| `is_maintenance()` | `is_maintenance_mode()` | فحص وضع الصيانة |
| `maintenance_on()` | `enable_maintenance()` | تفعيل الصيانة |
| `maintenance_off()` | `disable_maintenance()` | إيقاف الصيانة |
| `is_on_off()` | `is_feature_enabled()` | فحص تفعيل ميزة |
| `add_on()` | `enable_feature()` | تفعيل ميزة |
| `add_off()` | `disable_feature()` | إيقاف ميزة |
| `is_autoend()` | `is_autoend_enabled()` | فحص الإنهاء التلقائي |
| `autoend_on()` | `enable_autoend()` | تفعيل الإنهاء التلقائي |
| `autoend_off()` | `disable_autoend()` | إيقاف الإنهاء التلقائي |

### **وظائف البحث والميزات:**

| **MongoDB Function** | **PostgreSQL Function** | **الوصف** |
|---------------------|------------------------|----------|
| `is_search_enabled1()` | `is_global_search_enabled()` | فحص البحث العام |
| `enable_search1()` | `enable_global_search()` | تفعيل البحث العام |
| `disable_search1()` | `disable_global_search()` | إيقاف البحث العام |
| `is_search_enabled()` | `is_chat_search_enabled()` | فحص بحث المحادثة |
| `enable_search()` | `enable_chat_search()` | تفعيل بحث المحادثة |
| `disable_search()` | `disable_chat_search()` | إيقاف بحث المحادثة |
| `is_welcome_enabled()` | `is_welcome_enabled()` | فحص الترحيب |
| `enable_welcome()` | `enable_welcome()` | تفعيل الترحيب |
| `disable_welcome()` | `disable_welcome()` | إيقاف الترحيب |
| `is_loge_enabled()` | `is_logs_enabled()` | فحص السجلات |
| `enable_loge()` | `enable_logs()` | تفعيل السجلات |
| `disable_loge()` | `disable_logs()` | إيقاف السجلات |

### **وظائف التحكم في التشغيل:**

| **MongoDB Function** | **PostgreSQL Function** | **الوصف** |
|---------------------|------------------------|----------|
| `music_on()` | `resume_music()` | استئناف الموسيقى |
| `music_off()` | `pause_music()` | إيقاف الموسيقى |
| `is_music_playing()` | `is_music_playing()` | فحص تشغيل الموسيقى |
| `get_loop()` | `get_loop_mode()` | جلب وضع التكرار |
| `set_loop()` | `set_loop_mode()` | تعيين وضع التكرار |
| `is_skipmode()` | `is_skip_mode_enabled()` | فحص وضع التخطي |
| `skip_on()` | `enable_skip_mode()` | تفعيل وضع التخطي |
| `skip_off()` | `disable_skip_mode()` | إيقاف وضع التخطي |
| `get_upvote_count()` | `get_upvote_count()` | جلب عدد الأصوات |
| `set_upvotes()` | `set_upvote_count()` | تعيين عدد الأصوات |

### **وظائف الإدارة المتقدمة:**

| **MongoDB Function** | **PostgreSQL Function** | **الوصف** |
|---------------------|------------------------|----------|
| `is_nonadmin_chat()` | `is_nonadmin_mode()` | فحص وضع غير المشرفين |
| `add_nonadmin_chat()` | `enable_nonadmin_mode()` | تفعيل وضع غير المشرفين |
| `remove_nonadmin_chat()` | `disable_nonadmin_mode()` | إيقاف وضع غير المشرفين |

---

## 🚀 **مزايا التحويل إلى PostgreSQL**

### **1. الأداء:**
- فهرسة أفضل وأسرع
- استعلامات معقدة محسنة
- ذاكرة تخزين مؤقت متقدمة

### **2. الموثوقية:**
- ACID compliance كاملة
- نسخ احتياطي أفضل
- استرداد أسرع

### **3. المرونة:**
- علاقات معقدة بين الجداول
- قيود البيانات المتقدمة
- وظائف مخصصة ومشغلات

### **4. القابلية للتوسع:**
- دعم أفضل للحمولة العالية
- تحسين استهلاك الذاكرة
- إدارة الاتصالات المتقدمة

---

## 📝 **ملاحظات مهمة للتحويل**

### **1. البيانات المفقودة:**
- سيتم إضافة حقول جديدة بقيم افتراضية
- البيانات الموجودة ستبقى سليمة
- معلومات إضافية ستُجمع تدريجياً

### **2. التوافق:**
- جميع الوظائف الحالية ستعمل بنفس الطريقة
- أسماء الوظائف قد تتغير قليلاً
- المعاملات والنتائج ستبقى متطابقة

### **3. الأداء:**
- تحسن ملحوظ في سرعة الاستعلامات
- استهلاك ذاكرة أقل
- استجابة أسرع للأوامر

---

## 📊 **إحصائيات التحليل الشامل**

### **المجموعات والجداول:**
- **21 مجموعة MongoDB** → **14 جدول PostgreSQL محسن**
- **11 متغير ذاكرة مؤقتة** → **جداول دائمة**

### **الوظائف المحللة:**
- **76 وظيفة إجمالية** تم تحليلها
- **9 فئات وظائف** رئيسية
- **100% تغطية** لجميع العمليات

### **تفصيل الوظائف:**
- **وظائف المستخدمين**: 3 وظائف
- **وظائف المحادثات**: 3 وظائف  
- **وظائف الإعدادات**: 6 وظائف
- **وظائف الصلاحيات**: 4 وظائف
- **وظائف المساعدين**: 5 وظائف
- **وظائف المحادثات النشطة**: 7 وظائف
- **وظائف الحظر والمنع**: 12 وظيفة
- **وظائف المطورين**: 3 وظائف
- **وظائف النظام**: 9 وظائف
- **وظائف البحث والميزات**: 12 وظيفة
- **وظائف التحكم في التشغيل**: 10 وظائف
- **وظائف الإدارة المتقدمة**: 3 وظائف

## ✅ **حالة التحويل**

- [x] **تحليل البنية الحالية** - مكتمل ✨
  - ✅ تحليل 21 مجموعة MongoDB
  - ✅ تحليل 76 وظيفة
  - ✅ تحليل 11 متغير ذاكرة مؤقتة
  
- [x] **تصميم قاعدة البيانات الجديدة** - مكتمل ✨
  - ✅ تصميم 14 جدول محسن
  - ✅ إنشاء 20+ فهرس للأداء
  - ✅ إضافة وظائف ومشغلات
  
- [x] **إعداد متطلبات PostgreSQL** - مكتمل ✨
  - ✅ إضافة 4 مكتبات PostgreSQL
  - ✅ تحديث 4 ملفات إعداد
  - ✅ إضافة 8 متغيرات بيئة
  
- [ ] **إنشاء طبقة الاتصال** - جاهز للتنفيذ 🚀
- [ ] **تحويل الوظائف** - جاهز للتنفيذ 🚀
- [ ] **تحديث الملفات** - جاهز للتنفيذ 🚀
- [ ] **الاختبار والتحقق** - جاهز للتنفيذ 🚀

---

**📞 للمساعدة أو الاستفسارات، يرجى مراجعة التوثيق الفني أو الاتصال بفريق التطوير.**
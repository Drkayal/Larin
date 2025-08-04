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

## 🔄 **مطابقة الوظائف**

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

## ✅ **حالة التحويل**

- [x] **تحليل البنية الحالية** - مكتمل
- [x] **تصميم قاعدة البيانات الجديدة** - مكتمل  
- [x] **إعداد متطلبات PostgreSQL** - مكتمل
- [ ] **إنشاء طبقة الاتصال** - قيد التنفيذ
- [ ] **تحويل الوظائف** - قيد الانتظار
- [ ] **تحديث الملفات** - قيد الانتظار
- [ ] **الاختبار والتحقق** - قيد الانتظار

---

**📞 للمساعدة أو الاستفسارات، يرجى مراجعة التوثيق الفني أو الاتصال بفريق التطوير.**
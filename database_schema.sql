-- =====================================================
-- ZeMusic Bot PostgreSQL Database Schema
-- تصميم قاعدة البيانات لتحويل من MongoDB إلى PostgreSQL
-- =====================================================

-- إنشاء قاعدة البيانات
-- CREATE DATABASE zemusic_bot;

-- الاتصال بقاعدة البيانات
-- \c zemusic_bot;

-- =====================================================
-- 1. جدول المستخدمين (Users)
-- =====================================================
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

-- =====================================================
-- 2. جدول المحادثات (Chats)
-- =====================================================
CREATE TABLE IF NOT EXISTS chats (
    chat_id BIGINT PRIMARY KEY,
    chat_type VARCHAR(20) NOT NULL, -- 'private', 'group', 'supergroup', 'channel'
    title VARCHAR(255),
    username VARCHAR(255),
    description TEXT,
    member_count INTEGER DEFAULT 0,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- =====================================================
-- 3. جدول إعدادات المحادثات (Chat Settings)
-- =====================================================
CREATE TABLE IF NOT EXISTS chat_settings (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    language VARCHAR(10) DEFAULT 'ar',
    play_mode VARCHAR(20) DEFAULT 'everyone', -- 'everyone', 'admins'
    play_type VARCHAR(20) DEFAULT 'music', -- 'music', 'video'
    channel_play_mode INTEGER DEFAULT NULL, -- للقنوات المتصلة
    upvote_count INTEGER DEFAULT 5,
    auto_end BOOLEAN DEFAULT FALSE,
    skip_mode BOOLEAN DEFAULT TRUE,
    non_admin_commands BOOLEAN DEFAULT FALSE,
    search_enabled BOOLEAN DEFAULT TRUE,
    welcome_enabled BOOLEAN DEFAULT FALSE,
    logs_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chat_id)
);

-- =====================================================
-- 4. جدول المستخدمين المصرح لهم (Authorized Users)
-- =====================================================
CREATE TABLE IF NOT EXISTS authorized_users (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    user_name VARCHAR(255) NOT NULL,
    authorized_by BIGINT REFERENCES users(user_id),
    authorized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes JSONB DEFAULT '{}',
    UNIQUE(chat_id, user_id)
);

-- =====================================================
-- 5. جدول المطورين (Sudo Users)
-- =====================================================
CREATE TABLE IF NOT EXISTS sudo_users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    added_by BIGINT REFERENCES users(user_id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id)
);

-- =====================================================
-- 6. جدول المستخدمين المحظورين محلياً (Banned Users)
-- =====================================================
CREATE TABLE IF NOT EXISTS banned_users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    banned_by BIGINT REFERENCES users(user_id),
    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id)
);

-- =====================================================
-- 7. جدول المستخدمين المحظورين عامياً (Globally Banned Users)
-- =====================================================
CREATE TABLE IF NOT EXISTS gbanned_users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    banned_by BIGINT REFERENCES users(user_id),
    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id)
);

-- =====================================================
-- 8. جدول المحادثات المحظورة (Blacklisted Chats)
-- =====================================================
CREATE TABLE IF NOT EXISTS blacklisted_chats (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    blacklisted_by BIGINT REFERENCES users(user_id),
    blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(chat_id)
);

-- =====================================================
-- 9. جدول المحادثات النشطة (Active Chats)
-- =====================================================
CREATE TABLE IF NOT EXISTS active_chats (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    is_video BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    current_track JSONB DEFAULT '{}',
    UNIQUE(chat_id)
);

-- =====================================================
-- 10. جدول قوائم الانتظار (Play Queue)
-- =====================================================
CREATE TABLE IF NOT EXISTS play_queue (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    track_data JSONB NOT NULL,
    position INTEGER NOT NULL,
    added_by BIGINT REFERENCES users(user_id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_played BOOLEAN DEFAULT FALSE
);

-- =====================================================
-- 11. جدول المساعدين (Assistants)
-- =====================================================
CREATE TABLE IF NOT EXISTS assistants (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    assistant_number INTEGER NOT NULL CHECK (assistant_number BETWEEN 1 AND 5),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(chat_id)
);

-- =====================================================
-- 12. جدول إعدادات النظام (System Settings)
-- =====================================================
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(20) DEFAULT 'string', -- 'string', 'integer', 'boolean', 'json'
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(setting_key)
);

-- =====================================================
-- 13. جدول إحصائيات البوت (Bot Stats)
-- =====================================================
CREATE TABLE IF NOT EXISTS bot_stats (
    id SERIAL PRIMARY KEY,
    stat_date DATE DEFAULT CURRENT_DATE,
    total_users INTEGER DEFAULT 0,
    total_chats INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    active_chats INTEGER DEFAULT 0,
    total_plays INTEGER DEFAULT 0,
    total_downloads INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stat_date)
);

-- =====================================================
-- 14. جدول سجل الأنشطة (Activity Logs)
-- =====================================================
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    chat_id BIGINT REFERENCES chats(chat_id),
    action VARCHAR(100) NOT NULL,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- الفهارس للأداء الأمثل (Indexes)
-- =====================================================

-- فهارس المستخدمين
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_language ON users(language_code);
CREATE INDEX IF NOT EXISTS idx_users_activity ON users(last_activity);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- فهارس المحادثات
CREATE INDEX IF NOT EXISTS idx_chats_type ON chats(chat_type);
CREATE INDEX IF NOT EXISTS idx_chats_username ON chats(username);
CREATE INDEX IF NOT EXISTS idx_chats_activity ON chats(last_activity);
CREATE INDEX IF NOT EXISTS idx_chats_active ON chats(is_active);

-- فهارس إعدادات المحادثات
CREATE INDEX IF NOT EXISTS idx_chat_settings_language ON chat_settings(language);
CREATE INDEX IF NOT EXISTS idx_chat_settings_play_mode ON chat_settings(play_mode);
CREATE INDEX IF NOT EXISTS idx_chat_settings_updated ON chat_settings(updated_at);

-- فهارس المستخدمين المصرح لهم
CREATE INDEX IF NOT EXISTS idx_auth_users_chat ON authorized_users(chat_id);
CREATE INDEX IF NOT EXISTS idx_auth_users_user ON authorized_users(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_users_name ON authorized_users(user_name);

-- فهارس قوائل الانتظار
CREATE INDEX IF NOT EXISTS idx_queue_chat ON play_queue(chat_id);
CREATE INDEX IF NOT EXISTS idx_queue_position ON play_queue(chat_id, position);
CREATE INDEX IF NOT EXISTS idx_queue_played ON play_queue(is_played);
CREATE INDEX IF NOT EXISTS idx_queue_added ON play_queue(added_at);

-- فهارس المحادثات النشطة
CREATE INDEX IF NOT EXISTS idx_active_chats_video ON active_chats(is_video);
CREATE INDEX IF NOT EXISTS idx_active_chats_started ON active_chats(started_at);

-- فهارس سجل الأنشطة
CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_chat ON activity_logs(chat_id);
CREATE INDEX IF NOT EXISTS idx_activity_action ON activity_logs(action);
CREATE INDEX IF NOT EXISTS idx_activity_date ON activity_logs(created_at);

-- فهارس الإحصائيات
CREATE INDEX IF NOT EXISTS idx_stats_date ON bot_stats(stat_date);

-- =====================================================
-- البيانات الأولية (Initial Data)
-- =====================================================

-- إعدادات النظام الأولية
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('maintenance_mode', 'false', 'boolean', 'وضع الصيانة للبوت'),
('auto_end_enabled', 'true', 'boolean', 'تفعيل الإنهاء التلقائي'),
('global_search_enabled', 'true', 'boolean', 'تفعيل البحث العام'),
('max_queue_size', '50', 'integer', 'الحد الأقصى لقائمة الانتظار'),
('default_language', 'ar', 'string', 'اللغة الافتراضية'),
('bot_version', '1.0.0', 'string', 'إصدار البوت'),
('last_backup', '', 'string', 'آخر نسخة احتياطية')
ON CONFLICT (setting_key) DO NOTHING;

-- إحصائيات اليوم الحالي
INSERT INTO bot_stats (stat_date) VALUES (CURRENT_DATE)
ON CONFLICT (stat_date) DO NOTHING;

-- =====================================================
-- وظائف مساعدة (Helper Functions)
-- =====================================================

-- وظيفة لتحديث آخر نشاط للمستخدم
CREATE OR REPLACE FUNCTION update_user_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- وظيفة لتحديث آخر نشاط للمحادثة
CREATE OR REPLACE FUNCTION update_chat_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE chats SET last_activity = CURRENT_TIMESTAMP WHERE chat_id = NEW.chat_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- وظيفة لتحديث إعدادات المحادثة
CREATE OR REPLACE FUNCTION update_chat_settings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- المشغلات (Triggers)
-- =====================================================

-- مشغل لتحديث نشاط المستخدم عند إضافة سجل
DROP TRIGGER IF EXISTS trigger_update_user_activity ON activity_logs;
CREATE TRIGGER trigger_update_user_activity
    AFTER INSERT ON activity_logs
    FOR EACH ROW
    WHEN (NEW.user_id IS NOT NULL)
    EXECUTE FUNCTION update_user_activity();

-- مشغل لتحديث نشاط المحادثة عند إضافة سجل
DROP TRIGGER IF EXISTS trigger_update_chat_activity ON activity_logs;
CREATE TRIGGER trigger_update_chat_activity
    AFTER INSERT ON activity_logs
    FOR EACH ROW
    WHEN (NEW.chat_id IS NOT NULL)
    EXECUTE FUNCTION update_chat_activity();

-- مشغل لتحديث timestamp عند تعديل إعدادات المحادثة
DROP TRIGGER IF EXISTS trigger_update_chat_settings ON chat_settings;
CREATE TRIGGER trigger_update_chat_settings
    BEFORE UPDATE ON chat_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_chat_settings_timestamp();

-- =====================================================
-- صلاحيات المستخدمين (User Permissions)
-- =====================================================

-- إنشاء مستخدم للتطبيق (اختياري)
-- CREATE USER zemusic_app WITH PASSWORD 'your_secure_password';
-- GRANT CONNECT ON DATABASE zemusic_bot TO zemusic_app;
-- GRANT USAGE ON SCHEMA public TO zemusic_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO zemusic_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO zemusic_app;

-- =====================================================
-- تم إنشاء قاعدة البيانات بنجاح
-- =====================================================
-- توافق: جدول/عرض audio_files للملاءمة مع أكواد قديمة
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'audio_files'
    ) THEN
        CREATE TABLE audio_files (
            id SERIAL PRIMARY KEY,
            video_id VARCHAR(255) UNIQUE NOT NULL,
            title TEXT NOT NULL,
            file_path TEXT,
            file_size BIGINT DEFAULT 0,
            audio_quality VARCHAR(10) DEFAULT '320',
            file_format VARCHAR(10) DEFAULT 'mp3',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    END IF;
END $$;
#!/bin/bash

echo "🚀 بدء تشغيل بوت الموسيقى..."

# تفعيل البيئة الافتراضية
echo "📦 تفعيل البيئة الافتراضية..."
source venv/bin/activate

# بدء تشغيل PostgreSQL إذا لم يكن يعمل
echo "🗄️ التحقق من حالة PostgreSQL..."
if ! sudo service postgresql status > /dev/null 2>&1; then
    echo "⚡ بدء تشغيل PostgreSQL..."
    sudo service postgresql start
fi

# التحقق من الاتصال بقاعدة البيانات
echo "🔍 التحقق من الاتصال بقاعدة البيانات..."
if ! sudo -u postgres psql -d zemusic_bot -c "SELECT 1;" > /dev/null 2>&1; then
    echo "❌ فشل في الاتصال بقاعدة البيانات!"
    exit 1
fi

echo "✅ PostgreSQL يعمل بنجاح!"

# تحميل متغيرات البيئة
echo "🔧 تحميل متغيرات البيئة..."
set -a
source .env
set +a

# بدء تشغيل البوت
echo "🎵 بدء تشغيل البوت..."
python3 -m ZeMusic
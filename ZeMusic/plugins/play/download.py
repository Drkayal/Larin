import os
import re
import requests
import config
import aiohttp
import aiofiles
import yt_dlp
# استخدام PostgreSQL wrapper بدلاً من psycopg2 المباشر
import cachetools
from datetime import timedelta
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from youtube_search import YoutubeSearch
from ZeMusic.platforms.Youtube import cookies
from ZeMusic import app
from ZeMusic.plugins.play.filters import command
from ZeMusic.utils.decorators import AdminActual
from ZeMusic.utils.database import is_search_enabled, enable_search, disable_search
from ZeMusic.core.postgres import execute_query, fetch_value, fetch_all

# ----- إعداد التخزين المؤقت -----
CACHE_EXPIRATION = timedelta(hours=24)
search_cache = cachetools.TTLCache(maxsize=1000, ttl=CACHE_EXPIRATION.total_seconds())

# ----- تهيئة قاعدة البيانات التلقائية -----
async def init_db():
    try:
        # إنشاء جدول audio_files
        await execute_query("""
        CREATE TABLE IF NOT EXISTS audio_files (
            id SERIAL PRIMARY KEY,
            video_id TEXT UNIQUE,
            title TEXT,
            file_path TEXT,
            file_size INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            download_count INTEGER DEFAULT 0
        )
        """)
        
        # إنشاء جدول search_history  
        await execute_query("""
        CREATE TABLE IF NOT EXISTS search_history (
            id SERIAL PRIMARY KEY,
            query TEXT,
            video_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
    except Exception as e:
        print(f"خطأ في إنشاء الجداول: {str(e)}")

# ----- وظائف قاعدة البيانات -----
async def get_cached_audio(video_id: str):
    try:
        result = await fetch_all("""
        SELECT file_path, file_size 
        FROM audio_files 
        WHERE video_id = $1
        """, video_id)
        
        if result:
            return {'path': result[0][0], 'size': result[0][1]}
        return None
    except Exception as e:
        print(f"خطأ في قاعدة البيانات: {str(e)}")
        return None

async def save_audio_to_db(video_id: str, title: str, file_path: str, file_size: int):
    try:
        await execute_query("""
        INSERT INTO audio_files (video_id, title, file_path, file_size)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (video_id) DO UPDATE 
        SET download_count = audio_files.download_count + 1
        """, video_id, title, file_path, file_size)
    except Exception as e:
        print(f"خطأ في حفظ الملف: {str(e)}")

async def log_search(query: str, video_id: str):
    try:
        await execute_query("""
        INSERT INTO search_history (query, video_id)
        VALUES ($1, $2)
        """, query, video_id)
    except Exception as e:
        print(f"خطأ في تسجيل البحث: {str(e)}")

# ----- خدمات التحويل الخارجية -----
CONVERSION_SERVICES = [
    "https://api.vevioz.com/api/widget/mp3",
    "https://yt5s.com/en/api/convert",
    "https://api.onlinevideoconverter.pro/api/convert"
]

async def download_audio_external(url: str, output_dir: str, title: str) -> str:
    try:
        # تجربة خدمات التحويل المختلفة
        for service in CONVERSION_SERVICES:
            try:
                # الحصول على معرف الفيديو من الرابط
                video_id = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url).group(1)
                
                # بناء رابط التحويل
                if "vevioz" in service:
                    api_url = f"{service}/{video_id}"
                    response = requests.get(api_url)
                    data = response.json()
                    download_url = data['url']
                elif "yt5s" in service:
                    api_url = f"{service}/{video_id}"
                    payload = {"v": video_id, "ftype": "mp3", "fquality": 128}
                    response = requests.post(api_url, json=payload)
                    data = response.json()
                    download_url = data['d_url']
                else:
                    api_url = service
                    payload = {"url": url, "format": "mp3"}
                    response = requests.post(api_url, data=payload)
                    data = response.json()
                    download_url = data['download_url']
                
                # تنزيل الملف الصوتي
                file_path = os.path.join(output_dir, f"{title[:50]}.mp3")
                response = requests.get(download_url, stream=True)
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                return file_path
            except Exception as e:
                print(f"فشلت خدمة التحويل {service}: {str(e)}")
        
        print("جميع خدمات التحويل فشلت")
        return None
    except Exception as e:
        print(f"خطأ في التحميل الخارجي: {str(e)}")
        return None

def remove_if_exists(path):
    if os.path.exists(path):
        os.remove(path)

# ----- تهيئة قاعدة البيانات عند البدء -----
# سيتم تهيئة قاعدة البيانات تلقائياً عند أول استخدام

channel = "KHAYAL70"      
lnk = f"https://t.me/{config.CHANNEL_LINK}"
Nem = config.BOT_NAME + " ابحث"

@app.on_message(command(["song", "/song", "بحث", Nem,"يوت"]) & filters.group)
async def song_downloader(client, message: Message):
    chat_id = message.chat.id 
    if not await is_search_enabled(chat_id):
        return await message.reply_text("<b>⟡عذراً عزيزي اليوتيوب معطل لتفعيل اليوتيوب اكتب تفعيل اليوتيوب</b>")
        
    query = " ".join(message.command[1:])
    m = await message.reply_text("<b>⇜ جـارِ البحث ..</b>")
    
    try:
        # التحقق من التخزين المؤقت في الذاكرة أولاً
        if query in search_cache:
            video_info = search_cache[query]
            await process_video_download(client, message, m, video_info, query)
            return
        
        # البحث في قاعدة البيانات عن نتائج سابقة
        cached_result = await search_in_db(query)
        if cached_result:
            await m.edit("✅ تم العثور على نتيجة في قاعدة البيانات")
            await process_video_download(client, message, m, cached_result, query)
            return
            
        results = YoutubeSearch(query, max_results=1).to_dict()
        if not results:
            await m.edit("- لم يتم العثـور على نتائج حاول مجددا")
            return

        link = f"https://youtube.com{results[0]['url_suffix']}"
        title = results[0]["title"][:40]
        title_clean = re.sub(r'[\\/*?:"<>|]', "", title)  # تنظيف اسم الملف
        thumbnail = results[0]["thumbnails"][0]
        thumb_name = f"{title_clean}.jpg"
        video_id = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', link).group(1)

        # تحميل الصورة المصغرة
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumbnail) as resp:
                    if resp.status == 200:
                        f = await aiofiles.open(thumb_name, mode='wb')
                        await f.write(await resp.read())
                        await f.close()
        except Exception as thumb_error:
            print(f"خطأ في تحميل الصورة المصغرة: {thumb_error}")
            # استخدام صورة افتراضية
            thumb_name = None

        duration = results[0]["duration"]
        video_info = {
            'id': video_id,
            'title': title,
            'url': link,
            'duration': duration
        }
        
        # تخزين النتيجة في الذاكرة المؤقتة
        search_cache[query] = video_info
        await process_video_download(client, message, m, video_info, query)
        
    except Exception as e:
        await m.edit("❌ **خطأ في البحث**\n\nلم يتم العثور على نتائج. جرب:\n"
                    "• كلمات مختلفة للبحث\n"
                    "• تأكد من صحة اسم الأغنية\n"
                    "• حاول مرة أخرى لاحقاً")
        print(f"خطأ في البحث: {str(e)}")
        return

async def process_video_download(client, message, m, video_info, query):
    user_id = message.from_user.id
    video_id = video_info['id']
    video_title = video_info['title']
    video_url = video_info['url']
    duration = video_info.get('duration', '0:00')
    
    # تسجيل البحث في قاعدة البيانات
    await log_search(query, video_id)
    
    # التحقق من وجود الملف في قاعدة البيانات
    cached_audio = await get_cached_audio(video_id)
    if cached_audio:
        await send_cached_audio(client, message, m, cached_audio['path'], video_title, duration)
        return
    
    # إذا لم يوجد في قاعدة البيانات، قم بالتحميل
    await m.edit("<b>جاري التحميل ♪</b>")
    
    try:
        # إنشاء مجلد خاص للمستخدم
        user_dir = f"downloads/{user_id}"
        os.makedirs(user_dir, exist_ok=True)
        
        # تحميل الصوت باستخدام الطريقة الأصلية أولاً
        file_path = await download_audio_original(video_url, user_dir, video_title)
        
        if not file_path:
            # إذا فشلت الطريقة الأصلية، استخدم الخدمات الخارجية
            file_path = await download_audio_external(video_url, user_dir, video_title)
            
            if not file_path:
                await m.edit("❌ فشل التحميل، جرب لاحقًا")
                return
        
        # التحقق من حجم الملف
        file_size = os.path.getsize(file_path)
        
        # حفظ في قاعدة البيانات
        await save_audio_to_db(video_id, video_title, file_path, file_size)
        
        # إرسال الملف
        await send_audio_file(client, message, m, file_path, video_title, duration)
        
    except Exception as e:
        await m.edit(f"❌ فشل التحميل: {str(e)}")
        print(f"خطأ في التحميل: {str(e)}")

async def search_in_db(query: str):
    try:
        # البحث عن video_id من تاريخ البحث
        result = await fetch_all("""
        SELECT video_id 
        FROM search_history 
        WHERE query ILIKE $1 
        ORDER BY created_at DESC 
        LIMIT 1
        """, f"%{query}%")
        
        if not result:
            return None
        
        video_id = result[0][0]
        
        # البحث عن معلومات الصوت
        audio_info = await fetch_all("""
        SELECT video_id, title, file_path
        FROM audio_files 
        WHERE video_id = $1
        """, video_id)
        
        if audio_info:
            return {
                'id': audio_info[0][0],
                'title': audio_info[0][1],
                'url': f"https://www.youtube.com/watch?v={audio_info[0][0]}",
                'file_path': audio_info[0][2]
            }
        return None
    except Exception as e:
        print(f"خطأ في البحث بقاعدة البيانات: {str(e)}")
        return None

async def download_audio_original(url: str, output_dir: str, title: str) -> str:
    try:
        title_clean = re.sub(r'[\\/*?:"<>|]', "", title)
        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "keepvideo": False,
            "geo_bypass": True,
            "outtmpl": os.path.join(output_dir, f"{title_clean}.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "cookiefile": f"{cookies()}",
            "extractor_retries": 3,
            "retries": 3,
            "fragment_retries": 3,
            "http_headers": {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            },
            "extract_flat": False,
            "writethumbnail": False,
            "writeinfojson": False,
            "ignoreerrors": False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info_dict)
            
    except Exception as e:
        print(f"خطأ في التحميل الأصلي: {str(e)}")
        return None

async def send_audio_file(client, message, m, file_path, title, duration):
    # حساب مدة الأغنية
    secmul, dur, dur_arr = 1, 0, duration.split(":")
    for i in range(len(dur_arr) - 1, -1, -1):
        dur += int(float(dur_arr[i])) * secmul
        secmul *= 60

    try:
        # إرسال الصوت
        await message.reply_audio(
            audio=file_path,
            caption=f"ᴍʏ ᴡᴏʀʟᴅ 𓏺 @{channel} ",
            title=title,
            performer="YouTube",
            duration=dur,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="♪ 𝐋𝐚𝐫𝐢𝐧 ♪", url=lnk),
                    ],
                ]
            ),
        )
        await m.delete()
        
    except Exception as e:
        await m.edit(f"❌ فشل في إرسال الملف: {str(e)}")
        print(f"خطأ في الإرسال: {str(e)}")
    finally:
        # حذف الملفات المؤقتة
        try:
            remove_if_exists(file_path)
        except Exception as e:
            print(f"خطأ في حذف الملف: {str(e)}")

async def send_cached_audio(client, message, m, file_path, title, duration):
    # حساب مدة الأغنية
    secmul, dur, dur_arr = 1, 0, duration.split(":")
    for i in range(len(dur_arr) - 1, -1, -1):
        dur += int(float(dur_arr[i])) * secmul
        secmul *= 60

    try:
        # إرسال الصوت
        await message.reply_audio(
            audio=file_path,
            caption=f"🎵 **تم التحميل من الذاكرة المؤقتة**\n\n"
                   f"📀 **العنوان:** {title}\n"
                   f"⏱️ **المدة:** {duration}\n\n"
                   f"ᴍʏ ᴡᴏʀʟᴅ 𓏺 @{channel}",
            title=title,
            performer="YouTube",
            duration=dur,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="♪ 𝐋𝐚𝐫𝐢𝐧 ♪", url=lnk),
                    ],
                ]
            ),
        )
        await m.delete()
        
    except Exception as e:
        await m.edit(f"❌ فشل في إرسال الملف: {str(e)}")
        print(f"خطأ في الإرسال: {str(e)}")

@app.on_message(command(["تعطيل اليوتيوب"]) & filters.group)
@AdminActual
async def disable_search_command(client, message: Message, _):
    chat_id = message.chat.id
    if not await is_search_enabled(chat_id):
        await message.reply_text("<b>⟡اليوتيوب معطل من قبل يالطيب</b>")
        return
    await disable_search(chat_id)
    await message.reply_text("<b>⟡تم تعطيل اليوتيوب بنجاح</b>")


@app.on_message(command(["تفعيل اليوتيوب"]) & filters.group)
@AdminActual
async def enable_search_command(client, message: Message, _):
    chat_id = message.chat.id
    if await is_search_enabled(chat_id):
        await message.reply_text("<b>⟡اليوتيوب مفعل من قبل يالطيب</b>")
        return
    await enable_search(chat_id)
    await message.reply_text("<b>⟡تم تفعيل اليوتيوب بنجاح</b>")

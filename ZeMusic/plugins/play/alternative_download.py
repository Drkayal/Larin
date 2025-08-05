import os
import re
import requests
import config
import aiohttp
import aiofiles
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from youtube_search import YoutubeSearch
from ZeMusic.platforms.Youtube import cookies
from ZeMusic import app
from ZeMusic.plugins.play.filters import command
from ZeMusic.utils.decorators import AdminActual
from ZeMusic.utils.database import is_search_enabled, enable_search, disable_search

def remove_if_exists(path):
    if os.path.exists(path):
        os.remove(path)

channel = "KHAYAL70"      
lnk = f"https://t.me/{config.CHANNEL_LINK}"
Nem = config.BOT_NAME + " بحث بديل"

async def try_alternative_sources(query, message):
    """محاولة استخدام مصادر بديلة للتحميل"""
    
    # قائمة بالمصادر البديلة
    alternative_extractors = [
        "ytsearch1:",  # البحث المباشر في YouTube
        "soundcloud:",  # SoundCloud
    ]
    
    for extractor in alternative_extractors:
        try:
            search_query = f"{extractor}{query}" if not extractor.endswith(":") else f"{extractor} {query}"
            
            ydl_opts = {
                "format": "bestaudio/best",
                "keepvideo": False,
                "geo_bypass": True,
                "outtmpl": f"alt_download_{query[:20]}.%(ext)s",
                "quiet": True,
                "no_warnings": True,
                "extractor_retries": 2,
                "retries": 2,
                "http_headers": {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                },
                "extract_flat": False,
                "ignoreerrors": True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(search_query, download=True)
                if info_dict:
                    audio_file = ydl.prepare_filename(info_dict)
                    return audio_file, info_dict
                    
        except Exception as e:
            print(f"فشل في المصدر {extractor}: {e}")
            continue
    
    return None, None

@app.on_message(command(["بحث_بديل", "alt_search"]) & filters.group)
async def alternative_song_downloader(client, message: Message):
    chat_id = message.chat.id 
    if not await is_search_enabled(chat_id):
        return await message.reply_text("<b>⟡عذراً عزيزي اليوتيوب معطل لتفعيل اليوتيوب اكتب تفعيل اليوتيوب</b>")
        
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply_text("❌ **خطأ**\n\nيرجى كتابة اسم الأغنية للبحث\n\nمثال: `/بحث_بديل أغنية جميلة`")
    
    m = await message.reply_text("<b>⇜ جـارِ البحث بالطرق البديلة ..</b>")
    
    try:
        # محاولة البحث العادي أولاً
        results = YoutubeSearch(query, max_results=1).to_dict()
        if not results:
            await m.edit("❌ **لم يتم العثور على نتائج**\n\nجرب كلمات مختلفة للبحث")
            return

        title = results[0]["title"][:40]
        title_clean = re.sub(r'[\\/*?:"<>|]', "", title)
        duration = results[0]["duration"]
        
        await m.edit("<b>⇜ جاري التحميل بالطرق البديلة ♪</b>")
        
        # محاولة التحميل بالطرق البديلة
        audio_file, info_dict = await try_alternative_sources(query, message)
        
        if audio_file and os.path.exists(audio_file):
            # حساب مدة الأغنية
            try:
                secmul, dur, dur_arr = 1, 0, duration.split(":")
                for i in range(len(dur_arr) - 1, -1, -1):
                    dur += int(float(dur_arr[i])) * secmul
                    secmul *= 60
            except:
                dur = info_dict.get('duration', 180)  # افتراضي 3 دقائق

            # إرسال الصوت
            await message.reply_audio(
                audio=audio_file,
                caption=f"🎵 **تم التحميل بنجاح**\n\n"
                       f"📀 **العنوان:** {title}\n"
                       f"⏱️ **المدة:** {duration}\n"
                       f"🔄 **المصدر:** طرق بديلة\n\n"
                       f"ᴍʏ ᴡᴏʀʟᴅ 𓏺 @{channel}",
                title=title,
                performer=info_dict.get("uploader", "Unknown") if info_dict else "Unknown",
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
            
            # حذف الملف المؤقت
            remove_if_exists(audio_file)
            
        else:
            await m.edit("❌ **فشل في التحميل**\n\n"
                        "عذراً، لا يمكن تحميل هذا المحتوى حالياً.\n"
                        "جرب:\n"
                        "• كلمات مختلفة للبحث\n"
                        "• المحاولة مرة أخرى لاحقاً\n"
                        "• استخدام الأمر العادي `/song`")

    except Exception as e:
        await m.edit("❌ **خطأ في البحث البديل**\n\n"
                    "حدث خطأ غير متوقع. جرب مرة أخرى لاحقاً.")
        print(f"خطأ في البحث البديل: {str(e)}")

# إضافة معلومات حول الأمر الجديد
@app.on_message(command(["help_alt", "مساعدة_بديل"]) & filters.group)
async def help_alternative_download(client, message: Message):
    help_text = """
🔄 **البحث البديل**

استخدم هذا الأمر عندما يفشل البحث العادي:

**الأوامر:**
• `/بحث_بديل [اسم الأغنية]`
• `/alt_search [song name]`

**المميزات:**
✅ يستخدم مصادر متعددة
✅ يتجاوز قيود YouTube
✅ جودة صوت عالية
✅ سرعة تحميل محسنة

**مثال:**
`/بحث_بديل أغنية جميلة`
"""
    
    await message.reply_text(help_text)
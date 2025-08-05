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
Nem = config.BOT_NAME + " ابحث"

@app.on_message(command(["song", "/song", "بحث", Nem,"يوت"]) & filters.group)
async def song_downloader(client, message: Message):
    chat_id = message.chat.id 
    if not await is_search_enabled(chat_id):
        return await message.reply_text("<b>⟡عذراً عزيزي اليوتيوب معطل لتفعيل اليوتيوب اكتب تفعيل اليوتيوب</b>")
        
    query = " ".join(message.command[1:])
    m = await message.reply_text("<b>⇜ جـارِ البحث ..</b>")
    
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        if not results:
            await m.edit("- لم يتم العثـور على نتائج حاول مجددا")
            return

        link = f"https://youtube.com{results[0]['url_suffix']}"
        title = results[0]["title"][:40]
        title_clean = re.sub(r'[\\/*?:"<>|]', "", title)  # تنظيف اسم الملف
        thumbnail = results[0]["thumbnails"][0]
        thumb_name = f"{title_clean}.jpg"

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

    except Exception as e:
        await m.edit("❌ **خطأ في البحث**\n\nلم يتم العثور على نتائج. جرب:\n"
                    "• كلمات مختلفة للبحث\n"
                    "• تأكد من صحة اسم الأغنية\n"
                    "• حاول مرة أخرى لاحقاً")
        print(f"خطأ في البحث: {str(e)}")
        return
    
    await m.edit("<b>جاري التحميل ♪</b>")
    
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",  # تحسين تحديد الصيغة
        "keepvideo": False,
        "geo_bypass": True,
        "outtmpl": f"{title_clean}.%(ext)s",  # استخدام اسم نظيف للملف
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

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)  # التنزيل مباشرة
            audio_file = ydl.prepare_filename(info_dict)

        # حساب مدة الأغنية
        secmul, dur, dur_arr = 1, 0, duration.split(":")
        for i in range(len(dur_arr) - 1, -1, -1):
            dur += int(float(dur_arr[i])) * secmul
            secmul *= 60

        # إرسال الصوت
        await message.reply_audio(
            audio=audio_file,
            caption=f"ᴍʏ ᴡᴏʀʟᴅ 𓏺 @{channel} ",
            title=title,
            performer=info_dict.get("uploader", "Unknown"),
            thumb=thumb_name,
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
        error_msg = str(e)
        print(f"خطأ في التحميل: {error_msg}")
        
        # معالجة خاصة لأخطاء YouTube المختلفة
        if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
            await m.edit("❌ **خطأ في التحميل**\n\n"
                        "يواجه YouTube قيود جديدة. جاري المحاولة بطريقة بديلة...")
            
            # محاولة بديلة بدون cookies
            try:
                ydl_opts_fallback = {
                    "format": "bestaudio/best",
                    "keepvideo": False,
                    "geo_bypass": True,
                    "outtmpl": f"{title_clean}.%(ext)s",
                    "quiet": True,
                    "no_warnings": True,
                    "extractor_retries": 5,
                    "retries": 5,
                    "http_headers": {
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    },
                    "extract_flat": False,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts_fallback) as ydl_fallback:
                    info_dict = ydl_fallback.extract_info(link, download=True)
                    audio_file = ydl_fallback.prepare_filename(info_dict)
                
                # إرسال الصوت
                await message.reply_audio(
                    audio=audio_file,
                    caption=f"ᴍʏ ᴡᴏʀʟᴅ 𓏺 @{channel} ",
                    title=title,
                    performer=info_dict.get("uploader", "Unknown"),
                    thumb=thumb_name,
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
                
            except Exception as fallback_error:
                # محاولة أخيرة باستخدام ytsearch
                try:
                    await m.edit("🔄 **محاولة أخيرة...**\n\nجاري البحث بطريقة مختلفة...")
                    
                    ydl_opts_final = {
                        "format": "bestaudio/best",
                        "keepvideo": False,
                        "geo_bypass": True,
                        "outtmpl": f"{title_clean}_final.%(ext)s",
                        "quiet": True,
                        "no_warnings": True,
                        "extract_flat": False,
                        "ignoreerrors": True,
                    }
                    
                    search_query = f"ytsearch1:{query}"
                    
                    with yt_dlp.YoutubeDL(ydl_opts_final) as ydl_final:
                        info_dict = ydl_final.extract_info(search_query, download=True)
                        if info_dict and 'entries' in info_dict and info_dict['entries']:
                            entry = info_dict['entries'][0]
                            audio_file = ydl_final.prepare_filename(entry)
                            
                            # إرسال الصوت
                            await message.reply_audio(
                                audio=audio_file,
                                caption=f"🎵 **تم التحميل بنجاح**\n\n"
                                       f"📀 **العنوان:** {title}\n"
                                       f"⏱️ **المدة:** {duration}\n"
                                       f"🔄 **المصدر:** بحث مباشر\n\n"
                                       f"ᴍʏ ᴡᴏʀʟᴅ 𓏺 @{channel}",
                                title=title,
                                performer=entry.get("uploader", "Unknown"),
                                thumb=thumb_name,
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
                            remove_if_exists(audio_file)
                            return
                            
                except Exception as final_error:
                    print(f"خطأ في المحاولة الأخيرة: {final_error}")
                
                await m.edit("❌ **فشل في التحميل**\n\n"
                           "عذراً، لا يمكن تحميل هذا المحتوى حالياً بسبب قيود YouTube.\n\n"
                           "💡 **جرب البدائل:**\n"
                           "• `/بحث_بديل [اسم الأغنية]` - للبحث البديل\n"
                           "• كلمات مختلفة للبحث\n"
                           "• المحاولة مرة أخرى لاحقاً")
                print(f"خطأ في المحاولة البديلة: {fallback_error}")
        else:
            await m.edit("❌ **خطأ في التحميل**\n\n"
                        "حدث خطأ غير متوقع. جرب مرة أخرى لاحقاً.")
            print(f"خطأ عام: {error_msg}")

    # حذف الملفات المؤقتة
    try:
        remove_if_exists(audio_file)
        remove_if_exists(thumb_name)
    except Exception as e:
        print(e)


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

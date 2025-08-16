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
from ZeMusic.utils.redis_cache import get_cached_search, set_cached_search, get_cached_audio, set_cached_audio

def remove_if_exists(path):
    if os.path.exists(path):
        os.remove(path)

channel = "KHAYAL70"      
lnk = f"https://t.me/{config.CHANNEL_LINK}"
Nem = config.BOT_NAME + " ابحث"

@app.on_message(command(["song", "/song", "بحث", Nem,"يوت"]) & filters.group, group=-2)
async def song_downloader(client, message: Message):
    print("[DEBUG] song_downloader triggered in groups")
    chat_id = message.chat.id 
    if not await is_search_enabled(chat_id):
        return await message.reply_text("<b>⟡عذراً عزيزي اليوتيوب معطل لتفعيل اليوتيوب اكتب تفعيل اليوتيوب</b>")
        
    query = " ".join(message.command[1:]) if getattr(message, "command", None) else (message.text.split(" ", 1)[1].strip() if message.text and " " in message.text else "")
    if not query:
        return await message.reply_text("استخدم: بحث <الاسم> أو song <الاسم>")
    m = await message.reply_text("<b>⇜ جـارِ البحث ..</b>")
    
    try:
        # 1) محاولة من الكاش
        cached = get_cached_search(query)
        if cached:
            vidid = cached.get('vidid')
            ca = get_cached_audio(vidid)
            if ca and os.path.exists(ca.get('path','')):
                audio_file = ca['path']
                title = cached.get('title','')[:40]
                thumbnail = cached.get('thumb','')
                duration = cached.get('duration','0:00')
                title_clean = re.sub(r'[\\/*?:"<>|]', "", title)
                thumb_name = f"{title_clean}.jpg"
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(thumbnail) as resp:
                            if resp.status == 200:
                                f = await aiofiles.open(thumb_name, mode='wb')
                                await f.write(await resp.read())
                                await f.close()
                except Exception:
                    pass
                secmul, dur, dur_arr = 1, 0, (duration or '0:00').split(":")
                for i in range(len(dur_arr) - 1, -1, -1):
                    dur += int(float(dur_arr[i])) * secmul
                    secmul *= 60
                await message.reply_audio(
                    audio=audio_file,
                    caption=f"ᴍʏ ᴡᴏʀʟᴅ 𓏺 @{channel} ",
                    title=title,
                    performer=ca.get('uploader','Unknown'),
                    thumb=thumb_name if os.path.exists(thumb_name) else None,
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
                return
            results = [
                {
                    'url_suffix': f"/watch?v={cached.get('vidid')}",
                    'title': cached.get('title', ''),
                    'thumbnails': [cached.get('thumb', '')],
                    'duration': cached.get('duration', '0:00')
                }
            ]
        else:
            results = YoutubeSearch(query, max_results=1).to_dict()
        if not results:
            await m.edit("- لم يتم العثـور على نتائج حاول مجددا")
            return

        link = f"https://youtube.com{results[0]['url_suffix']}"
        title = results[0]["title"][:40]
        title_clean = re.sub(r'[\\/*?:"<>|]', "", title)  # تنظيف اسم الملف
        thumbnail = results[0]["thumbnails"][0] if isinstance(results[0]["thumbnails"], list) else results[0]["thumbnails"]
        thumb_name = f"{title_clean}.jpg"

        # تحميل الصورة المصغرة
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(thumb_name, mode='wb')
                    await f.write(await resp.read())
                    await f.close()

        duration = results[0]["duration"]

    except Exception as e:
        await m.edit("- لم يتم العثـور على نتائج حاول مجددا")
        print(str(e))
        return
    
    await m.edit("<b>جاري التحميل ♪</b>")
    
    # 2) إذا كان لدينا كاش للصوت على video_id أرسله مباشرة
    try:
        vidid = results[0].get('url_suffix','').split('v=')[-1]
        ca = get_cached_audio(vidid)
        if ca and os.path.exists(ca.get('path','')):
            audio_file = ca['path']
            info_uploader = ca.get('uploader','Unknown')
            # إرسال الصوت من الكاش
            secmul, dur, dur_arr = 1, 0, duration.split(":")
            for i in range(len(dur_arr) - 1, -1, -1):
                dur += int(float(dur_arr[i])) * secmul
                secmul *= 60
            await message.reply_audio(
                audio=audio_file,
                caption=f"ᴍʏ ᴡᴏʀʟᴅ 𓏺 @{channel} ",
                title=title,
                performer=info_uploader,
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
            return
    except Exception:
        pass
    
    ydl_opts = {
        "format": "bestaudio[ext=m4a]",  # تحديد صيغة M4A
        "keepvideo": False,
        "geo_bypass": True,
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "quiet": True,
        "cookiefile": f"{cookies()}",
        "proxy": "",
        "retries": 5,
        "fragment_retries": 5,
        "extractor_retries": 3,
        "nocheckcertificate": True,
        "noplaylist": True,
        "geo_bypass_country": "US",
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)  # التنزيل مباشرة
            audio_file = ydl.prepare_filename(info_dict)
            # تخزين الكاش
            try:
                set_cached_search(query, {
                    'vidid': info_dict.get('id'),
                    'title': info_dict.get('title', title),
                    'thumb': thumbnail,
                    'duration': duration,
                })
                set_cached_audio(info_dict.get('id'), {
                    'path': audio_file,
                    'uploader': info_dict.get('uploader', 'Unknown'),
                })
            except Exception:
                pass
    except Exception as e:
        err = str(e)
        if "Sign in to confirm you're not a bot" in err or "Use --cookies" in err:
            from ZeMusic.platforms.Youtube import cookies as pick_cookie, ban_cookie
            bad_cookie = ydl_opts.get("cookiefile")
            if bad_cookie:
                ban_cookie(bad_cookie)
                ydl_opts["cookiefile"] = pick_cookie()
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                        info_dict = ydl2.extract_info(link, download=True)
                        audio_file = ydl2.prepare_filename(info_dict)
                        try:
                            set_cached_search(query, {
                                'vidid': info_dict.get('id'),
                                'title': info_dict.get('title', title),
                                'thumb': thumbnail,
                                'duration': duration,
                            })
                            set_cached_audio(info_dict.get('id'), {
                                'path': audio_file,
                                'uploader': info_dict.get('uploader', 'Unknown'),
                            })
                        except Exception:
                            pass
                except Exception as e2:
                    await m.edit(f"error, wait for bot owner to fix\n\nError: {str(e2)}")
                    print(e2)
                    return
        elif "Requested format is not available" in err or "Only images are available" in err:
            ydl_opts["format"] = "bestaudio/best"
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl3:
                    info_dict = ydl3.extract_info(link, download=True)
                    audio_file = ydl3.prepare_filename(info_dict)
                    try:
                        set_cached_search(query, {
                            'vidid': info_dict.get('id'),
                            'title': info_dict.get('title', title),
                            'thumb': thumbnail,
                            'duration': duration,
                        })
                        set_cached_audio(info_dict.get('id'), {
                            'path': audio_file,
                            'uploader': info_dict.get('uploader', 'Unknown'),
                        })
                    except Exception:
                        pass
            except Exception as e3:
                await m.edit(f"error, wait for bot owner to fix\n\nError: {str(e3)}")
                print(e3)
                return
        else:
            await m.edit(f"error, wait for bot owner to fix\n\nError: {err}")
            print(e)
            return
    
    # إرسال الصوت النهائي
    secmul, dur, dur_arr = 1, 0, duration.split(":")
    for i in range(len(dur_arr) - 1, -1, -1):
        dur += int(float(dur_arr[i])) * secmul
        secmul *= 60
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

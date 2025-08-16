import os
import re
import config
import aiohttp
import aiofiles
from ZeMusic.platforms.Youtube import cookies
import yt_dlp
from yt_dlp import YoutubeDL
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from youtube_search import YoutubeSearch
from ZeMusic import app
from ZeMusic.plugins.play.filters import command
from ZeMusic.utils.redis_cache import get_cached_search, set_cached_search, get_cached_audio, set_cached_audio


def remove_if_exists(path):
    if os.path.exists(path):
        os.remove(path)

channel = "KHAYAL70"
lnk = f"https://t.me/{config.CHANNEL_LINK}"
Nem = config.BOT_NAME + " ابحث"

@app.on_message(command(["song", "/song", "بحث", Nem,"يوت"]) & filters.channel)
async def song_downloader3(client, message: Message):
    query = " ".join(message.command[1:])
    m = await message.reply_text("<b>⇜ جـارِ البحث ..</b>")
    
    try:
        # 1) محاولة من الكاش
        cached = get_cached_search(query)
        if cached:
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
        title_clean = re.sub(r'[\\/*?:"<>|]', "", title)
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
    
    # 2) إرسال من الكاش إن وُجد ملف الصوت
    try:
        vidid = results[0]['url_suffix'].split('v=')[-1]
        ca = get_cached_audio(vidid)
        if ca and os.path.exists(ca.get('path','')):
            audio_file = ca['path']
            info_uploader = ca.get('uploader','Unknown')
            # حساب مدة
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
                            [InlineKeyboardButton(text="♪ 𝐋𝐚𝐫𝐢𝐧 ♪", url=lnk)][0],
                        ],
                    ]
                ),
            )
            await m.delete()
            return
    except Exception:
        pass
    
    await m.edit("<b>جاري التحميل ♪</b>")
    
    ydl_opts = {
        "format": "bestaudio[ext=m4a]",  # تحديد صيغة M4A
        "keepvideo": False,
        "geo_bypass": True,
        "outtmpl": f"{title_clean}.%(ext)s",  # استخدام اسم نظيف للملف
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

    # حذف الملفات المؤقتة
    try:
        remove_if_exists(audio_file)
        remove_if_exists(thumb_name)
    except Exception as e:
        print(e)

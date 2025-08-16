import asyncio
import glob
import os
import random
import re
from typing import Union

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from yt_dlp import YoutubeDL

import config
from ZeMusic.utils.database import is_on_off
from ZeMusic.utils.formatters import time_to_seconds, seconds_to_min
from ZeMusic.utils.decorators import asyncify

_PROXY_VARS = [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "all_proxy", "ALL_PROXY", "no_proxy", "NO_PROXY",
]

def _clean_env():
    env = os.environ.copy()
    for k in _PROXY_VARS:
        env.pop(k, None)
    return env

for _k in _PROXY_VARS:
    os.environ.pop(_k, None)


def cookies():
    """الحصول على ملف cookies موثوق لاستخدامه مع yt-dlp
    - يفضّل المسارات المحددة في config.COOKIES_FILES إن وُجدت وتوجد على القرص
    - وإلا يختار أحدث ملف داخل مجلد cookies يحتوي على سطور يوتيوب
    - وإلا ينشئ basic_cookies.txt كحل أخير (قد لا يتجاوز تحقق روبوت يوتيوب)
    """
    try:
        # 1) تفضيل المسارات من config
        try:
            candidates = []
            if getattr(config, "COOKIES_FILES", None):
                for path in config.COOKIES_FILES:
                    if not path:
                        continue
                    abs_path = path if os.path.isabs(path) else os.path.join(os.getcwd(), path)
                    if os.path.exists(abs_path):
                        try:
                            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                                txt = f.read(2048)
                            if ".youtube.com" in txt or "youtube.com" in txt:
                                # أعد مساراً نسبياً متوافقاً مع بقية الكود
                                rel = os.path.relpath(abs_path, os.getcwd())
                                return rel
                        except Exception:
                            pass
        except Exception:
            pass

        # 2) اختيار أحدث ملف في مجلد cookies يحتوي على سطور يوتيوب
        folder_path = os.path.join(os.getcwd(), "cookies")
        if os.path.isdir(folder_path):
            txt_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".txt")]
            txt_files = [f for f in txt_files if os.path.isfile(f)]
            # فرز بحسب آخر تعديل
            txt_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            for abs_path in txt_files:
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        head = f.read(4096)
                    if ".youtube.com" in head or "youtube.com" in head:
                        return os.path.relpath(abs_path, os.getcwd())
                except Exception:
                    continue

        # 3) إنشاء ملف أساسي كحل أخير
        os.makedirs(folder_path, exist_ok=True)
        basic_cookies = """# Netscape HTTP Cookie File
.youtube.com	TRUE	/	FALSE	0	PREF	hl=en&tz=UTC
.youtube.com	TRUE	/	TRUE	0	SOCS	CAI
.youtube.com	TRUE	/	TRUE	0	YSC	dQw4w9WgXcQ
"""
        basic_path = os.path.join(folder_path, "basic_cookies.txt")
        with open(basic_path, 'w', encoding='utf-8') as f:
            f.write(basic_cookies)
        return os.path.relpath(basic_path, os.getcwd())
    except Exception:
        # في حال حدوث خطأ غير متوقع، حاول المسار السابق إن وجد
        return "cookies/basic_cookies.txt"


async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=_clean_env(),
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    @asyncify
    def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset in (None,):
            return None
        return text[offset : offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            if str(duration_min) == "None":
                duration_sec = 0
            else:
                duration_sec = int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
        return title

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            duration = result["duration"]
        return duration

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return thumbnail

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        cmd = [
            "yt-dlp",
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            "--cookies", cookies(),
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "--extractor-retries", "3",
            "--retries", "3",
            f"{link}",
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=_clean_env(),
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            error_msg = stderr.decode()
            # Try with different user agent if bot detection
            if "Sign in to confirm you're not a bot" in error_msg:
                # Try with different approach
                try:
                    import config
                    if hasattr(config, 'INVIDIOUS_SERVERS') and config.INVIDIOUS_SERVERS:
                        # Extract video ID and try with Invidious
                        video_id = link.split('/')[-1] if '/' in link else link.split('=')[-1]
                        invidious_url = f"{config.INVIDIOUS_SERVERS[0]}/watch?v={video_id}"
                        cmd_fallback = [
                            "yt-dlp",
                            "-g",
                            "-f",
                            "best[height<=?720][width<=?1280]",
                            "--cookies", cookies(),
                            "--user-agent", "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36",
                            invidious_url,
                        ]
                        proc2 = await asyncio.create_subprocess_exec(
                            *cmd_fallback,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                            env=_clean_env(),
                        )
                        stdout2, _ = await proc2.communicate()
                        if stdout2:
                            return 1, stdout2.decode().split("\n")[0]
                except:
                    pass
            return 0, error_msg

    async def playlist(self, link, limit, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]

        cmd = (
            f"yt-dlp -i --compat-options no-youtube-unavailable-videos "
            f'--cookies {cookies()} --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" '
            f'--extractor-retries 3 --retries 3 --get-id --flat-playlist --playlist-end {limit} --skip-download "{link}" '
            f"2>/dev/null"
        )

        playlist = await shell_cmd(cmd)

        try:
            result = [key for key in playlist.split("\n") if key]
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if link.startswith("http://") or link.startswith("https://"):
            return await self._track(link)
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration_min = result["duration"]
                vidid = result["id"]
                yturl = result["link"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            track_details = {
                "title": title,
                "link": yturl,
                "vidid": vidid,
                "duration_min": duration_min,
                "thumb": thumbnail,
            }
            return track_details, vidid
        except Exception:
            return await self._track(link)

    @asyncify
    def _track(self, q):
        options = {
            "format": "best",
            "noplaylist": True,
            "quiet": True,
            "extract_flat": "in_playlist",
            "cookiefile": f"{cookies()}",
            "proxy": "",
        }
        with YoutubeDL(options) as ydl:
            info_dict = ydl.extract_info(f"ytsearch: {q}", download=False)
            details = info_dict.get("entries")[0]
            info = {
                "title": details["title"],
                "link": details["url"],
                "vidid": details["id"],
                "duration_min": (
                    seconds_to_min(details["duration"])
                    if details["duration"] != 0
                    else None
                ),
                "thumb": details["thumbnails"][0]["url"],
            }
            return info, details["id"]

    @asyncify
    def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        ytdl_opts = {
            "quiet": True,
            "cookiefile": f"{cookies()}",
            "proxy": "",
        }

        ydl = YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    str(format["format"])
                except Exception:
                    continue
                if "dash" not in str(format["format"]).lower():
                    try:
                        format["format"]
                        format["filesize"]
                        format["format_id"]
                        format["ext"]
                        format["format_note"]
                    except KeyError:
                        continue
                    formats_available.append(
                        {
                            "format": format["format"],
                            "filesize": format["filesize"],
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": link,
                        }
                    )
        return formats_available, link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()

        def audio_dl():
            ydl_optssx = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": f"{cookies()}",
                "extractor_retries": 5,
                "retries": 5,
                "fragment_retries": 5,
                "http_headers": {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                },
                "proxy": "",
            }

            x = YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def video_dl():
            ydl_optssx = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": f"{cookies()}",
                "proxy": "",
            }

            x = YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def song_video_dl():
            formats = f"{format_id}+140"
            fpath = f"downloads/{title}"
            ydl_optssx = {
                "format": formats,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
                "cookiefile": f"{cookies()}",
                "proxy": "",
            }

            x = YoutubeDL(ydl_optssx)
            x.download([link])

        def song_audio_dl():
            fpath = f"downloads/{title}.%(ext)s"
            ydl_optssx = {
                "format": format_id,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
                "cookiefile": f"{cookies()}",
                "proxy": "",
            }

            x = YoutubeDL(ydl_optssx)
            x.download([link])

        if songvideo:
            await loop.run_in_executor(None, song_video_dl)
            fpath = f"downloads/{title}.mp4"
            return fpath
        elif songaudio:
            await loop.run_in_executor(None, song_audio_dl)
            fpath = f"downloads/{title}.mp3"
            return fpath
        elif video:
            if await is_on_off(config.YTDOWNLOADER):
                direct = True
                downloaded_file = await loop.run_in_executor(None, video_dl)
            else:
                command = [
                    "yt-dlp",
                    "-g",
                    "-f",
                    "best[height<=?720][width<=?1280]",
                    f"--cookies {cookies()}",
                    link,
                ]

                proc = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()

                if stdout:
                    downloaded_file = stdout.decode().split("\n")[0]
                    direct = None
                else:
                    return
        else:
            direct = True
            downloaded_file = await loop.run_in_executor(None, audio_dl)

        return downloaded_file, direct

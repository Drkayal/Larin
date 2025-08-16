import asyncio
import os

from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
    TelegramServerError,
)

from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio, MediumQualityVideo
from pytgcalls.types.stream import StreamAudioEnded

import config
from ZeMusic import LOGGER, YouTube, app
from ZeMusic.misc import db
from ZeMusic.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from ZeMusic.utils.exceptions import AssistantErr
from ZeMusic.utils.formatters import check_duration, seconds_to_min, speed_converter
from ZeMusic.utils.inline.play import stream_markup
from ZeMusic.utils.stream.autoclear import auto_clean
from ZeMusic.utils.thumbnails import get_thumb
from strings import get_string
from pyrogram.raw.functions.channels import GetFullChannel
from pyrogram.raw.functions.messages import GetFullChat
from pyrogram.raw.functions.phone import CreateGroupCall
from pyrogram.raw.types import InputPeerChannel, InputPeerChat
from pyrogram.errors import ChatAdminRequired


autoend = {}
counter = {}


async def _clear_(chat_id):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)


async def _ensure_active_group_call(assistant: Client, chat_id: int) -> bool:
	"""Ensure there is an active voice/video chat in the target chat.
	Tries to create one via assistant if missing (requires can_manage_video_chats).
	Falls back to bot app if assistant lacks permission.
	"""
	try:
		peer = await assistant.resolve_peer(chat_id)
		full = None
		if isinstance(peer, InputPeerChannel):
			full = await assistant.invoke(GetFullChannel(channel=peer))
		elif isinstance(peer, InputPeerChat):
			full = await assistant.invoke(GetFullChat(chat_id=peer.chat_id))
		else:
			return False
		full_chat = getattr(full, "full_chat", None) or full
		call = getattr(full_chat, "call", None)
		if call is not None:
			return True
		# No active call -> try to create (channels only)
		if isinstance(peer, InputPeerChannel):
			try:
				await assistant.invoke(CreateGroupCall(peer=peer, random_id=assistant.rnd_id() // 9000000000))
				await asyncio.sleep(1.0)
				return True
			except ChatAdminRequired:
				LOGGER(__name__).warning("Assistant lacks permission to start video chat (ChatAdminRequired), trying with bot app")
				try:
					bot_peer = await app.resolve_peer(chat_id)
					if isinstance(bot_peer, InputPeerChannel):
						await app.invoke(CreateGroupCall(peer=bot_peer, random_id=app.rnd_id() // 9000000000))
						await asyncio.sleep(1.0)
						return True
				except Exception as ex:
					LOGGER(__name__).warning(f"Bot CreateGroupCall failed: {type(ex).__name__}: {ex}")
				return False
			except Exception as e:
				LOGGER(__name__).warning(f"CreateGroupCall failed: {type(e).__name__}: {e}")
				return False
		return False
	except Exception as e:
		LOGGER(__name__).warning(f"_ensure_active_group_call failed: {type(e).__name__}: {e}")
		return False


class Call(PyTgCalls):
    def __init__(self):
        self.userbot1 = Client(
            name="ZeAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
        )
        self.one = PyTgCalls(
            self.userbot1,
            cache_duration=100,
        )
        self.userbot2 = Client(
            name="ZeAss2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
        )
        self.two = PyTgCalls(
            self.userbot2,
            cache_duration=100,
        )
        self.userbot3 = Client(
            name="ZeAss3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
        )
        self.three = PyTgCalls(
            self.userbot3,
            cache_duration=100,
        )
        self.userbot4 = Client(
            name="ZeAss4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
        )
        self.four = PyTgCalls(
            self.userbot4,
            cache_duration=100,
        )
        self.userbot5 = Client(
            name="ZeAss5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
        )
        self.five = PyTgCalls(
            self.userbot5,
            cache_duration=100,
        )

    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause_stream(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume_stream(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave_group_call(chat_id)
        except Exception as e:
            LOGGER(__name__).warning(f"Failed to stop stream: {e}")

    async def register_assistant(self, idx: int, session_string: str) -> bool:
        """إضافة حساب مساعد أثناء التشغيل وربطه بـ PyTgCalls.
        idx ∈ {1..5}
        """
        try:
            name = f"ZeAss{idx}"
            client = Client(
                name=name,
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=session_string,
            )
            pytgc = PyTgCalls(client, cache_duration=100)
            await client.start()
            await pytgc.start()
            if idx == 1:
                self.userbot1 = client
                self.one = pytgc
            elif idx == 2:
                self.userbot2 = client
                self.two = pytgc
            elif idx == 3:
                self.userbot3 = client
                self.three = pytgc
            elif idx == 4:
                self.userbot4 = client
                self.four = pytgc
            elif idx == 5:
                self.userbot5 = client
                self.five = pytgc
            else:
                return False
            return True
        except Exception as e:
            LOGGER(__name__).warning(f"register_assistant failed for #{idx}: {e}")
            return False

    async def speedup_stream(self, chat_id: int, file_path, speed, playing):
        assistant = await group_assistant(self, chat_id)
        if str(speed) != str("1.0"):
            base = os.path.basename(file_path)
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            if not os.path.isdir(chatdir):
                os.makedirs(chatdir)
            out = os.path.join(chatdir, base)
            if not os.path.isfile(out):
                if str(speed) == str("0.5"):
                    vs = 2.0
                if str(speed) == str("0.75"):
                    vs = 1.35
                if str(speed) == str("1.5"):
                    vs = 0.68
                if str(speed) == str("2.0"):
                    vs = 0.5
                proc = await asyncio.create_subprocess_exec(
                    "ffmpeg",
                    "-i", file_path,
                    "-filter:v", f"setpts={vs}*PTS",
                    "-filter:a", f"atempo={speed}",
                    out,
                    stdin=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
            else:
                pass
        else:
            out = file_path
        dur = await asyncio.get_event_loop().run_in_executor(None, check_duration, out)
        dur = int(dur)
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration = seconds_to_min(dur)
        stream = (
            AudioVideoPiped(
                out,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
                additional_ffmpeg_parameters=f"-ss {played} -to {duration}",
            )
            if playing[0]["streamtype"] == "video"
            else AudioPiped(
                out,
                audio_parameters=HighQualityAudio(),
                additional_ffmpeg_parameters=f"-ss {played} -to {duration}",
            )
        )
        if str(db[chat_id][0]["file"]) == str(file_path):
            await assistant.change_stream(chat_id, stream)
        else:
            raise AssistantErr("Umm")
        if str(db[chat_id][0]["file"]) == str(file_path):
            exis = (playing[0]).get("old_dur")
            if not exis:
                db[chat_id][0]["old_dur"] = db[chat_id][0]["dur"]
                db[chat_id][0]["old_second"] = db[chat_id][0]["seconds"]
            db[chat_id][0]["played"] = con_seconds
            db[chat_id][0]["dur"] = duration
            db[chat_id][0]["seconds"] = dur
            db[chat_id][0]["speed_path"] = out
            db[chat_id][0]["speed"] = speed

    async def force_stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            check.pop(0)
        except:
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        try:
            await assistant.leave_group_call(chat_id)
        except:
            pass

    async def skip_stream(
        self,
        chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        if video:
            stream = AudioVideoPiped(
                link,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
        else:
            stream = AudioPiped(link, audio_parameters=HighQualityAudio())
        await assistant.change_stream(
            chat_id,
            stream,
        )

    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistant = await group_assistant(self, chat_id)
        stream = (
            AudioVideoPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
                additional_ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
            if mode == "video"
            else AudioPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
                additional_ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
        )
        await assistant.change_stream(chat_id, stream)

    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOGGER_ID)
        await assistant.join_group_call(
            config.LOGGER_ID,
            AudioVideoPiped(link),
        )
        await asyncio.sleep(0.2)
        await assistant.leave_group_call(config.LOGGER_ID)

    async def _join_group_call_retry(self, assistant, chat_id: int, stream, attempts: int = 3):
        # Ensure active call first
        await _ensure_active_group_call(assistant, chat_id)
        for i in range(attempts):
            try:
                # small jitter to avoid server spikes
                await asyncio.sleep(0.5 * (i + 1))
                await assistant.join_group_call(chat_id, stream)
                return
            except TelegramServerError as e:
                # try to ensure call exists then retry, with a forced leave
                try:
                    await assistant.leave_group_call(chat_id)
                except Exception:
                    pass
                await _ensure_active_group_call(assistant, chat_id)
                if i < attempts - 1:
                    await asyncio.sleep(1.0 + i)
                    continue
                raise e

    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        language = await get_lang(chat_id)
        _ = get_string(language)
        if video:
            stream = AudioVideoPiped(
                link,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
        else:
            stream = (
                AudioVideoPiped(
                    link,
                    audio_parameters=HighQualityAudio(),
                    video_parameters=MediumQualityVideo(),
                )
                if video
                else AudioPiped(link, audio_parameters=HighQualityAudio())
            )
        try:
            await self._join_group_call_retry(assistant, chat_id, stream, attempts=3)
        except NoActiveGroupCall:
            raise AssistantErr(_["call_8"])
        except AlreadyJoinedError:
            raise AssistantErr(_["call_9"])
        except TelegramServerError:
            # After retries, try one last time as audio-only fallback
            try:
                fallback_stream = AudioPiped(link, audio_parameters=HighQualityAudio())
                await self._join_group_call_retry(assistant, chat_id, fallback_stream, attempts=1)
            except Exception:
                raise AssistantErr(_["call_10"])
        except Exception as e:
            # Fallback: if FFmpeg encoder issue on video, retry as audio-only
            try:
                import ntgcalls  # type: ignore
                is_ff_err = isinstance(e, getattr(ntgcalls, 'FFmpegError', Exception)) or ('encoder' in str(e).lower())
            except Exception:
                is_ff_err = 'encoder' in str(e).lower()
            if video and is_ff_err:
                try:
                    fallback_stream = AudioPiped(link, audio_parameters=HighQualityAudio())
                    await self._join_group_call_retry(assistant, chat_id, fallback_stream, attempts=2)
                except Exception:
                    raise AssistantErr(_["call_10"])
            else:
                raise
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)
        if await is_autoend():
            counter[chat_id] = {}
            users = len(await assistant.get_participants(chat_id))
            if users == 1:
                autoend[chat_id] = datetime.now() + timedelta(minutes=1)

    
    async def change_stream(self, client, chat_id):
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
            await auto_clean(popped)
            if not check:
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)
        except:
            try:
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)
            except:
                return
        else:
            queued = check[0]["file"]
            language = await get_lang(chat_id)
            _ = get_string(language)
            title = (check[0]["title"]).title()
            user = check[0]["by"]
            original_chat_id = check[0]["chat_id"]
            streamtype = check[0]["streamtype"]
            videoid = check[0]["vidid"]
            db[chat_id][0]["played"] = 0
            exis = (check[0]).get("old_dur")
            if exis:
                db[chat_id][0]["dur"] = exis
                db[chat_id][0]["seconds"] = check[0]["old_second"]
                db[chat_id][0]["speed_path"] = None
                db[chat_id][0]["speed"] = 1.0
            video = True if str(streamtype) == "video" else False
            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                if video:
                    stream = AudioVideoPiped(
                        link,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                else:
                    stream = AudioPiped(
                        link,
                        audio_parameters=HighQualityAudio(),
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except Exception:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                img = await get_thumb(videoid)
                button = stream_markup(_, chat_id)
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            elif "vid_" in queued:
                mystic = await app.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, direct = await YouTube.download(
                        videoid,
                        mystic,
                        videoid=True,
                        video=True if str(streamtype) == "video" else False,
                    )
                except:
                    return await mystic.edit_text(
                        _["call_6"], disable_web_page_preview=True
                    )
                if video:
                    stream = AudioVideoPiped(
                        file_path,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                else:
                    stream = AudioPiped(
                        file_path,
                        audio_parameters=HighQualityAudio(),
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                img = await get_thumb(videoid)
                button = stream_markup(_, chat_id)
                await mystic.delete()
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
            elif "index_" in queued:
                stream = (
                    AudioVideoPiped(
                        videoid,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                    if str(streamtype) == "video"
                    else AudioPiped(videoid, audio_parameters=HighQualityAudio())
                )
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                button = stream_markup(_, chat_id)
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=config.STREAM_IMG_URL,
                    caption=_["stream_2"].format(user),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            else:
                if video:
                    stream = AudioVideoPiped(
                        queued,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                else:
                    stream = AudioPiped(
                        queued,
                        audio_parameters=HighQualityAudio(),
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                if videoid == "telegram":
                    button = stream_markup(_, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=config.TELEGRAM_AUDIO_URL
                        if str(streamtype) == "audio"
                        else config.TELEGRAM_VIDEO_URL,
                        caption=_["stream_1"].format(
                            config.SUPPORT_CHAT, title[:23], check[0]["dur"], user
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                elif videoid == "soundcloud":
                    button = stream_markup(_, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=config.SOUNCLOUD_IMG_URL,
                        caption=_["stream_1"].format(
                            config.SUPPORT_CHAT, title[:23], check[0]["dur"], user
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                else:
                    img = await get_thumb(videoid)
                    button = stream_markup(_, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=img,
                        caption=_["stream_1"].format(
                            f"https://t.me/{app.username}?start=info_{videoid}",
                            title[:23],
                            check[0]["dur"],
                            user,
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"

    
    async def ping(self):
        pings = []
        if config.STRING1:
            pings.append(await self.one.ping)
        if config.STRING2:
            pings.append(await self.two.ping)
        if config.STRING3:
            pings.append(await self.three.ping)
        if config.STRING4:
            pings.append(await self.four.ping)
        if config.STRING5:
            pings.append(await self.five.ping)
        return str(round(sum(pings) / len(pings), 3))

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Client...\n")
        if config.STRING1:
            await self.one.start()
        if config.STRING2:
            await self.two.start()
        if config.STRING3:
            await self.three.start()
        if config.STRING4:
            await self.four.start()
        if config.STRING5:
            await self.five.start()

    
    async def decorators(self):
        """
        تفعيل معالجات أحداث PyTgCalls بشكل توافقـي إن كانت متاحة في الإصدار الحالي.
        """
        try:
            # handler عند انتهاء البث
            async def _stream_end(client, update):
                try:
                    if hasattr(update, 'chat_id'):
                        await self.change_stream(client, update.chat_id)
                except Exception as e:
                    LOGGER(__name__).error(f"خطأ في stream_end_handler: {e}")

            # handlers للخدمات (طرد/مغادرة/إغلاق المكالمة)
            async def _service_handler(_, chat_id: int):
                try:
                    await self.stop_stream(chat_id)
                except Exception:
                    pass

            for client in [self.one, self.two, self.three, self.four, self.five]:
                if not client:
                    continue
                # اربط إن كانت الدالة مدعومة في هذا الإصدار
                if hasattr(client, 'on_stream_end'):
                    client.on_stream_end()(_stream_end)
                if hasattr(client, 'on_kicked'):
                    client.on_kicked()(_service_handler)
                if hasattr(client, 'on_closed_voice_chat'):
                    client.on_closed_voice_chat()(_service_handler)
                if hasattr(client, 'on_left'):
                    client.on_left()(_service_handler)

            LOGGER(__name__).info("تم تهيئة PyTgCalls مع معالجات الأحداث")
        except Exception as e:
            LOGGER(__name__).warning(f"تعذّر ربط معالجات الأحداث: {type(e).__name__}: {e}")

    async def stop_stream_force(self, chat_id: int):
        try:
            assistant = await group_assistant(self, chat_id)
            try:
                await assistant.leave_group_call(chat_id)
            except Exception:
                pass
            try:
                await _clear_(chat_id)
            except Exception:
                pass
        except Exception:
            pass


Mody = Call()

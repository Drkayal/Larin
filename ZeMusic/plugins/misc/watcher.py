from pyrogram import filters
from pyrogram.types import Message

from ZeMusic import app
from ZeMusic.core.call import Mody
from ZeMusic.utils.redis_cache import is_music_replies_enabled

# قائمة المسارات/الوحدات التي نريد تعطيل ردودها
_TARGET_MODULES = {
	"ZeMusic.plugins.play.Abod",
	"ZeMusic.plugins.play.bot",
	"ZeMusic.plugins.play.cmds",
	"ZeMusic.plugins.play.devm",
	"ZeMusic.plugins.play.zzcmd",
	"ZeMusic.plugins.play.كيبورد",
	"ZeMusic.plugins.play.نادي المطور",
	"ZeMusic.plugins.bot.start",
	"ZeMusic.plugins.Managed.Bot",
	"ZeMusic.plugins.Managed.BotName",
	"ZeMusic.plugins.Managed.Gpt",
	"ZeMusic.plugins.Managed.Telegraph",
	"ZeMusic.plugins.Managed.قاعدة",
	"ZeMusic.utils.inline.start",
	"ZeMusic.utils.inline.stats",
}


@app.on_message()
async def _global_music_replies_guard(client, message):
	try:
		if is_music_replies_enabled():
			return
		# التعطيل صامت: لا نفعل شيئاً هنا لتجنب تضارب مع باقي الأوامر
		return
	except Exception:
		return


welcome = 20
close = 30


@app.on_message(filters.video_chat_started, group=welcome)
@app.on_message(filters.video_chat_ended, group=close)
async def welcome(_, message: Message):
    await Mody.stop_stream_force(message.chat.id)

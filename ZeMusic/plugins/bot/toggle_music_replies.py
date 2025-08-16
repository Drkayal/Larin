from pyrogram import filters
from ZeMusic import app
import config
from ZeMusic.utils.redis_cache import set_music_replies_enabled
import importlib, sys

OWNER_ID = config.OWNER_ID

_BLOCKED_MODULES = {
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


def _remove_blocked_handlers():
	try:
		dispatcher = getattr(app, "dispatcher", None)
		if not dispatcher:
			return
		groups = getattr(dispatcher, "groups", {})
		for g, handlers in list(groups.items()):
			try:
				new_list = []
				for h in handlers:
					mod = getattr(h.callback, "__module__", "")
					if mod in _BLOCKED_MODULES:
						continue
					new_list.append(h)
				groups[g] = new_list
			except Exception:
				continue
	except Exception:
		pass


def _reload_blocked_modules():
	for name in _BLOCKED_MODULES:
		try:
			if name in sys.modules:
				importlib.reload(sys.modules[name])
			else:
				importlib.import_module(name)
		except Exception:
			continue


@app.on_message(filters.user(OWNER_ID) & filters.command(["تعطيل ردود الميوزك"], ""))
async def disable_music_replies(_, message):
	set_music_replies_enabled(False)
	_remove_blocked_handlers()
	await message.reply_text("تم تعطيل ردود الميوزك")


@app.on_message(filters.user(OWNER_ID) & filters.command(["تفعيل ردود الميوزك"], ""))
async def enable_music_replies(_, message):
	set_music_replies_enabled(True)
	_reload_blocked_modules()
	await message.reply_text("تم تفعيل ردود الميوزك")
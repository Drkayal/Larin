from ZeMusic.core.bot import Mody
from ZeMusic.core.dir import dirr
from ZeMusic.core.git import git
from ZeMusic.core.userbot import Userbot
from ZeMusic.misc import dbb, heroku

from .logging import LOGGER

dirr()
git()
dbb()
heroku()

app = Mody()
userbot = Userbot()

# منع تسجيل هاندلرز من وحدات معينة عند تعطيل ردود الميوزك
try:
	from ZeMusic.utils.redis_cache import is_music_replies_enabled
	from pyrogram.handlers.handler import Handler

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

	_original_add_handler = app.add_handler

	def _wrapped_add_handler(handler: Handler, group: int = 0):
		try:
			if not is_music_replies_enabled():
				mod = getattr(handler.callback.__module__, "__str__", lambda: handler.callback.__module__)()
				if mod in _BLOCKED_MODULES:
					# تجاهل تسجيل هذا الهاندلر عند التعطيل
					return
		except Exception:
			pass
		return _original_add_handler(handler, group)

	app.add_handler = _wrapped_add_handler
except Exception:
	pass

from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()

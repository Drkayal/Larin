from pyrogram import filters
from ZeMusic import app
import config
from ZeMusic.utils.redis_cache import set_music_replies_enabled

OWNER_ID = config.OWNER_ID

@app.on_message(filters.user(OWNER_ID) & filters.command(["تعطيل ردود الميوزك"], ""))
async def disable_music_replies(_, message):
	ok = set_music_replies_enabled(False)
	await message.reply_text("تم تعطيل ردود الميوزك" if ok else "تعذر الوصول إلى نظام الكاش")

@app.on_message(filters.user(OWNER_ID) & filters.command(["تفعيل ردود الميوزك"], ""))
async def enable_music_replies(_, message):
	ok = set_music_replies_enabled(True)
	await message.reply_text("تم تفعيل ردود الميوزك" if ok else "تعذر الوصول إلى نظام الكاش")
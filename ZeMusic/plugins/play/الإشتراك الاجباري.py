from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChatWriteForbidden
from ZeMusic import app
import config
from ZeMusic.misc import SUDOERS


def _normalize_channel(value: str) -> tuple[str, str]:
	if not value:
		return "", ""
	v = value.strip()
	if v.startswith("https://t.me/"):
		slug = v.split("https://t.me/")[-1].lstrip("@")
	elif v.startswith("@"):
		slug = v[1:]
	else:
		slug = v
	url = f"https://t.me/{slug}" if not slug.startswith("-100") else v
	return slug, url

Muntazer_raw = config.CHANNEL_ASHTRAK
Muntazer, Muntazer_url = _normalize_channel(Muntazer_raw)

@app.on_message(filters.incoming & filters.private, group=-1)
async def must_join_channel(app: Client, msg: Message):
	# تجاوز لمالك البوت والمخولين
	try:
		if msg.from_user and (msg.from_user.id == config.OWNER_ID or msg.from_user.id in SUDOERS):
			return
	except Exception:
		pass
	if not Muntazer:
		return
	try:
		try:
			await app.get_chat_member(Muntazer, msg.from_user.id)
		except UserNotParticipant:
			link = Muntazer_url
			if not link:
				return
			try:
				await msg.reply(
					f"⟡ عزيزي {msg.from_user.mention} \n⟡ عليك الأشتراك في قناة البوت \n⟡ قناة البوت : @{Muntazer}.",
					disable_web_page_preview=True,
					reply_markup=InlineKeyboardMarkup([
						[InlineKeyboardButton(text="اضغط للإشتراك", url=link)]
					])
				)
				await msg.stop_propagation()
			except ChatWriteForbidden:
				pass
	except ChatAdminRequired:
		# لا توقف التمرير إن لم أكن أدمن
		return


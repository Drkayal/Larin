from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChatWriteForbidden
from ZeMusic import app
import config
from ZeMusic.misc import SUDOERS

Muntazer = config.CHANNEL_ASHTRAK
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
			link = None
			try:
				if Muntazer.isalpha():
					link = "https://t.me/" + Muntazer
				else:
					chat_info = await app.get_chat(Muntazer)
					link = chat_info.invite_link
			except ChatAdminRequired:
				# لا توقف التمرير إن لم أكن أدمن
				return
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
		print(f"I m not admin in the MUST_JOIN chat {Muntazer}!")


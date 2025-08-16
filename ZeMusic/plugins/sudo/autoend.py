from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatType

import asyncio
import time

from ZeMusic import app
from ZeMusic.misc import SUDOERS
from ZeMusic.utils.database import get_client, is_active_chat

# تخزين آخر نشاط تشغيل لكل دردشة
_LAST_ACTIVITY: dict[int, float] = {}
_AUTO_LEAVE_ENABLED: bool = False
_CHECK_INTERVAL_SECONDS: int = 60  # فحص كل دقيقة
_IDLE_LIMIT_SECONDS: int = 10 * 60  # عشر دقائق


def mark_activity(chat_id: int) -> None:
	_LAST_ACTIVITY[chat_id] = time.time()


async def _auto_leave_loop() -> None:
	while True:
		await asyncio.sleep(_CHECK_INTERVAL_SECONDS)
		if not _AUTO_LEAVE_ENABLED:
			continue
		# نحصل على جميع المساعدين
		try:
			from ZeMusic.core.userbot import assistants
		except Exception:
			assistants = []
		for num in assistants:
			client = await get_client(num)
			try:
				async for dialog in client.get_dialogs():
					if dialog.chat.type not in (ChatType.SUPERGROUP, ChatType.GROUP, ChatType.CHANNEL):
						continue
					chat_id = dialog.chat.id
					# لا نغادر إذا كان هناك تشغيل نشط بحسب ذاكرة التشغيل
					if await is_active_chat(chat_id):
						mark_activity(chat_id)
						continue
					# تحقق من آخر نشاط معروف
					last = _LAST_ACTIVITY.get(chat_id, 0)
					if last == 0:
						# أول مرة نراه بدون نشاط
						mark_activity(chat_id)
						continue
					if time.time() - last >= _IDLE_LIMIT_SECONDS:
						# مغادرة بصمت
						try:
							await client.leave_chat(chat_id)
						except Exception:
							pass
			except Exception:
				continue


@app.on_message(filters.command(["تفعيل المغادره التلقائيه"], "") & SUDOERS)
async def enable_auto_leave(_, message: Message):
	global _AUTO_LEAVE_ENABLED
	_AUTO_LEAVE_ENABLED = True
	await message.reply_text("تم تفعيل المغادرة التلقائية للمساعدين بصمت بعد 10 دقائق من عدم الاستخدام.")


@app.on_message(filters.command(["تعطيل المغادره التلقائيه"], "") & SUDOERS)
async def disable_auto_leave(_, message: Message):
	global _AUTO_LEAVE_ENABLED
	_AUTO_LEAVE_ENABLED = False
	await message.reply_text("تم تعطيل المغادرة التلقائية للمساعدين.")


# بدء الحلقة الخلفية
asyncio.create_task(_auto_leave_loop())

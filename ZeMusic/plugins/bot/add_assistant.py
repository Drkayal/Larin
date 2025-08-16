import os
import re
from pyrogram import filters
from pyrogram.types import Message

from ZeMusic import app, userbot
import config
from ZeMusic.core.call import Mody

OWNER_ID = config.OWNER_ID

_SESSION_PROMPT_FLAG = f"owner:add_assistant:await:{OWNER_ID}"

# تخزين بسيط بالذاكرة كبديل عن Redis
_flag_mem = {"await": False}


def _set_flag(val: bool) -> None:
	_flag_mem["await"] = val


def _get_flag() -> bool:
	return bool(_flag_mem.get("await"))


def _store_session_in_env(session: str) -> None:
	# ضعها في أول متغير STRING_SESSION* الفارغ
	pairs = {}
	for idx in range(1, 6):
		key = "STRING_SESSION" if idx == 1 else f"STRING_SESSION{idx}"
		cur = getattr(config, f"STRING{idx}")
		if not cur:
			pairs[key] = session
			break
	if not pairs:
		# لا يوجد خانة فارغة
		return
	# تحديث .env
	root = os.getcwd()
	p = os.path.join(root, ".env")
	lines = []
	try:
		if os.path.exists(p):
			with open(p, "r", encoding="utf-8") as f:
				lines = f.readlines()
	except Exception:
		lines = []
	existing = set()
	new_lines = []
	for ln in lines:
		m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=.*$", ln)
		if not m:
			new_lines.append(ln)
			continue
		k = m.group(1)
		if k in pairs:
			new_lines.append(f"{k}='{pairs[k]}'\n")
			existing.add(k)
		else:
			new_lines.append(ln)
	for k, v in pairs.items():
		if k not in existing:
			new_lines.append(f"{k}='{v}'\n")
	try:
		with open(p, "w", encoding="utf-8") as f:
			f.writelines(new_lines)
	except Exception:
		pass


@app.on_message(filters.user(OWNER_ID) & filters.command(["اضافه حساب مساعد"], ""))
async def ask_session(_, message: Message):
	_set_flag(True)
	await message.reply_text("أرسل الآن كود جلسة Pyrogram للحساب المساعد الجديد.")


@app.on_message(filters.user(OWNER_ID))
async def on_session(_, message: Message):
	if not _get_flag():
		return
	if not message.text:
		return await message.reply_text("الرجاء إرسال كود الجلسة كنص.")
	# استهلاك العلم
	_set_flag(False)
	session = message.text.strip()
	# محاولة إضافة الحساب
	ok = False
	try:
		ok = await userbot.add_assistant(session)
		if ok:
			# اربط PyTgCalls للمكالمات لنفس المؤشر الأول الفارغ
			for idx in range(1, 6):
				if not getattr(config, f"STRING{idx}"):
					continue
			# اختر أول خانة امتلأت الآن
			for idx in range(1, 6):
				if getattr(config, f"STRING{idx}") == session:
					await Mody.register_assistant(idx, session)
					break
	except Exception:
		ok = False
	if not ok:
		return await message.reply_text("تعذر التحقق من كود الجلسة أو لا توجد خانة متاحة. جرب كوداً آخر.")
	# حفظ في .env وفي config
	_store_session_in_env(session)
	await message.reply_text("تمت إضافة الحساب المساعد وتشغيله بنجاح.")
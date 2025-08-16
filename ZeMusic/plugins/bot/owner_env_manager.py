import os
import re
import json
from typing import Optional, Dict, Any

from pyrogram import filters
from pyrogram.types import Message

from ZeMusic import app
import config
from ZeMusic.utils.redis_cache import get_client as get_redis

OWNER_ID = config.OWNER_ID
_STATE_KEY = f"owner:env:state:{OWNER_ID}"

# تخزين ذاكرية بديلة عند عدم توفر Redis
_state_mem: Dict[int, Dict[str, Any]] = {}


def _normalize_slug(text: str) -> str:
	"""يزيل @ و https://t.me/ والشرطات المائلة بنهاية الرابط."""
	s = (text or "").strip()
	s = s.replace("\u200f", "").replace("\u200e", "")  # إزالة محارف RTL/LTR إن وجدت
	m = re.match(r"https?://t\.me/(.+)$", s, flags=re.IGNORECASE)
	if m:
		s = m.group(1)
	s = s.lstrip('@').strip('/')
	return s


def _normalize_logger_id(text: str) -> Optional[int]:
	"""يقبل فقط رقم ID. يرفض الروابط/اليوزرات."""
	s = (text or "").strip()
	# منع الروابط/اليوزرات
	if s.startswith("http") or s.startswith("t.me") or s.startswith("@"):
		return None
	# السماح بالأرقام السالبة/الموجبة
	try:
		val = int(s)
		return val
	except Exception:
		return None


def _update_env_vars(pairs: Dict[str, str]) -> bool:
	"""تحديث ملف .env وإضافة المفاتيح عند عدم وجودها، مع الحفاظ على باقي الأسطر."""
	root = os.getcwd()
	path = os.path.join(root, ".env")
	lines = []
	try:
		if os.path.exists(path):
			with open(path, "r", encoding="utf-8") as f:
				lines = f.readlines()
	except Exception:
		lines = []
	existing_keys = set()
	new_lines = []
	for ln in lines:
		m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=.*$", ln)
		if not m:
			new_lines.append(ln)
			continue
		key = m.group(1)
		if key in pairs:
			val = pairs[key]
			new_lines.append(f"{key}={val}\n")
			existing_keys.add(key)
		else:
			new_lines.append(ln)
	# إضافة المفاتيح غير الموجودة
	for k, v in pairs.items():
		if k not in existing_keys:
			new_lines.append(f"{k}={v}\n")
	try:
		with open(path, "w", encoding="utf-8") as f:
			f.writelines(new_lines)
		return True
	except Exception:
		return False


def _apply_runtime_updates(pairs: Dict[str, str]) -> None:
	for k, v in pairs.items():
		os.environ[k] = v
		# تحديث كائن config في الذاكرة للتأثير الفوري حيث أمكن
		try:
			if k == "LOGGER_ID":
				setattr(config, k, int(v))
			else:
				setattr(config, k, v)
		except Exception:
			pass


def _set_state(data: Dict[str, Any]) -> None:
	client = get_redis()
	if client:
		try:
			client.setex(_STATE_KEY, 1800, json.dumps(data, ensure_ascii=False))
			return
		except Exception:
			pass
	_state_mem[OWNER_ID] = data


def _get_state() -> Optional[Dict[str, Any]]:
	client = get_redis()
	if client:
		try:
			val = client.get(_STATE_KEY)
			if val:
				return json.loads(val)
		except Exception:
			pass
	return _state_mem.get(OWNER_ID)


def _clear_state() -> None:
	client = get_redis()
	if client:
		try:
			client.delete(_STATE_KEY)
			return
		except Exception:
			pass
	_state_mem.pop(OWNER_ID, None)


# الأوامر - بدون سلاش
@app.on_message(filters.user(OWNER_ID) & filters.command(["تغيير اسم البوت"], ""))
async def change_bot_name(_, message: Message):
	_set_state({"action": "bot_name", "step": 1})
	await message.reply_text("أرسل اسم البوت الجديد.")


@app.on_message(filters.user(OWNER_ID) & filters.command(["تغيير قناه السورس"], ""))
async def change_source_channel(_, message: Message):
	_set_state({"action": "source_channel", "step": 1})
	await message.reply_text("أرسل اسم قناة السورس الجديد.")


@app.on_message(filters.user(OWNER_ID) & filters.command(["تغيير قناه المتجر"], ""))
async def change_store_channel(_, message: Message):
	_set_state({"action": "store_channel", "step": 1})
	await message.reply_text("أرسل اسم قناة المتجر الجديد.")


@app.on_message(filters.user(OWNER_ID) & filters.command(["تغيير قروب السجل", "تغيير قورب السجل"], ""))
async def change_logger(_, message: Message):
	_set_state({"action": "logger_id", "step": 1})
	await message.reply_text("أرسل الآن ايدي قروب السجل (رقم يبدأ عادة بـ -100...).")


@app.on_message(filters.user(OWNER_ID) & filters.command(["تغيير قناه الاشتراك الاجباري"], ""))
async def change_force_sub(_, message: Message):
	_set_state({"action": "force_sub", "step": 1})
	await message.reply_text("أرسل رابط/يوزر قناة الاشتراك الإجباري (بدون @ أو https://t.me/ سيتم التنسيق تلقائياً).")


@app.on_message(filters.user(OWNER_ID) & filters.command(["تغيير اسم الذكاء الاصطناعي"], ""))
async def change_gpt_name(_, message: Message):
	_set_state({"action": "gpt_name", "step": 1})
	await message.reply_text("أرسل اسم الذكاء الاصطناعي الجديد.")


@app.on_message(filters.user(OWNER_ID))
async def on_owner_reply(_, message: Message):
	# تجاهل إن لم تكن هناك حالة قائمة
	state = _get_state()
	if not state:
		return
	if not message.text:
		return await message.reply_text("الرجاء إرسال نص صالح.")

	action = state.get("action")
	step = int(state.get("step", 1))
	text = message.text.strip()

	if action == "bot_name" and step == 1:
		new_name = text
		pairs = {"BOT_NAME": new_name}
		_apply_runtime_updates(pairs)
		_update_env_vars(pairs)
		_clear_state()
		return await message.reply_text(f"تم تحديث اسم البوت إلى: {new_name}")

	if action == "gpt_name" and step == 1:
		new_name = text
		pairs = {"GPT_NAME": new_name}
		_apply_runtime_updates(pairs)
		_update_env_vars(pairs)
		_clear_state()
		return await message.reply_text(f"تم تحديث اسم الذكاء الاصطناعي إلى: {new_name}")

	if action == "source_channel":
		if step == 1:
			# استلمنا الاسم
			state["name"] = text
			state["step"] = 2
			_set_state(state)
			return await message.reply_text("أرسل الآن رابط/يوزر قناة السورس.")
		elif step == 2:
			slug = _normalize_slug(text)
			name = state.get("name", "")
			pairs = {"CHANNEL_NAME": name, "CHANNEL_LINK": slug}
			_apply_runtime_updates(pairs)
			_update_env_vars(pairs)
			_clear_state()
			return await message.reply_text(f"تم تحديث قناة السورس: الاسم='{name}', الرابط='{slug}'")

	if action == "store_channel":
		if step == 1:
			state["name"] = text
			state["step"] = 2
			_set_state(state)
			return await message.reply_text("أرسل الآن رابط/يوزر قناة المتجر.")
		elif step == 2:
			slug = _normalize_slug(text)
			name = state.get("name", "")
			pairs = {"STORE_NAME": name, "STORE_LINK": slug}
			_apply_runtime_updates(pairs)
			_update_env_vars(pairs)
			_clear_state()
			return await message.reply_text(f"تم تحديث قناة المتجر: الاسم='{name}', الرابط='{slug}'")

	if action == "logger_id" and step == 1:
		val = _normalize_logger_id(text)
		if val is None:
			return await message.reply_text("⚠️ الرجاء إرسال ايدي رقمي لقروب السجل فقط.")
		pairs = {"LOGGER_ID": str(val)}
		_apply_runtime_updates(pairs)
		_update_env_vars(pairs)
		_clear_state()
		return await message.reply_text(f"تم تحديث ايدي قروب السجل إلى: {val}")

	if action == "force_sub" and step == 1:
		slug = _normalize_slug(text)
		if not slug:
			return await message.reply_text("⚠️ لم يتم التعرف على رابط/يوزر صالح.")
		pairs = {"CHANNEL_ASHTRAK": slug}
		_apply_runtime_updates(pairs)
		_update_env_vars(pairs)
		_clear_state()
		return await message.reply_text(f"تم تحديث قناة الاشتراك الإجباري إلى: {slug}")

	# حالة غير متوقعة
	_clear_state()
	await message.reply_text("انتهت العملية أو حدث خطأ، أعد المحاولة.")
import os
import re
import json
import time
import asyncio
from typing import List, Tuple

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from ZeMusic import app
import config

from ZeMusic.utils.redis_cache import get_client as get_redis

try:
	from yt_dlp import YoutubeDL  # type: ignore
except Exception:
	YoutubeDL = None

OWNER_ID = config.OWNER_ID

_COOKIES_DIR = os.path.join(os.getcwd(), "cookies")
_TEST_URL = "https://www.youtube.com/watch?v=BaW_jenozKc"
_PENDING_SCAN_KEY = f"cookies:scan:pending:{OWNER_ID}"
_AWAIT_UPLOAD_KEY = f"cookies:await_upload:{OWNER_ID}"


def _collect_cookie_files() -> List[str]:
	files: List[str] = []
	# من config.COOKIES_FILES
	try:
		for path in (getattr(config, "COOKIES_FILES", []) or []):
			if not path:
				continue
			p = path if os.path.isabs(path) else os.path.join(os.getcwd(), path)
			if os.path.isfile(p):
				files.append(p)
	except Exception:
		pass
	# من مجلد cookies
	try:
		if os.path.isdir(_COOKIES_DIR):
			for f in os.listdir(_COOKIES_DIR):
				if f.endswith(".txt"):
					p = os.path.join(_COOKIES_DIR, f)
					if os.path.isfile(p):
						files.append(p)
	except Exception:
		pass
	# إزالة التكرار مع الحفاظ على الترتيب
	seen = set()
	uniq: List[str] = []
	for p in files:
		if p in seen:
			continue
		seen.add(p)
		uniq.append(p)
	return uniq


def _looks_like_youtube_cookies(path: str) -> bool:
	try:
		with open(path, "r", encoding="utf-8", errors="ignore") as f:
			head = f.read(4096)
		return (".youtube.com" in head) or ("youtube.com" in head) or ("Netscape" in head)
	except Exception:
		return False


async def _scan_cookie_with_ytdlp(path: str) -> Tuple[str, bool, str]:
	"""يرجع (المسار، صالح؟، سبب/تفصيل)."""
	if YoutubeDL is None:
		return (path, _looks_like_youtube_cookies(path), "yt_dlp غير مثبت")
	opts = {
		"quiet": True,
		"skip_download": True,
		"cookiefile": path,
		"proxy": "",
		"nocheckcertificate": True,
		"geo_bypass": True,
		"geo_bypass_country": "US",
		"retries": 2,
	}

	def _run() -> Tuple[bool, str]:
		try:
			with YoutubeDL(opts) as ydl:
				ydl.extract_info(_TEST_URL, download=False)
			return (True, "ok")
		except Exception as e:
			msg = str(e)
			# اعتبر رسائل معينة مؤشر فساد/عدم صلاحية
			bad_patterns = [
				"Sign in to confirm",
				"Use --cookies",
				"Video unavailable",
				"403",
				"429",
			]
			is_bad = any(k in msg for k in bad_patterns)
			return (not is_bad and _looks_like_youtube_cookies(path), msg[:200])

	ok, detail = await asyncio.to_thread(_run)
	return (path, ok, detail)


async def _scan_all_cookies() -> Tuple[List[str], List[Tuple[str, str]]]:
	files = _collect_cookie_files()
	if not files:
		return [], []
	results = await asyncio.gather(*[_scan_cookie_with_ytdlp(p) for p in files])
	invalid: List[Tuple[str, str]] = []
	valid: List[str] = []
	for path, ok, detail in results:
		if ok:
			valid.append(path)
		else:
			invalid.append((path, detail))
	return valid, invalid


def _human_list(paths: List[str]) -> str:
	if not paths:
		return "لا يوجد"
	return "\n".join(f"- {os.path.relpath(p, os.getcwd())}" for p in paths)


@app.on_message(filters.user(OWNER_ID) & filters.command(["فحص الكوكيز"], ""))
async def cmd_scan_cookies(_, message: Message):
	await message.reply_text("⏳ جارِ فحص ملفات الكوكيز... قد يستغرق ذلك قليلاً")
	valid, invalid = await _scan_all_cookies()
	invalid_paths = [p for p, _ in invalid]
	client = get_redis()
	if client:
		try:
			client.setex(_PENDING_SCAN_KEY, 900, json.dumps(invalid_paths, ensure_ascii=False))
		except Exception:
			pass
	text = (
		"✅ فحص الكوكيز انتهى\n\n"
		f"الصالحة: {len(valid)}\n"
		f"التالفة/غير الصالحة: {len(invalid)}\n\n"
	)
	if invalid:
		preview = "\n".join(f"- {os.path.basename(p)}" for p in invalid_paths[:15])
		if len(invalid) > 15:
			preview += f"\n... والمزيد ({len(invalid)-15})"
		text += "الملفات التالفة المقترح حذفها:\n" + preview
		kb = InlineKeyboardMarkup(
			[
				[
					InlineKeyboardButton("🗑️ حذف التالفة", callback_data="cookies_del_confirm"),
					InlineKeyboardButton("↩️ إلغاء", callback_data="cookies_del_cancel"),
				]
			]
		)
		await message.reply_text(text, reply_markup=kb)
	else:
		await message.reply_text(text + "لا توجد ملفات تالفة.")


@app.on_callback_query(filters.user(OWNER_ID) & filters.regex("^cookies_del_(confirm|cancel)$"))
async def on_delete_confirm(_, cq: CallbackQuery):
	data = cq.data or ""
	client = get_redis()
	if data.endswith("cancel"):
		if client:
			try:
				client.delete(_PENDING_SCAN_KEY)
			except Exception:
				pass
		return await cq.answer("تم الإلغاء", show_alert=False)

	# confirm
	invalid_paths: List[str] = []
	if client:
		try:
			val = client.get(_PENDING_SCAN_KEY)
			if val:
				invalid_paths = list(json.loads(val))
			client.delete(_PENDING_SCAN_KEY)
		except Exception:
			invalid_paths = []
	deleted = 0
	errs = 0
	for p in invalid_paths:
		try:
			if os.path.exists(p):
				os.remove(p)
				deleted += 1
		except Exception:
			errs += 1
	await cq.message.edit_text(f"تم حذف {deleted} ملفاً تالفاً. {'حدثت أخطاء بسيطة' if errs else ''}")
	await cq.answer("تم التنفيذ", show_alert=False)


@app.on_message(filters.user(OWNER_ID) & filters.command(["اضافه كوكيز"], ""))
async def cmd_add_cookies(_, message: Message):
	client = get_redis()
	if client:
		try:
			client.setex(_AWAIT_UPLOAD_KEY, 600, "1")
		except Exception:
			pass
	await message.reply_text(
		"أرسل الآن ملف الكوكيز بصيغة .txt كـ مستند (Document).\n"
		"سيتم حفظه تلقائياً بدون تعارض في مجلد cookies."
	)


def _sanitize_filename(name: str) -> str:
	name = os.path.splitext(os.path.basename(name))[0]
	name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._")
	return name or f"cookie_{int(time.time())}"


def _unique_path(basename: str) -> str:
	os.makedirs(_COOKIES_DIR, exist_ok=True)
	base = _sanitize_filename(basename)
	candidate = os.path.join(_COOKIES_DIR, f"{base}.txt")
	idx = 1
	while os.path.exists(candidate):
		candidate = os.path.join(_COOKIES_DIR, f"{base}_{idx}.txt")
		idx += 1
	return candidate


@app.on_message(filters.user(OWNER_ID) & filters.document)
async def on_cookie_document(_, message: Message):
	client = get_redis()
	flag = None
	if client:
		try:
			flag = client.get(_AWAIT_UPLOAD_KEY)
		except Exception:
			flag = None
	if not flag:
		return
	# استهلاك العلم
	if client:
		try:
			client.delete(_AWAIT_UPLOAD_KEY)
		except Exception:
			pass

	doc = message.document
	if not doc:
		return await message.reply_text("الرجاء إرسال الملف كمستند.")
	file_name = doc.file_name or "cookies.txt"
	target = _unique_path(file_name)
	try:
		saved_path = await message.download(file_name=target)
	except Exception as e:
		return await message.reply_text(f"تعذر حفظ الملف: {e}")
	# تحقق سريع
	ok = _looks_like_youtube_cookies(saved_path)
	await message.reply_text(
		"✅ تم حفظ ملف الكوكيز: " + os.path.basename(saved_path) + ("\n⚠️ قد لا يكون صالحاً" if not ok else "")
	)
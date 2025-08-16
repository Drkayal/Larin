import asyncio
import importlib
import subprocess
import sys
import os
import shutil
import platform
import tarfile
import tempfile
from urllib.request import urlretrieve

# Apply compatibility patch before importing pytgcalls
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ntgcalls_patch

# إضافة نظام إنشاء قاعدة البيانات التلقائي (سيتم الاستيراد عند الحاجة)
auto_setup_database = None

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from ZeMusic import LOGGER, app, userbot
from ZeMusic.core.call import Mody
from ZeMusic.misc import sudo
from ZeMusic.plugins import ALL_MODULES
from ZeMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS

# إضافة دعم PostgreSQL
if config.DATABASE_TYPE == "postgresql":
	from ZeMusic.core.postgres import init_postgres, close_postgres
	from ZeMusic.database.setup import setup_database
	from ZeMusic.database.migrations import run_migrations


def _ffmpeg_static_url() -> str:
	arch = platform.machine().lower()
	base = "https://johnvansickle.com/ffmpeg/releases"
	if "aarch64" in arch or arch == "arm64":
		return f"{base}/ffmpeg-release-arm64-static.tar.xz"
	if arch.startswith("arm") or arch.startswith("armv7"):
		return f"{base}/ffmpeg-release-armhf-static.tar.xz"
	# default linux x86_64
	return f"{base}/ffmpeg-release-amd64-static.tar.xz"


def _ensure_ffmpeg_locally(bin_dir: str) -> bool:
	try:
		os.makedirs(bin_dir, exist_ok=True)
		ffmpeg_path = os.path.join(bin_dir, "ffmpeg")
		ffprobe_path = os.path.join(bin_dir, "ffprobe")
		if shutil.which("ffmpeg") and shutil.which("ffprobe"):
			return True
		if os.path.isfile(ffmpeg_path) and os.path.isfile(ffprobe_path):
			os.environ["PATH"] = f"{bin_dir}:{os.environ.get('PATH','')}"
			return True
		url = _ffmpeg_static_url()
		with tempfile.TemporaryDirectory() as td:
			archive = os.path.join(td, "ffmpeg-static.tar.xz")
			urlretrieve(url, archive)
			with tarfile.open(archive, mode="r:xz") as tar:
				tar.extractall(td)
			# find extracted folder
			folder = None
			for name in os.listdir(td):
				p = os.path.join(td, name)
				if os.path.isdir(p) and name.startswith("ffmpeg-") and name.endswith("-static"):
					folder = p
					break
			if not folder:
				return False
			src_ffmpeg = os.path.join(folder, "ffmpeg")
			src_ffprobe = os.path.join(folder, "ffprobe")
			shutil.copy2(src_ffmpeg, ffmpeg_path)
			shutil.copy2(src_ffprobe, ffprobe_path)
			os.chmod(ffmpeg_path, 0o755)
			os.chmod(ffprobe_path, 0o755)
			os.environ["PATH"] = f"{bin_dir}:{os.environ.get('PATH','')}"
			return True
	except Exception as e:
		LOGGER(__name__).warning(f"تعذر تجهيز ffmpeg/ffprobe محلياً: {type(e).__name__}: {e}")
		return False


def _bootstrap_ffmpeg() -> None:
	bin_dir = os.path.join(os.getcwd(), "bin")
	if shutil.which("ffprobe") and shutil.which("ffmpeg"):
		return
	ok = _ensure_ffmpeg_locally(bin_dir)
	if ok:
		LOGGER(__name__).info("تم تجهيز ffmpeg/ffprobe محلياً وإضافتهما إلى PATH")
	else:
		LOGGER(__name__).warning("ffprobe/ffmpeg غير متوفرين وقد تفشل بعض الوظائف. يُفضّل تثبيتهما على النظام.")


async def preflight_checks() -> None:
	"""Perform basic startup checks and log clear messages."""
	try:
		# Database check
		if config.DATABASE_TYPE == "postgresql":
			ok = await setup_database()
			if not ok:
				LOGGER(__name__).error("فشل في إعداد قاعدة البيانات. تأكد من إعدادات POSTGRES_* ثم أعد المحاولة.")
				raise RuntimeError("Database setup failed")
		# Filesystem checks
		cookies_dir = os.path.join(os.getcwd(), "cookies")
		if not os.path.isdir(cookies_dir):
			try:
				os.makedirs(cookies_dir, exist_ok=True)
				LOGGER(__name__).info("تم إنشاء مجلد cookies لعمليات YouTube")
			except Exception as e:
				LOGGER(__name__).warning(f"تعذر إنشاء مجلد cookies: {e}")
		# Ensure ffmpeg/ffprobe availability (non-root bootstrap)
		_bootstrap_ffmpeg()
	except Exception as e:
		LOGGER(__name__).error(f"فشل فحص التمهيد: {e}")
		raise


async def auto_install_postgresql():
	"""
	تثبيت وإعداد PostgreSQL تلقائياً
	"""
	try:
		LOGGER(__name__).info("🔍 التحقق من تثبيت PostgreSQL...")
		
		# التحقق من وجود PostgreSQL
		result = subprocess.run(['which', 'psql'], capture_output=True, text=True)
		if result.returncode != 0:
			LOGGER(__name__).info("📦 تثبيت PostgreSQL...")
			
			# تثبيت PostgreSQL
			install_cmd = "sudo apt update && sudo apt install postgresql postgresql-contrib -y"
			result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True)
			
			if result.returncode != 0:
				LOGGER(__name__).error("❌ فشل في تثبيت PostgreSQL")
				return False
			
			LOGGER(__name__).info("✅ تم تثبيت PostgreSQL بنجاح")
		
		# بدء تشغيل PostgreSQL
		LOGGER(__name__).info("⚡ بدء تشغيل PostgreSQL...")
		start_cmd = "sudo service postgresql start"
		result = subprocess.run(start_cmd, shell=True, capture_output=True, text=True)
		
		if result.returncode != 0:
			LOGGER(__name__).error("❌ فشل في بدء تشغيل PostgreSQL")
			return False
		
		LOGGER(__name__).info("✅ تم بدء تشغيل PostgreSQL")
		
		# إعداد كلمة مرور للمستخدم postgres (إذا لم تكن موجودة)
		LOGGER(__name__).info("🔐 إعداد كلمة مرور للمستخدم postgres...")
		
		# التحقق من وجود كلمة مرور
		check_cmd = "sudo -u postgres psql -c \"SELECT 1;\""
		result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
		
		if result.returncode != 0:
			# إعداد كلمة مرور افتراضية
			password = getattr(config, 'POSTGRES_PASSWORD', 'zemusic123')
			password_cmd = f"sudo -u postgres psql -c \"ALTER USER postgres PASSWORD '{password}';\""
			result = subprocess.run(password_cmd, shell=True, capture_output=True, text=True)
			
			if result.returncode != 0:
				LOGGER(__name__).error("❌ فشل في إعداد كلمة مرور PostgreSQL")
				return False
			
			LOGGER(__name__).info("✅ تم إعداد كلمة مرور PostgreSQL")
		else:
			LOGGER(__name__).info("ℹ️ كلمة مرور PostgreSQL موجودة بالفعل")
		
		return True
		
	except Exception as e:
		LOGGER(__name__).error(f"❌ خطأ في تثبيت PostgreSQL: {e}")
		return False


async def auto_create_database():
	"""
	إنشاء قاعدة البيانات تلقائياً إذا لم تكن موجودة
	"""
	try:
		LOGGER(__name__).info("🗄️ التحقق من وجود قاعدة البيانات...")
		
		# الحصول على اسم قاعدة البيانات
		db_name = getattr(config, 'POSTGRES_DB', 'zemusic_bot')
		
		# التحقق من وجود قاعدة البيانات
		check_cmd = f"sudo -u postgres psql -c \"SELECT 1 FROM pg_database WHERE datname = '{db_name}';\""
		result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
		
		if result.returncode != 0 or "1 row" not in result.stdout:
			LOGGER(__name__).info(f"📊 إنشاء قاعدة البيانات: {db_name}")
			
			# إنشاء قاعدة البيانات
			create_cmd = f"sudo -u postgres psql -c \"CREATE DATABASE \"{db_name}\" OWNER postgres;\""
			result = subprocess.run(create_cmd, shell=True, capture_output=True, text=True)
			
			if result.returncode != 0:
				LOGGER(__name__).error(f"❌ فشل في إنشاء قاعدة البيانات: {db_name}")
				return False
			
			LOGGER(__name__).info(f"✅ تم إنشاء قاعدة البيانات: {db_name}")
		else:
			LOGGER(__name__).info(f"ℹ️ قاعدة البيانات {db_name} موجودة بالفعل")
		
		return True
		
	except Exception as e:
		LOGGER(__name__).error(f"❌ خطأ في إنشاء قاعدة البيانات: {e}")
		return False


async def init() -> None:
	if config.DATABASE_TYPE == "postgresql":
		try:
			await init_postgres()
		except Exception:
			pass
	await preflight_checks()
	await sudo()
	try:
		users = await get_gbanned()
		for user_id in users:
			BANNED_USERS.add(user_id)
	except:
		pass
	try:
		users = await get_banned_users()
		for user_id in users:
			BANNED_USERS.add(user_id)
	except:
		pass
	await app.start()
	# start periodic cleanup task (24h by default)
	try:
		from ZeMusic.utils.database import start_cleanup_task
		await start_cleanup_task()
	except Exception:
		pass
	loaded = 0
	if os.getenv("SEARCH_ONLY", "0") == "1":
		allowed_suffixes = {
			".play.بحث",
			".play.بحث قناه",
			".play.download",
		}
		for all_module in ALL_MODULES:
			try:
				if all_module in allowed_suffixes:
					importlib.import_module("ZeMusic.plugins" + all_module)
					loaded += 1
					LOGGER("ZeMusic.plugins").info(f"Imported plugin {all_module}")
			except Exception as e:
				LOGGER("ZeMusic.plugins").warning(f"فشل استيراد البلجن {all_module}: {type(e).__name__}: {e}")
				continue
		LOGGER("ZeMusic.plugins").info(f"SEARCH_ONLY: تم تحميل {loaded} بلجن بحث فقط")
	else:
		for all_module in ALL_MODULES:
			try:
				importlib.import_module("ZeMusic.plugins" + all_module)
				LOGGER("ZeMusic.plugins").info(f"Imported plugin {all_module}")
			except Exception as e:
				LOGGER("ZeMusic.plugins").warning(f"فشل استيراد البلجن {all_module}: {type(e).__name__}: {e}")
				continue
	# Optional: keep only search plugins
	if os.getenv("SEARCH_ONLY", "0") == "1":
		try:
			dispatcher = getattr(app, "dispatcher", None)
			allowed = {
				"ZeMusic.plugins.play.بحث",
				"ZeMusic.plugins.play.بحث قناه",
				"ZeMusic.plugins.play.download",
			}
			kept = 0
			removed = 0
			if dispatcher:
				groups = getattr(dispatcher, "groups", {})
				for g, handlers in list(groups.items()):
					new_list = []
					for h in handlers:
						mod = getattr(h.callback, "__module__", "")
						if mod in allowed:
							new_list.append(h)
							kept += 1
						else:
							removed += 1
					groups[g] = new_list
			LOGGER("ZeMusic.plugins").info(f"SEARCH_ONLY مفعّل: أبقينا {kept} ومع إزالة {removed} من الهاندلرز.")
		except Exception as e:
			LOGGER("ZeMusic.plugins").warning(f"تعذر تفعيل SEARCH_ONLY: {type(e).__name__}: {e}")
	LOGGER("ZeMusic.plugins").info("تنزيل معلومات السورس...")
	try:
		await userbot.start()
	except Exception as e:
		LOGGER("ZeMusic.userbot").warning(f"تعذّر تشغيل المساعدين: {type(e).__name__}. سيستمر البوت بدون مساعدين.")
	try:
		await Mody.start()
	except Exception as e:
		LOGGER("ZeMusic.calls").warning(f"تعذّر تشغيل نظام المكالمات حالياً: {type(e).__name__}.")
	try:
		await Mody.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
	except NoActiveGroupCall:
		LOGGER("ZeMusic").warning(
			"No active group call found. Bot will continue without initial stream..."
		)
	except:
		pass
	await Mody.decorators()
	LOGGER("ZeMusic").info(
		"جاري تشغيل البوت\nتم التنصيب على سورس الملك بنجاح\nقناة السورس https://t.me/EF_19"
	)
	await idle()
	await app.stop()
	try:
		await userbot.stop()
	except Exception:
		pass
	if config.DATABASE_TYPE == "postgresql":
		try:
			await close_postgres()
		except Exception:
			pass


if __name__ == "__main__":
	asyncio.get_event_loop().run_until_complete(init())

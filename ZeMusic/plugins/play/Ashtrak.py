from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.types import InlineKeyboardMarkup as Markup, InlineKeyboardButton as Button
from pyrogram.enums import ChatType
from pyrogram.errors import UserNotParticipant, ChatAdminRequired
from ZeMusic import app
import config
from ZeMusic.plugins.play.filters import command


def _normalize_channel(value: str) -> tuple[str, str]:
    """Return (slug_or_id, url) for a given channel value from config."""
    if not value:
        return "", ""
    v = value.strip()
    # Accept forms: https://t.me/slug, @slug, slug, -100... id
    if v.startswith("https://t.me/"):
        slug = v.split("https://t.me/")[-1].lstrip("@")
    elif v.startswith("@"):
        slug = v[1:]
    else:
        slug = v
    url = f"https://t.me/{slug}" if not slug.startswith("-100") else v
    return slug, url

channel_raw = config.CHANNEL_ASHTRAK
channel_slug, channel_url = _normalize_channel(channel_raw)
Nem = config.BOT_NAME + " شغل"

async def subscription(_, __: Client, message: Message):
    user_id = message.from_user.id
    # If channel not configured, allow
    if not channel_slug:
        return True
    try:
        # Try membership check; if bot lacks admin in channel, skip enforcement
        await app.get_chat_member(channel_slug, user_id)
    except UserNotParticipant:
        return False
    except ChatAdminRequired:
        return True
    except Exception:
        # If any unexpected error occurs, don't block the user
        return True
    return True
    
subscribed = filters.create(subscription)

# تعريف دالة لمعالجة الأوامر
@app.on_message(command(["تشغيل", "بحث", "تخطي", "استئناف", "تقديم", "تحميل", "توقف", "مؤقت", "كمل", "كملي", "لارين بحث", "غنيلي", "شعر", "قران", "اذكار", "ادعيه", "play", "شغلي", "/start", "vplay", "vتشغيل", "cplay", "cvplay", "playforce", "vplayforce", "cplayforce", "cvplayforce", "start", "stats", "الاوامر", "اوامر", "ميوزك", "بنج", "سرعه", "song", "/song", "شغل",Nem]) & ~subscribed)
async def command_handler(_: Client, message: Message):
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        user_id = message.from_user.id
        user = message.from_user.first_name
        if not channel_url:
            return
        markup = Markup([
            [Button(text="اضغط للإشتراك", url=channel_url)]
        ])
        await message.reply(
            f"<b>↤عذراً عزيزي {user}\n↤عليك الإشتراك في قناة البوت اولاً",
            reply_markup=markup
        )

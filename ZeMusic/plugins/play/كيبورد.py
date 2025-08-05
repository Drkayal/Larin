import asyncio
from pyrogram import Client, filters
from strings.filters import command
from ZeMusic.utils.decorators import AdminActual
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InputMediaPhoto,
    Message,
)
from ZeMusic import (Apple, Resso, SoundCloud, Spotify, Telegram, YouTube, app)

# استيراد OWNER_ID و DEV_ID من ملف config.py
try:
    from config import OWNER_ID, DEV_ID
except ImportError:
    OWNER_ID = []
    DEV_ID = []

# إذا كانت OWNER_ID أو DEV_ID ليست قائمة، نحولها إلى قائمة
if not isinstance(OWNER_ID, list):
    OWNER_ID = [OWNER_ID]
if not isinstance(DEV_ID, list):
    DEV_ID = [DEV_ID]

# قائمة المطورين: OWNER_ID + DEV_ID
DEVELOPER_IDS = OWNER_ID + DEV_ID

# --- لوحات مفاتيح المستخدمين العاديين ---
REPLY_MESSAGE = "<b>⟡ اهلا بك عزيزي اليك قائمه الاوامر</b>"
REPLY_MESSAGE_BUTTONS = [
    [("‹ غنيلي ›")],
    [("‹ صور ›"), ("‹ انمي ›")],
    [("‹ متحركه ›"), ("‹ اقتباسات ›")],
    [("‹ افتارات شباب ›"), ("‹ افتار بنات ›")],
    [("‹ هيدرات ›"), ("‹ قران ›")],
    [("‹ اخفاء الكيبورد ›")]
]

# --- لوحات مفاتيح المطورين ---
# لوحة المفاتيح الأساسية للمطورين
DEV_KEYBOARD = [
    ["الاحصائيات و الاذاعه"],
    ["تعيين مجموعه السجل"],
    ["اداره الحسابات المساعده"],
    ["اعدادات البوت"],
    ["اعدادات اوامر المطور"],
    ["اختبار البينج"],
    ["تعطيل التواصل", "تفعيل التواصل"],
    ["اعادة التشغيل"],
    ["كيبورد الاعضاء"]
]

# لوحة مفاتيح الإحصائيات والإذاعة
STATS_BROADCAST_KEYBOARD = [
    ["الاحصائيات"],
    ["الاذاعة"],
    ["القائمه الرئيسية"]
]

# لوحة مفاتيح إدارة الحسابات المساعدة
ACCOUNTS_MANAGEMENT_KEYBOARD = [
    ["اضافه حساب مساعد"],
    ["حذف حساب مساعد"],
    ["الحسابات المساعدة"],
    ["تفعيل المغادره التلقائية"],
    ["تعطيل المغادره التلقائية"],
    ["القائمه الرئيسية"]
]

# لوحة مفاتيح إعدادات البوت
BOT_SETTINGS_KEYBOARD = [
    ["تفعيل الاشتراك الاجباري"],
    ["تعطيل الاشتراك الاجباري"],
    ["تعيين قناة البوت"],
    ["تعيين قناة المتجر"],
    ["تحديث البوت"],
    ["القائمه الرئيسية"]
]

# لوحة مفاتيح إعدادات أوامر المطور
DEV_COMMANDS_SETTINGS_KEYBOARD = [
    ["تغيير اسم البوت"],
    ["وضع رد المطور"],
    ["تغيير كليشه المطور"],
    ["تعطيل كليشه المطور"],
    ["تعطيل كليشه الستارت"],
    ["تعطيل كليشه التفعيل"],
    ["تعطيل كليشه الاوامر"],
    ["تعطيل ردود البوت"],
    ["القائمه الرئيسية"]
]

# --- معالجات الأوامر ---
# معالج لأوامر /start و /cmds
@app.on_message(filters.private & (filters.command("start") | filters.command("cmds")))
async def cpanel(_, message: Message):
    user_id = message.from_user.id
    
    # التحقق إذا كان المستخدم مطوراً
    if user_id in DEVELOPER_IDS:
        # للمطورين: نرسل كيبورد المطورين
        text = "<b>⟡ مرحباً بك أيها المطور! إليك لوحة تحكم المطورين</b>"
        await message.reply(
            text=text,
            reply_markup=ReplyKeyboardMarkup(DEV_KEYBOARD, resize_keyboard=True, selective=True)
        )
    else:
        # للمستخدمين العاديين: نرسل كيبورد الأوامر العادي
        await message.reply(
            text=REPLY_MESSAGE,
            reply_markup=ReplyKeyboardMarkup(REPLY_MESSAGE_BUTTONS, resize_keyboard=True, selective=True)
        )

# معالج لزر "كيبورد الاعضاء" للمطورين فقط
@app.on_message(filters.private & filters.regex("كيبورد الاعضاء") & filters.user(DEVELOPER_IDS))
async def show_member_keyboard(_, message: Message):
    await message.reply(
        text=REPLY_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(REPLY_MESSAGE_BUTTONS, resize_keyboard=True, selective=True)
    )

# معالج لإخفاء الكيبورد
@app.on_message(filters.regex("‹ اخفاء الكيبورد ›") & filters.private)
async def down(client, message):
    await message.reply(
        text="<b>- تم اغلاق الكيبورد.</b>",
        reply_markup=ReplyKeyboardRemove(selective=True)
    )

# --- معالجات لوحات المفاتيح المتفرعة للمطورين ---
# معالج للعودة إلى القائمة الرئيسية
@app.on_message(filters.private & filters.regex("القائمه الرئيسية") & filters.user(DEVELOPER_IDS))
async def return_to_main_menu(_, message: Message):
    await message.reply(
        text="<b>⟡ العودة إلى القائمة الرئيسية للمطورين</b>",
        reply_markup=ReplyKeyboardMarkup(DEV_KEYBOARD, resize_keyboard=True, selective=True)
    )

# معالج لقسم الإحصائيات والإذاعة
@app.on_message(filters.private & filters.regex("الاحصائيات و الاذاعه") & filters.user(DEVELOPER_IDS))
async def stats_and_broadcast_section(_, message: Message):
    await message.reply(
        text="<b>⟡ قسم الإحصائيات والإذاعة - اختر الإجراء المطلوب:</b>",
        reply_markup=ReplyKeyboardMarkup(STATS_BROADCAST_KEYBOARD, resize_keyboard=True, selective=True)
    )

# معالج لقسم إدارة الحسابات المساعدة
@app.on_message(filters.private & filters.regex("اداره الحسابات المساعده") & filters.user(DEVELOPER_IDS))
async def accounts_management_section(_, message: Message):
    await message.reply(
        text="<b>⟡ قسم إدارة الحسابات المساعدة - اختر الإجراء المطلوب:</b>",
        reply_markup=ReplyKeyboardMarkup(ACCOUNTS_MANAGEMENT_KEYBOARD, resize_keyboard=True, selective=True)
    )

# معالج لقسم إعدادات البوت
@app.on_message(filters.private & filters.regex("اعدادات البوت") & filters.user(DEVELOPER_IDS))
async def bot_settings_section(_, message: Message):
    await message.reply(
        text="<b>⟡ قسم إعدادات البوت - اختر الإجراء المطلوب:</b>",
        reply_markup=ReplyKeyboardMarkup(BOT_SETTINGS_KEYBOARD, resize_keyboard=True, selective=True)
    )

# معالج لقسم إعدادات أوامر المطور
@app.on_message(filters.private & filters.regex("اعدادات اوامر المطور") & filters.user(DEVELOPER_IDS))
async def dev_commands_settings_section(_, message: Message):
    await message.reply(
        text="<b>⟡ قسم إعدادات أوامر المطور - اختر الإجراء المطلوب:</b>",
        reply_markup=ReplyKeyboardMarkup(DEV_COMMANDS_SETTINGS_KEYBOARD, resize_keyboard=True, selective=True)
    )

#@app.on_message(filters.group & command("‹ ربط القنوات ›"))
#async def dowhmo(client: Client, message: Message):
    #await message.reply_text("""- هلا والله\n◌<b>عشان تشغل بالقنوات لازم تسوي بعض الخطوات وهي◌</b> :\n\n1 -› تدخل البوت قناتك وترفعه مشرف\n2 -› ترجع للقروب وتكتب { <b>ربط + يوزر القناة</b> }\n3 -› <b>اضغط على زر اوامر التشغيل عشان تعرف كيف تشغل</b>.""",
        #reply_markup=InlineKeyboardMarkup(
            #[
                #[
                    #InlineKeyboardButton(
                        #"قناة السورس", url=f"https://t.me/EF_19"),
                #],[
                    #InlineKeyboardButton(
                        #"• ضيفني لقروبك 🎻", url=f"https://t.me/{app.username}?startgroup=true"),
                #],
            #]
        #),
        #disable_web_page_preview=True
    #)


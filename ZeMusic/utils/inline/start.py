from pyrogram.types import InlineKeyboardButton
import config
from ZeMusic import app

Lnk= "https://t.me/" +config.CHANNEL_LINK

def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text="أضفني إلى مجموعتك",
                url=f"https://t.me/{app.username}?startgroup=true",
            )
        ],
        [InlineKeyboardButton(text="الأوامر", callback_data="zzzback")],
        [
            InlineKeyboardButton(text=config.STORE_NAME, url=config.STORE_LINK),
            InlineKeyboardButton(text=config.CHANNEL_NAME, url=config.CHANNEL_LINK)
        ],
        [InlineKeyboardButton(text="𝐃𝐞𝐯", user_id=config.OWNER_ID),
        ],
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text="أضفني إلى مجموعتك",
                url=f"https://t.me/{app.username}?startgroup=true",
            )
        ],
        [InlineKeyboardButton(text="الأوامر", callback_data="zzzback")],
        [
            InlineKeyboardButton(text="𝙳𝙴𝚅 𝙱𝙾𝚃", user_id=config.OWNER_ID),
            InlineKeyboardButton(text=config.CHANNEL_NAME, url=Lnk),
        ],
    ]
    return buttons

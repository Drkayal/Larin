from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus, ParseMode

import config

from ..logging import LOGGER


class Mody(Client):
    def __init__(self):
        LOGGER(__name__).info(f"يتم تشغيل البوت..")
        super().__init__(
            name="ZeMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            parse_mode=ParseMode.HTML,
            max_concurrent_transmissions=7,
        )

    async def start(self):
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name + " " + (self.me.last_name or "")
        self.username = self.me.username
        self.mention = self.me.mention

        try:
            await self.send_message(
                chat_id=config.LOGGER_ID,
                text=f"<u><b>» {self.mention} ʙᴏᴛ sᴛᴀʀᴛᴇᴅ :</b><u>\n\nɪᴅ : <code>{self.id}</code>\nɴᴀᴍᴇ : {self.name}\nᴜsᴇʀɴᴀᴍᴇ : @{self.username}",
            )
            
            a = await self.get_chat_member(config.LOGGER_ID, self.id)
            if a.status != ChatMemberStatus.ADMINISTRATOR:
                LOGGER(__name__).warning(
                    "Bot is not an admin in the log group/channel. Continuing anyway..."
                )
        except (errors.ChannelInvalid, errors.PeerIdInvalid):
            LOGGER(__name__).warning(
                "Bot cannot access the log group/channel. Continuing without logging to channel..."
            )
        except Exception as ex:
            LOGGER(__name__).warning(
                f"Bot cannot access the log group/channel. Reason: {type(ex).__name__}. Continuing anyway..."
            )
        LOGGER(__name__).info(f"تم تسغيل {self.name} بنجاح..")

    async def stop(self):
        await super().stop()

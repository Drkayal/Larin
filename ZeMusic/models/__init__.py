"""
ZeMusic Database Models
نماذج قاعدة البيانات لبوت ZeMusic
"""

from .base import BaseModel
from .users import User
from .chats import Chat, ChatSettings
from .auth import AuthorizedUser, SudoUser
from .bans import BannedUser, GBannedUser, BlacklistedChat
from .activity import ActiveChat, PlayQueue, Assistant
from .system import SystemSetting, BotStats, ActivityLog
from .downloads import AudioCache, SearchHistory, DownloadStats, CacheMetrics, PopularContent

__all__ = [
    # Base
    "BaseModel",
    
    # Users & Chats
    "User",
    "Chat", 
    "ChatSettings",
    
    # Authorization
    "AuthorizedUser",
    "SudoUser",
    
    # Bans & Restrictions
    "BannedUser",
    "GBannedUser", 
    "BlacklistedChat",
    
    # Activity & Queue
    "ActiveChat",
    "PlayQueue",
    "Assistant",
    
    # System
    "SystemSetting",
    "BotStats",
    "ActivityLog",
    
    # Downloads & Cache
    "AudioCache",
    "SearchHistory",
    "DownloadStats",
    "CacheMetrics",
    "PopularContent",
]
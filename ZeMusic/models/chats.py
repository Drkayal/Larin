"""
Chat Models
نماذج المحادثات وإعداداتها
"""

from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from .base import BaseModel

@dataclass
class Chat(BaseModel):
    """
    نموذج المحادثة
    يمثل جدول chats في قاعدة البيانات
    """
    
    # المعرف الأساسي
    chat_id: int
    
    # نوع المحادثة
    chat_type: str  # 'private', 'group', 'supergroup', 'channel'
    
    # معلومات المحادثة
    title: Optional[str] = None
    username: Optional[str] = None
    description: Optional[str] = None
    member_count: int = 0
    
    # حالة المحادثة
    is_active: bool = True
    
    # التواريخ
    joined_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """تنفيذ بعد إنشاء النموذج"""
        # التأكد من صحة chat_id
        if not isinstance(self.chat_id, int):
            raise ValueError("chat_id يجب أن يكون رقم صحيح")
        
        # التأكد من نوع المحادثة
        valid_types = ['private', 'group', 'supergroup', 'channel']
        if self.chat_type not in valid_types:
            raise ValueError(f"chat_type يجب أن يكون أحد: {valid_types}")
        
        # تنظيف البيانات
        if self.title:
            self.title = self.title.strip()[:255]
        if self.username:
            self.username = self.username.strip().replace('@', '')[:255]
        if self.description:
            self.description = self.description.strip()
    
    @property
    def is_private(self) -> bool:
        """هل هذه محادثة خاصة"""
        return self.chat_type == 'private'
    
    @property
    def is_group(self) -> bool:
        """هل هذه مجموعة"""
        return self.chat_type in ['group', 'supergroup']
    
    @property
    def is_channel(self) -> bool:
        """هل هذه قناة"""
        return self.chat_type == 'channel'
    
    @property
    def display_name(self) -> str:
        """اسم العرض للمحادثة"""
        if self.title:
            return self.title
        if self.username:
            return f"@{self.username}"
        return f"Chat {abs(self.chat_id)}"
    
    def update_activity(self):
        """تحديث آخر نشاط"""
        self.last_activity = datetime.utcnow()
        self.update_timestamp()
    
    def update_member_count(self, count: int):
        """تحديث عدد الأعضاء"""
        self.member_count = max(0, count)
        self.update_timestamp()
    
    @classmethod
    def from_telegram_chat(cls, telegram_chat):
        """إنشاء من كائن Telegram Chat"""
        return cls(
            chat_id=telegram_chat.id,
            chat_type=telegram_chat.type.value if hasattr(telegram_chat.type, 'value') else str(telegram_chat.type),
            title=telegram_chat.title,
            username=telegram_chat.username,
            description=getattr(telegram_chat, 'description', None),
            member_count=getattr(telegram_chat, 'members_count', 0),
        )
    
    def __str__(self) -> str:
        return f"Chat({self.chat_id}, {self.display_name})"


@dataclass 
class ChatSettings(BaseModel):
    """
    نموذج إعدادات المحادثة
    يمثل جدول chat_settings في قاعدة البيانات
    """
    
    # المعرف الأساسي
    id: Optional[int] = field(default=None)
    chat_id: int = 0
    
    # إعدادات اللغة والتشغيل
    language: str = "ar"
    play_mode: str = "everyone"  # 'everyone', 'admins'
    play_type: str = "music"     # 'music', 'video'
    
    # إعدادات متقدمة
    channel_play_mode: Optional[int] = None
    upvote_count: int = 5
    auto_end: bool = False
    skip_mode: bool = True
    non_admin_commands: bool = False
    
    # إعدادات الميزات
    search_enabled: bool = True
    welcome_enabled: bool = False
    logs_enabled: bool = False
    
    def __post_init__(self):
        """تنفيذ بعد إنشاء النموذج"""
        # التأكد من صحة chat_id
        if not isinstance(self.chat_id, int):
            raise ValueError("chat_id يجب أن يكون رقم صحيح")
        
        # التأكد من قيم الإعدادات
        if self.play_mode not in ['everyone', 'admins']:
            self.play_mode = 'everyone'
        
        if self.play_type not in ['music', 'video']:
            self.play_type = 'music'
        
        if self.language not in ['ar', 'en', 'hi', 'pa']:
            self.language = 'ar'
        
        # التأكد من الحدود
        self.upvote_count = max(1, min(50, self.upvote_count))
    
    def update_language(self, language: str):
        """تحديث اللغة"""
        valid_languages = ['ar', 'en', 'hi', 'pa']
        if language in valid_languages:
            self.language = language
            self.update_timestamp()
    
    def update_play_mode(self, mode: str):
        """تحديث وضع التشغيل"""
        if mode in ['everyone', 'admins']:
            self.play_mode = mode
            self.update_timestamp()
    
    def update_play_type(self, play_type: str):
        """تحديث نوع التشغيل"""
        if play_type in ['music', 'video']:
            self.play_type = play_type
            self.update_timestamp()
    
    def update_upvote_count(self, count: int):
        """تحديث عدد الأصوات المطلوبة"""
        self.upvote_count = max(1, min(50, count))
        self.update_timestamp()
    
    def enable_feature(self, feature: str):
        """تفعيل ميزة"""
        if hasattr(self, f"{feature}_enabled"):
            setattr(self, f"{feature}_enabled", True)
            self.update_timestamp()
    
    def disable_feature(self, feature: str):
        """إيقاف ميزة"""
        if hasattr(self, f"{feature}_enabled"):
            setattr(self, f"{feature}_enabled", False)
            self.update_timestamp()
    
    def is_feature_enabled(self, feature: str) -> bool:
        """فحص تفعيل ميزة"""
        return getattr(self, f"{feature}_enabled", False)
    
    def get_settings_dict(self) -> Dict[str, Any]:
        """الحصول على الإعدادات كقاموس"""
        return {
            'language': self.language,
            'play_mode': self.play_mode,
            'play_type': self.play_type,
            'channel_play_mode': self.channel_play_mode,
            'upvote_count': self.upvote_count,
            'auto_end': self.auto_end,
            'skip_mode': self.skip_mode,
            'non_admin_commands': self.non_admin_commands,
            'search_enabled': self.search_enabled,
            'welcome_enabled': self.welcome_enabled,
            'logs_enabled': self.logs_enabled,
        }
    
    def __str__(self) -> str:
        return f"ChatSettings(chat_id={self.chat_id}, language={self.language})"
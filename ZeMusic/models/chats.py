"""
Chat Models
نماذج المحادثات وإعداداتها
"""

from datetime import datetime
from typing import Optional, Dict, Any

from .base import BaseModel

class Chat(BaseModel):
    """
    نموذج المحادثة
    يمثل جدول chats في قاعدة البيانات
    """
    
    def __init__(self, chat_id: int, chat_type: str, title: Optional[str] = None,
                 username: Optional[str] = None, description: Optional[str] = None,
                 member_count: int = 0, is_active: bool = True,
                 joined_at: Optional[datetime] = None, 
                 last_activity: Optional[datetime] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        """تهيئة نموذج المحادثة"""
        super().__init__()
        
        # المعرف الأساسي
        self.chat_id = chat_id
        
        # نوع المحادثة
        self.chat_type = chat_type
        
        # معلومات المحادثة
        self.title = title
        self.username = username
        self.description = description
        self.member_count = member_count
        
        # حالة المحادثة
        self.is_active = is_active
        
        # التواريخ
        self.joined_at = joined_at or datetime.utcnow()
        self.last_activity = last_activity or datetime.utcnow()
        
        # تحديث التواريخ المشتركة إذا تم تمريرها
        if created_at:
            self.created_at = created_at
        if updated_at:
            self.updated_at = updated_at
        
        # التحقق من صحة البيانات وتنظيفها
        self.validate()
    
    def validate(self):
        """التحقق من صحة البيانات وتنظيفها"""
        # التأكد من صحة chat_id
        if not isinstance(self.chat_id, int):
            raise ValueError("chat_id يجب أن يكون رقم صحيح")
        
        # التأكد من نوع المحادثة
        valid_types = ['private', 'group', 'supergroup', 'channel']
        if self.chat_type not in valid_types:
            raise ValueError(f"chat_type يجب أن يكون من: {valid_types}")
        
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
        """الاسم المعروض للمحادثة"""
        if self.title:
            return self.title
        elif self.username:
            return f"@{self.username}"
        else:
            return str(self.chat_id)
    
    def update_activity(self):
        """تحديث وقت آخر نشاط"""
        self.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_member_count(self, count: int):
        """تحديث عدد الأعضاء"""
        if count >= 0:
            self.member_count = count
            self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """إلغاء تفعيل المحادثة"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self):
        """تفعيل المحادثة"""
        self.is_active = True
        self.updated_at = datetime.utcnow()


class ChatSettings(BaseModel):
    """
    نموذج إعدادات المحادثة
    يمثل جدول chat_settings في قاعدة البيانات
    """
    
    def __init__(self, chat_id: int, id: Optional[int] = None,
                 language: str = "ar", play_mode: str = "everyone", 
                 play_type: str = "music", channel_play_mode: Optional[int] = None,
                 upvote_count: int = 5, auto_end: bool = False,
                 skip_mode: bool = True, non_admin_commands: bool = False,
                 search_enabled: bool = True, welcome_enabled: bool = False,
                 logs_enabled: bool = False,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        """تهيئة نموذج إعدادات المحادثة"""
        super().__init__()
        
        # المعرف الأساسي
        self.chat_id = chat_id
        self.id = id
        
        # إعدادات اللغة والتشغيل
        self.language = language
        self.play_mode = play_mode
        self.play_type = play_type
        
        # إعدادات متقدمة
        self.channel_play_mode = channel_play_mode
        self.upvote_count = upvote_count
        self.auto_end = auto_end
        self.skip_mode = skip_mode
        self.non_admin_commands = non_admin_commands
        
        # إعدادات الميزات
        self.search_enabled = search_enabled
        self.welcome_enabled = welcome_enabled
        self.logs_enabled = logs_enabled
        
        # تحديث التواريخ المشتركة إذا تم تمريرها
        if created_at:
            self.created_at = created_at
        if updated_at:
            self.updated_at = updated_at
        
        # التحقق من صحة البيانات وتنظيفها
        self.validate()
    
    def validate(self):
        """التحقق من صحة البيانات وتنظيفها"""
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
        valid_modes = ['everyone', 'admins']
        if mode in valid_modes:
            self.play_mode = mode
            self.update_timestamp()
    
    def update_play_type(self, play_type: str):
        """تحديث نوع التشغيل"""
        valid_types = ['music', 'video']
        if play_type in valid_types:
            self.play_type = play_type
            self.update_timestamp()
    
    def toggle_search(self):
        """تبديل حالة البحث"""
        self.search_enabled = not self.search_enabled
        self.update_timestamp()
    
    def toggle_welcome(self):
        """تبديل حالة الترحيب"""
        self.welcome_enabled = not self.welcome_enabled
        self.update_timestamp()
    
    def toggle_logs(self):
        """تبديل حالة السجلات"""
        self.logs_enabled = not self.logs_enabled
        self.update_timestamp()
    
    def update_timestamp(self):
        """تحديث الوقت"""
        self.updated_at = datetime.utcnow()
    
    def reset_to_defaults(self):
        """إعادة تعيين الإعدادات للقيم الافتراضية"""
        self.language = "ar"
        self.play_mode = "everyone"
        self.play_type = "music"
        self.channel_play_mode = None
        self.upvote_count = 5
        self.auto_end = False
        self.skip_mode = True
        self.non_admin_commands = False
        self.search_enabled = True
        self.welcome_enabled = False
        self.logs_enabled = False
        self.update_timestamp()
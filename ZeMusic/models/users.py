"""
User Model
نموذج المستخدمين
"""

from datetime import datetime
from typing import Optional, Dict, Any

from .base import BaseModel

class User(BaseModel):
    """
    نموذج المستخدم
    يمثل جدول users في قاعدة البيانات
    """
    
    def __init__(self, user_id: int, first_name: Optional[str] = None, 
                 last_name: Optional[str] = None, username: Optional[str] = None,
                 language_code: str = "ar", is_bot: bool = False, 
                 is_premium: bool = False, is_active: bool = True,
                 joined_at: Optional[datetime] = None, 
                 last_activity: Optional[datetime] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        """تهيئة نموذج المستخدم"""
        super().__init__()
        
        # المعرف الأساسي
        self.user_id = user_id
        
        # معلومات المستخدم الأساسية
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.language_code = language_code
        
        # حالة المستخدم
        self.is_bot = is_bot
        self.is_premium = is_premium
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
        # التأكد من صحة user_id
        if not isinstance(self.user_id, int) or self.user_id <= 0:
            raise ValueError("user_id يجب أن يكون رقم صحيح موجب")
        
        # تنظيف البيانات
        if self.first_name:
            self.first_name = self.first_name.strip()[:255]
        if self.last_name:
            self.last_name = self.last_name.strip()[:255]
        if self.username:
            self.username = self.username.strip().replace('@', '')[:255]
    

    
    @property
    def full_name(self) -> str:
        """الاسم الكامل للمستخدم"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) or f"User {self.user_id}"
    
    @property
    def mention(self) -> str:
        """منشن المستخدم"""
        if self.username:
            return f"@{self.username}"
        return self.full_name
    
    @property
    def is_private_chat(self) -> bool:
        """هل هذا مستخدم (وليس مجموعة)"""
        return self.user_id > 0
    
    def update_activity(self):
        """تحديث آخر نشاط"""
        self.last_activity = datetime.utcnow()
        self.update_timestamp()
    
    def deactivate(self):
        """إلغاء تفعيل المستخدم"""
        self.is_active = False
        self.update_timestamp()
    
    def activate(self):
        """تفعيل المستخدم"""
        self.is_active = True
        self.update_timestamp()
    
    def to_telegram_dict(self) -> dict:
        """تحويل إلى تنسيق Telegram"""
        return {
            "id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "language_code": self.language_code,
            "is_bot": self.is_bot,
            "is_premium": self.is_premium,
        }
    
    @classmethod
    def from_telegram_user(cls, telegram_user):
        """إنشاء من كائن Telegram User"""
        return cls(
            user_id=telegram_user.id,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            username=telegram_user.username,
            language_code=getattr(telegram_user, 'language_code', 'ar'),
            is_bot=getattr(telegram_user, 'is_bot', False),
            is_premium=getattr(telegram_user, 'is_premium', False),
        )
    
    def __str__(self) -> str:
        return f"User({self.user_id}, {self.full_name})"
    
    def __repr__(self) -> str:
        return f"User(user_id={self.user_id}, username={self.username}, full_name='{self.full_name}')"
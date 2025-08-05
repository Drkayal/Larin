"""
User Model
نموذج المستخدمين
"""

from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class User:
    """
    نموذج المستخدم
    يمثل جدول users في قاعدة البيانات
    """
    
    # المعرف الأساسي (بدون قيمة افتراضية)
    user_id: int
    
    # معلومات المستخدم الأساسية
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: str = "ar"
    
    # حالة المستخدم
    is_bot: bool = False
    is_premium: bool = False
    is_active: bool = True
    
    # التواريخ
    created_at: Optional[datetime] = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = field(default_factory=datetime.utcnow)
    joined_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """تنفيذ بعد إنشاء النموذج"""
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
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل النموذج إلى قاموس"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                result[key] = value
            elif isinstance(value, list):
                result[key] = value
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """إنشاء النموذج من قاموس"""
        # تحويل التواريخ من string إلى datetime
        for key in ['created_at', 'updated_at', 'joined_at', 'last_activity']:
            if key in data and isinstance(data[key], str):
                try:
                    data[key] = datetime.fromisoformat(data[key])
                except ValueError:
                    pass
        return cls(**data)
    
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
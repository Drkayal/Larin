"""
Ban Models
نماذج الحظر والمنع
"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from .base import BaseModel

@dataclass
class BannedUser(BaseModel):
    """
    نموذج المستخدم المحظور محلياً
    يمثل جدول banned_users في قاعدة البيانات
    """
    
    # المعرفات
    id: Optional[int] = None
    user_id: int = 0
    
    # معلومات الحظر
    banned_by: Optional[int] = None
    banned_at: datetime = field(default_factory=datetime.utcnow)
    reason: Optional[str] = None
    
    # الحالة
    is_active: bool = True
    
    def __post_init__(self):
        """تنفيذ بعد إنشاء النموذج"""
        if not isinstance(self.user_id, int) or self.user_id <= 0:
            raise ValueError("user_id يجب أن يكون رقم صحيح موجب")
        
        if self.reason:
            self.reason = self.reason.strip()[:500]
    
    def unban(self):
        """إلغاء الحظر"""
        self.is_active = False
        self.update_timestamp()
    
    def reban(self):
        """إعادة الحظر"""
        self.is_active = True
        self.update_timestamp()
    
    def __str__(self) -> str:
        return f"BannedUser(user_id={self.user_id}, active={self.is_active})"


@dataclass
class GBannedUser(BaseModel):
    """
    نموذج المستخدم المحظور عامياً
    يمثل جدول gbanned_users في قاعدة البيانات
    """
    
    # المعرفات
    id: Optional[int] = None
    user_id: int = 0
    
    # معلومات الحظر
    banned_by: Optional[int] = None
    banned_at: datetime = field(default_factory=datetime.utcnow)
    reason: Optional[str] = None
    
    # الحالة
    is_active: bool = True
    
    def __post_init__(self):
        """تنفيذ بعد إنشاء النموذج"""
        if not isinstance(self.user_id, int) or self.user_id <= 0:
            raise ValueError("user_id يجب أن يكون رقم صحيح موجب")
        
        if self.reason:
            self.reason = self.reason.strip()[:500]
    
    def ungban(self):
        """إلغاء الحظر العام"""
        self.is_active = False
        self.update_timestamp()
    
    def regban(self):
        """إعادة الحظر العام"""
        self.is_active = True
        self.update_timestamp()
    
    def __str__(self) -> str:
        return f"GBannedUser(user_id={self.user_id}, active={self.is_active})"


@dataclass
class BlacklistedChat(BaseModel):
    """
    نموذج المحادثة المحظورة
    يمثل جدول blacklisted_chats في قاعدة البيانات
    """
    
    # المعرفات
    id: Optional[int] = None
    chat_id: int = 0
    
    # معلومات الحظر
    blacklisted_by: Optional[int] = None
    blacklisted_at: datetime = field(default_factory=datetime.utcnow)
    reason: Optional[str] = None
    
    # الحالة
    is_active: bool = True
    
    def __post_init__(self):
        """تنفيذ بعد إنشاء النموذج"""
        if not isinstance(self.chat_id, int):
            raise ValueError("chat_id يجب أن يكون رقم صحيح")
        
        if self.reason:
            self.reason = self.reason.strip()[:500]
    
    def whitelist(self):
        """إزالة من القائمة السوداء"""
        self.is_active = False
        self.update_timestamp()
    
    def blacklist(self):
        """إعادة إلى القائمة السوداء"""
        self.is_active = True
        self.update_timestamp()
    
    def __str__(self) -> str:
        return f"BlacklistedChat(chat_id={self.chat_id}, active={self.is_active})"
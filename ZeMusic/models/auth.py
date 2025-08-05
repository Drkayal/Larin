"""
Authorization Models
نماذج الصلاحيات والمطورين
"""

from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from .base import BaseModel

@dataclass
class AuthorizedUser(BaseModel):
    """
    نموذج المستخدم المصرح له
    يمثل جدول authorized_users في قاعدة البيانات
    """
    
    # المعرفات
    id: Optional[int] = None
    chat_id: int = 0
    user_id: int = 0
    
    # معلومات التصريح
    user_name: str = ""
    authorized_by: Optional[int] = None
    authorized_at: datetime = field(default_factory=datetime.utcnow)
    
    # بيانات إضافية
    notes: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """تنفيذ بعد إنشاء النموذج"""
        if not isinstance(self.chat_id, int) or not isinstance(self.user_id, int):
            raise ValueError("chat_id و user_id يجب أن يكونا أرقام صحيحة")
        
        if not self.user_name:
            self.user_name = f"User_{self.user_id}"
        
        self.user_name = self.user_name.strip()[:255]
    
    def add_note(self, key: str, value: Any):
        """إضافة ملاحظة"""
        self.notes[key] = value
        self.update_timestamp()
    
    def remove_note(self, key: str):
        """حذف ملاحظة"""
        if key in self.notes:
            del self.notes[key]
            self.update_timestamp()
    
    def get_note(self, key: str, default=None):
        """الحصول على ملاحظة"""
        return self.notes.get(key, default)
    
    def __str__(self) -> str:
        return f"AuthorizedUser(chat_id={self.chat_id}, user_id={self.user_id}, name={self.user_name})"


@dataclass
class SudoUser(BaseModel):
    """
    نموذج المطور
    يمثل جدول sudo_users في قاعدة البيانات
    """
    
    # المعرفات
    id: Optional[int] = None
    user_id: int = 0
    
    # معلومات الإضافة
    added_by: Optional[int] = None
    added_at: datetime = field(default_factory=datetime.utcnow)
    
    # الحالة
    is_active: bool = True
    
    def __post_init__(self):
        """تنفيذ بعد إنشاء النموذج"""
        if not isinstance(self.user_id, int) or self.user_id <= 0:
            raise ValueError("user_id يجب أن يكون رقم صحيح موجب")
    
    def activate(self):
        """تفعيل المطور"""
        self.is_active = True
        self.update_timestamp()
    
    def deactivate(self):
        """إلغاء تفعيل المطور"""
        self.is_active = False
        self.update_timestamp()
    
    def __str__(self) -> str:
        return f"SudoUser(user_id={self.user_id}, active={self.is_active})"
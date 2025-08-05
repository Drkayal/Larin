"""
Activity Models
نماذج النشاط وقوائم الانتظار والمساعدين
"""

from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from .base import BaseModel

@dataclass
class ActiveChat(BaseModel):
    """
    نموذج المحادثة النشطة
    يمثل جدول active_chats في قاعدة البيانات
    """
    
    # المعرفات
    id: Optional[int] = None
    chat_id: int = 0
    
    # معلومات النشاط
    is_video: bool = False
    started_at: datetime = field(default_factory=datetime.utcnow)
    current_track: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """تنفيذ بعد إنشاء النموذج"""
        if not isinstance(self.chat_id, int):
            raise ValueError("chat_id يجب أن يكون رقم صحيح")
    
    def update_current_track(self, track_data: Dict[str, Any]):
        """تحديث المقطع الحالي"""
        self.current_track = track_data
        self.update_timestamp()
    
    def clear_current_track(self):
        """مسح المقطع الحالي"""
        self.current_track = {}
        self.update_timestamp()
    
    def set_video_mode(self, is_video: bool):
        """تعيين وضع الفيديو"""
        self.is_video = is_video
        self.update_timestamp()
    
    def __str__(self) -> str:
        return f"ActiveChat(chat_id={self.chat_id}, video={self.is_video})"


@dataclass
class PlayQueue(BaseModel):
    """
    نموذج قائمة الانتظار
    يمثل جدول play_queue في قاعدة البيانات
    """
    
    # المعرفات
    id: Optional[int] = None
    chat_id: int = 0
    
    # بيانات المقطع
    track_data: Dict[str, Any] = field(default_factory=dict)
    position: int = 0
    
    # معلومات الإضافة
    added_by: Optional[int] = None
    added_at: datetime = field(default_factory=datetime.utcnow)
    
    # حالة التشغيل
    is_played: bool = False
    
    def __post_init__(self):
        """تنفيذ بعد إنشاء النموذج"""
        if not isinstance(self.chat_id, int):
            raise ValueError("chat_id يجب أن يكون رقم صحيح")
        
        if not isinstance(self.position, int) or self.position < 0:
            raise ValueError("position يجب أن يكون رقم صحيح غير سالب")
    
    def mark_as_played(self):
        """تعليم كمشغل"""
        self.is_played = True
        self.update_timestamp()
    
    def mark_as_unplayed(self):
        """تعليم كغير مشغل"""
        self.is_played = False
        self.update_timestamp()
    
    def update_position(self, new_position: int):
        """تحديث الموضع"""
        if new_position >= 0:
            self.position = new_position
            self.update_timestamp()
    
    def get_track_title(self) -> str:
        """الحصول على عنوان المقطع"""
        return self.track_data.get('title', 'Unknown Track')
    
    def get_track_duration(self) -> str:
        """الحصول على مدة المقطع"""
        return self.track_data.get('duration', '00:00')
    
    def __str__(self) -> str:
        return f"PlayQueue(chat_id={self.chat_id}, position={self.position}, title={self.get_track_title()})"


@dataclass
class Assistant(BaseModel):
    """
    نموذج المساعد
    يمثل جدول assistants في قاعدة البيانات
    """
    
    # المعرفات
    id: Optional[int] = None
    chat_id: int = 0
    
    # رقم المساعد
    assistant_number: int = 1
    
    # معلومات التخصيص
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    def __post_init__(self):
        """تنفيذ بعد إنشاء النموذج"""
        if not isinstance(self.chat_id, int):
            raise ValueError("chat_id يجب أن يكون رقم صحيح")
        
        if not isinstance(self.assistant_number, int) or not (1 <= self.assistant_number <= 5):
            raise ValueError("assistant_number يجب أن يكون بين 1 و 5")
    
    def activate(self):
        """تفعيل المساعد"""
        self.is_active = True
        self.update_timestamp()
    
    def deactivate(self):
        """إلغاء تفعيل المساعد"""
        self.is_active = False
        self.update_timestamp()
    
    def change_assistant(self, new_number: int):
        """تغيير رقم المساعد"""
        if 1 <= new_number <= 5:
            self.assistant_number = new_number
            self.assigned_at = datetime.utcnow()
            self.update_timestamp()
    
    def __str__(self) -> str:
        return f"Assistant(chat_id={self.chat_id}, number={self.assistant_number}, active={self.is_active})"
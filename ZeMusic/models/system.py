"""
System Models
نماذج النظام والإحصائيات وسجل الأنشطة
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from .base import BaseModel

@dataclass
class SystemSetting(BaseModel):
    """
    نموذج إعدادات النظام
    يمثل جدول system_settings في قاعدة البيانات
    """
    
    # المعرفات
    id: Optional[int] = None
    
    # الإعدادات
    setting_key: str = ""
    setting_value: Optional[str] = None
    setting_type: str = "string"  # 'string', 'integer', 'boolean', 'json'
    description: Optional[str] = None
    
    def __post_init__(self):
        """تنفيذ بعد إنشاء النموذج"""
        if not self.setting_key:
            raise ValueError("setting_key مطلوب")
        
        self.setting_key = self.setting_key.strip()[:100]
        
        if self.setting_type not in ['string', 'integer', 'boolean', 'json']:
            self.setting_type = 'string'
        
        if self.description:
            self.description = self.description.strip()
    
    def get_value(self):
        """الحصول على القيمة بالنوع الصحيح"""
        if self.setting_value is None:
            return None
        
        if self.setting_type == 'integer':
            try:
                return int(self.setting_value)
            except:
                return 0
        elif self.setting_type == 'boolean':
            return self.setting_value.lower() in ['true', '1', 'yes', 'on']
        elif self.setting_type == 'json':
            try:
                import json
                return json.loads(self.setting_value)
            except:
                return {}
        else:
            return self.setting_value
    
    def set_value(self, value):
        """تعيين القيمة"""
        if self.setting_type == 'json':
            import json
            self.setting_value = json.dumps(value, ensure_ascii=False)
        else:
            self.setting_value = str(value)
        self.update_timestamp()
    
    def __str__(self) -> str:
        return f"SystemSetting(key={self.setting_key}, value={self.setting_value})"


@dataclass
class BotStats(BaseModel):
    """
    نموذج إحصائيات البوت
    يمثل جدول bot_stats في قاعدة البيانات
    """
    
    # المعرفات
    id: Optional[int] = None
    stat_date: date = field(default_factory=date.today)
    
    # الإحصائيات
    total_users: int = 0
    total_chats: int = 0
    active_users: int = 0
    active_chats: int = 0
    total_plays: int = 0
    total_downloads: int = 0
    
    def __post_init__(self):
        """تنفيذ بعد إنشاء النموذج"""
        # التأكد من أن الأرقام غير سالبة
        self.total_users = max(0, self.total_users)
        self.total_chats = max(0, self.total_chats)
        self.active_users = max(0, self.active_users)
        self.active_chats = max(0, self.active_chats)
        self.total_plays = max(0, self.total_plays)
        self.total_downloads = max(0, self.total_downloads)
    
    def increment_users(self, count: int = 1):
        """زيادة عدد المستخدمين"""
        self.total_users += count
        self.update_timestamp()
    
    def increment_chats(self, count: int = 1):
        """زيادة عدد المحادثات"""
        self.total_chats += count
        self.update_timestamp()
    
    def increment_plays(self, count: int = 1):
        """زيادة عدد التشغيلات"""
        self.total_plays += count
        self.update_timestamp()
    
    def increment_downloads(self, count: int = 1):
        """زيادة عدد التحميلات"""
        self.total_downloads += count
        self.update_timestamp()
    
    def update_active_counts(self, active_users: int, active_chats: int):
        """تحديث أعداد النشاط"""
        self.active_users = max(0, active_users)
        self.active_chats = max(0, active_chats)
        self.update_timestamp()
    
    def get_stats_dict(self) -> Dict[str, Any]:
        """الحصول على الإحصائيات كقاموس"""
        return {
            'date': self.stat_date.isoformat(),
            'total_users': self.total_users,
            'total_chats': self.total_chats,
            'active_users': self.active_users,
            'active_chats': self.active_chats,
            'total_plays': self.total_plays,
            'total_downloads': self.total_downloads,
        }
    
    def __str__(self) -> str:
        return f"BotStats(date={self.stat_date}, users={self.total_users}, chats={self.total_chats})"


@dataclass
class ActivityLog(BaseModel):
    """
    نموذج سجل الأنشطة
    يمثل جدول activity_logs في قاعدة البيانات
    """
    
    # المعرفات
    id: Optional[int] = None
    
    # معلومات المستخدم والمحادثة
    user_id: Optional[int] = None
    chat_id: Optional[int] = None
    
    # معلومات النشاط
    action: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    # معلومات تقنية
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def __post_init__(self):
        """تنفيذ بعد إنشاء النموذج"""
        if not self.action:
            raise ValueError("action مطلوب")
        
        self.action = self.action.strip()[:100]
        
        if self.ip_address:
            self.ip_address = self.ip_address.strip()
        
        if self.user_agent:
            self.user_agent = self.user_agent.strip()
    
    def add_detail(self, key: str, value: Any):
        """إضافة تفصيل"""
        self.details[key] = value
    
    def get_detail(self, key: str, default=None):
        """الحصول على تفصيل"""
        return self.details.get(key, default)
    
    def set_user_info(self, user_id: int, chat_id: Optional[int] = None):
        """تعيين معلومات المستخدم"""
        self.user_id = user_id
        if chat_id:
            self.chat_id = chat_id
    
    def set_network_info(self, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """تعيين معلومات الشبكة"""
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
    
    @classmethod
    def create_action_log(cls, action: str, user_id: Optional[int] = None, 
                         chat_id: Optional[int] = None, **details):
        """إنشاء سجل نشاط سريع"""
        return cls(
            action=action,
            user_id=user_id,
            chat_id=chat_id,
            details=details
        )
    
    def __str__(self) -> str:
        return f"ActivityLog(action={self.action}, user_id={self.user_id}, chat_id={self.chat_id})"
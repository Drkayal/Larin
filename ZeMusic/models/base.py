"""
Base Model Class
النموذج الأساسي لجميع نماذج قاعدة البيانات
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import json

@dataclass
class BaseModel:
    """
    النموذج الأساسي لجميع جداول قاعدة البيانات
    """
    
    # الحقول المشتركة
    created_at: Optional[datetime] = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = field(default_factory=datetime.utcnow)
    
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
    
    def to_json(self) -> str:
        """تحويل النموذج إلى JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """إنشاء نموذج من قاموس"""
        # تحويل التواريخ من نص إلى datetime
        for key, value in data.items():
            if key in ['created_at', 'updated_at', 'joined_at', 'last_activity', 
                      'authorized_at', 'banned_at', 'blacklisted_at', 'added_at', 'started_at']:
                if isinstance(value, str):
                    try:
                        data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except:
                        data[key] = datetime.utcnow()
        
        return cls(**data)
    
    def update_timestamp(self):
        """تحديث وقت التعديل"""
        self.updated_at = datetime.utcnow()

# دوال مساعدة للاستعلامات
class QueryBuilder:
    """
    بناء الاستعلامات SQL بطريقة آمنة
    """
    
    @staticmethod
    def build_insert(table: str, data: Dict[str, Any]) -> tuple[str, tuple]:
        """بناء استعلام INSERT"""
        columns = list(data.keys())
        placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])
        values = tuple(data.values())
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        return query, values
    
    @staticmethod
    def build_update(table: str, data: Dict[str, Any], where_clause: str, where_values: tuple) -> tuple[str, tuple]:
        """بناء استعلام UPDATE"""
        set_clauses = []
        values = []
        
        for i, (column, value) in enumerate(data.items()):
            set_clauses.append(f"{column} = ${i+1}")
            values.append(value)
        
        # إضافة قيم WHERE
        where_placeholders = []
        for i, _ in enumerate(where_values):
            where_placeholders.append(f"${len(values) + i + 1}")
        
        values.extend(where_values)
        
        # استبدال placeholders في WHERE clause
        where_formatted = where_clause
        for i, placeholder in enumerate(where_placeholders):
            where_formatted = where_formatted.replace(f"${i+1}", placeholder, 1)
        
        query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {where_formatted}"
        return query, tuple(values)
    
    @staticmethod
    def build_select(table: str, columns: List[str] = None, where_clause: str = None, 
                    order_by: str = None, limit: int = None) -> str:
        """بناء استعلام SELECT"""
        if columns is None:
            columns = ["*"]
        
        query = f"SELECT {', '.join(columns)} FROM {table}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return query
    
    @staticmethod
    def build_delete(table: str, where_clause: str) -> str:
        """بناء استعلام DELETE"""
        return f"DELETE FROM {table} WHERE {where_clause}"

# دوال تحويل البيانات
class DataConverter:
    """
    تحويل البيانات بين التنسيقات المختلفة
    """
    
    @staticmethod
    def dict_to_jsonb(data: Dict[str, Any]) -> str:
        """تحويل قاموس إلى JSONB"""
        return json.dumps(data, ensure_ascii=False)
    
    @staticmethod
    def jsonb_to_dict(jsonb_str: str) -> Dict[str, Any]:
        """تحويل JSONB إلى قاموس"""
        if not jsonb_str:
            return {}
        try:
            return json.loads(jsonb_str)
        except:
            return {}
    
    @staticmethod
    def list_to_array(data: List[Any]) -> List[Any]:
        """تحويل قائمة Python إلى PostgreSQL array"""
        return data
    
    @staticmethod
    def array_to_list(array_data: Any) -> List[Any]:
        """تحويل PostgreSQL array إلى قائمة Python"""
        if isinstance(array_data, list):
            return array_data
        return []

# استثناءات مخصصة
class ModelError(Exception):
    """خطأ في النموذج"""
    pass

class ValidationError(ModelError):
    """خطأ في التحقق من البيانات"""
    pass

class DatabaseError(ModelError):
    """خطأ في قاعدة البيانات"""
    pass
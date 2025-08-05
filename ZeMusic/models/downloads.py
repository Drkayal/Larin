"""
ZeMusic Download System Models
نماذج نظام التحميل المتقدم لبوت ZeMusic
"""

from datetime import datetime
from typing import Optional, Dict, Any
from .base import BaseModel


class AudioCache(BaseModel):
    """
    نموذج تخزين معلومات الملفات الصوتية المؤقت
    """
    
    def __init__(self):
        self.table_name = "audio_cache"
        self.create_sql = """
        CREATE TABLE IF NOT EXISTS audio_cache (
            id SERIAL PRIMARY KEY,
            video_id VARCHAR(255) UNIQUE NOT NULL,
            title TEXT NOT NULL,
            uploader VARCHAR(500),
            duration INTEGER DEFAULT 0,
            file_path TEXT,
            file_size BIGINT DEFAULT 0,
            audio_quality VARCHAR(10) DEFAULT '320',
            file_format VARCHAR(10) DEFAULT 'mp3',
            thumbnail_url TEXT,
            view_count BIGINT DEFAULT 0,
            like_count BIGINT DEFAULT 0,
            upload_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            download_count INTEGER DEFAULT 0,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_available BOOLEAN DEFAULT TRUE,
            metadata JSONB
        );
        
        CREATE INDEX IF NOT EXISTS idx_audio_cache_video_id ON audio_cache(video_id);
        CREATE INDEX IF NOT EXISTS idx_audio_cache_title ON audio_cache(title);
        CREATE INDEX IF NOT EXISTS idx_audio_cache_created_at ON audio_cache(created_at);
        CREATE INDEX IF NOT EXISTS idx_audio_cache_download_count ON audio_cache(download_count);
        CREATE INDEX IF NOT EXISTS idx_audio_cache_last_accessed ON audio_cache(last_accessed);
        """


class SearchHistory(BaseModel):
    """
    نموذج تاريخ عمليات البحث
    """
    
    def __init__(self):
        self.table_name = "search_history"
        self.create_sql = """
        CREATE TABLE IF NOT EXISTS search_history (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            chat_id BIGINT NOT NULL,
            query TEXT NOT NULL,
            video_id VARCHAR(255),
            result_count INTEGER DEFAULT 0,
            search_type VARCHAR(50) DEFAULT 'youtube',
            language VARCHAR(10) DEFAULT 'ar',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            response_time_ms INTEGER DEFAULT 0,
            was_cached BOOLEAN DEFAULT FALSE,
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_history(user_id);
        CREATE INDEX IF NOT EXISTS idx_search_history_chat_id ON search_history(chat_id);
        CREATE INDEX IF NOT EXISTS idx_search_history_query ON search_history(query);
        CREATE INDEX IF NOT EXISTS idx_search_history_created_at ON search_history(created_at);
        CREATE INDEX IF NOT EXISTS idx_search_history_video_id ON search_history(video_id);
        """


class DownloadStats(BaseModel):
    """
    نموذج إحصائيات التحميل
    """
    
    def __init__(self):
        self.table_name = "download_stats"
        self.create_sql = """
        CREATE TABLE IF NOT EXISTS download_stats (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            chat_id BIGINT NOT NULL,
            video_id VARCHAR(255) NOT NULL,
            audio_title TEXT,
            download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_size BIGINT DEFAULT 0,
            download_time_seconds INTEGER DEFAULT 0,
            audio_quality VARCHAR(10) DEFAULT '320',
            file_format VARCHAR(10) DEFAULT 'mp3',
            source_platform VARCHAR(50) DEFAULT 'youtube',
            was_cached BOOLEAN DEFAULT FALSE,
            success BOOLEAN DEFAULT TRUE,
            error_code VARCHAR(50),
            error_message TEXT,
            user_agent TEXT,
            ip_address INET,
            country_code VARCHAR(5),
            device_type VARCHAR(50)
        );
        
        CREATE INDEX IF NOT EXISTS idx_download_stats_user_id ON download_stats(user_id);
        CREATE INDEX IF NOT EXISTS idx_download_stats_chat_id ON download_stats(chat_id);
        CREATE INDEX IF NOT EXISTS idx_download_stats_video_id ON download_stats(video_id);
        CREATE INDEX IF NOT EXISTS idx_download_stats_download_date ON download_stats(download_date);
        CREATE INDEX IF NOT EXISTS idx_download_stats_success ON download_stats(success);
        """


class CacheMetrics(BaseModel):
    """
    نموذج مقاييس التخزين المؤقت
    """
    
    def __init__(self):
        self.table_name = "cache_metrics"
        self.create_sql = """
        CREATE TABLE IF NOT EXISTS cache_metrics (
            id SERIAL PRIMARY KEY,
            metric_date DATE DEFAULT CURRENT_DATE,
            total_cached_files INTEGER DEFAULT 0,
            total_cache_size_mb BIGINT DEFAULT 0,
            cache_hits INTEGER DEFAULT 0,
            cache_misses INTEGER DEFAULT 0,
            cache_hit_ratio DECIMAL(5,2) DEFAULT 0.00,
            files_cleaned INTEGER DEFAULT 0,
            space_freed_mb BIGINT DEFAULT 0,
            average_file_size_mb DECIMAL(10,2) DEFAULT 0.00,
            most_popular_video_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE UNIQUE INDEX IF NOT EXISTS idx_cache_metrics_date ON cache_metrics(metric_date);
        CREATE INDEX IF NOT EXISTS idx_cache_metrics_created_at ON cache_metrics(created_at);
        """


class PopularContent(BaseModel):
    """
    نموذج المحتوى الأكثر شعبية
    """
    
    def __init__(self):
        self.table_name = "popular_content"
        self.create_sql = """
        CREATE TABLE IF NOT EXISTS popular_content (
            id SERIAL PRIMARY KEY,
            video_id VARCHAR(255) UNIQUE NOT NULL,
            title TEXT NOT NULL,
            uploader VARCHAR(500),
            download_count INTEGER DEFAULT 0,
            unique_users_count INTEGER DEFAULT 0,
            last_downloaded TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            trending_score DECIMAL(10,2) DEFAULT 0.00,
            category VARCHAR(100),
            tags TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_popular_content_video_id ON popular_content(video_id);
        CREATE INDEX IF NOT EXISTS idx_popular_content_download_count ON popular_content(download_count DESC);
        CREATE INDEX IF NOT EXISTS idx_popular_content_trending_score ON popular_content(trending_score DESC);
        CREATE INDEX IF NOT EXISTS idx_popular_content_last_downloaded ON popular_content(last_downloaded);
        """
"""
YouTube Fallback Extractor
حلول بديلة لاستخراج روابط YouTube عند فشل yt-dlp
"""

import aiohttp
import asyncio
import json
import re
from typing import Optional, Dict, Any
import config

class YouTubeFallback:
    def __init__(self):
        self.invidious_servers = getattr(config, 'INVIDIOUS_SERVERS', [
            "https://inv.nadeko.net",
            "https://invidious.nerdvpn.de", 
            "https://yewtu.be",
            "https://invidious.f5.si"
        ])
        
    async def extract_video_id(self, url: str) -> Optional[str]:
        """استخراج video ID من رابط YouTube"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def get_video_info_invidious(self, video_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على معلومات الفيديو من Invidious"""
        for server in self.invidious_servers:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{server}/api/v1/videos/{video_id}"
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            return {
                                'title': data.get('title', 'Unknown'),
                                'duration': data.get('lengthSeconds', 0),
                                'thumbnail': data.get('videoThumbnails', [{}])[0].get('url', ''),
                                'formats': data.get('adaptiveFormats', []) + data.get('formatStreams', [])
                            }
            except Exception as e:
                print(f"خطأ في الخادم {server}: {e}")
                continue
        return None
    
    async def get_best_audio_url(self, video_id: str) -> Optional[str]:
        """الحصول على أفضل رابط صوتي"""
        info = await self.get_video_info_invidious(video_id)
        if not info:
            return None
            
        # البحث عن أفضل جودة صوتية
        audio_formats = []
        for fmt in info.get('formats', []):
            if fmt.get('type', '').startswith('audio/'):
                audio_formats.append(fmt)
        
        if audio_formats:
            # ترتيب حسب الجودة
            audio_formats.sort(key=lambda x: int(x.get('bitrate', 0)), reverse=True)
            return audio_formats[0].get('url')
        
        return None
    
    async def search_youtube(self, query: str, limit: int = 5) -> list:
        """البحث في YouTube عبر Invidious"""
        results = []
        for server in self.invidious_servers:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{server}/api/v1/search"
                    params = {
                        'q': query,
                        'type': 'video',
                        'region': 'US'
                    }
                    async with session.get(url, params=params, timeout=15) as response:
                        if response.status == 200:
                            data = await response.json()
                            for item in data[:limit]:
                                results.append({
                                    'id': item.get('videoId'),
                                    'title': item.get('title'),
                                    'duration': item.get('lengthSeconds', 0),
                                    'thumbnail': item.get('videoThumbnails', [{}])[0].get('url', ''),
                                    'url': f"https://www.youtube.com/watch?v={item.get('videoId')}"
                                })
                            return results
            except Exception as e:
                print(f"خطأ في البحث عبر {server}: {e}")
                continue
        return results

# إنشاء instance عام
youtube_fallback = YouTubeFallback()
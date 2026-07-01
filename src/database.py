"""
Supabase database client for youtube-revenge-factory.
"""
from __future__ import annotations
import os, json
from typing import Any, Dict, List, Optional
from supabase import create_client, Client

class Database:
    """Simplified Supabase client."""
    
    def __init__(self):
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        if url and key:
            self.client: Client = create_client(url, key)
        else:
            self.client = None
            print("WARNING: SUPABASE_URL/KEY not set — running in offline mode")
    
    def is_connected(self) -> bool:
        return self.client is not None
    
    # --- Settings ---
    def get_setting(self, key: str) -> Optional[Any]:
        if not self.client: return None
        result = self.client.table("settings").select("*").eq("key", key).execute()
        if result.data:
            return result.data[0]["value"]
        return None
    
    def set_setting(self, key: str, value: Any):
        if not self.client: return
        data = {"key": key, "value": value}
        self.client.table("settings").upsert(data, on_conflict="key").execute()
    
    def get_all_settings(self) -> Dict:
        if not self.client: return {}
        result = self.client.table("settings").select("*").execute()
        return {row["key"]: row["value"] for row in result.data}
    
    # --- Channels ---
    def save_channel(self, channel_data: Dict) -> Optional[str]:
        if not self.client: return None
        result = self.client.table("channels").upsert(
            channel_data, on_conflict="channel_id"
        ).execute()
        return result.data[0]["id"] if result.data else None
    
    def get_active_channels(self) -> List[Dict]:
        if not self.client: return []
        result = self.client.table("channels").select("*").eq("is_active", True).execute()
        return result.data
    
    # --- Videos ---
    def save_video(self, video_data: Dict) -> Optional[str]:
        if not self.client: return None
        result = self.client.table("videos").insert(video_data).execute()
        return result.data[0]["id"] if result.data else None
    
    def update_video_status(self, video_id: str, status: str, **extra):
        if not self.client: return
        update = {"status": status, **extra}
        self.client.table("videos").update(update).eq("id", video_id).execute()
    
    def get_videos_by_status(self, status: str) -> List[Dict]:
        if not self.client: return []
        result = self.client.table("videos").select("*").eq("status", status).order("created_at", desc=True).execute()
        return result.data
    
    def get_recent_videos(self, limit: int = 20) -> List[Dict]:
        if not self.client: return []
        result = self.client.table("videos").select("*").order("created_at", desc=True).limit(limit).execute()
        return result.data
    
    # --- Analytics ---
    def upsert_analytics(self, video_id: str, date: str, data: Dict):
        if not self.client: return
        record = {"video_id": video_id, "date": date, **data}
        self.client.table("analytics").upsert(record, on_conflict="video_id,date").execute()

# Singleton
db = Database()
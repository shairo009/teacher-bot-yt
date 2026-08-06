"""
Channel Growth & Analytics Engine
Fetches view counts, likes, and engagement metrics for uploaded videos via YouTube Data API.
Auto-tunes topic priorities, hashtags, and metadata to maximize channel growth.
"""

import json
from pathlib import Path

class ChannelAnalytics:
    def __init__(self, uploader=None):
        self.uploader = uploader

    def analyze_performance(self, history_file: Path) -> dict:
        """Fetch views & likes for history videos and return growth recommendations."""
        if not history_file.exists():
            return {"status": "no_history"}
        
        try:
            with open(history_file) as f:
                history = json.load(f)
        except Exception:
            return {"status": "read_error"}
        
        uploaded_items = [h for h in history if h.get("uploaded") and h.get("video_id")]
        
        if not uploaded_items or not self.uploader or not getattr(self.uploader, "youtube", None):
            return {
                "status": "baseline_active",
                "total_uploaded": len(uploaded_items),
                "message": "Tracking active. Analytics will auto-tune after videos accumulate views."
            }
        
        video_ids = [h["video_id"] for h in uploaded_items[-50:] if "video_id" in h]
        if not video_ids:
            return {"status": "no_video_ids"}
        
        try:
            resp = self.uploader.youtube.videos().list(
                part="statistics,snippet",
                id=",".join(video_ids)
            ).execute()
            
            stats_by_series = {}
            total_views = 0
            total_likes = 0
            
            for item in resp.get("items", []):
                v_stats = item.get("statistics", {})
                views = int(v_stats.get("viewCount", 0))
                likes = int(v_stats.get("likeCount", 0))
                total_views += views
                total_likes += likes
                
                tags = item.get("snippet", {}).get("tags", [])
                series = tags[0] if tags else "General"
                
                if series not in stats_by_series:
                    stats_by_series[series] = {"views": 0, "likes": 0, "count": 0}
                stats_by_series[series]["views"] += views
                stats_by_series[series]["likes"] += likes
                stats_by_series[series]["count"] += 1
                
            top_series = max(stats_by_series, key=lambda s: stats_by_series[s]["views"]) if stats_by_series else None
            
            return {
                "status": "success",
                "total_views": total_views,
                "total_likes": total_likes,
                "stats_by_series": stats_by_series,
                "top_series": top_series,
                "recommendation": f"Boost frequency of high-performing series: {top_series}" if top_series else "Maintain balanced cycle"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

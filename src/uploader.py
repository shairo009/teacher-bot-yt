"""
YouTube Uploader — Super Human Edition
Smart metadata, custom thumbnails, playlists, scheduling.
Looks like a real education creator, not a bot.
"""

import os
import json
import random
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

try:
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
except ImportError:
    print("Installing Google API libraries...")
    os.system("pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 -q")
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request


class YouTubeUploader:
    SCOPES = ['https://www.googleapis.com/auth/youtube']

    def __init__(self, token_path='token.json', secrets_path='client_secrets.json'):
        self.token_path = Path(token_path)
        self.secrets_path = Path(secrets_path)
        self.youtube = None
        self._playlist_cache = {}

    def authenticate(self):
        """Authenticate with YouTube API using OAuth2."""
        creds = None

        if self.token_path.exists():
            try:
                from google.oauth2.credentials import Credentials
                with open(self.token_path, 'r', encoding='utf-8-sig') as f:
                    token_data = json.load(f)
                creds = Credentials.from_authorized_user_info(token_data, self.SCOPES)
            except Exception as e:
                print(f"  ⚠ Token load warning: {e}")
                pass


        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.secrets_path.exists():
                    print(f"ERROR: {self.secrets_path} not found!")
                    return False
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.secrets_path), self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(self.token_path, 'w') as f:
                json.dump({
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': creds.scopes
                }, f)

        self.youtube = build('youtube', 'v3', credentials=creds)
        return True

    # ─── METADATA GENERATION ───────────────────────────────────────

    def generate_metadata(self, topic):
        """Generate human-like metadata from topic data.

        Args:
            topic: dict with keys: topic, class, chapter, subtopics

        Returns:
            dict with title, description, tags
        """
        topic_name = topic.get('topic', 'Math')
        class_num = topic.get('class', 6)
        chapter = topic.get('chapter', '')
        subtopics = topic.get('subtopics', [])

        title = self._generate_title(topic_name, class_num, chapter)
        description = self._generate_description(topic_name, class_num, chapter, subtopics)
        tags = self._generate_tags(topic_name, class_num, chapter, subtopics)

        return {
            'title': title,
            'description': description,
            'tags': tags,
        }

    def _generate_title(self, topic_name, class_num, chapter):
        """Generate SEO-friendly title with random variation."""
        templates = [
            f"Class {class_num} Math | {topic_name} | NCERT English",
            f"Learn {topic_name} easily | Class {class_num} Math | NCERT",
            f"Class {class_num} Math | {topic_name} | Learn in English",
            f"Math Fun: {topic_name} | Class {class_num} NCERT",
            f"{topic_name} | Class {class_num} | NCERT Mathematics",
            f"Class {class_num} | {topic_name} | Fun with Math | NCERT",
        ]
        title = random.choice(templates)
        # YouTube title limit: 100 chars
        return title[:100]

    def _generate_description(self, topic_name, class_num, chapter, subtopics):
        """Generate rich description with timestamps and hashtags."""
        # Timestamps for subtopics
        timestamp_lines = []
        t = 15  # Start after intro
        for i, sub in enumerate(subtopics[:6]):
            m, s = divmod(t, 60)
            timestamp_lines.append(f"{m}:{s:02d} {sub}")
            t += random.randint(20, 40)

        timestamps = "\n".join(timestamp_lines) if timestamp_lines else "0:15 Main lesson"

        # Random intro lines
        intros = [
            f"📚 Class {class_num} - {chapter}",
            f"🎯 Topic: {topic_name}",
            "",
            f"⏱️ Timestamps:",
            timestamps,
            "",
            f"📝 This video is based on NCERT Class {class_num} Math curriculum.",
            "If you liked the video, hit Like 👍 and Subscribe!",
            "Don't forget to press the Bell 🔔 icon!",
            "",
            "📌 More Class-wise Videos:",
            "https://www.youtube.com/@shairo009/playlists",
            "",
            "📖 NCERT Books: https://ncert.nic.in/textbook.php",
            "",
        ]

        # Hashtags
        topic_clean = topic_name.replace(' ', '')
        hashtags = [
            f"#NCERT", f"#Class{class_num}Math", f"#{topic_clean}",
            "#MathTutorial", "#MathForKids", "#Mathematics",
            f"#Class{class_num}", "#NCERTMath", "#MathShorts",
        ]

        description = "\n".join(intros) + "\n" + " ".join(hashtags)
        return description[:5000]  # YouTube limit

    def _generate_tags(self, topic_name, class_num, chapter, subtopics):
        """Generate 15-20 SEO tags."""
        tags = [
            topic_name,
            f"class {class_num} math",
            f"class {class_num} maths",
            "ncert math",
            f"ncert class {class_num}",
            f"math class {class_num}",
            "mathematics",
            "learn math",
            "math tutorial",
            "ncert english",
            "maths for kids",
            "math tutorial for kids",
            f"class {class_num} ncert",
            "math basics",
        ]

        # Add chapter name
        if chapter:
            tags.append(chapter.lower())
            tags.append(f"{chapter} english")

        # Add subtopics as tags
        for sub in subtopics[:5]:
            tags.append(sub.lower())

        # Shuffle for naturalness
        random.shuffle(tags)
        return tags[:20]

    # ─── PLAYLIST MANAGEMENT ───────────────────────────────────────

    def get_or_create_playlist(self, title, description=""):
        """Find existing playlist by title, or create new one."""
        if title in self._playlist_cache:
            return self._playlist_cache[title]

        # Search existing playlists
        try:
            response = self.youtube.playlists().list(
                part='snippet',
                mine=True,
                maxResults=50
            ).execute()

            for item in response.get('items', []):
                if item['snippet']['title'] == title:
                    playlist_id = item['id']
                    self._playlist_cache[title] = playlist_id
                    return playlist_id
        except Exception as e:
            print(f"  Playlist search error: {e}")

        # Create new playlist
        try:
            response = self.youtube.playlists().insert(
                part='snippet,status',
                body={
                    'snippet': {
                        'title': title,
                        'description': description,
                        'defaultLanguage': 'en'
                    },
                    'status': {
                        'privacyStatus': 'public'
                    }
                }
            ).execute()

            playlist_id = response['id']
            self._playlist_cache[title] = playlist_id
            print(f"  Created playlist: {title}")
            return playlist_id

        except Exception as e:
            print(f"  Playlist creation error: {e}")
            return None

    def add_to_playlist(self, video_id, playlist_id):
        """Add video to a playlist."""
        if not playlist_id:
            return False
        try:
            self.youtube.playlistItems().insert(
                part='snippet',
                body={
                    'snippet': {
                        'playlistId': playlist_id,
                        'resourceId': {
                            'kind': 'youtube#video',
                            'videoId': video_id
                        }
                    }
                }
            ).execute()
            print(f"  Added to playlist")
            return True
        except Exception as e:
            print(f"  Playlist add error: {e}")
            return False

    # ─── THUMBNAIL ─────────────────────────────────────────────────

    def set_thumbnail(self, video_id, thumbnail_path):
        """Set custom thumbnail for a video."""
        if not thumbnail_path or not os.path.exists(thumbnail_path):
            return False
        try:
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype='image/png')
            ).execute()
            print(f"  Thumbnail set!")
            return True
        except Exception as e:
            print(f"  Thumbnail error: {e}")
            return False

    # ─── SCHEDULING ────────────────────────────────────────────────

    def get_next_peak_hour(self):
        """Get next peak hour for upload (IST = UTC+5:30).
        Peak hours: 8-10 AM, 2-4 PM, 6-9 PM IST.
        """
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)

        # Peak windows (hour, minute) in IST
        peaks = [
            (8, random.randint(0, 30)),   # Morning
            (9, random.randint(0, 30)),
            (14, random.randint(0, 30)),  # Afternoon
            (15, random.randint(0, 30)),
            (18, random.randint(0, 30)),  # Evening (best)
            (19, random.randint(0, 30)),
            (20, random.randint(0, 30)),
        ]

        # Find next peak window
        for hour, minute in peaks:
            candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if candidate > now:
                return candidate

        # Tomorrow morning
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=8, minute=random.randint(0, 30), second=0, microsecond=0)

    # ─── MAIN UPLOAD ───────────────────────────────────────────────

    def upload_video(self, video_path, metadata, thumbnail_path=None,
                     playlist_id=None, schedule=False):
        """Upload video with full human-like metadata.

        Args:
            video_path: Path to video file
            metadata: dict with title, description, tags
            thumbnail_path: Path to custom thumbnail (optional)
            playlist_id: Playlist to add video to (optional)
            schedule: If True, schedule for next peak hour

        Returns:
            video_id on success, None on failure
        """
        if not self.youtube:
            if not self.authenticate():
                return None

        if not os.path.exists(video_path):
            print(f"Video file not found: {video_path}")
            return None

        title = metadata.get('title', 'Math Lesson')[:100]
        description = metadata.get('description', '')[:5000]
        tags = metadata.get('tags', [])

        # Determine privacy & publish time
        if schedule:
            privacy = 'private'
            publish_at = self.get_next_peak_hour()
            publish_iso = publish_at.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            print(f"  Scheduled for: {publish_at.strftime('%d %b %I:%M %p IST')}")
        else:
            privacy = 'public'
            publish_iso = None

        # Recording date: 1-3 days ago (not suspiciously same-day)
        days_ago = random.randint(1, 3)
        recording_date = (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime('%Y-%m-%dT00:00:00Z')

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '27',  # Education
                'defaultLanguage': 'en',
                'defaultAudioLanguage': 'en',
            },
            'status': {
                'privacyStatus': privacy,
                'selfDeclaredMadeForKids': False,
                'embeddable': True,
                'license': 'youtube',
                'publicStatsViewable': True,
            },
            'recordingDetails': {
                'recordingDate': recording_date,
            }
        }

        # Add publishAt for scheduled videos
        if publish_iso:
            body['status']['publishAt'] = publish_iso

        try:
            # Random pre-upload delay (2-15 seconds, simulates human)
            delay = random.randint(2, 15)
            print(f"  Preparing upload... ({delay}s)")
            time.sleep(delay)

            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            request = self.youtube.videos().insert(
                part='snippet,status,recordingDetails',
                body=body,
                media_body=media
            )

            print(f"  Uploading: {title}")
            response = request.execute()
            video_id = response.get('id')
            print(f"  Uploaded! Video ID: {video_id}")
            print(f"  https://youtu.be/{video_id}")

            # Set custom thumbnail
            if thumbnail_path:
                self.set_thumbnail(video_id, thumbnail_path)

            # Add to playlist
            if playlist_id:
                self.add_to_playlist(video_id, playlist_id)

            return video_id

        except Exception as e:
            print(f"  Upload failed: {e}")
            return None

    def upload(self, video_path, title, description="", tags=None,
               thumbnail_path=None, category_id="27", made_for_kids=False,
               playlist_id=None, schedule=False):
        """Upload video directly with individual parameter arguments."""
        metadata = {
            'title': title,
            'description': description,
            'tags': tags or [],
            'categoryId': category_id,
        }
        return self.upload_video(video_path, metadata, thumbnail_path=thumbnail_path,
                                 playlist_id=playlist_id, schedule=schedule)



if __name__ == "__main__":
    print("YouTube Uploader — Super Human Edition")
    print("Usage: Import and use YouTubeUploader class")

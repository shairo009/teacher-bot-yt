"""
YouTube uploader with truthful metadata and private-first publishing.
Public or scheduled release requires a review bound to the exact video and metadata.
Local checks cannot certify copyright clearance, policy compliance or monetization.
"""

import os
import json
import random
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta

try:
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
except ImportError:
    # Importing a module must never install packages or contact external services.
    MediaFileUpload = build = InstalledAppFlow = Request = None


class YouTubeUploader:
    SCOPES = ['https://www.googleapis.com/auth/youtube']

    def __init__(self, token_path='token.json', secrets_path='client_secrets.json', *,
                 allow_interactive_auth=False):
        self.token_path = Path(token_path)
        self.secrets_path = Path(secrets_path)
        self.youtube = None
        self.allow_interactive_auth = allow_interactive_auth
        self._playlist_cache = {}

    def authenticate(self):
        """Authenticate with YouTube API using OAuth2."""
        if build is None:
            raise RuntimeError('Install requirements.txt before using YouTube upload')
        creds = None

        if self.token_path.exists():
            try:
                from google.oauth2.credentials import Credentials
                with open(self.token_path, 'r', encoding='utf-8-sig') as f:
                    token_data = json.load(f)
                creds = Credentials.from_authorized_user_info(token_data)
            except Exception as e:
                print(f"  ⚠ Token load warning: {e}")
                pass



        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"  ⚠ Token refresh failed: {e}")
                    creds = None
            
            if not creds or not creds.valid:
                if not self.allow_interactive_auth:
                    print('Valid OAuth credentials required; interactive authentication is disabled.')
                    return False
                if not self.secrets_path.exists():
                    print(f"ERROR: {self.secrets_path} not found!")
                    return False
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.secrets_path), self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Preserve expiry so future runs can refresh correctly.
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(self.token_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(creds.to_json())
            self.token_path.chmod(0o600)

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
        # Only actual edit timings can justify timestamps. List topics instead.
        timestamps = "\n".join(str(sub) for sub in subtopics[:6]) or topic_name

        # Random intro lines
        intros = [
            f"📚 Class {class_num} - {chapter}",
            f"🎯 Topic: {topic_name}",
            "",
            "Topics covered:",
            timestamps,
            "",
            f"📝 This video is based on NCERT Class {class_num} Math curriculum.",
            "If you liked the video, hit Like 👍 and Subscribe!",
            "Don't forget to press the Bell 🔔 icon!",
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

    @staticmethod
    def review_fingerprint(video_path, metadata):
        """Bind an editorial approval to both the media bytes and upload metadata."""
        digest = hashlib.sha256()
        with open(video_path, 'rb') as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(chunk)
        fields = {k: v for k, v in metadata.items() if k != 'publication_review'}
        digest.update(json.dumps(fields, sort_keys=True, ensure_ascii=False,
                                 allow_nan=False).encode('utf-8'))
        return digest.hexdigest()

    @classmethod
    def validate_upload(cls, video_path, metadata, schedule=False):
        """Local guardrails, not a legal opinion or a YouTube approval."""
        if not Path(video_path).is_file() or Path(video_path).stat().st_size == 0:
            raise ValueError('Video file is missing or empty')
        if not isinstance(metadata, dict):
            raise ValueError('metadata must be an object')
        for field in ('made_for_kids', 'contains_synthetic_media'):
            if type(metadata.get(field)) is not bool:
                raise ValueError(f'{field} requires an explicit boolean decision')
        title, description = metadata.get('title', ''), metadata.get('description', '')
        if not isinstance(title, str) or not title.strip() or len(title) > 100 or any(c in title for c in '<>'):
            raise ValueError('Title must be 1-100 characters without angle brackets')
        if not isinstance(description, str) or len(description.encode('utf-8')) > 5000 or any(c in description for c in '<>'):
            raise ValueError('Description must be at most 5000 UTF-8 bytes without angle brackets')
        tags = metadata.get('tags', [])
        if not isinstance(tags, list) or any(not isinstance(t, str) or not t.strip() or any(c in t for c in '<>') for t in tags):
            raise ValueError('Tags must be a list of nonempty strings without angle brackets')
        # YouTube counts separators and quotation marks around tags containing spaces.
        tag_length = sum(len(t) + (2 if ' ' in t else 0) for t in tags) + max(0, len(tags) - 1)
        if tag_length > 500:
            raise ValueError('Combined tags exceed the YouTube 500-character limit')
        privacy = metadata.get('privacy_status', 'private')
        if privacy not in ('private', 'unlisted', 'public'):
            raise ValueError('Invalid privacy_status')
        if privacy != 'private' or schedule:
            review = metadata.get('publication_review')
            if not isinstance(review, dict) or not str(review.get('reviewed_by', '')).strip():
                raise ValueError('Public, unlisted and scheduled release require editorial review')
            for check in ('rights_cleared', 'original_value', 'metadata_accurate', 'audience_checked', 'disclosure_checked'):
                if review.get(check) is not True:
                    raise ValueError(f'Publication review missing: {check}')
            if review.get('fingerprint') != cls.review_fingerprint(video_path, metadata):
                raise ValueError('Publication review does not match this video and metadata')

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
        # Validate before OAuth or any network call; never silently truncate claims.
        self.validate_upload(video_path, metadata, schedule)
        if not self.youtube:
            if not self.authenticate():
                return None

        title = metadata['title']
        description = metadata.get('description', '')
        tags = metadata.get('tags', [])

        # Determine privacy & publish time
        if schedule:
            privacy = 'private'
            publish_at = self.get_next_peak_hour()
            publish_iso = publish_at.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            print(f"  Scheduled for: {publish_at.strftime('%d %b %I:%M %p IST')}")
        else:
            privacy = metadata.get('privacy_status', 'private')
            publish_iso = None

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': str(metadata.get('categoryId', metadata.get('category_id', '15'))),
                'defaultLanguage': metadata.get('language', 'en'),
            },
            'status': {
                'privacyStatus': privacy,
                'selfDeclaredMadeForKids': metadata['made_for_kids'],
                'containsSyntheticMedia': metadata['contains_synthetic_media'],
                'embeddable': True,
                'license': 'youtube',
                'publicStatsViewable': True,
            },
        }
        if metadata.get('audio_language'):
            body['snippet']['defaultAudioLanguage'] = metadata['audio_language']

        # Add publishAt for scheduled videos
        if publish_iso:
            body['status']['publishAt'] = publish_iso

        try:
            media = MediaFileUpload(video_path, mimetype='video/mp4',
                                    chunksize=8 * 1024 * 1024, resumable=True)
            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )

            print(f"  Uploading: {title}")
            response = request.execute()
            video_id = response.get('id')
            if not isinstance(video_id, str) or not video_id.strip():
                return None
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
               thumbnail_path=None, category_id="27", made_for_kids=None,
               playlist_id=None, schedule=False, privacy_status='private',
               contains_synthetic_media=False, publication_review=None):
        """Upload video directly with individual parameter arguments."""
        metadata = {
            'title': title,
            'description': description,
            'tags': tags or [],
            'categoryId': category_id,
            'made_for_kids': made_for_kids,
            'contains_synthetic_media': contains_synthetic_media,
            'privacy_status': privacy_status,
            'publication_review': publication_review,
        }
        return self.upload_video(video_path, metadata, thumbnail_path=thumbnail_path,
                                 playlist_id=playlist_id, schedule=schedule)



if __name__ == "__main__":
    print('YouTube Uploader — private-first, reviewed publication')
    print("Usage: Import and use YouTubeUploader class")

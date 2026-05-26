# Keep existing uploader from story-type repo
import os
import json
from pathlib import Path

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
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

    def __init__(self, token_path='token.json', secrets_path='client_secrets.json'):
        self.token_path = Path(token_path)
        self.secrets_path = Path(secrets_path)
        self.youtube = None

    def authenticate(self):
        """Authenticate with YouTube API using OAuth2."""
        creds = None

        # Load existing token
        if self.token_path.exists():
            try:
                creds = self.TOKEN_PATH = self.token_path
                from google.oauth2.credentials import Credentials
                creds = Credentials.from_authorized_user_file(str(self.token_path), self.SCOPES)
            except Exception:
                pass

        # If no valid credentials, get new ones
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

            # Save credentials
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

    def upload_video(self, video_path, title, description, tags=None, privacy='public'):
        """Upload video to YouTube."""
        if not self.youtube:
            if not self.authenticate():
                return None

        if not os.path.exists(video_path):
            print(f"Video file not found: {video_path}")
            return None

        title = title[:100]  # YouTube title limit

        body = {
            'snippet': {
                'title': title,
                'description': description[:5000],
                'tags': tags or [],
                'categoryId': '27'  # Education
            },
            'status': {
                'privacyStatus': privacy,
                'selfDeclaredMadeForKids': False
            }
        }

        try:
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )

            print("  Uploading... (this may take a while)")
            response = request.execute()
            video_id = response.get('id')
            print(f"  ✅ Uploaded! Video ID: {video_id}")
            print(f"  🔗 https://youtu.be/{video_id}")
            return video_id

        except Exception as e:
            print(f"  Upload failed: {e}")
            return None


if __name__ == "__main__":
    print("YouTube Uploader module")
    print("Usage: Import and use YouTubeUploader class")
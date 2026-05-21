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
        from google.oauth2.credentials import Credentials

        # 1. Try to load from environment variables first (for GitHub Actions)
        token_json_env = os.environ.get('TOKEN_JSON')
        if token_json_env:
            try:
                token_data = json.loads(token_json_env)
                creds = Credentials.from_authorized_user_info(token_data, self.SCOPES)
                print("✅ Authenticated using TOKEN_JSON environment variable")
            except Exception as e:
                print(f"Warning: Failed to load credentials from TOKEN_JSON env: {e}")

        # 2. Load existing token file
        if not creds and self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_path), self.SCOPES)
                print("✅ Authenticated using token.json file")
            except Exception:
                pass

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    print("✅ Credentials refreshed")
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    creds = None
            
            if not creds:
                # 3. Try to load client secrets from environment
                client_secrets_env = os.environ.get('CLIENT_SECRETS_JSON')
                if client_secrets_env:
                    try:
                        secrets_data = json.loads(client_secrets_env)
                        flow = InstalledAppFlow.from_client_config(secrets_data, self.SCOPES)
                        creds = flow.run_local_server(port=0)
                    except Exception as e:
                        print(f"Error using CLIENT_SECRETS_JSON env: {e}")

                if not creds:
                    if not self.secrets_path.exists():
                        print(f"ERROR: No credentials found in environment or {self.secrets_path}!")
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
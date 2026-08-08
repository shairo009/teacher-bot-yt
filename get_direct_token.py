import os, json, urllib.parse, requests, subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

secrets_data = json.load(open('client_secrets.json'))
CLIENT_SECRETS = secrets_data.get('installed') or secrets_data.get('web')
CLIENT_ID = CLIENT_SECRETS['client_id']
CLIENT_SECRET = CLIENT_SECRETS['client_secret']
REDIRECT_URI = 'http://localhost:8080/'

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if 'code' in params:
            code = params['code'][0]
            print(f"Received Auth Code: {code[:10]}...")
            
            # Exchange code for tokens directly via HTTP POST
            resp = requests.post('https://oauth2.googleapis.com/token', data={
                'code': code,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'redirect_uri': REDIRECT_URI,
                'grant_type': 'authorization_code'
            })
            token_resp = resp.json()
            
            if 'access_token' in token_resp:
                token_data = {
                    'token': token_resp.get('access_token'),
                    'refresh_token': token_resp.get('refresh_token'),
                    'token_uri': 'https://oauth2.googleapis.com/token',
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'scopes': ['https://www.googleapis.com/auth/youtube.upload']
                }

                # Save token locally
                with open('token.json', 'w', encoding='utf-8') as f:
                    json.dump(token_data, f)
                print("✅ 1. TOKEN_JSON_SAVED_LOCALLY")

                # Update GitHub Secrets TOKEN_JSON
                token_str = json.dumps(token_data)
                subprocess.run(['gh', 'secret', 'set', 'TOKEN_JSON', '--repo', 'shairo009/teacher-bot-yt'], input=token_str.encode('utf-8'), check=True)
                print("✅ 2. GITHUB_SECRET_TOKEN_UPDATED")

                # Trigger fresh production workflow run
                subprocess.run(['gh', 'workflow', 'run', 'generate.yml', '--repo', 'shairo009/teacher-bot-yt', '-f', 'force=true'], check=True)
                print("🚀 3. PRODUCTION_WORKFLOW_RUN_DISPATCHED")

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<h1>SUCCESS! New YouTube Channel Connected and Workflow Triggered! You may close this window.</h1>")
                os._exit(0)
            else:
                print("ERROR:", token_resp)
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"<h1>Token Exchange Error</h1>")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Waiting for auth code...")

print("Server starting on port 8080...")
server = HTTPServer(('localhost', 8080), OAuthHandler)
server.serve_forever()

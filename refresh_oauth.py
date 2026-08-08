import os, json, subprocess
from google_auth_oauthlib.flow import InstalledAppFlow

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

print("Launching Google OAuth Account Switcher on port 8080...")
flow = InstalledAppFlow.from_client_secrets_file(
    'client_secrets.json',
    scopes=['https://www.googleapis.com/auth/youtube.upload']
)

creds = flow.run_local_server(port=8080, prompt='select_account consent')

token_data = {
    'token': creds.token,
    'refresh_token': creds.refresh_token,
    'token_uri': creds.token_uri,
    'client_id': creds.client_id,
    'client_secret': creds.client_secret,
    'scopes': creds.scopes
}

# 1. Save locally
with open('token.json', 'w', encoding='utf-8') as f:
    json.dump(token_data, f)

print("✅ NEW_TOKEN_SAVED_LOCALLY!")

# 2. Update GitHub Secret TOKEN_JSON
token_str = json.dumps(token_data)
subprocess.run(['gh', 'secret', 'set', 'TOKEN_JSON', '--repo', 'shairo009/teacher-bot-yt'], input=token_str.encode('utf-8'), check=True)
print("✅ GITHUB_SECRET_TOKEN_UPDATED!")

# 3. Trigger fresh workflow run on GitHub Actions
subprocess.run(['gh', 'workflow', 'run', 'generate.yml', '--repo', 'shairo009/teacher-bot-yt', '-f', 'force=true'], check=True)
print("🚀 WORKFLOW_DISPATCHED_SUCCESSFULLY!")

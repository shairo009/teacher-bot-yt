import os, json
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

with open('token.json', 'w') as f:
    json.dump(token_data, f)

print("NEW_CHANNEL_TOKEN_SAVED_8080")

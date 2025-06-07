import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LinkedIn API credentials
LINKEDIN_CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
LINKEDIN_CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
LINKEDIN_REDIRECT_URI = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:8000/linkedin/callback')

# LinkedIn API endpoints
LINKEDIN_AUTH_URL = 'https://www.linkedin.com/oauth/v2/authorization'
LINKEDIN_TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
LINKEDIN_API_BASE_URL = 'https://api.linkedin.com/v2'

# Required scopes for job search
LINKEDIN_SCOPES = [
    'r_liteprofile',
    'r_emailaddress',
    'r_basicprofile',
    'r_organization_social',
    'w_member_social'
] 
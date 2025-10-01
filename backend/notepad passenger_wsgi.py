import os
import sys

# Will be updated with actual cPanel username during deployment
CPANEL_USERNAME = 'CPANEL_USER'

# Add backend directory to path
backend_path = f'/home/{CPANEL_USERNAME}/kbaa_election/backend'
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'kbaa_election.production
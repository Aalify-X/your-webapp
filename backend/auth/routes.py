import os
import requests

def is_valid_whop_user(token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get('https://api.whop.com/v1/me', headers=headers)
    return response.status_code == 200

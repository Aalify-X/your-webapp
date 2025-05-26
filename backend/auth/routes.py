import os
import requests
from flask import Blueprint, request, jsonify
from . import whop_api

def is_valid_whop_user(token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get('https://api.whop.com/v1/me', headers=headers)
    return response.status_code == 200

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/verify-whop-token', methods=['POST'])
def verify_whop_token():
    """Verify Whop user token"""
    headers = request.headers
    user_token_data = whop_api.verify_user_token(headers)
    
    if not user_token_data:
        return jsonify({"error": "Invalid or missing user token"}), 401
        
    return jsonify({
        "success": True,
        "user_id": user_token_data.userId,
        "user_name": user_token_data.userName
    })

@auth_bp.route('/whop-profile', methods=['GET'])
def get_whop_profile():
    """Get Whop user profile"""
    headers = request.headers
    user_token_data = whop_api.verify_user_token(headers)
    
    if not user_token_data:
        return jsonify({"error": "Invalid or missing user token"}), 401
        
    # Get user profile using Whop API
    try:
        user_profile = whop_api.PublicUser({
            "userId": user_token_data.userId
        })
        return jsonify(user_profile)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

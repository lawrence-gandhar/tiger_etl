"""URL Constants for the Tiger ETL application.

This module contains all URL-related constants used throughout the application
for routing, redirects, and API endpoints.
"""

# ==========================================
# Base URLs
# ==========================================

# Authentication URLs
LOGIN_URL = "/login"
SIGNUP_URL = "/signup"
LOGOUT_URL = "/logout"
DASHBOARD_URL = "/dashboard"
HOME_URL = "/"

# ==========================================
# Redirect URLs with Query Parameters
# ==========================================

# Success redirect URLs
LOGIN_SUCCESS_URL = "/?login=success"
SIGNUP_SUCCESS_URL = "/login?signup=success"
LOGOUT_SUCCESS_URL = "/login?logout=success"

# Error redirect URLs
LOGOUT_FAILED_URL = "/login?logout=failed"
AUTHENTICATION_REQUIRED_URL = "/login?error=authentication_required"

# ==========================================
# API URLs
# ==========================================

API_BASE_URL = "/api/v1"
API_AUTH_URL = f"{API_BASE_URL}/auth"
API_USERS_URL = f"{API_BASE_URL}/users"
API_SESSIONS_URL = f"{API_BASE_URL}/sessions"

# ==========================================
# HTTP Status Codes
# ==========================================

HTTP_REDIRECT = 303

# Base Template Constants for Tiger ETL Site Management
"""
This module contains constants for template names used in the Tiger ETL application.
These constants help maintain consistency and avoid hardcoded template names throughout the application.
"""

# Authentication Templates
LOGIN_TEMPLATE = "login.htm"
SIGNUP_TEMPLATE = "signup.htm"

# Dashboard Templates
DASHBOARD_TEMPLATE = "dashboard.htm"
HOME_TEMPLATE = "home.htm"

# User Management Templates
USER_PROFILE_TEMPLATE = "user_profile.htm"
USER_LIST_TEMPLATE = "user_list.htm"

# Error Templates
ERROR_404_TEMPLATE = "error_404.htm"
ERROR_500_TEMPLATE = "error_500.htm"

# Form Templates
CONTACT_TEMPLATE = "contact.htm"
SETTINGS_TEMPLATE = "settings.htm"

# Data Management Templates
DATA_UPLOAD_TEMPLATE = "data_upload.htm"
DATA_VIEW_TEMPLATE = "data_view.htm"
PIPELINE_TEMPLATE = "pipeline.htm"

# Report Templates
REPORT_LIST_TEMPLATE = "report_list.htm"
REPORT_DETAIL_TEMPLATE = "report_detail.htm"

# Admin Templates
ADMIN_DASHBOARD_TEMPLATE = "admin_dashboard.htm"
ADMIN_USERS_TEMPLATE = "admin_users.htm"

# All template constants for easy reference
ALL_TEMPLATES = {
    "login": LOGIN_TEMPLATE,
    "signup": SIGNUP_TEMPLATE,
    "dashboard": DASHBOARD_TEMPLATE,
    "home": HOME_TEMPLATE,
    "user_profile": USER_PROFILE_TEMPLATE,
    "user_list": USER_LIST_TEMPLATE,
    "error_404": ERROR_404_TEMPLATE,
    "error_500": ERROR_500_TEMPLATE,
    "contact": CONTACT_TEMPLATE,
    "settings": SETTINGS_TEMPLATE,
    "data_upload": DATA_UPLOAD_TEMPLATE,
    "data_view": DATA_VIEW_TEMPLATE,
    "pipeline": PIPELINE_TEMPLATE,
    "report_list": REPORT_LIST_TEMPLATE,
    "report_detail": REPORT_DETAIL_TEMPLATE,
    "admin_dashboard": ADMIN_DASHBOARD_TEMPLATE,
    "admin_users": ADMIN_USERS_TEMPLATE,
}

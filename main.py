from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from modules.site_management.base_site_management import (
    LOGIN_TEMPLATE,
    SIGNUP_TEMPLATE
)
from modules.authentication_management.auth import signup_user, authenticate_user, SignupError, AuthenticationError
from modules.authentication_management.session_manager import create_session, logout_session, get_current_user
from constants import (
    LOGOUT_FAILED_URL,
    DASHBOARD_URL,
    SIGNUP_SUCCESS_URL,
    LOGOUT_SUCCESS_URL,
    AUTHENTICATION_REQUIRED_URL
)

# Create FastAPI app
app = FastAPI(title="Tiger ETL", description="Tiger ETL Application", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request, login: str = None):
    """
    Render the login page
    """
    context = {"request": request}
    
    # Check if user is already logged in
    current_user = get_current_user(request)
    if current_user:
        context["current_user"] = current_user
        context["success_message"] = "Welcome back! You are already logged in."
    elif login == "success":
        context["success_message"] = "Login successful! Welcome back."
    
    return templates.TemplateResponse(LOGIN_TEMPLATE, context)


@app.get("/login", response_class=HTMLResponse)
async def login_route(request: Request, signup: str = None, logout: str = None, error: str = None):
    """
    Alternative login route
    """
    context = {"request": request}
    
    # Check if user is already logged in
    current_user = get_current_user(request)
    if current_user:
        context["current_user"] = current_user
        context["success_message"] = "Welcome back! You are already logged in."
    elif signup == "success":
        context["success_message"] = "Account created successfully! Please log in."
    elif logout == "success":
        context["success_message"] = "You have been logged out successfully."
    elif logout == "failed":
        context["error"] = "Logout failed. Please try again."
    elif error == "authentication_required":
        context["error"] = "Please log in to access this page."
    
    return templates.TemplateResponse(LOGIN_TEMPLATE, context)


@app.post("/login")
async def login_submit(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...)
):
    """
    Handle login form submission
    """
    try:
        # Use the authenticate_user function from auth module
        user = authenticate_user(email=email, password=password)
        
        if user:
            # Authentication successful - create session
            create_session(user, request, response)
            
            # Redirect to dashboard
            return RedirectResponse(url=DASHBOARD_URL, status_code=303)
        else:
            # Authentication failed
            return templates.TemplateResponse(LOGIN_TEMPLATE, {
                "request": request,
                "error": "Invalid email or password"
            })
            
    except AuthenticationError as e:
        # Handle authentication-specific errors
        return templates.TemplateResponse(LOGIN_TEMPLATE, {
            "request": request,
            "error": str(e)
        })
    except Exception:
        # Handle unexpected errors
        return templates.TemplateResponse(LOGIN_TEMPLATE, {
            "request": request,
            "error": "An unexpected error occurred. Please try again."
        })


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """
    Render the signup page
    """
    return templates.TemplateResponse(SIGNUP_TEMPLATE, {"request": request})


@app.post("/signup")
async def signup_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    """
    Handle signup form submission
    """
    try:
        # Use the signup_user function from auth module
        signup_user(
            email=email,
            password=password,
            confirm_password=confirm_password
        )
        
        # Redirect to login with success message
        return RedirectResponse(url=SIGNUP_SUCCESS_URL, status_code=303)
        
    except SignupError as e:
        # Handle signup-specific errors
        return templates.TemplateResponse(SIGNUP_TEMPLATE, {
            "request": request,
            "error": str(e)
        })
    except Exception:
        # Handle unexpected errors
        return templates.TemplateResponse(SIGNUP_TEMPLATE, {
            "request": request,
            "error": "An unexpected error occurred. Please try again."
        })


@app.post("/logout")
async def logout_submit(request: Request, response: Response):
    """
    Handle logout request
    """
    try:
        # Logout the current session
        logout_success = logout_session(request, response)
        
        if logout_success:
            return RedirectResponse(url=LOGOUT_SUCCESS_URL, status_code=303)
        else:
            return RedirectResponse(url=LOGOUT_FAILED_URL, status_code=303)
            
    except Exception:
        return RedirectResponse(url=LOGOUT_FAILED_URL, status_code=303)


@app.get("/logout", response_class=HTMLResponse)
async def logout_page(request: Request, response: Response):
    """
    Handle logout via GET request (for convenience)
    """
    try:
        # Logout the current session
        logout_success = logout_session(request, response)
        
        if logout_success:
            return RedirectResponse(url=LOGOUT_SUCCESS_URL, status_code=303)
        else:
            return RedirectResponse(url=LOGOUT_FAILED_URL, status_code=303)
            
    except Exception:
        return RedirectResponse(url=LOGOUT_FAILED_URL, status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """
    Protected dashboard page - requires authentication
    """
    # Check if user is logged in
    current_user = get_current_user(request)
    if not current_user:
        # Redirect to login if not authenticated
        return RedirectResponse(url=AUTHENTICATION_REQUIRED_URL, status_code=303)
    
    # User is authenticated, show dashboard using template
    return templates.TemplateResponse("dashboard/dashboard.htm", {
        "request": request,
        "current_user": current_user
    })

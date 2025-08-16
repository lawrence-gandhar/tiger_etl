from fastapi import APIRouter, Request, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from modules.site_management.base_site_management import (
    LOGIN_TEMPLATE,
    SIGNUP_TEMPLATE,
)
from modules.authentication_management.auth import (
    signup_user,
    authenticate_user,
    SignupError,
    AuthenticationError,
)
from modules.authentication_management.session_manager import (
    create_session,
    logout_session,
    get_current_user,
)
from constants import (
    LOGOUT_FAILED_URL,
    DASHBOARD_URL,
    SIGNUP_SUCCESS_URL,
    LOGOUT_SUCCESS_URL,
    AUTHENTICATION_REQUIRED_URL,
)

# Setup router and templates
router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request, login: str = None):
    context = {"request": request}
    current_user = get_current_user(request)

    if current_user:
        context["current_user"] = current_user
        context["success_message"] = "Welcome back! You are already logged in."
    elif login == "success":
        context["success_message"] = "Login successful! Welcome back."

    return templates.TemplateResponse(LOGIN_TEMPLATE, context)


@router.get("/login", response_class=HTMLResponse)
async def login_route(request: Request, signup: str = None, logout: str = None, error: str = None):
    context = {"request": request}
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


@router.post("/login")
async def login_submit(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
):
    try:
        user = authenticate_user(email=email, password=password)

        if user:
            create_session(user, request, response)
            return RedirectResponse(url=DASHBOARD_URL, status_code=303)
        else:
            return templates.TemplateResponse(LOGIN_TEMPLATE, {
                "request": request,
                "error": "Invalid email or password"
            })

    except AuthenticationError as e:
        return templates.TemplateResponse(LOGIN_TEMPLATE, {"request": request, "error": str(e)})
    except Exception as e:
        return templates.TemplateResponse(LOGIN_TEMPLATE, {"request": request, "error": str(e)})


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse(SIGNUP_TEMPLATE, {"request": request})


@router.post("/signup")
async def signup_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_passwd: str = Form(...),
):
    try:
        signup_user(email=email, password=password, confirm_passwd=confirm_passwd)
        return RedirectResponse(url=SIGNUP_SUCCESS_URL, status_code=303)

    except SignupError as e:
        return templates.TemplateResponse(SIGNUP_TEMPLATE, {"request": request, "error": str(e)})
    except Exception as e:
        return templates.TemplateResponse(SIGNUP_TEMPLATE, {"request": request, "error": str(e)})


@router.post("/logout")
async def logout_submit(request: Request, response: Response):
    try:
        logout_success = logout_session(request, response)
        if logout_success:
            return RedirectResponse(url=LOGOUT_SUCCESS_URL, status_code=303)
        else:
            return RedirectResponse(url=LOGOUT_FAILED_URL, status_code=303)
    except Exception:
        return RedirectResponse(url=LOGOUT_FAILED_URL, status_code=303)


@router.get("/logout", response_class=HTMLResponse)
async def logout_page(request: Request, response: Response):
    try:
        logout_success = logout_session(request, response)
        if logout_success:
            return RedirectResponse(url=LOGOUT_SUCCESS_URL, status_code=303)
        else:
            return RedirectResponse(url=LOGOUT_FAILED_URL, status_code=303)
    except Exception:
        return RedirectResponse(url=LOGOUT_FAILED_URL, status_code=303)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url=AUTHENTICATION_REQUIRED_URL, status_code=303)

    return templates.TemplateResponse("dashboard/dashboard.htm", {
        "request": request,
        "current_user": current_user
    })

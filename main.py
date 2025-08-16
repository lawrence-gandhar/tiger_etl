from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from site_management.user_management.user_management_routes import router as auth_router

app = FastAPI(title="Tiger ETL", description="Tiger ETL Application", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include authentication router
app.include_router(auth_router)

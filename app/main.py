from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import CustomException
from app.middleware.cors import setup_cors
from app.middleware.rate_limiting import setup_rate_limiting
from app.middleware.logging import setup_logging

# create FastAPI instance
app = FastAPI(
	title="HIV Program Activities Tracker API",
	description="API for managing HIV Program activities, planning, and financial tracking",
	version="1.0.0",
	docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
	redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# setup middleware
setup_cors(app)
setup_rate_limiting(app)
setup_logging(app)

# include routers
app.include_router(api_router, prefix="/api/v1")

# global exception handler
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
	return JSONResponse(
		status_code=exc.status_code,
		content={
			"success": False,
			"error": {
				"code": exc.error_code,
				"message": exc.message,
				"details": exc.details
			}
		}
	)

# health check endpoint
@app.get("/health")
async def health_check():
	return {
		"status": "healthy",
		"version": "1.0.0"
	}

if __name__ == "__main__":
	uvicorn.run(
		"app.main:app",
		host="0.0.0.0",
		port=8000,
		reload=settings.ENVIRONMENT == "development"
	)
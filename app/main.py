import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.database import create_tables
from app.services.rate_limiter import setup_rate_limiting

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("")
    print("  +==================================================+")
    print("  |  Raseel Platform v" + settings.app_version + "                          |")
    print("  |  Environment: " + settings.app_env + "                          |")
    print("  |  Data Region: " + settings.data_region + "                      |")
    print("  +==================================================+")
    try:
        create_tables()
        print("  |  Database:        Ready                         |")
    except Exception as e:
        print("  |  Database Error:  " + str(e)[:28] + "  |")
    print("  |  PDPL Compliance: Active                        |")
    print("  |  AI Agents:       Loaded                        |")
    print("  |  Prayer Times:    Active                        |")
    print("  |  Auth System:     Active                        |")
    print("  |  Rate Limiting:   Active                        |")
    print("  |  Guardrails:      Active                        |")
    print("  +==================================================+")
    print("  |  Docs:    http://127.0.0.1:8000/api/docs        |")
    print("  |  Health:  http://127.0.0.1:8000/api/health      |")
    print("  +==================================================+")
    print("")
    yield
    print("")
    print("  Raseel Platform stopped.")
    print("")


app = FastAPI(
    title="Raseel Platform",
    description="Saudi PDPL-Compliant WhatsApp Automation Platform with AI Agents",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

setup_rate_limiting(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routes.auth import router as auth_router
from app.api.routes import health, businesses, conversations, webhooks, consent
from app.api.routes import products, orders, appointments, prayer, analytics
from app.api.routes import customers

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(health.router, prefix="/api", tags=["Health & Compliance"])
app.include_router(businesses.router, prefix="/api/businesses", tags=["Businesses"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["Conversations & AI"])
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Appointments"])
app.include_router(consent.router, prefix="/api/consent", tags=["PDPL Consent"])
app.include_router(prayer.router, prefix="/api/cultural", tags=["Cultural Intelligence"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics & Dashboard"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["WhatsApp Webhooks"])


@app.get("/")
async def root():
    return {
        "platform": "Raseel",
        "version": settings.app_version,
        "status": "running",
        "region": settings.data_region,
        "pdpl_compliant": True,
        "rate_limiting": True,
        "ai_guardrails": True,
        "endpoints": {
            "docs": "/api/docs",
            "health": "/api/health",
            "auth": "/api/auth",
            "businesses": "/api/businesses",
            "products": "/api/products/?business_id=xxx",
            "conversations": "/api/conversations/process",
            "webhooks": "/api/webhooks/whatsapp",
        },
    }

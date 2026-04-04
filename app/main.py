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
    print("  +==================================================+")
    try:
        create_tables()
        print("  |  Database:        Ready                         |")
    except Exception as e:
        print("  |  Database Error:  " + str(e)[:28] + "  |")
    
    # Auto-create admin on startup
    try:
        from app.database import get_db
        from app.models.user import User
        from app.core.security import get_password_hash
        import uuid
        db = next(get_db())
        existing = db.query(User).filter(User.email == "admin@raseel.sa").first()
        if not existing:
            admin = User(
                id=str(uuid.uuid4()),
                email="admin@raseel.sa",
                hashed_password=get_password_hash("Raseel2026!"),
                full_name="Raseel Admin",
                role="super_admin",
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("  |  Admin:           Created                       |")
        else:
            print("  |  Admin:           Already exists                |")
    except Exception as e:
        print("  |  Admin Error:     " + str(e)[:28] + "  |")
    
    print("  +==================================================+")
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


@app.get("/api/setup/create-admin")
async def setup_admin():
    try:
        from app.database import get_db
        from app.models.user import User
        from app.core.security import get_password_hash
        import uuid
        db = next(get_db())
        existing = db.query(User).filter(User.email == "admin@raseel.sa").first()
        if existing:
            return {"status": "already exists", "email": "admin@raseel.sa"}
        admin = User(
            id=str(uuid.uuid4()),
            email="admin@raseel.sa",
            hashed_password=get_password_hash("Raseel2026!"),
            full_name="Raseel Admin",
            role="super_admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        return {"status": "created", "email": "admin@raseel.sa"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/")
async def root():
    return {
        "platform": "Raseel",
        "version": settings.app_version,
        "status": "running",
        "region": settings.data_region,
        "pdpl_compliant": True,
    }

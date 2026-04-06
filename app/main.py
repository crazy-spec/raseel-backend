import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import create_tables
from app.services.rate_limiter import setup_rate_limiting

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("")
    print("  +==================================================+")
    print("  |  Raseel Platform                                 |")
    print("  +==================================================+")
    try:
        create_tables()
        print("  |  Database:        Ready                         |")
    except Exception as e:
        print("  |  Database Error:  " + str(e)[:28] + "  |")

    # AUTO CREATE ADMIN
    try:
        from app.database import get_db
        from app.models.user import User
        from app.auth.utils import hash_password
        import uuid
        db = next(get_db())
        existing = db.query(User).filter(User.email == "admin@raseel.sa").first()
        if not existing:
            admin = User(
                id=str(uuid.uuid4()),
                email="admin@raseel.sa",
                password_hash=hash_password("Raseel2026!"),
                full_name="Raseel Admin",
                role="super_admin",
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("  |  Admin:           Created                       |")
        else:
            existing.password_hash = hash_password("Raseel2026!")
            existing.role = "super_admin"
            existing.is_active = True
            db.commit()
            print("  |  Admin:           Updated                       |")
    except Exception as e:
        print("  |  Admin Error:     " + str(e)[:28] + "  |")

    # AUTO SEED DEMO DATA
    try:
        from app.database import SessionLocal
        from app.models.business import Business
        from app.models.product import Product
        from app.models.customer import Customer
        from app.models.conversation import Conversation, Message
        from app.compliance.encryption import encrypt_pii, hash_for_lookup
        import uuid
        from datetime import datetime, timedelta
        import random

        db2 = SessionLocal()
        biz_count = db2.query(Business).count()

        if biz_count < 6:
            print("  |  Seeding demo data...                           |")

            sectors = [
                ("Al Najma Restaurant", "مطعم النجمة", "restaurant", "Dammam", "NAJMA001", [
                    ("Kabsa", "كبسة", "Traditional Saudi rice with chicken", 45.00),
                    ("Mandi", "مندي", "Slow cooked lamb with rice", 65.00),
                    ("Shawarma", "شاورما", "Grilled chicken wrap", 18.00),
                    ("Mutabbaq", "مطبق", "Stuffed pancake with meat", 25.00),
                    ("Harees", "هريس", "Wheat and meat porridge", 35.00),
                    ("Saleeg", "سليق", "White rice cooked in broth", 40.00),
                    ("Arabic Coffee", "قهوة عربية", "Traditional Saudi coffee", 8.00),
                    ("Fresh Juice", "عصير طازج", "Seasonal fruit juice", 12.00),
                    ("Pepsi", "بيبسي", "Cold soft drink", 5.00),
                    ("Kunafa", "كنافة", "Sweet cheese pastry", 20.00),
                ]),
                ("Al Shifa Medical Center", "مركز الشفاء الطبي", "medical", "Riyadh", "SHIFA001", [
                    ("General Consultation", "استشارة عامة", "General doctor visit", 150.00),
                    ("Specialist Consultation", "استشارة تخصصية", "Specialist doctor visit", 250.00),
                    ("Blood Test", "تحليل دم", "Complete blood count", 80.00),
                    ("X-Ray", "أشعة سينية", "Digital X-ray imaging", 120.00),
                    ("ECG", "رسم قلب", "Electrocardiogram", 100.00),
                    ("Dental Checkup", "فحص أسنان", "Routine dental examination", 200.00),
                    ("Eye Examination", "فحص عيون", "Complete eye exam", 180.00),
                    ("Vaccination", "تطعيم", "Standard vaccination", 90.00),
                    ("Physiotherapy", "علاج طبيعي", "One physiotherapy session", 160.00),
                    ("Nutrition Consultation", "استشارة تغذية", "Diet and nutrition advice", 130.00),
                ]),
                ("Golden Palm Hotel", "فندق النخلة الذهبية", "hotel", "Jeddah", "HOTEL001", [
                    ("Standard Room", "غرفة عادية", "Comfortable standard room", 350.00),
                    ("Deluxe Room", "غرفة ديلوكس", "Spacious deluxe room", 550.00),
                    ("Suite", "جناح", "Luxury suite with sea view", 950.00),
                    ("Family Room", "غرفة عائلية", "Large room for families", 650.00),
                    ("Breakfast Buffet", "بوفيه إفطار", "Full breakfast buffet", 75.00),
                    ("Airport Transfer", "توصيل مطار", "Round trip airport transfer", 120.00),
                    ("Laundry Service", "خدمة غسيل", "Same day laundry service", 50.00),
                    ("Spa Session", "جلسة سبا", "One hour spa treatment", 200.00),
                    ("Meeting Room", "قاعة اجتماعات", "Half day meeting room", 500.00),
                    ("Pool Access", "دخول مسبح", "Full day pool access", 40.00),
                ]),
                ("Al Madinah Retail Store", "متجر المدينة", "retail", "Medina", "RETAIL001", [
                    ("Saudi Dates Box", "صندوق تمر سعودي", "Premium Ajwa dates 1kg", 85.00),
                    ("Oud Perfume", "عطر عود", "Authentic Saudi oud perfume", 250.00),
                    ("Thobe", "ثوب", "Traditional white thobe", 120.00),
                    ("Abaya", "عباءة", "Elegant black abaya", 180.00),
                    ("Prayer Beads", "مسبحة", "Handcrafted prayer beads", 45.00),
                    ("Arabic Coffee Set", "طقم قهوة عربية", "Dallah and cups set", 95.00),
                    ("Zamzam Water 5L", "ماء زمزم 5 لتر", "Authentic Zamzam water", 30.00),
                    ("Miswak Pack", "سواك", "Natural miswak pack of 10", 25.00),
                    ("Saudi Honey", "عسل سعودي", "Pure Sidr honey 500g", 120.00),
                    ("Incense Bakhoor", "بخور", "Premium bakhoor incense", 65.00),
                ]),
                ("Lujain Beauty Salon", "صالون لجين للتجميل", "salon", "Khobar", "SALON001", [
                    ("Haircut", "قص شعر", "Professional haircut and styling", 80.00),
                    ("Hair Color", "صبغة شعر", "Full hair coloring", 250.00),
                    ("Highlights", "هايلايت", "Partial or full highlights", 350.00),
                    ("Keratin Treatment", "كيراتين", "Smoothing keratin treatment", 450.00),
                    ("Manicure", "مانيكير", "Full manicure with polish", 60.00),
                    ("Pedicure", "باديكير", "Full pedicure with polish", 80.00),
                    ("Facial", "فيشل", "Deep cleansing facial", 150.00),
                    ("Eyebrow Threading", "تشكيل حواجب", "Eyebrow shaping", 30.00),
                    ("Makeup", "مكياج", "Full makeup application", 200.00),
                    ("Henna", "حناء", "Traditional henna design", 100.00),
                ]),
                ("Noor Education Center", "مركز نور التعليمي", "education", "Riyadh", "EDU001", [
                    ("Arabic Language Course", "دورة اللغة العربية", "Beginner to advanced Arabic", 800.00),
                    ("English Language Course", "دورة اللغة الإنجليزية", "IELTS preparation course", 1200.00),
                    ("Math Tutoring", "تدريس رياضيات", "One-on-one math tutoring per hour", 80.00),
                    ("Science Tutoring", "تدريس علوم", "Science subjects tutoring per hour", 80.00),
                    ("Quran Memorization", "حفظ القرآن", "Quran memorization program", 500.00),
                    ("Computer Skills", "مهارات حاسوب", "Basic computer skills course", 600.00),
                    ("Coding for Kids", "برمجة للأطفال", "Programming basics for children", 900.00),
                    ("Business English", "إنجليزية أعمال", "Professional business English", 1500.00),
                    ("SAT Preparation", "تحضير SAT", "Full SAT prep course", 2000.00),
                    ("Summer Program", "برنامج صيفي", "Intensive summer learning program", 1800.00),
                ]),
            ]

            customers_data = [
                ("Ahmed Al-Ghamdi", "+966501234001"),
                ("Mohammed Al-Qahtani", "+966501234002"),
                ("Abdullah Al-Zahrani", "+966501234003"),
                ("Khalid Al-Harbi", "+966501234004"),
                ("Sara Al-Mutairi", "+966501234005"),
            ]

            for i, (name_en, name_ar, sector, city, code, products) in enumerate(sectors):
                biz = Business(
                    id=str(uuid.uuid4()),
                    name_en=name_en,
                    name_ar=name_ar,
                    sector=sector,
                    city=city,
                    whatsapp_phone="+9665011110" + str(i + 1).zfill(2),
                    is_active=True,
                    tier="professional",
                    access_code=code,
                )
                db2.add(biz)
                db2.flush()

                for pname_en, pname_ar, desc, price in products:
                    db2.add(Product(
                        id=str(uuid.uuid4()),
                        business_id=biz.id,
                        name_en=pname_en,
                        name_ar=pname_ar,
                        description_en=desc,
                        description_ar=desc,
                        price=price,
                        is_available=True,
                        category="item",
                    ))

                for cname, cphone in customers_data:
                    c = Customer(
                        id=str(uuid.uuid4()),
                        business_id=biz.id,
                        phone_encrypted=encrypt_pii(cphone),
                        phone_hash=hash_for_lookup(cphone),
                        name_encrypted=encrypt_pii(cname),
                        consent_status="granted",
                        consent_granted_at=datetime.utcnow(),
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    )
                    db2.add(c)
                    db2.flush()

                    conv = Conversation(
                        id=str(uuid.uuid4()),
                        business_id=biz.id,
                        customer_id=c.id,
                        status="active",
                        sector_context=sector,
                        created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
                    )
                    db2.add(conv)
                    db2.flush()

                    db2.add(Message(
                        id=str(uuid.uuid4()),
                        conversation_id=conv.id,
                        business_id=biz.id,
                        direction="inbound",
                        sender_type="customer",
                        message_type="text",
                        content="Hello, I need help with " + name_en,
                        created_at=datetime.utcnow() - timedelta(minutes=30),
                    ))
                    db2.add(Message(
                        id=str(uuid.uuid4()),
                        conversation_id=conv.id,
                        business_id=biz.id,
                        direction="outbound",
                        sender_type="ai",
                        message_type="text",
                        content="Welcome to " + name_en + "! How can I assist you today?",
                        created_at=datetime.utcnow() - timedelta(minutes=29),
                    ))

            db2.commit()
            print("  |  Demo Data:       Seeded                        |")
        else:
            print("  |  Demo Data:       Already exists                |")

        db2.close()

    except Exception as e:
        print("  |  Seed Error:      " + str(e)[:28] + "  |")

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
        from app.auth.utils import hash_password
        import uuid
        db = next(get_db())
        existing = db.query(User).filter(User.email == "admin@raseel.sa").first()
        if existing:
            existing.password_hash = hash_password("Raseel2026!")
            existing.role = "super_admin"
            existing.is_active = True
            db.commit()
            return {"status": "updated", "email": "admin@raseel.sa", "role": "super_admin"}
        admin = User(
            id=str(uuid.uuid4()),
            email="admin@raseel.sa",
            password_hash=hash_password("Raseel2026!"),
            full_name="Raseel Admin",
            role="super_admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        return {"status": "created", "email": "admin@raseel.sa"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/api/setup/seed-all")
async def seed_all_sectors():
    try:
        from app.database import SessionLocal
        from app.models.user import User
        from app.models.business import Business
        from app.models.product import Product
        from app.models.customer import Customer
        from app.models.conversation import Conversation, Message
        from app.compliance.encryption import encrypt_pii, hash_for_lookup
        import uuid
        from datetime import datetime, timedelta
        import random

        db = SessionLocal()

        admin = db.query(User).filter(User.email == "admin@raseel.sa").first()
        if not admin:
            db.close()
            return {"status": "error", "detail": "Admin not found"}

        existing = db.query(Business).count()
        if existing >= 6:
            db.close()
            return {"status": "already seeded", "businesses": existing}

        sectors = [
            ("Al Najma Restaurant", "مطعم النجمة", "restaurant", "Dammam", "NAJMA001", [
                ("Kabsa", "كبسة", "Traditional Saudi rice with chicken", 45.00),
                ("Mandi", "مندي", "Slow cooked lamb with rice", 65.00),
                ("Shawarma", "شاورما", "Grilled chicken wrap", 18.00),
                ("Mutabbaq", "مطبق", "Stuffed pancake with meat", 25.00),
                ("Harees", "هريس", "Wheat and meat porridge", 35.00),
                ("Saleeg", "سليق", "White rice cooked in broth", 40.00),
                ("Arabic Coffee", "قهوة عربية", "Traditional Saudi coffee", 8.00),
                ("Fresh Juice", "عصير طازج", "Seasonal fruit juice", 12.00),
                ("Pepsi", "بيبسي", "Cold soft drink", 5.00),
                ("Kunafa", "كنافة", "Sweet cheese pastry", 20.00),
            ]),
            ("Al Shifa Medical Center", "مركز الشفاء الطبي", "medical", "Riyadh", "SHIFA001", [
                ("General Consultation", "استشارة عامة", "General doctor visit", 150.00),
                ("Specialist Consultation", "استشارة تخصصية", "Specialist doctor visit", 250.00),
                ("Blood Test", "تحليل دم", "Complete blood count", 80.00),
                ("X-Ray", "أشعة سينية", "Digital X-ray imaging", 120.00),
                ("ECG", "رسم قلب", "Electrocardiogram", 100.00),
                ("Dental Checkup", "فحص أسنان", "Routine dental examination", 200.00),
                ("Eye Examination", "فحص عيون", "Complete eye exam", 180.00),
                ("Vaccination", "تطعيم", "Standard vaccination", 90.00),
                ("Physiotherapy", "علاج طبيعي", "One physiotherapy session", 160.00),
                ("Nutrition Consultation", "استشارة تغذية", "Diet and nutrition advice", 130.00),
            ]),
            ("Golden Palm Hotel", "فندق النخلة الذهبية", "hotel", "Jeddah", "HOTEL001", [
                ("Standard Room", "غرفة عادية", "Comfortable standard room", 350.00),
                ("Deluxe Room", "غرفة ديلوكس", "Spacious deluxe room", 550.00),
                ("Suite", "جناح", "Luxury suite with sea view", 950.00),
                ("Family Room", "غرفة عائلية", "Large room for families", 650.00),
                ("Breakfast Buffet", "بوفيه إفطار", "Full breakfast buffet", 75.00),
                ("Airport Transfer", "توصيل مطار", "Round trip airport transfer", 120.00),
                ("Laundry Service", "خدمة غسيل", "Same day laundry service", 50.00),
                ("Spa Session", "جلسة سبا", "One hour spa treatment", 200.00),
                ("Meeting Room", "قاعة اجتماعات", "Half day meeting room", 500.00),
                ("Pool Access", "دخول مسبح", "Full day pool access", 40.00),
            ]),
            ("Al Madinah Retail Store", "متجر المدينة", "retail", "Medina", "RETAIL001", [
                ("Saudi Dates Box", "صندوق تمر سعودي", "Premium Ajwa dates 1kg", 85.00),
                ("Oud Perfume", "عطر عود", "Authentic Saudi oud perfume", 250.00),
                ("Thobe", "ثوب", "Traditional white thobe", 120.00),
                ("Abaya", "عباءة", "Elegant black abaya", 180.00),
                ("Prayer Beads", "مسبحة", "Handcrafted prayer beads", 45.00),
                ("Arabic Coffee Set", "طقم قهوة عربية", "Dallah and cups set", 95.00),
                ("Zamzam Water 5L", "ماء زمزم 5 لتر", "Authentic Zamzam water", 30.00),
                ("Miswak Pack", "سواك", "Natural miswak pack of 10", 25.00),
                ("Saudi Honey", "عسل سعودي", "Pure Sidr honey 500g", 120.00),
                ("Incense Bakhoor", "بخور", "Premium bakhoor incense", 65.00),
            ]),
            ("Lujain Beauty Salon", "صالون لجين للتجميل", "salon", "Khobar", "SALON001", [
                ("Haircut", "قص شعر", "Professional haircut and styling", 80.00),
                ("Hair Color", "صبغة شعر", "Full hair coloring", 250.00),
                ("Highlights", "هايلايت", "Partial or full highlights", 350.00),
                ("Keratin Treatment", "كيراتين", "Smoothing keratin treatment", 450.00),
                ("Manicure", "مانيكير", "Full manicure with polish", 60.00),
                ("Pedicure", "باديكير", "Full pedicure with polish", 80.00),
                ("Facial", "فيشل", "Deep cleansing facial", 150.00),
                ("Eyebrow Threading", "تشكيل حواجب", "Eyebrow shaping", 30.00),
                ("Makeup", "مكياج", "Full makeup application", 200.00),
                ("Henna", "حناء", "Traditional henna design", 100.00),
            ]),
            ("Noor Education Center", "مركز نور التعليمي", "education", "Riyadh", "EDU001", [
                ("Arabic Language Course", "دورة اللغة العربية", "Beginner to advanced Arabic", 800.00),
                ("English Language Course", "دورة اللغة الإنجليزية", "IELTS preparation course", 1200.00),
                ("Math Tutoring", "تدريس رياضيات", "One-on-one math tutoring per hour", 80.00),
                ("Science Tutoring", "تدريس علوم", "Science subjects tutoring per hour", 80.00),
                ("Quran Memorization", "حفظ القرآن", "Quran memorization program", 500.00),
                ("Computer Skills", "مهارات حاسوب", "Basic computer skills course", 600.00),
                ("Coding for Kids", "برمجة للأطفال", "Programming basics for children", 900.00),
                ("Business English", "إنجليزية أعمال", "Professional business English", 1500.00),
                ("SAT Preparation", "تحضير SAT", "Full SAT prep course", 2000.00),
                ("Summer Program", "برنامج صيفي", "Intensive summer learning program", 1800.00),
            ]),
        ]

        customers_data = [
            ("Ahmed Al-Ghamdi", "+966501234001"),
            ("Mohammed Al-Qahtani", "+966501234002"),
            ("Abdullah Al-Zahrani", "+966501234003"),
            ("Khalid Al-Harbi", "+966501234004"),
            ("Sara Al-Mutairi", "+966501234005"),
        ]

        created = []

        for i, (name_en, name_ar, sector, city, code, products) in enumerate(sectors):
            biz = Business(
                id=str(uuid.uuid4()),
                name_en=name_en,
                name_ar=name_ar,
                sector=sector,
                city=city,
                whatsapp_phone="+9665011110" + str(i + 1).zfill(2),
                is_active=True,
                tier="professional",
                access_code=code,
            )
            db.add(biz)
            db.flush()

            for pname_en, pname_ar, desc, price in products:
                db.add(Product(
                    id=str(uuid.uuid4()),
                    business_id=biz.id,
                    name_en=pname_en,
                    name_ar=pname_ar,
                    description_en=desc,
                    description_ar=desc,
                    price=price,
                    is_available=True,
                    category="item",
                ))

            for cname, cphone in customers_data:
                c = Customer(
                    id=str(uuid.uuid4()),
                    business_id=biz.id,
                    phone_encrypted=encrypt_pii(cphone),
                    phone_hash=hash_for_lookup(cphone),
                    name_encrypted=encrypt_pii(cname),
                    consent_status="granted",
                    consent_granted_at=datetime.utcnow(),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                )
                db.add(c)
                db.flush()

                conv = Conversation(
                    id=str(uuid.uuid4()),
                    business_id=biz.id,
                    customer_id=c.id,
                    status="active",
                    sector_context=sector,
                    created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
                )
                db.add(conv)
                db.flush()

                db.add(Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conv.id,
                    business_id=biz.id,
                    direction="inbound",
                    sender_type="customer",
                    message_type="text",
                    content="Hello, I need help with " + name_en,
                    created_at=datetime.utcnow() - timedelta(minutes=30),
                ))
                db.add(Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conv.id,
                    business_id=biz.id,
                    direction="outbound",
                    sender_type="ai",
                    message_type="text",
                    content="Welcome to " + name_en + "! How can I assist you today?",
                    created_at=datetime.utcnow() - timedelta(minutes=29),
                ))

            created.append(name_en)

        db.commit()
        db.close()
        return {"status": "success", "seeded": created}

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

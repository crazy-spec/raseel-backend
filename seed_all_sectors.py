"""
Seed all 6 sectors with Saudi demo data.
Triggered via: GET /api/setup/seed-all
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
os.environ["USE_SQLITE"] = "true"

from app.database import create_tables, SessionLocal
from app.models.user import User, UserRole
from app.auth.utils import hash_password
import uuid
from datetime import datetime, timedelta
import random

def get_db():
    db = SessionLocal()
    try:
        return db
    except:
        db.close()
        raise

def seed_all():
    create_tables()
    db = SessionLocal()

    try:
        # ============================================================
        # GET ADMIN USER
        # ============================================================
        admin = db.query(User).filter(User.email == "admin@raseel.sa").first()
        if not admin:
            print("Admin not found. Run create_admin.py first.")
            return

        # ============================================================
        # IMPORT MODELS
        # ============================================================
        from app.models.business import Business
        from app.models.product import Product
        from app.models.customer import Customer
        from app.models.conversation import Conversation, Message
        from app.models.order import Order, OrderItem
        from app.models.appointment import Appointment

        # ============================================================
        # SECTOR 1 — RESTAURANT
        # ============================================================
        print("Creating Restaurant...")
        r1 = Business(
            id=str(uuid.uuid4()),
            name_en="Al Najma Restaurant",
            name_ar="مطعم النجمة",
            sector="restaurant",
            city="Dammam",
            whatsapp_phone="+966501111001",
            is_active=True,
            tier="professional",
            owner_id=admin.id,
            access_code="NAJMA001",
        )
        db.add(r1)
        db.flush()

        restaurant_products = [
            ("Kabsa", "كبسة", "Traditional Saudi rice with chicken", 45.00),
            ("Mandi", "مندي", "Slow cooked lamb with rice", 65.00),
            ("Shawarma", "شاورما", "Grilled chicken wrap", 18.00),
            ("Mutabbaq", "مطبق", "Stuffed pancake with meat", 25.00),
            ("Harees", "هريس", "Wheat and meat porridge", 35.00),
            ("Saleeg", "سليق", "White rice cooked in broth", 40.00),
            ("Jareesh", "جريش", "Crushed wheat dish", 30.00),
            ("Pepsi", "بيبسي", "Cold soft drink", 5.00),
            ("Fresh Juice", "عصير طازج", "Seasonal fruit juice", 12.00),
            ("Arabic Coffee", "قهوة عربية", "Traditional Saudi coffee", 8.00),
        ]
        for name_en, name_ar, desc, price in restaurant_products:
            db.add(Product(
                id=str(uuid.uuid4()),
                business_id=r1.id,
                name_en=name_en,
                name_ar=name_ar,
                description=desc,
                price=price,
                is_available=True,
                category="food",
            ))

        # ============================================================
        # SECTOR 2 — MEDICAL
        # ============================================================
        print("Creating Medical Center...")
        r2 = Business(
            id=str(uuid.uuid4()),
            name_en="Al Shifa Medical Center",
            name_ar="مركز الشفاء الطبي",
            sector="medical",
            city="Riyadh",
            whatsapp_phone="+966501111002",
            is_active=True,
            tier="professional",
            owner_id=admin.id,
            access_code="SHIFA001",
        )
        db.add(r2)
        db.flush()

        medical_products = [
            ("General Consultation", "استشارة عامة", "General doctor visit", 150.00),
            ("Specialist Consultation", "استشارة تخصصية", "Specialist doctor visit", 250.00),
            ("Blood Test", "تحليل دم", "Complete blood count", 80.00),
            ("X-Ray", "أشعة سينية", "Digital X-ray imaging", 120.00),
            ("ECG", "رسم قلب", "Electrocardiogram", 100.00),
            ("Dental Checkup", "فحص أسنان", "Routine dental examination", 200.00),
            ("Eye Examination", "فحص عيون", "Complete eye exam", 180.00),
            ("Vaccination", "تطعيم", "Standard vaccination", 90.00),
            ("Physiotherapy Session", "جلسة علاج طبيعي", "One physiotherapy session", 160.00),
            ("Nutrition Consultation", "استشارة تغذية", "Diet and nutrition advice", 130.00),
        ]
        for name_en, name_ar, desc, price in medical_products:
            db.add(Product(
                id=str(uuid.uuid4()),
                business_id=r2.id,
                name_en=name_en,
                name_ar=name_ar,
                description=desc,
                price=price,
                is_available=True,
                category="service",
            ))

        # ============================================================
        # SECTOR 3 — HOTEL
        # ============================================================
        print("Creating Hotel...")
        r3 = Business(
            id=str(uuid.uuid4()),
            name_en="Golden Palm Hotel",
            name_ar="فندق النخلة الذهبية",
            sector="hotel",
            city="Jeddah",
            whatsapp_phone="+966501111003",
            is_active=True,
            tier="enterprise",
            owner_id=admin.id,
            access_code="HOTEL001",
        )
        db.add(r3)
        db.flush()

        hotel_products = [
            ("Standard Room", "غرفة عادية", "Comfortable standard room", 350.00),
            ("Deluxe Room", "غرفة ديلوكس", "Spacious deluxe room", 550.00),
            ("Suite", "جناح", "Luxury suite with sea view", 950.00),
            ("Family Room", "غرفة عائلية", "Large room for families", 650.00),
            ("Breakfast Buffet", "بوفيه إفطار", "Full breakfast buffet", 75.00),
            ("Airport Transfer", "توصيل مطار", "Round trip airport transfer", 120.00),
            ("Laundry Service", "خدمة غسيل", "Same day laundry service", 50.00),
            ("Spa Session", "جلسة سبا", "One hour spa treatment", 200.00),
            ("Meeting Room", "قاعة اجتماعات", "Half day meeting room", 500.00),
            ("Swimming Pool Access", "دخول مسبح", "Full day pool access", 40.00),
        ]
        for name_en, name_ar, desc, price in hotel_products:
            db.add(Product(
                id=str(uuid.uuid4()),
                business_id=r3.id,
                name_en=name_en,
                name_ar=name_ar,
                description=desc,
                price=price,
                is_available=True,
                category="accommodation",
            ))

        # ============================================================
        # SECTOR 4 — RETAIL
        # ============================================================
        print("Creating Retail Store...")
        r4 = Business(
            id=str(uuid.uuid4()),
            name_en="Al Madinah Retail Store",
            name_ar="متجر المدينة",
            sector="retail",
            city="Medina",
            whatsapp_phone="+966501111004",
            is_active=True,
            tier="starter",
            owner_id=admin.id,
            access_code="RETAIL001",
        )
        db.add(r4)
        db.flush()

        retail_products = [
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
        ]
        for name_en, name_ar, desc, price in retail_products:
            db.add(Product(
                id=str(uuid.uuid4()),
                business_id=r4.id,
                name_en=name_en,
                name_ar=name_ar,
                description=desc,
                price=price,
                is_available=True,
                category="product",
            ))

        # ============================================================
        # SECTOR 5 — SALON
        # ============================================================
        print("Creating Salon...")
        r5 = Business(
            id=str(uuid.uuid4()),
            name_en="Lujain Beauty Salon",
            name_ar="صالون لجين للتجميل",
            sector="salon",
            city="Khobar",
            whatsapp_phone="+966501111005",
            is_active=True,
            tier="professional",
            owner_id=admin.id,
            access_code="SALON001",
        )
        db.add(r5)
        db.flush()

        salon_products = [
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
        ]
        for name_en, name_ar, desc, price in salon_products:
            db.add(Product(
                id=str(uuid.uuid4()),
                business_id=r5.id,
                name_en=name_en,
                name_ar=name_ar,
                description=desc,
                price=price,
                is_available=True,
                category="service",
            ))

        # ============================================================
        # SECTOR 6 — EDUCATION
        # ============================================================
        print("Creating Education Center...")
        r6 = Business(
            id=str(uuid.uuid4()),
            name_en="Noor Education Center",
            name_ar="مركز نور التعليمي",
            sector="education",
            city="Riyadh",
            whatsapp_phone="+966501111006",
            is_active=True,
            tier="professional",
            owner_id=admin.id,
            access_code="EDU001",
        )
        db.add(r6)
        db.flush()

        education_products = [
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
        ]
        for name_en, name_ar, desc, price in education_products:
            db.add(Product(
                id=str(uuid.uuid4()),
                business_id=r6.id,
                name_en=name_en,
                name_ar=name_ar,
                description=desc,
                price=price,
                is_available=True,
                category="course",
            ))

        # ============================================================
        # CUSTOMERS — shared across businesses
        # ============================================================
        print("Creating customers...")
        customers_data = [
            ("Ahmed Al-Ghamdi", "+966501234001", "Riyadh"),
            ("Mohammed Al-Qahtani", "+966501234002", "Jeddah"),
            ("Abdullah Al-Zahrani", "+966501234003", "Dammam"),
            ("Khalid Al-Harbi", "+966501234004", "Khobar"),
            ("Omar Al-Shehri", "+966501234005", "Medina"),
            ("Fatima Al-Dosari", "+966501234006", "Riyadh"),
            ("Noura Al-Rashidi", "+966501234007", "Jeddah"),
            ("Sara Al-Mutairi", "+966501234008", "Dammam"),
            ("Lama Al-Otaibi", "+966501234009", "Khobar"),
            ("Hessa Al-Saud", "+966501234010", "Riyadh"),
        ]

        businesses = [r1, r2, r3, r4, r5, r6]
        all_customers = []

        for biz in businesses:
            for name, phone, city in customers_data:
                c = Customer(
                    id=str(uuid.uuid4()),
                    business_id=biz.id,
                    name=name,
                    phone=phone,
                    city=city,
                    consent_given=True,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                )
                db.add(c)
                all_customers.append((biz, c))

        db.flush()

        # ============================================================
        # CONVERSATIONS
        # ============================================================
        print("Creating conversations...")
        conv_data = [
            (r1, "Hi, what is your menu today?", "مرحبا، ما هو منيوكم اليوم؟"),
            (r2, "I need to book an appointment", "أريد حجز موعد"),
            (r3, "Do you have rooms available?", "هل عندكم غرف متاحة؟"),
            (r4, "What is the price of dates?", "ما سعر التمر؟"),
            (r5, "I want to book a haircut", "أريد حجز قص شعر"),
            (r6, "Tell me about English courses", "أخبرني عن دورات الإنجليزية"),
        ]

        for biz, msg_en, msg_ar in conv_data:
            conv = Conversation(
                id=str(uuid.uuid4()),
                business_id=biz.id,
                customer_phone="+966501234001",
                customer_name="Ahmed Al-Ghamdi",
                status="active",
                created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
            )
            db.add(conv)
            db.flush()

            db.add(Message(
                id=str(uuid.uuid4()),
                conversation_id=conv.id,
                role="user",
                content=msg_en,
                created_at=datetime.utcnow() - timedelta(minutes=30),
            ))
            db.add(Message(
                id=str(uuid.uuid4()),
                conversation_id=conv.id,
                role="assistant",
                content="Thank you for contacting " + biz.name_en + ". How can I help you today?",
                created_at=datetime.utcnow() - timedelta(minutes=29),
            ))

        db.commit()
        print("")
        print("=" * 50)
        print("  ALL 6 SECTORS SEEDED SUCCESSFULLY")
        print("=" * 50)
        print("  Restaurant:  Al Najma Restaurant")
        print("  Medical:     Al Shifa Medical Center")
        print("  Hotel:       Golden Palm Hotel")
        print("  Retail:      Al Madinah Retail Store")
        print("  Salon:       Lujain Beauty Salon")
        print("  Education:   Noor Education Center")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print("ERROR: " + str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()

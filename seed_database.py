import os
import sys
import uuid
import hashlib
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["USE_SQLITE"] = "false"
os.environ["DATABASE_URL"] = "postgresql+psycopg2://raseel_user:raseel_secure_2026@localhost:5432/raseel_db"

print("=" * 60)
print("  RASEEL Platform - PostgreSQL Database Seeder")
print("=" * 60)

try:
    from app.database import engine, SessionLocal, Base
    from app.models.business import Business
    from app.models.product import Product
    from app.models.customer import Customer
    print("[OK] All imports successful")
except Exception as e:
    print("[ERROR] Import failed:", str(e))
    sys.exit(1)

BUSINESSES = [
    {
        "id": "aded8e65-6dd0-4b25-9442-ba85029e7d72",
        "name_en": "Al-Baik Restaurant",
        "name_ar": "\u0645\u0637\u0639\u0645 \u0627\u0644\u0628\u064a\u0643",
        "sector": "restaurant",
        "city": "Riyadh",
        "access_code": "ALBAIK001",
        "whatsapp_phone": "+966500000001",
    },
    {
        "id": "6f83e915-a0bd-433f-bb7e-b09e7d140abc",
        "name_en": "Safa Medical Center",
        "name_ar": "\u0645\u0631\u0643\u0632 \u0635\u0641\u0627 \u0627\u0644\u0637\u0628\u064a",
        "sector": "medical",
        "city": "Jeddah",
        "access_code": "SAFAMED01",
        "whatsapp_phone": "+966500000002",
    },
    {
        "id": "4f0fa677-1c4d-4c2c-a14d-4a9428db1471",
        "name_en": "Rosh Rayhaan Hotel",
        "name_ar": "\u0641\u0646\u062f\u0642 \u0631\u0648\u0634 \u0631\u064a\u062d\u0627\u0646",
        "sector": "hotel",
        "city": "Riyadh",
        "access_code": "ROSHRAY01",
        "whatsapp_phone": "+966500000003",
    },
    {
        "id": "044d4bff-2645-4d8b-9c63-f9c1a86c2fa2",
        "name_en": "Jarir Bookstore",
        "name_ar": "\u0645\u0643\u062a\u0628\u0629 \u062c\u0631\u064a\u0631",
        "sector": "retail",
        "city": "Riyadh",
        "access_code": "JARIR0001",
        "whatsapp_phone": "+966500000004",
    },
    {
        "id": "835ccefe-94d1-4bf4-b44a-72557ead246f",
        "name_en": "Nabila Beauty Salon",
        "name_ar": "\u0635\u0627\u0644\u0648\u0646 \u0646\u0628\u064a\u0644\u0629",
        "sector": "salon",
        "city": "Jeddah",
        "access_code": "NABILA001",
        "whatsapp_phone": "+966500000005",
    },
    {
        "id": "859dd632-e6e4-4b42-a221-1923a9fb3aa4",
        "name_en": "Riyadh International Academy",
        "name_ar": "\u0623\u0643\u0627\u062f\u064a\u0645\u064a\u0629 \u0627\u0644\u0631\u064a\u0627\u0636 \u0627\u0644\u062f\u0648\u0644\u064a\u0629",
        "sector": "education",
        "city": "Riyadh",
        "access_code": "RIYADAC01",
        "whatsapp_phone": "+966500000006",
    },
]

PRODUCTS = {
    "aded8e65-6dd0-4b25-9442-ba85029e7d72": [
        ("Broasted Chicken", "\u0628\u0631\u0648\u0633\u062a\u062f \u062f\u062c\u0627\u062c", "chicken", 28),
        ("Chicken Fillet", "\u0641\u064a\u0644\u064a\u0647 \u062f\u062c\u0627\u062c", "chicken", 25),
        ("Chicken Nuggets", "\u0646\u0627\u062c\u062a\u0633 \u062f\u062c\u0627\u062c", "chicken", 18),
        ("Chicken Wings", "\u0623\u062c\u0646\u062d\u0629 \u062f\u062c\u0627\u062c", "chicken", 22),
        ("Chicken Shawarma", "\u0634\u0627\u0648\u0631\u0645\u0627 \u062f\u062c\u0627\u062c", "chicken", 15),
        ("Fish Fillet", "\u0641\u064a\u0644\u064a\u0647 \u0633\u0645\u0643", "seafood", 30),
        ("Shrimp Meal", "\u0648\u062c\u0628\u0629 \u0631\u0648\u0628\u064a\u0627\u0646", "seafood", 35),
        ("Grilled Fish", "\u0633\u0645\u0643 \u0645\u0634\u0648\u064a", "seafood", 40),
        ("Beef Burger", "\u0628\u0631\u062c\u0631 \u0644\u062d\u0645", "burgers", 25),
        ("Chicken Burger", "\u0628\u0631\u062c\u0631 \u062f\u062c\u0627\u062c", "burgers", 20),
        ("Double Burger", "\u0628\u0631\u062c\u0631 \u062f\u0628\u0644", "burgers", 32),
        ("French Fries", "\u0628\u0637\u0627\u0637\u0633 \u0645\u0642\u0644\u064a\u0629", "sides", 8),
        ("Coleslaw", "\u0643\u0648\u0644 \u0633\u0644\u0648", "sides", 6),
        ("Hummus", "\u062d\u0645\u0635", "sides", 10),
        ("Garden Salad", "\u0633\u0644\u0637\u0629 \u062e\u0636\u0631\u0627\u0621", "sides", 12),
        ("Pepsi", "\u0628\u064a\u0628\u0633\u064a", "drinks", 5),
        ("Miranda", "\u0645\u064a\u0631\u0646\u062f\u0627", "drinks", 5),
        ("Water", "\u0645\u0627\u0621", "drinks", 3),
        ("Fresh Juice", "\u0639\u0635\u064a\u0631 \u0637\u0627\u0632\u062c", "drinks", 12),
        ("Tea", "\u0634\u0627\u064a", "drinks", 5),
        ("Family Meal", "\u0648\u062c\u0628\u0629 \u0639\u0627\u0626\u0644\u064a\u0629", "meals", 89),
        ("Kids Meal", "\u0648\u062c\u0628\u0629 \u0623\u0637\u0641\u0627\u0644", "meals", 18),
        ("Broasted Meal", "\u0648\u062c\u0628\u0629 \u0628\u0631\u0648\u0633\u062a\u062f", "meals", 32),
        ("Seafood Platter", "\u0637\u0628\u0642 \u0628\u062d\u0631\u064a", "meals", 65),
        ("Combo Meal", "\u0648\u062c\u0628\u0629 \u0643\u0648\u0645\u0628\u0648", "meals", 38),
    ],
    "6f83e915-a0bd-433f-bb7e-b09e7d140abc": [
        ("General Consultation", "\u0627\u0633\u062a\u0634\u0627\u0631\u0629 \u0637\u0628 \u0639\u0627\u0645", "consultations", 150),
        ("Dental Consultation", "\u0627\u0633\u062a\u0634\u0627\u0631\u0629 \u0623\u0633\u0646\u0627\u0646", "consultations", 200),
        ("Dermatology Consultation", "\u0627\u0633\u062a\u0634\u0627\u0631\u0629 \u062c\u0644\u062f\u064a\u0629", "consultations", 250),
        ("Eye Consultation", "\u0627\u0633\u062a\u0634\u0627\u0631\u0629 \u0639\u064a\u0648\u0646", "consultations", 200),
        ("Pediatric Consultation", "\u0627\u0633\u062a\u0634\u0627\u0631\u0629 \u0623\u0637\u0641\u0627\u0644", "consultations", 180),
        ("Complete Blood Test", "\u062a\u062d\u0644\u064a\u0644 \u062f\u0645 \u0634\u0627\u0645\u0644", "tests", 120),
        ("Diabetes Test", "\u062a\u062d\u0644\u064a\u0644 \u0633\u0643\u0631", "tests", 50),
        ("Cholesterol Test", "\u062a\u062d\u0644\u064a\u0644 \u0643\u0648\u0644\u0633\u062a\u0631\u0648\u0644", "tests", 80),
        ("X-Ray", "\u0623\u0634\u0639\u0629 \u0633\u064a\u0646\u064a\u0629", "tests", 150),
        ("Ultrasound", "\u0633\u0648\u0646\u0627\u0631", "tests", 200),
        ("Teeth Cleaning", "\u062a\u0646\u0638\u064a\u0641 \u0623\u0633\u0646\u0627\u0646", "dental", 150),
        ("Dental Filling", "\u062d\u0634\u0648\u0629 \u0623\u0633\u0646\u0627\u0646", "dental", 200),
        ("Tooth Extraction", "\u062e\u0644\u0639 \u0636\u0631\u0633", "dental", 250),
        ("Teeth Whitening", "\u062a\u0628\u064a\u064a\u0636 \u0623\u0633\u0646\u0627\u0646", "dental", 500),
        ("Dental Braces", "\u062a\u0642\u0648\u064a\u0645 \u0623\u0633\u0646\u0627\u0646", "dental", 5000),
        ("Medical Facial", "\u062a\u0646\u0638\u064a\u0641 \u0628\u0634\u0631\u0629 \u0637\u0628\u064a", "skincare", 300),
        ("Laser Treatment", "\u0639\u0644\u0627\u062c \u0628\u0627\u0644\u0644\u064a\u0632\u0631", "skincare", 800),
        ("Botox", "\u0628\u0648\u062a\u0648\u0643\u0633", "skincare", 1200),
        ("Filler", "\u0641\u064a\u0644\u0631", "skincare", 1500),
        ("Chemical Peel", "\u062a\u0642\u0634\u064a\u0631 \u0643\u064a\u0645\u064a\u0627\u0626\u064a", "skincare", 400),
        ("Full Checkup", "\u0641\u062d\u0635 \u0634\u0627\u0645\u0644", "packages", 500),
        ("Family Package", "\u0628\u0627\u0642\u0629 \u0627\u0644\u0623\u0633\u0631\u0629", "packages", 1200),
        ("Pre-Marriage Test", "\u0641\u062d\u0635 \u0645\u0627 \u0642\u0628\u0644 \u0627\u0644\u0632\u0648\u0627\u062c", "packages", 800),
        ("Employee Checkup", "\u0641\u062d\u0635 \u0627\u0644\u0639\u0645\u0627\u0644\u0629", "packages", 350),
        ("Women Health Package", "\u0628\u0627\u0642\u0629 \u0635\u062d\u0629 \u0627\u0644\u0645\u0631\u0623\u0629", "packages", 900),
    ],
    "4f0fa677-1c4d-4c2c-a14d-4a9428db1471": [
        ("Standard Room", "\u063a\u0631\u0641\u0629 \u0639\u0627\u062f\u064a\u0629", "rooms", 450),
        ("Deluxe Room", "\u063a\u0631\u0641\u0629 \u062f\u064a\u0644\u0648\u0643\u0633", "rooms", 750),
        ("Family Suite", "\u062c\u0646\u0627\u062d \u0639\u0627\u0626\u0644\u064a", "rooms", 1200),
        ("Presidential Suite", "\u062c\u0646\u0627\u062d \u0631\u0626\u0627\u0633\u064a", "rooms", 3000),
        ("Executive Room", "\u063a\u0631\u0641\u0629 \u062a\u0646\u0641\u064a\u0630\u064a\u0629", "rooms", 950),
        ("Swedish Massage", "\u0645\u0633\u0627\u062c \u0633\u0648\u064a\u062f\u064a", "spa", 250),
        ("Thai Massage", "\u0645\u0633\u0627\u062c \u062a\u0627\u064a\u0644\u0627\u0646\u062f\u064a", "spa", 300),
        ("Hot Stone Massage", "\u0645\u0633\u0627\u062c \u062d\u062c\u0631 \u0633\u0627\u062e\u0646", "spa", 350),
        ("Turkish Bath", "\u062d\u0645\u0627\u0645 \u062a\u0631\u0643\u064a", "spa", 200),
        ("Moroccan Bath", "\u062d\u0645\u0627\u0645 \u0645\u063a\u0631\u0628\u064a", "spa", 280),
        ("Jacuzzi Session", "\u062c\u0644\u0633\u0629 \u062c\u0627\u0643\u0648\u0632\u064a", "spa", 150),
        ("Breakfast Buffet", "\u0641\u0637\u0648\u0631 \u0628\u0648\u0641\u064a\u0647", "dining", 95),
        ("Lunch Buffet", "\u063a\u062f\u0627\u0621 \u0628\u0648\u0641\u064a\u0647", "dining", 150),
        ("Dinner Buffet", "\u0639\u0634\u0627\u0621 \u0628\u0648\u0641\u064a\u0647", "dining", 180),
        ("Room Service", "\u062e\u062f\u0645\u0629 \u0627\u0644\u063a\u0631\u0641", "dining", 50),
        ("Laundry Service", "\u063a\u0633\u064a\u0644 \u0645\u0644\u0627\u0628\u0633", "services", 80),
        ("Airport Transfer", "\u0646\u0642\u0644 \u0645\u0646 \u0627\u0644\u0645\u0637\u0627\u0631", "services", 150),
        ("Limousine", "\u0644\u064a\u0645\u0648\u0632\u064a\u0646", "services", 500),
        ("Premium WiFi", "\u0648\u0627\u064a \u0641\u0627\u064a \u0645\u0645\u064a\u0632", "services", 50),
        ("Meeting Room", "\u0642\u0627\u0639\u0629 \u0627\u062c\u062a\u0645\u0627\u0639\u0627\u062a", "events", 1500),
        ("Conference Hall", "\u0642\u0627\u0639\u0629 \u0645\u0624\u062a\u0645\u0631\u0627\u062a", "events", 5000),
        ("Wedding Hall", "\u0642\u0627\u0639\u0629 \u0623\u0641\u0631\u0627\u062d", "events", 15000),
        ("Birthday Setup", "\u062a\u062c\u0647\u064a\u0632 \u0639\u064a\u062f \u0645\u064a\u0644\u0627\u062f", "events", 2000),
        ("Business Center", "\u0645\u0631\u0643\u0632 \u0623\u0639\u0645\u0627\u0644", "events", 300),
    ],
    "044d4bff-2645-4d8b-9c63-f9c1a86c2fa2": [
        ("iPhone 15 Pro", "\u0622\u064a\u0641\u0648\u0646 15 \u0628\u0631\u0648", "electronics", 4999),
        ("Samsung S24", "\u0633\u0627\u0645\u0633\u0648\u0646\u062c S24", "electronics", 3999),
        ("iPad Air", "\u0622\u064a\u0628\u0627\u062f \u0625\u064a\u0631", "electronics", 2499),
        ("MacBook Air", "\u0645\u0627\u0643 \u0628\u0648\u0643 \u0625\u064a\u0631", "electronics", 4299),
        ("AirPods Pro", "\u0625\u064a\u0631\u0628\u0648\u062f\u0632 \u0628\u0631\u0648", "electronics", 999),
        ("Apple Watch", "\u0633\u0627\u0639\u0629 \u0623\u0628\u0644", "electronics", 1699),
        ("PlayStation 5", "\u0628\u0644\u0627\u064a\u0633\u062a\u064a\u0634\u0646 5", "gaming", 2099),
        ("Xbox Series X", "\u0625\u0643\u0633 \u0628\u0648\u0643\u0633 \u0633\u064a\u0631\u064a\u0632 \u0625\u0643\u0633", "gaming", 1999),
        ("Nintendo Switch", "\u0646\u064a\u0646\u062a\u0646\u062f\u0648 \u0633\u0648\u064a\u062a\u0634", "gaming", 1399),
        ("Gaming Controller", "\u064a\u062f \u062a\u062d\u0643\u0645", "gaming", 279),
        ("PSN Card 100", "\u0628\u0637\u0627\u0642\u0629 PSN 100", "gaming", 100),
        ("Arabic Novel", "\u0631\u0648\u0627\u064a\u0629 \u0639\u0631\u0628\u064a\u0629", "books", 45),
        ("Children Book", "\u0643\u062a\u0627\u0628 \u0623\u0637\u0641\u0627\u0644", "books", 35),
        ("Educational Book", "\u0643\u062a\u0627\u0628 \u062a\u0639\u0644\u064a\u0645\u064a", "books", 65),
        ("Holy Quran", "\u0645\u0635\u062d\u0641 \u0634\u0631\u064a\u0641", "books", 50),
        ("Cookbook", "\u0643\u062a\u0627\u0628 \u0637\u0628\u062e", "books", 55),
        ("Printer", "\u0637\u0627\u0628\u0639\u0629", "office", 599),
        ("Ink Cartridge", "\u062d\u0628\u0631 \u0637\u0627\u0628\u0639\u0629", "office", 120),
        ("A4 Paper Box", "\u0643\u0631\u062a\u0648\u0646 \u0648\u0631\u0642 A4", "office", 85),
        ("Pen Set", "\u0637\u0642\u0645 \u0623\u0642\u0644\u0627\u0645", "office", 45),
        ("Phone Case", "\u062c\u0631\u0627\u0628 \u062c\u0648\u0627\u0644", "accessories", 79),
        ("Fast Charger", "\u0634\u0627\u062d\u0646 \u0633\u0631\u064a\u0639", "accessories", 149),
        ("Power Bank", "\u0628\u0627\u0648\u0631 \u0628\u0627\u0646\u0643", "accessories", 199),
    ],
    "835ccefe-94d1-4bf4-b44a-72557ead246f": [
        ("Haircut", "\u0642\u0635 \u0634\u0639\u0631", "hair", 150),
        ("Hair Color", "\u0635\u0628\u063a\u0629 \u0634\u0639\u0631", "hair", 300),
        ("Blow Dry", "\u0633\u0634\u0648\u0627\u0631", "hair", 100),
        ("Protein Treatment", "\u0639\u0644\u0627\u062c \u0628\u0631\u0648\u062a\u064a\u0646", "hair", 800),
        ("Keratin Treatment", "\u0639\u0644\u0627\u062c \u0643\u064a\u0631\u0627\u062a\u064a\u0646", "hair", 1000),
        ("Bridal Hair", "\u062a\u0633\u0631\u064a\u062d\u0629 \u0639\u0631\u0648\u0633", "hair", 500),
        ("Henna", "\u062d\u0646\u0627\u0621", "hair", 200),
        ("Facial Cleansing", "\u062a\u0646\u0638\u064a\u0641 \u0628\u0634\u0631\u0629", "skincare", 200),
        ("Skin Peeling", "\u062a\u0642\u0634\u064a\u0631 \u0628\u0634\u0631\u0629", "skincare", 250),
        ("Gold Mask", "\u0645\u0627\u0633\u0643 \u0630\u0647\u0628\u064a", "skincare", 350),
        ("HydraFacial", "\u0647\u064a\u062f\u0631\u0627\u0641\u064a\u0634\u0644", "skincare", 400),
        ("Microneedling", "\u0645\u064a\u0643\u0631\u0648\u0646\u064a\u062f\u0644\u0646\u062c", "skincare", 500),
        ("Manicure", "\u0645\u0627\u0646\u064a\u0643\u064a\u0631", "nails", 80),
        ("Pedicure", "\u0628\u062f\u064a\u0643\u064a\u0631", "nails", 100),
        ("Gel Nails", "\u0623\u0638\u0627\u0641\u0631 \u062c\u0644", "nails", 150),
        ("Nail Art", "\u0641\u0646 \u0627\u0644\u0623\u0638\u0627\u0641\u0631", "nails", 200),
        ("Evening Makeup", "\u0645\u064a\u0643\u0627\u0628 \u0633\u0647\u0631\u0629", "makeup", 300),
        ("Bridal Makeup", "\u0645\u064a\u0643\u0627\u0628 \u0639\u0631\u0648\u0633", "makeup", 800),
        ("Light Makeup", "\u0645\u064a\u0643\u0627\u0628 \u062e\u0641\u064a\u0641", "makeup", 200),
        ("Lashes", "\u0631\u0645\u0648\u0634", "makeup", 150),
        ("Bridal Package", "\u0628\u0627\u0642\u0629 \u0627\u0644\u0639\u0631\u0648\u0633 \u0627\u0644\u0634\u0627\u0645\u0644\u0629", "packages", 2500),
        ("Relaxation Package", "\u0628\u0627\u0642\u0629 \u0627\u0644\u0627\u0633\u062a\u0631\u062e\u0627\u0621", "packages", 600),
        ("Renewal Package", "\u0628\u0627\u0642\u0629 \u0627\u0644\u062a\u062c\u062f\u064a\u062f", "packages", 900),
        ("Monthly Membership", "\u0639\u0636\u0648\u064a\u0629 \u0634\u0647\u0631\u064a\u0629", "packages", 1500),
    ],
    "859dd632-e6e4-4b42-a221-1923a9fb3aa4": [
        ("English Language", "\u0627\u0644\u0644\u063a\u0629 \u0627\u0644\u0625\u0646\u062c\u0644\u064a\u0632\u064a\u0629", "languages", 1500),
        ("French Language", "\u0627\u0644\u0644\u063a\u0629 \u0627\u0644\u0641\u0631\u0646\u0633\u064a\u0629", "languages", 1800),
        ("German Language", "\u0627\u0644\u0644\u063a\u0629 \u0627\u0644\u0623\u0644\u0645\u0627\u0646\u064a\u0629", "languages", 1800),
        ("IELTS Prep", "\u062a\u062d\u0636\u064a\u0631 \u0622\u064a\u0644\u062a\u0633", "languages", 2500),
        ("TOEFL Prep", "\u062a\u062d\u0636\u064a\u0631 \u062a\u0648\u0641\u0644", "languages", 2200),
        ("Python Programming", "\u0628\u0631\u0645\u062c\u0629 \u0628\u0627\u064a\u062b\u0648\u0646", "technology", 3000),
        ("Web Development", "\u062a\u0637\u0648\u064a\u0631 \u0645\u0648\u0627\u0642\u0639", "technology", 3500),
        ("Mobile Apps", "\u062a\u0637\u0648\u064a\u0631 \u062a\u0637\u0628\u064a\u0642\u0627\u062a", "technology", 4000),
        ("Cybersecurity", "\u0623\u0645\u0646 \u0633\u064a\u0628\u0631\u0627\u0646\u064a", "technology", 4500),
        ("Data Analysis", "\u062a\u062d\u0644\u064a\u0644 \u0628\u064a\u0627\u0646\u0627\u062a", "technology", 3500),
        ("AI Course", "\u062f\u0648\u0631\u0629 \u0630\u0643\u0627\u0621 \u0627\u0635\u0637\u0646\u0627\u0639\u064a", "technology", 5000),
        ("Kids Math", "\u0631\u064a\u0627\u0636\u064a\u0627\u062a \u0623\u0637\u0641\u0627\u0644", "kids", 800),
        ("Kids Science", "\u0639\u0644\u0648\u0645 \u0623\u0637\u0641\u0627\u0644", "kids", 800),
        ("Kids English", "\u0625\u0646\u062c\u0644\u064a\u0632\u064a \u0623\u0637\u0641\u0627\u0644", "kids", 1000),
        ("Kids Robotics", "\u0631\u0648\u0628\u0648\u062a\u064a\u0643\u0633 \u0623\u0637\u0641\u0627\u0644", "kids", 1200),
        ("Art and Drawing", "\u0641\u0646 \u0648\u0631\u0633\u0645", "kids", 600),
        ("Project Management", "\u0625\u062f\u0627\u0631\u0629 \u0645\u0634\u0627\u0631\u064a\u0639", "business", 2500),
        ("Digital Marketing", "\u062a\u0633\u0648\u064a\u0642 \u0631\u0642\u0645\u064a", "business", 2000),
        ("Accounting", "\u0645\u062d\u0627\u0633\u0628\u0629", "business", 2200),
        ("Entrepreneurship", "\u0631\u064a\u0627\u062f\u0629 \u0623\u0639\u0645\u0627\u0644", "business", 1800),
        ("IT Diploma", "\u062f\u0628\u0644\u0648\u0645 \u062a\u0642\u0646\u064a\u0629 \u0645\u0639\u0644\u0648\u0645\u0627\u062a", "certificates", 8000),
        ("PMP Certificate", "\u0634\u0647\u0627\u062f\u0629 PMP", "certificates", 4500),
        ("CPA Prep", "\u062a\u062d\u0636\u064a\u0631 CPA", "certificates", 5000),
        ("HR Diploma", "\u062f\u0628\u0644\u0648\u0645 \u0645\u0648\u0627\u0631\u062f \u0628\u0634\u0631\u064a\u0629", "certificates", 6000),
    ],
}

CUSTOMERS = [
    ("aded8e65-6dd0-4b25-9442-ba85029e7d72", "Ahmed Al-Rahman", "+966501234567", "ar"),
    ("aded8e65-6dd0-4b25-9442-ba85029e7d72", "Sara Mohammed", "+966502345678", "ar"),
    ("6f83e915-a0bd-433f-bb7e-b09e7d140abc", "Fatima Hassan", "+966503456789", "ar"),
    ("6f83e915-a0bd-433f-bb7e-b09e7d140abc", "Omar Abdullah", "+966504567890", "ar"),
    ("4f0fa677-1c4d-4c2c-a14d-4a9428db1471", "Khalid Al-Saud", "+966505678901", "ar"),
    ("4f0fa677-1c4d-4c2c-a14d-4a9428db1471", "Nora Al-Qahtani", "+966506789012", "ar"),
    ("044d4bff-2645-4d8b-9c63-f9c1a86c2fa2", "Mohammed Ali", "+966507890123", "en"),
    ("835ccefe-94d1-4bf4-b44a-72557ead246f", "Layla Ibrahim", "+966508901234", "ar"),
    ("835ccefe-94d1-4bf4-b44a-72557ead246f", "Reem Al-Harbi", "+966509012345", "ar"),
    ("859dd632-e6e4-4b42-a221-1923a9fb3aa4", "Yousef Ahmad", "+966500123456", "en"),
]


def seed_database():
    print("")
    print("[1/4] Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("  Tables created!")

    db = SessionLocal()
    try:
        existing = db.query(Business).first()
        if existing and "--reset" not in sys.argv:
            count_b = db.query(Business).count()
            count_p = db.query(Product).count()
            count_c = db.query(Customer).count()
            print("")
            print("  Database already has data:")
            print("    Businesses:", count_b)
            print("    Products:", count_p)
            print("    Customers:", count_c)
            print("")
            print("  To re-seed, run: python seed_database.py --reset")
            return

        if "--reset" in sys.argv:
            print("")
            print("[!] Resetting database...")
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            print("  Tables recreated!")

        print("")
        print("[2/4] Seeding 6 businesses...")
        for biz in BUSINESSES:
            business = Business(
                id=biz["id"],
                name_en=biz["name_en"],
                name_ar=biz["name_ar"],
                sector=biz["sector"],
                city=biz["city"],
                access_code=biz["access_code"],
                whatsapp_phone=biz["whatsapp_phone"],
                is_active=True,
            )
            db.add(business)
        db.flush()
        print("  6 businesses created!")

        print("")
        print("[3/4] Seeding products...")
        total_products = 0
        for business_id, products in PRODUCTS.items():
            for name_en, name_ar, category, price in products:
                product = Product(
                    id=str(uuid.uuid4()),
                    business_id=business_id,
                    name_en=name_en,
                    name_ar=name_ar,
                    category=category,
                    price=float(price),
                    is_available=True,
                )
                db.add(product)
                total_products += 1
            db.flush()
        print("  " + str(total_products) + " products created!")

        print("")
        print("[4/4] Seeding customers...")
        for biz_id, name, phone, lang in CUSTOMERS:
            phone_hash = hashlib.sha256(phone.encode()).hexdigest()
            customer = Customer(
                id=str(uuid.uuid4()),
                business_id=biz_id,
                name_encrypted=name,
                phone_hash=phone_hash,
                phone_encrypted=phone,
                preferred_language=lang,
                status="active",
            )
            db.add(customer)
        db.flush()
        print("  10 customers created!")

        db.commit()

        print("")
        print("=" * 60)
        print("  SEEDING COMPLETE!")
        print("=" * 60)
        print("  Businesses: 6")
        print("  Products:   " + str(total_products))
        print("  Customers:  10")
        print("")

    except Exception as e:
        db.rollback()
        print("")
        print("[ERROR] Seeding failed:", str(e))
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()


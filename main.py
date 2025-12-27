import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import datetime

# --- إعدادات قاعدة البيانات (Supabase) ---
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'local_backup.db')}"
else:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- الجداول ---
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    icon = Column(String)
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="products")
    prices = relationship("ProductPrice", back_populates="product", cascade="all, delete-orphan")

class ProductPrice(Base):
    __tablename__ = "product_prices"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    service_type = Column(String)
    price = Column(Float)
    product = relationship("Product", back_populates="prices")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    phone_number = Column(String, unique=True, index=True)
    password = Column(String)
    orders = relationship("Order", back_populates="user")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float)
    items_summary = Column(String)
    status = Column(String, default="جديد")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User", back_populates="orders")

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- 🔥 دالة التحديث (تجبر التحديث دائماً) 🔥 ---
def seed_database():
    db = SessionLocal()
    try:
        print("🧹 جاري تنظيف القائمة القديمة لتحديث الأسعار...")
        # 1. حذف الأسعار والمنتجات والأقسام القديمة (لضمان التحديث)
        db.query(ProductPrice).delete()
        db.query(Product).delete()
        db.query(Category).delete()
        db.commit()
        
        print("⚡ جاري كتابة القائمة الجديدة...")
        # 2. البيانات الجديدة (التي عدلتها أنت)
        data_structure = [
            {
                "category": "معاطف وسترات",
                "icon": "body",
                "products": [
                    {"name": "معطف (كوت) قماش", "prices": {"wash": 2500, "iron": 2500, "both": 5000}},
                    {"name": "معطف (كوت) جلد", "prices": {"wash": 2500, "iron": 2500, "both": 5000}},
                    {"name": "سترة رسمية", "prices": {"wash": 2500, "iron": 2500, "both": 5000}},
                    {"name": "معطف (كوت) طبي", "prices": {"wash": 2500, "iron": 2500, "both": 5000}},
                ]
            },
            {
                "category": "دشاديش",
                "icon": "man",
                "products": [
                    {"name": "دشداشة صيفية", "prices": {"wash": 2000, "iron": 2000, "both": 4000}},
                    {"name": "دشداشة شتوية (جوخ)", "prices": {"wash": 2000, "iron": 2000, "both": 4000}},
                    {"name": "فروة", "prices": {"wash": 5000, "iron": 5000, "both": 10000}},
                    {"name": "غترة (شماغ)", "prices": {"wash": 1000, "iron": 1000, "both": 2000}},
                    {"name": "يلگ", "prices": {"wash": 2000, "iron": 2000, "both": 3000}},
                ]
            },
            {
                "category": "بدلات",
                "icon": "briefcase",
                "products": [
                    {"name": "بدلة رسمية", "prices": {"wash": 5000, "iron": 5000, "both": 10000}},
                    {"name": "بدلة عسكرية", "prices": {"wash": 2000, "iron": 3000, "both": 5000}},
                ]
            },
            {
                "category": "فساتين",
                "icon": "woman",
                "products": [
                    {"name": "فستان اعراس", "prices": {"wash": 7500, "iron": 7500, "both": 15000}},
                    {"name": "فستان عادي", "prices": {"wash": 5000, "iron": 5000, "both": 10000}},
                    {"name": "عباة (جبة)", "prices": {"wash": 2500, "iron": 2500, "both": 5000}},
                ]
            },
            {
                "category": "أغطية ومفروشات",
                "icon": "bed",
                "products": [
                    {"name": "بطانية", "prices": {"wash": 5000, "iron": 0, "both": 5000}},
                    {"name": "شرشف نفر", "prices": {"wash": 3000, "iron": 0, "both": 3000}},
                    {"name": "شرشف نفرين", "prices": {"wash": 5000, "iron": 0, "both": 5000}},
                    {"name": "ستارة (بردة) مع تول", "prices": {"wash": 10000, "iron": 0, "both": 10000}},
                    {"name": "ستارة (بردة) بدون تول", "prices": {"wash": 5000, "iron": 0, "both": 5000}},
                    {"name": "الكاربت (زولية) م²", "prices": {"wash": 2000, "iron": 0, "both": 2000}},
                ]
            },
            {
                "category": "ملابس يومية",
                "icon": "shirt",
                "products": [
                    {"name": "قميص", "prices": {"wash": 1000, "iron": 1000, "both": 2000}},
                    {"name": "بنطال", "prices": {"wash": 1000, "iron": 1000, "both": 2000}},
                    {"name": "تيشيرت", "prices": {"wash": 1000, "iron": 1000, "both": 2000}},
                    {"name": "تراك", "prices": {"wash": 2000, "iron": 2000, "both": 4000}},
                    {"name": "تنورة", "prices": {"wash": 2500, "iron": 2500, "both": 5000}},
                    {"name": "جاكيت (قمصلة)", "prices": {"wash": 2500, "iron": 2500, "both": 5000}},
                    {"name": "شال", "prices": {"wash": 500, "iron": 500, "both": 1000}},
                ]
            },
            {
                "category": "قطع متفرقة",
                "icon": "basket",
                "products": [
                    {"name": "ملابس داخلية", "prices": {"wash": 500, "iron": 0, "both": 500}},
                    {"name": "حذاء", "prices": {"wash": 2000, "iron": 0, "both": 2000}},
                ]
            }
        ]

        for section in data_structure:
            cat_db = Category(name=section["category"], icon=section["icon"])
            db.add(cat_db)
            db.commit()
            db.refresh(cat_db)
            
            for prod in section["products"]:
                prod_db = Product(name=prod["name"], category_id=cat_db.id)
                db.add(prod_db)
                db.commit()
                db.refresh(prod_db)
                
                for s_type, price in prod["prices"].items():
                    db.add(ProductPrice(product_id=prod_db.id, service_type=s_type, price=price))
        
        db.commit()
        print("✅ تم تحديث الأسعار والمنتجات بنجاح!")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

seed_database()

# --- Pydantic Models ---
class UserRegister(BaseModel):
    full_name: str
    phone: str
    password: str

class UserLogin(BaseModel):
    phone: str
    password: str

class OrderCreate(BaseModel):
    user_phone: str
    total_amount: float
    items_summary: str

class OrderStatus(BaseModel):
    status: str

# --- Endpoints ---

@app.get("/categories-v2")
def get_categories_v2(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    results = []
    for cat in categories:
        products_list = []
        for prod in cat.products:
            prices_dict = {}
            for p in prod.prices:
                prices_dict[p.service_type] = p.price
            
            products_list.append({
                "id": prod.id,
                "name": prod.name,
                "prices": prices_dict
            })
        
        results.append({
            "id": cat.id,
            "name": cat.name,
            "icon": cat.icon,
            "products": products_list
        })
    return results

@app.post("/register")
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.phone_number == user.phone).first()
    if existing_user: return {"status": "exists"}
    new_user = User(full_name=user.full_name, phone_number=user.phone, password=user.password)
    db.add(new_user)
    db.commit()
    return {"status": "success", "user_name": new_user.full_name}

@app.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.phone_number == user.phone).first()
    if not db_user or str(db_user.password) != str(user.password):
        return {"status": "failed"}
    return {"status": "success", "user_name": db_user.full_name}

@app.get("/all-orders")
def get_all_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.id.desc()).all()
    results = []
    for o in orders:
        user_name = o.user.full_name if o.user else "مجهول"
        user_phone = o.user.phone_number if o.user else "---"
        results.append({
            "id": o.id,
            "amount": o.total_amount,
            "summary": o.items_summary,
            "status": o.status,
            "user_name": user_name,
            "user_phone": user_phone
        })
    return results

@app.post("/create-order")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.phone_number.contains(order.user_phone[-10:])).first()
    if not db_user: return {"status": "failed"}
    new_order = Order(user_id=db_user.id, total_amount=order.total_amount, items_summary=order.items_summary, status="جديد")
    db.add(new_order)
    db.commit()
    return {"status": "success", "order_id": new_order.id}

@app.put("/update-order/{order_id}")
def update_order(order_id: int, order: OrderStatus, db: Session = Depends(get_db)):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if db_order:
        db_order.status = order.status
        db.commit()
    return {"status": "success"}

@app.delete("/delete-order/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    db.query(Order).filter(Order.id == order_id).delete()
    db.commit()
    return {"status": "success"}

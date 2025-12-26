# main.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, User, Order, Category, ItemPrice
from typing import List
from fastapi.middleware.cors import CORSMiddleware # <--- 1. استدعاء المكتبة

SQLALCHEMY_DATABASE_URL = "sqlite:///./drayclean.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- 2. إضافة إعدادات السماح (CORS) ---
# هذا الكود يسمح لأي جهاز (موبايل أو ويب) بالاتصال بالسيرفر
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # السماح للجميع
    allow_credentials=True,
    allow_methods=["*"],     # السماح بكل العمليات (GET, POST...)
    allow_headers=["*"],     # السماح بكل الهيدرز
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- دالة تعبئة البيانات تلقائياً (تعمل عند بدء التشغيل) ---
def seed_database():
    db = SessionLocal()
    if db.query(Category).count() == 0:
        print("⚡ قاعدة البيانات فارغة، جاري تعبئة البيانات الافتراضية...")
        
        # قائمة البيانات الأولية
        initial_data = [
            {"name": "قميص", "icon": "shirt", "prices": {"wash": 500, "iron": 500, "both": 750}},
            {"name": "بنطال", "icon": "layers", "prices": {"wash": 750, "iron": 750, "both": 1250}},
            {"name": "بدلة", "icon": "briefcase", "prices": {"wash": 2000, "iron": 2000, "both": 3500}},
            {"name": "فستان", "icon": "woman", "prices": {"wash": 3000, "iron": 3000, "both": 5000}},
            {"name": "بطانية", "icon": "bed", "prices": {"wash": 4000, "iron": 0, "both": 4000}},
            {"name": "معطف", "icon": "body", "prices": {"wash": 2500, "iron": 1500, "both": 3500}},
        ]

        for item in initial_data:
            # 1. إنشاء الصنف
            cat = Category(name=item["name"], icon=item["icon"])
            db.add(cat)
            db.commit() # للحصول على الـ ID
            db.refresh(cat)
            
            # 2. إنشاء الأسعار للصنف
            for s_type, price in item["prices"].items():
                p = ItemPrice(category_id=cat.id, service_type=s_type, price=price)
                db.add(p)
        
        db.commit()
        print("✅ تم تعبئة البيانات بنجاح!")
    db.close()

# استدعاء الدالة عند تشغيل الملف
seed_database()

# --- الموديلات ---
class UserRegister(BaseModel):
    full_name: str
    phone: str
    password: str

class UserLogin(BaseModel):
    phone: str
    password: str

# أضف هذا الكلاس مع باقي الكلاسات في الأعلى
class OrderCreate(BaseModel):
    user_phone: str
    total_amount: float
    items_summary: str


class OrderStatus(BaseModel):
    status: str
# --- Endpoints ---

@app.get("/categories") # <--- هذا الرابط الجديد الذي سيستخدمه التطبيق
def get_categories(db: Session = Depends(get_db)):
    # 1. جلب كل الأصناف
    categories_db = db.query(Category).all()
    
    results = []
    for cat in categories_db:
        # 2. تحويل الأسعار من جدول إلى شكل JSON بسيط
        # نريد تحويلها لتصبح مثل: { 'wash': 500, 'iron': 500 }
        prices_dict = {}
        for p in cat.prices:
            prices_dict[p.service_type] = p.price
            
        # 3. بناء الشكل النهائي
        results.append({
            "id": str(cat.id),
            "name": cat.name,
            "icon": cat.icon,
            "prices": prices_dict
        })
        
    return results

@app.post("/register")
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.phone_number == user.phone).first()
    if existing_user: return {"status": "exists", "message": "المستخدم موجود"}
    
    new_user = User(full_name=user.full_name, phone_number=user.phone, password=user.password)
    db.add(new_user)
    db.commit()
    return {"status": "success", "message": "تم التسجيل"}

@app.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.phone_number == user.phone).first()
    if not db_user or str(db_user.password) != str(user.password):
        return {"status": "failed", "message": "بيانات خاطئة"}
    return {"status": "success", "user_name": db_user.full_name, "message": "تم الدخول"}

@app.get("/all-orders")
def get_all_orders(db: Session = Depends(get_db)):
    # جلب كل الطلبات وترتيبها من الأحدث للأقدم
    orders = db.query(Order).order_by(Order.id.desc()).all()
    
    results = []
    for o in orders:
        # نحتاج لاسم الزبون ورقمه، وهما موجودان في جدول User المرتبط
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
    # 1. البحث عن المستخدم صاحب الرقم
    # ملاحظة: نستخدم contains للبحث المرن في حال اختلاف صيغة الرقم
    # أو نبحث بالمطابقة المباشرة إذا كنت وحدت الأرقام
    db_user = db.query(User).filter(User.phone_number.contains(order.user_phone[-10:])).first()
    
    if not db_user:
        return {"status": "failed", "message": "المستخدم غير موجود"}
    
    # 2. إنشاء الطلب
    new_order = Order(
        user_id=db_user.id,
        total_amount=order.total_amount,
        items_summary=order.items_summary,
        status="جديد"
    )
    
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    return {"status": "success", "order_id": new_order.id}

@app.put("/update-order/{order_id}")
def update_order_status(order_id: int, order: OrderStatus, db: Session = Depends(get_db)):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        return {"status": "failed", "message": "الطلب غير موجود"}
    
    db_order.status = order.status
    db.commit()
    return {"status": "success"}
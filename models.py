# models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    full_name = Column(String)
    password = Column(String)
    is_active = Column(Boolean, default=True)
    
    # علاقة عكسية: المستخدم لديه طلبات كثيرة
    orders = relationship("Order", back_populates="user")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    icon = Column(String)
    prices = relationship("ItemPrice", back_populates="category")

class ItemPrice(Base):
    __tablename__ = "item_prices"
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    service_type = Column(String)
    price = Column(Float)
    category = relationship("Category", back_populates="prices")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float)
    items_summary = Column(String) # ملخص نصي للطلب
    status = Column(String, default="new") # new, completed
    
    # ربط الطلب بالمستخدم لنعرف من صاحب الطلب
    user = relationship("User", back_populates="orders")
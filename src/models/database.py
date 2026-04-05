from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import config
import os

# Создаем базовый класс для моделей
Base = declarative_base()

# Убеждаемся, что директория data существует
os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)

# Создаем строку подключения
DATABASE_URL = f"sqlite:///{config.DB_PATH}"

# Создаем engine и sessionmaker
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    """Модель пользователя в базе данных"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    subscription_key = Column(String, nullable=True)
    subscription_id = Column(Integer, nullable=True)
    subscription_active = Column(Boolean, default=False)
    subscription_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class Payment(Base):
    """Модель платежа"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, index=True)
    amount = Column(Float)
    months = Column(Integer)
    status = Column(String, default='pending')  # pending, completed, cancelled
    payment_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Payment(telegram_id={self.telegram_id}, amount={self.amount})>"


class AdminAction(Base):
    """Логирование действий администраторов"""
    __tablename__ = "admin_actions"
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, index=True)
    action = Column(String)
    target_user_id = Column(Integer, nullable=True)
    details = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Создаем все таблицы
def init_db():
    """Инициализация базы данных"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Получить сессию базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.product import Product

engine = create_engine("sqlite:///./users.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

product1 = Product(title="Ноутбук", price=999.99, count=5)
product2 = Product(title="Мышка", price=25.50, count=50)

db.add(product1)
db.add(product2)
db.commit()
print("Записи успешно добавлены в базу данных.")
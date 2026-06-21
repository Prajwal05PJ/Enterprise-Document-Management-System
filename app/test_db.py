from app.database.database import engine

try:
    with engine.connect() as conn:
        print("✅ Database connected successfully!")
except Exception as e:
    print(e)
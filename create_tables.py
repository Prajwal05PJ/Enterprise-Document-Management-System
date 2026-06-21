from app.database.database import engine
from app.database.base import Base

Base.metadata.create_all(bind=engine)

print("✅ Tables created successfully!")
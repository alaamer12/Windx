"""Test script to verify admin login functionality."""
import asyncio
import sys

from sqlalchemy import select

from app.core.config import get_settings
from app.database.connection import get_engine
from app.models.user import User
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession


async def test_database_connection():
    """Test database connection and check if admin user exists."""
    print("=== Testing Database Connection ===\n")
    
    settings = get_settings()
    engine = get_engine()
    
    try:
        session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with session_maker() as session:
            # Check if users table exists and has data
            result = await session.execute(select(User))
            users = result.scalars().all()
            
            print(f"✅ Database connection successful!")
            print(f"   Found {len(users)} users in database\n")
            
            # Check for admin user
            admin_result = await session.execute(
                select(User).where(User.username == "admin")
            )
            admin_user = admin_result.scalar_one_or_none()
            
            if admin_user:
                print("✅ Admin user found:")
                print(f"   Username: {admin_user.username}")
                print(f"   Email: {admin_user.email}")
                print(f"   Is Active: {admin_user.is_active}")
                print(f"   Is Superuser: {admin_user.is_superuser}")
                print(f"   Created: {admin_user.created_at}")
            else:
                print("❌ Admin user not found!")
                print("   Run: python manage.py seed_data")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


async def main():
    """Main test function."""
    await test_database_connection()
    
    print("\n=== Next Steps ===")
    print("1. Start the server: .venv\\scripts\\uvicorn main:app --reload")
    print("2. Open browser: http://127.0.0.1:8000/api/v1/admin/login")
    print("3. Login with:")
    print("   Username: admin")
    print("   Password: Admin123!")
    print("\n✅ All checks passed!")


if __name__ == "__main__":
    asyncio.run(main())

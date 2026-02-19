"""
Script to create an admin user
Run this after setting up the database
"""

import sys
import os
import asyncio
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.database import db_client
from src.models import User
from src.api.auth import hash_password
import uuid


async def create_admin_user():
    """Create the admin user"""
    email = "admin@cyberxltr.com"
    password = "CyberXLTR#01"  # Change this immediately after first login
    
    print(f"Creating admin user: {email}")
    
    async with db_client.get_session() as session:
        try:
            # Check if admin already exists
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.email == email)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"Admin user already exists: {email}")
                return
            
            # Create admin user
            hashed_password = hash_password(password)
            
            admin_user = User(
                id=uuid.uuid4(),
                email=email,
                encrypted_password=hashed_password,
                first_name="System",
                last_name="Admin",
                full_name="System Admin",
                global_role="admin",
                is_active=True,
                email_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(admin_user)
            await session.commit()
            
            print(f"✓ Admin user created successfully!")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            print(f"\n⚠️  IMPORTANT: Change the password immediately after first login!")
            
        except Exception as e:
            print(f"✗ Error creating admin user: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(create_admin_user())


#!/usr/bin/env python3
"""
Database initialization script for TU SANG Family Tree
Run this script to set up the database and create an admin user
"""

import os
import sys
from datetime import datetime, date
from app import app, db, User, FamilyMember, FamilyRelationship

def init_database():
    """Initialize the database with tables and sample data"""
    print("Initializing TU SANG Family Tree Database...")
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Creating admin user...")
            admin = User(
                username='admin',
                email='admin@tusangfamily.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✓ Admin user created: username=admin, password=admin123")
        else:
            print("✓ Admin user already exists")
        
        # Add sample family members (optional)
        if FamilyMember.query.count() == 0:
            print("Adding sample family members...")
            
            # Sample family members
            sample_members = [
                {
                    'full_name': 'Juan Santos TU SANG',
                    'chinese_name': '胡安·桑托斯·图桑',
                    'nickname': 'Papa Juan',
                    'gender': 'Male',
                    'birth_date': date(1950, 1, 15),
                    'birth_place': 'Manila, Philippines',
                    'is_alive': True,
                    'notes': 'Family patriarch'
                },
                {
                    'full_name': 'Maria Cruz TU SANG',
                    'chinese_name': '玛丽亚·克鲁兹·图桑',
                    'nickname': 'Mama Maria',
                    'gender': 'Female',
                    'birth_date': date(1955, 3, 20),
                    'birth_place': 'Cebu, Philippines',
                    'is_alive': True,
                    'notes': 'Family matriarch'
                },
                {
                    'full_name': 'Pedro Juan TU SANG',
                    'chinese_name': '佩德罗·胡安·图桑',
                    'nickname': 'Pete',
                    'gender': 'Male',
                    'birth_date': date(1980, 7, 10),
                    'birth_place': 'Manila, Philippines',
                    'is_alive': True,
                    'notes': 'First son'
                }
            ]
            
            for member_data in sample_members:
                member = FamilyMember(**member_data)
                db.session.add(member)
            
            db.session.commit()
            print("✓ Sample family members added")
        else:
            print("✓ Family members already exist")
        
        print("\n" + "="*50)
        print("Database initialization completed successfully!")
        print("="*50)
        print("\nNext steps:")
        print("1. Run the application: python app.py")
        print("2. Visit: http://localhost:5000")
        print("3. Login as admin: username=admin, password=admin123")
        print("4. Start adding your family members!")
        print("\nFor family members:")
        print("- They can add information without logging in")
        print("- Use the 'Add Family Member' form on the homepage")
        print("- All data will be reviewed by administrators")

def reset_database():
    """Reset the database (WARNING: This will delete all data)"""
    print("WARNING: This will delete ALL data in the database!")
    confirm = input("Type 'YES' to confirm: ")
    
    if confirm == 'YES':
        with app.app_context():
            print("Dropping all tables...")
            db.drop_all()
            print("Recreating tables...")
            db.create_all()
            print("Database reset completed.")
    else:
        print("Database reset cancelled.")

def show_status():
    """Show current database status"""
    with app.app_context():
        user_count = User.query.count()
        member_count = FamilyMember.query.count()
        relationship_count = FamilyRelationship.query.count()
        
        print("\nDatabase Status:")
        print(f"- Users: {user_count}")
        print(f"- Family Members: {member_count}")
        print(f"- Relationships: {relationship_count}")
        
        if user_count > 0:
            print("\nUsers:")
            for user in User.query.all():
                print(f"  - {user.username} ({'Admin' if user.is_admin else 'Regular'})")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'init':
            init_database()
        elif command == 'reset':
            reset_database()
        elif command == 'status':
            show_status()
        else:
            print("Available commands:")
            print("  python init_db.py init    - Initialize database")
            print("  python init_db.py reset   - Reset database (WARNING: deletes all data)")
            print("  python init_db.py status  - Show database status")
    else:
        init_database()

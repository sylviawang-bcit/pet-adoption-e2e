# 1. Cleaned up imports, and added Animal so we can drop it safely
from web import create_app, User, Animal, Image, db 

def setup_database():
    app = create_app()

    with app.app_context():
        # 2. 'with db:' automatically opens and safely closes the connection
        with db:
            # 3. Drop child tables (Animal) BEFORE parent tables (User)
            db.drop_tables([Image, Animal, User], safe=True)
            
            # Recreate them
            db.create_tables([User, Animal, Image], safe=True)

            # Insert Data (Fixed Carlos's email)
            User.create(
                first_name="Marvin", 
                last_name="Ursua", 
                email="marvinlu19@gmail.com", 
                phone_number="6043415550"
            )
            
            User.create(
                first_name="Carlos", 
                last_name="Waung", 
                email="carlos.waung@gmail.com", # Added prefix
                phone_number="6043415550"
            )

if __name__ == "__main__":
    setup_database()
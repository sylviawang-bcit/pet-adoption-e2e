from web import create_app
from web.database import db
from web.models import User, Animal, Image, Admin

app = create_app()

PETS = [
    ("Rex", "Dog", "Labrador", "Male", 3, "large", "Black", "House trained", "Friendly and active."),
    ("Milo", "Cat", "Tabby", "Male", 2, "small", "Orange", "House trained", "Loves naps in the sun."),
    ("Bella", "Dog", "Corgi", "Female", 5, "medium", "Tan", "Not house trained", "Gentle, good with kids."),
    ("Luna", "Cat", "Siamese", "Female", 1, "small", "Cream", "Not house trained", "Curious and playful."),
]

with db.atomic():
    # start from a clean state every time
    Image.delete().execute()
    Animal.delete().execute()
    Admin.delete().execute()

    owner = User.get_or_none() or User.create(
        first_name="Test", last_name="Owner", email="owner@test.com", phone_number="6040000000"
    )

    for name, species, breed, gender, age, size, color, trained, desc in PETS:
        pet = Animal.create(owner=owner, name=name, species=species, breed=breed, gender=gender,
                            age=age, size=size, color=color, house_trained=trained, description=desc)
        Image.create(animal=pet, url=f"https://placehold.co/300x200?text={name}", is_primary=True)

    admin = Admin(username="admin")
    admin.set_password("admin123")
    admin.save()

print(f"Seeded {Animal.select().count()} pets and 1 admin (admin / admin123)")
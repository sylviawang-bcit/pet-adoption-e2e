import pytest
from .shared import client, ANIMAL_DATA, TEST_IMAGE_URL, TEST_USER_ID, TEST_NON_PRIMARY_IMAGE_URL
from web.models import Animal, User, Image
from web.database import db

class TestIndex:
    def test_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_featured_pet_shows(self, client):
        response = client.get("/")
        assert b"gallery-card" in response.data

class TestAddPet:
    def test_add_pet(self, client):
        data = ANIMAL_DATA
        data["url"] = TEST_IMAGE_URL
        response = client.post("/add_pet", data=ANIMAL_DATA, follow_redirects=True)
        assert response.status_code == 200
        pet = Animal.get_or_none(Animal.name == "Mr. Test")
        assert pet is not None
        # cleanup
        Image.delete().where(Image.animal_id == pet.id).execute()
        Animal.delete().where(Animal.id == pet.id).execute()

class TestHomepagePetImage:
    def test_homepage_shows_primary_image(self, client):
        """
        Each pet can have multiple images. To determine which of its images to show on the home page's Featured Pets section, every image has an is_primary attribute that is either True or False. If an image has is_primary = True, then it will be shown in Featured Pet.

        This is one of two tests that evaluates this behaviour. This test creates a test animal temporarily, which is then temporarily shown on Featured Pet. Next, it fetches the home page's data and checks whether or not the Featured Pet's image is its primary one by comparing it to the test primary image stored in shared.py.

        The second test is found in unit_test.py...
         
        """

        test_animal = None

        try:
            # Save existing animals/images currently in DB
            existing_animals = list(Animal.select())
            existing_images = list(Image.select())

            # Removes existing animals/images from DB temporarily
            Image.delete().execute()
            Animal.delete().execute()

            # Creates a test animal (writes it to the DB temporarily)
            test_animal = Animal.create(
                owner=TEST_USER_ID,
                name=ANIMAL_DATA["name"],
                species=ANIMAL_DATA["species"],
                breed=ANIMAL_DATA["breed"],
                gender=ANIMAL_DATA["gender"],
                age=ANIMAL_DATA["age"],
                size=ANIMAL_DATA["size"],
                color=ANIMAL_DATA["color"],
                house_trained=ANIMAL_DATA["house_trained"],
                description=ANIMAL_DATA["description"],
            )

            Image.create(
                animal=test_animal,
                url=TEST_NON_PRIMARY_IMAGE_URL,
                is_primary=False
            )
            
            Image.create(
                animal=test_animal,
                url=TEST_IMAGE_URL,
                is_primary=True
            )

            response = client.get("/")

            data = response.data.decode()

            assert TEST_IMAGE_URL in data
            assert TEST_NON_PRIMARY_IMAGE_URL not in data

        finally:
            # Deletes created Image and Animal instances as cleanup
            Image.delete().where(Image.animal == test_animal).execute()

            if test_animal:
                test_animal.delete_instance()

            # Restores original pet and animal data in the DB (rewrites them back into the DB)

            for existing_animal in existing_animals:
                existing_animal.save(force_insert=True)

            for existing_image in existing_images:
                existing_image.save(force_insert=True)
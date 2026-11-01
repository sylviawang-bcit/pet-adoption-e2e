import pytest

from .shared import ANIMAL_DATA, TEST_USER_ID, TEST_NON_PRIMARY_IMAGE_URL, TEST_IMAGE_URL
from web.models import Animal, User, Image


class TestAnimal():

    def test_has_fields(self):
        pet = Animal(**ANIMAL_DATA)
        # Cannot test for foreign keys without saving the parent to the database
        assert pet.name == ANIMAL_DATA["name"]
        assert pet.species == ANIMAL_DATA["species"]
        assert pet.breed == ANIMAL_DATA["breed"]
        assert pet.gender == ANIMAL_DATA["gender"]
        assert pet.age == ANIMAL_DATA["age"]
        assert pet.size == ANIMAL_DATA["size"]
        assert pet.color == ANIMAL_DATA["color"]
        assert pet.house_trained == ANIMAL_DATA["house_trained"]
        assert pet.description == ANIMAL_DATA["description"]

    def test_to_dict(self):
        pet = Animal(**ANIMAL_DATA)
        for key, val in pet.to_dict().items():
            if key in ["id", "owner"]:
                continue
            assert val == ANIMAL_DATA[key]

class TestPrimaryImage:
    def test_animal_primary_image(self):
        """
        This is the second test related to primary images (for the first one, see integration_test.py).

        Rather than testing the home page, this simply temporarily creates a test animal, then runs a SELECT statement that includes a primary image in its JOIN clause. Similar to the first test, it compares the queried primary image to the one stored in shared.py.

        While the first test ensures that the home page shows the correct image, this one ensures that its underlying query contains the correct image.
        """
        try:
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

            animal_data = (
                Animal
                .select(
                    Animal.id,
                    Animal.name,
                    Image.url.alias("primary_image")
                )
                .join(
                    Image,
                    on=(
                        (Image.animal == Animal.id) &
                        (Image.is_primary == True)
                    )
                )
                .where(Animal.id == test_animal.id)
                .dicts()
                .get()
            )

            assert animal_data["primary_image"] == TEST_IMAGE_URL

        finally:
            # Deletes created Image and Animal instances as cleanup
            if test_animal:
                Image.delete().where(Image.animal == test_animal).execute()
                test_animal.delete_instance()
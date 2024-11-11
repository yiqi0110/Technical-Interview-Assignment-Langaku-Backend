import json
import os
from django.core.management.base import BaseCommand
from ecsite.models import Item, User


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        Item.objects.all().delete()
        User.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("All existing item data has been deleted"))

        try:
            json_file_path = os.path.join(os.path.dirname(__file__), "MOCK_DATA.json")

            with open(json_file_path) as json_file:
                data = json.load(json_file)
                items = [
                    Item(
                        name=item["name"],
                        price=item["price"],
                        quantity=item["quantity"],
                    )
                    for item in data
                ]
                Item.objects.bulk_create(items)

            User.objects.create_superuser(
                "testuser", email="testuser@example.com", password="testpassword"
            )

            self.stdout.write(self.style.SUCCESS("Mock data loaded successfully"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading data: {e}"))

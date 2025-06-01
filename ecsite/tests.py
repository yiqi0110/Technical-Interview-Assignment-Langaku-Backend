from rest_framework.test import APITestCase, APIClient, APIRequestFactory, force_authenticate

from django.contrib.auth.models import User
from .models import Item, Cart, CartItem
from django.urls import reverse
from rest_framework import status
from .views import ItemViewSet, CartViewSet

###############################################################################
## TODO: Add tests


class CartAPITests(APITestCase):
    test_data = [
        {"id":0,"name":"Cheese - St. Paulin","price":3289,"quantity":8},
        {"id":1,"name":"Veal - Leg, Provimi - 50 Lb Max","price":670,"quantity":14},
        {"id":2,"name":"Muffin Mix - Oatmeal","price":6212,"quantity":12},
        {"id":3,"name":"Kirsch - Schloss","price":8444,"quantity":8},
        {"id":4,"name":"Lettuce - Curly Endive","price":1798,"quantity":17},
        {"id":5,"name":"Lotus Root","price":2069,"quantity":6},
        {"id":6,"name":"Bread - Wheat Baguette","price":2912,"quantity":20},
        {"id":7,"name":"Wine - Pinot Noir Stoneleigh","price":9297,"quantity":5},
        {"id":8,"name":"Steampan - Lid For Half Size","price":7435,"quantity":3},
        {"id":9,"name":"Pepper - Yellow Bell","price":8021,"quantity":15}
        ]

    def setUp(self):
        # Initial Data set up.
        self.items = [
            Item(
                    name=item["name"],
                    price=item["price"],
                    quantity=item["quantity"],
            ) for item in self.test_data
        ]
        Item.objects.bulk_create(self.items)
        self.item = Item.objects.create(id=11, name="Bell Peppers", price=99, quantity=10)
        self.user = User.objects.create_user("UNITTEST",email="UNITTEST@example.com",password="UNITTEST")
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(cart=self.cart,item=self.item,quantity=1)

        # View set up.
        self.item_list_view = ItemViewSet.as_view({'get': 'list'})
        self.cart_list_view = CartViewSet.as_view({'get': 'list'})
        self.cart_add_view = CartViewSet.as_view({'post': 'add'})
        self.cart_purchase_view = CartViewSet.as_view({'post': 'purchase'})
        self.cart_remove_item_view = CartViewSet.as_view({'post': 'remove_item_from_cart'})

        # API set up.
        self.factory = APIRequestFactory()


    # $ python manage.py test ecsite.tests.CartAPITests.test_listing_items
    def test_listing_items(self):
        request = self.factory.get("/api/v1/items/")
        force_authenticate(request, user=self.user)
        response = self.item_list_view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 11)

    # $ python manage.py test ecsite.tests.CartAPITests.test_listing_cart
    def test_listing_cart(self):
        request = self.factory.get("/api/v1/cart/")
        force_authenticate(request, user=self.user)
        response = self.cart_list_view(request)
        cart = response.data.get("cart")
        cart_item_0 = cart[0]
        items = cart_item_0.get("items")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(cart), 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(cart_item_0.get("total_price"), 99)

    # $ python manage.py test ecsite.tests.CartAPITests.test_adding_item_to_cart_success
    def test_adding_item_to_cart_success(self):
        # Successful request as the quantity is lower or equal to the quantity of the item on stock.
        s_request = self.factory.post("/api/v1/cart/add/", {"item": 1, "quantity": 1}, content_type='application/json')
        force_authenticate(s_request, user=self.user)
        response = self.cart_add_view(s_request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # $ python manage.py test ecsite.tests.CartAPITests.test_adding_item_to_cart_failure
    def test_adding_item_to_cart_failure(self):
        # Failed request as the quantity is greater than the quantity of the item on stock.
        request = self.factory.post("/api/v1/cart/add/", {"item": 1, "quantity": 10}, content_type='application/json')
        force_authenticate(request, user=self.user)
        response = self.cart_add_view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # $ python manage.py test ecsite.tests.CartAPITests.test_purchase
    def test_purchase(self):
        request = self.factory.post("/api/v1/cart/purchase/")
        force_authenticate(request, user=self.user)
        response = self.cart_purchase_view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # $ python manage.py test ecsite.tests.CartAPITests.test_remove_item_from_cart
    def test_remove_item_from_cart(self):
        request = self.factory.post("/api/v1/cart/remove_item_from_cart/", {"item": 11}, content_type='application/json')
        force_authenticate(request, user=self.user)
        response = self.cart_remove_item_view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


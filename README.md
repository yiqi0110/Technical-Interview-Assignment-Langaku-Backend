# E-Commerce API

## Setup
If using Sqlite
```
python manage.py migrate
```

Load initial data
```
python manage.py init_data
```
Admin User
- username: testuser
- password: testpassword

# System Design

## VIEWS

### View All Items
*This view returns the entire list of items*

*Expected input/parameters*
```
    None
```

*Expected output*
```

{
    "count": 1000,
    "next": "http://127.0.0.1:8000/api/v1/items/?page=2",
    "previous": null,
    "results": [
        {
            "id": 5001,
            "name": "Wine - Port Late Bottled<input/> Vintage",
            "price": 1029,
            "quantity": 60
        },
        {
            "id": 5002,
            "name": "Appetizer - Crab And Brie",
            "price": 5000,
            "quantity": 10
        }, ...
    ]
}
```

### Modify Item
*This view modifies an item*

*Expected input/parameters*
```
{
    "id": 5001,
    "name": "Wine - Port Late Bottled Vintage",
    "price": 1029,
    "quantity": 12
}
```

*Expected output*
```
{
    "id": 5001,
    "name": "Wine - Port Late Bottled Vintage",
    "price": 1029,
    "quantity": 12
}
```

### View Cart
*This view returns the entire cart for the authenticated user/logged in user*

*Expected input/parameters*
```
    None
```

*Expected output*
```
{
    "cart": [
        {
            "items": [
                {
                    "item": {
                        "id": 5002,
                        "name": "Appetizer - Crab And Brie",
                        "price": 5000,
                        "quantity": 12
                    },
                    "quantity": 1
                },
                {
                    "item": {
                        "id": 5001,
                        "name": "Wine - Port Late Bottled Vintage",
                        "price": 1029,
                        "quantity": 9
                    },
                    "quantity": 3
                }
            ],
            "total_price": 8087,
            "item_values": {
                "5002": 1,
                "5001": 3
            }
        }
    ]
}
```

### Add Item to Cart
*This view returns the entire list of items*

*Expected input/parameters*
```
# "item" refering to the item id.
{
	"item": 5030, 
	"quantity": 1
}
```

*Expected output*
```
{
    "cart": {
        "items": [
            {
                "item": {
                    "id": 5001,
                    "name": "Wine - Port Late Bottled<input/> Vintage",
                    "price": 1029,
                    "quantity": 6
                },
                "quantity": 1
            },
            {
                "item": {
                    "id": 5002,
                    "name": "Appetizer - Crab And Brie",
                    "price": 5000,
                    "quantity": 11
                },
                "quantity": 1
            },
            {
                "item": {
                    "id": 5030,
                    "name": "Plate Pie Foil",
                    "price": 7056,
                    "quantity": 8
                },
                "quantity": 1
            }
        ],
        "total_price": 13085,
        "item_values": {
            "5001": 1,
            "5002": 1,
            "5030": 1
        }
    }
}
```

### Purchase Items in Cart
*This view performs the "basic" purchase functionality*

*Expected input/parameters*
```
    None
```

*Expected output*
```
{
    "cart": [
        {
            "items": [],
            "total_price": null,
            "item_values": null
        }
    ]
}
```

### Remove Item from Cart
*This view removes an item from the cart*

*Expected input/parameters*
```
{
    "item": 5001
}
```

*Expected output*
```
{
    "cart": {
        "items": [
            {
                "item": {
                    "id": 5002,
                    "name": "Appetizer - Crab And Brie",
                    "price": 5000,
                    "quantity": 11
                },
                "quantity": 1
            },
            {
                "item": {
                    "id": 5030,
                    "name": "Plate Pie Foil",
                    "price": 7056,
                    "quantity": 8
                },
                "quantity": 1
            }
        ],
        "total_price": 12056,
        "item_values": {
            "5002": 1,
            "5030": 1
        }
    }
}
```

### Audit Logs
*This view returns the entire list of purchase records*

*Expected input/parameters*
```
    None
```

*Expected output*
```
{
    "data": [
        {
            "username": "testuser3",
            "item": {
                "id": 5001,
                "name": "Wine - Port Late Bottled<input/> Vintage",
                "price": 1029,
                "quantity": 6
            },
            "quantity": 1,
            "timestamp": "2025-05-31T05:17:26.018787Z"
        },
        {
            "username": "testuser",
            "item": {
                "id": 5001,
                "name": "Wine - Port Late Bottled<input/> Vintage",
                "price": 1029,
                "quantity": 6
            },
            "quantity": 3,
            "timestamp": "2025-06-01T06:46:27.914284Z"
        }, ...
    ]
}
```

# Case Study

## case where the item’s stock may run out before the purchase is finalized
A solution for this could be when calling the purchase api endpoint, a response is created saying that "an item from your cart has ran out of stock". Similar to real application setting (like for amazon), the user would be prompted with an error message on the UI saying something along the lines of "Sorry, something went wrong. Navigating back to your cart in 5 seconds... etc.". After which, when directed back to the cart a model would display saying "'X' item is no longer in stock... etc.". Currently, the system should handle this case as when performing the update, it would run the record through the model, and since the model is set to positive integers, it would throw an error and roll back the transaction that failed.

- Some Puesdo-code could look like this:
```python
Class myView():
    def add():
        try:
            # functions to get cart, cart_items, and items.
            cart = cart
            cart_items = [x for cart_item in cart]
            items = [x for item in cart_items]

            for item in items:
                if item.quantity < cart_items[x].quantity:
                    return Response("item {} sold out".format(item.name), status=status.HTTP_404)

        except Exception as e:
            pass
```

## case a product price may change before the purchase is finalized
Given the way that the current serialzers are set, this would only be acheived by adding additional logic into the serializer to get prices of items at time of serialization. However, currently, when performing the purchase call, the items are locked (utilizing the select_for_update method for Django ORM). This means that the row is locked until the transaction is complete, so as long as the price did not change in the miliseconds between the user calling the API and the API hitting that line of code, then in theory, the price would be "fixed/unchangable".

# Assignment notes

## Concurrency
For this I used a variety of methods to including:
    - @transaction.atomic -> For simple transaction that I am not to worried about concurrency, like adding an item to a user's cart.
    - with transaction.atomic -> For complex transactions for the ability to get error handling.
    - F() statements -> For keeping specific columns concurrent.
    - select_for_update() -> For locking rows that are retrieved that are planned to be updated.

Transactions are important for concurrency and data integrity in general. But, I think that for concurrency, mulitple solutions should be used in tandum. For instance, using select_for_update() in tandum will help to lock the row on a SQL level, this helps provide the ability to rollback if something goes wrong and keep the row locked for that instance. However if there are 10,000 people trying to purchase the same item at the same time, like in case for name brand shoes going on sale. This approach can lead to delays and potential DB locks, in cases like this, it may be better to not use select_for_update(). As well as reducing complexity of the transaction, similiar to the difference between the following code.

*Transaction starting at the top of the function*
```python
def less_complex():
    try:          
        with transaction.atomic():
            cart = get_object_or_404(Cart, user=request.user)
            # Serialize the cart to get items.
            serializer = CartSerializer(cart)
            # Get items that are in the cart.
            items = Item.objects.filter(id__in=serializer.data["item_values"]).select_for_update()
            # Verifies idemponcy.
            if idempontent(request.user.username, serializer.data):
                return Response(serializer.data, status=status.HTTP_200_OK)
            # Initialize purchase_record list.
            purchase_records = []
            # Iterate through to update the quantity of the items that are being purchased.
            for item in items:
                purchase_quantity = serializer.data["item_values"][item.id]
                item.quantity = F("quantity") - purchase_quantity
                purchase_records.append(UserPurchaseRecord(
                    user=request.user,
                    item=item,
                    quantity=purchase_quantity
                ))
            # Perform bulk update for the purchased items.  
            Item.objects.bulk_update(items, ["quantity"], 100)
            # Bulk create UserPurchaseRecord
            UserPurchaseRecord.objects.bulk_create(purchase_records, 100)
            # Clear cart of items.
            CartItem.objects.filter(cart=cart).delete()
            # Final serializer for displaying cart after transaction.
            final = CartSerializer(cart)
            return Response({"cart": final.data}, status=status.HTTP_201_CREATED)
except IntegrityError as ie:
    return Response({"error": str(ie)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

*Reduced complexity of transaction*
```python
def less_complex():
    cart = get_object_or_404(Cart, user=request.user)
    # Serialize the cart to get items.
    serializer = CartSerializer(cart)
    # Get items that are in the cart.
    items = Item.objects.filter(id__in=serializer.data["item_values"]).select_for_update()
    # Verifies idemponcy.
    if idempontent(request.user.username, serializer.data):
        return Response(serializer.data, status=status.HTTP_200_OK)
    # Initialize purchase_record list.
    purchase_records = []
    # Iterate through to update the quantity of the items that are being purchased.
    for item in items:
        purchase_quantity = serializer.data["item_values"][item.id]
        item.quantity = F("quantity") - purchase_quantity
        purchase_records.append(UserPurchaseRecord(
            user=request.user,
            item=item,
            quantity=purchase_quantity
        ))
    try:          
        with transaction.atomic():

            # Perform bulk update for the purchased items.  
            Item.objects.bulk_update(items, ["quantity"], 100)

            # Bulk create UserPurchaseRecord
            UserPurchaseRecord.objects.bulk_create(purchase_records, 100)

            # Clear cart of items.
            CartItem.objects.filter(cart=cart).delete()
    except IntegrityError as ie:
        return Response({"error": str(ie)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # Final serializer for displaying cart after transaction.
    final = CartSerializer(cart)
    return Response({"cart": final.data}, status=status.HTTP_201_CREATED)
```

## Post request idempotency
I used a cached hashing mechanism to handle this. Effectively what this does is stores the user and the associated query sent in cached storage after it has been hashed. Then when the next call occurs, the system checks the stored cache and compares it to the new value. If the value is the same, the code just returns the basic view data. If the value is different, the code runs as expected.
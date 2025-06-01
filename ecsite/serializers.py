from rest_framework import serializers
from .models import CartItem, Item, Cart, UserPurchaseRecord
import re

class ItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(min_value=0)
    price = serializers.IntegerField(min_value=0)
    quantity = serializers.IntegerField(min_value=0)

    class Meta:
        model = Item
        fields = ["id", "name", "price", "quantity"]


class CartItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer()  # Nest the full item details
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = CartItem
        fields = ["item", "quantity"]
    
    def create(self, validated_data):
        return CartItem.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.item = validated_data.get('item', instance.item)
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.save()
        return instance


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cartitem_set', many=True)  # Include all cart items
    total_price = serializers.SerializerMethodField()  # Add calculated total price
    item_values = serializers.SerializerMethodField() # Add list of item ids
    
    class Meta:
        model = Cart
        fields = ["items", "total_price", "item_values"]
    
    def get_total_price(self, obj):
        # Calculate the total price of all items in the cart
        return sum(
            cart_item.item.price * cart_item.quantity 
            for cart_item in obj.cartitem_set.all()
        ) or None
    
    def get_item_values(self, obj):
        values = {}

        for cart_item in obj.cartitem_set.all():
            values[cart_item.item.id] = cart_item.quantity

        return values or None
    
    def update(self, instance, validated_data):
        instance.items = validated_data.get('items', instance.items)
        instance.save()
        return instance
    
class UserPurchaseRecordSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField() # Add username
    item = ItemSerializer()  # Nest the full item details
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = UserPurchaseRecord
        fields = ["username", "item", "quantity", "timestamp"]

    def get_username(self, obj): 
        return obj.user.username or None

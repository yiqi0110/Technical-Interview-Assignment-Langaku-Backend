from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, serializers
from rest_framework.authentication import (
    BasicAuthentication,
    SessionAuthentication,
)
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.management import call_command

from django.shortcuts import get_object_or_404
from django.db.models import F
from django.db import transaction, IntegrityError
from .models import Cart, CartItem, Item, UserPurchaseRecord
from .serializers import ItemSerializer, CartItemSerializer, CartSerializer, UserPurchaseRecordSerializer
from .helper import log_single_change, log_single_create, idempontent
from rest_framework.pagination import PageNumberPagination



# Disable CSRF check for this assigment
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


@api_view(["POST"])
def initialize_data(request):
    try:
        file_name = request.data.get("file", "MOCK_DATA.json")
        print(f"Initializing data from {file_name}")
        call_command("init_data", file=file_name)
        return Response(
            {"message": f"Data initialized successfully from {file_name}"},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


###############################################################################
## TODO: Implement the following views


class ItemViewSet(viewsets.ViewSet, PageNumberPagination):
    def list(self, request):
        try:
            # Get items ordered by id.
            items = Item.objects.all().order_by("id")

            # Set items to pagination set.
            results = self.paginate_queryset(items, request, view=self)

            # Serialize the results.
            serializer = ItemSerializer(results, many=True)

            return self.get_paginated_response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # NOTE: This is just to make testing easier, hense the lack of logging
    # and lack of auth controls 
    @csrf_exempt
    @action(detail=False, methods=["put"])
    def modify_item(self, request):
        try:
            # Get the item for update.
            item = get_object_or_404(Item, pk=request.data.get("id"))

            # Serialize for response.
            serializer = ItemSerializer(item)

            # Iterate over fields to update values based on request data.
            for field in item._meta.fields:
                if field.name in serializer.data:
                    setattr(item, field.name, request.data.get(field.name))

            # Save changes.
            item.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CartViewSet(viewsets.ViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    
    def out_of_stock_respone(self, available_stock):
        return Response({"error": f"Available stock is {available_stock}, please decrease ammount selected."}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        try:
            carts = Cart.objects.filter(user=request.user)
            serializer = CartSerializer(carts, many=True)

            # Check if any quantity is 0, if so, mark it as "Out of Stock"
            for i in range(len(serializer.data)):
                cart_items = serializer.data[i]
                for j in range(len(cart_items["items"])):
                    cart_item = cart_items["items"][j]
                    if cart_item["item"]["quantity"] <= 0:
                        cart_item["item"]["quantity"] = "Out of Stock"
            
            return Response({"cart": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Expected input format
    # {
    #   "item": <item_id>,
    #   "quantity": <quantity>
    # }
    @csrf_exempt
    @action(detail=False, methods=["post"])
    @transaction.atomic
    def add(self, request):
        try:           
            # Get the user's cart (or create if it doesn't exist).
            # NOTE: Something to add here would be verification that the request.user is indeed 
            # the user logged in or something along those lines.
            cart, created = Cart.objects.get_or_create(user=request.user)

            # Verifies idemponcy.
            if idempontent(request.user.username, request.body):
                final = CartSerializer(cart)
                return Response({"cart": final.data}, status=status.HTTP_201_CREATED)

            # Get the item and quantity from the request data.
            item_id = request.data.get("item")
            new_quantity = request.data.get("quantity")
            
            # Validate that the item exists.
            item = get_object_or_404(Item, pk=item_id)

            # Check if quantity is greater than item.quantity
            if new_quantity > item.quantity:
                return self.out_of_stock_respone(item.quantity)

            # Get cart_item, if it does not exist we create it.
            try:
                cart_item = CartItem.objects.get(
                    cart=cart,               
                    item=item
                )
                old_values = CartItemSerializer(cart_item).data
                cart_item.quantity = new_quantity
            except CartItem.DoesNotExist:
                cart_item = CartItem(
                    cart=cart,
                    item=item,
                    quantity=new_quantity
                )

            # Serialize for validation.
            serializer = CartItemSerializer(cart_item)

            # If cart_item was not found, then we create a temp object.
            if not cart_item.pk:
                deserializer = CartItemSerializer(data=serializer.data)
            else:
                deserializer = CartItemSerializer(cart_item, data=serializer.data)

            # Makes sure the data is valid based on the serializer.
            try:
                deserializer.is_valid(raise_exception=True)
            except serializers.ValidationError:
                return Response(deserializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Iterate over fields to update values based on request data.
                for field in cart_item._meta.fields:
                    if field.name in deserializer.validated_data:
                        setattr(item, field.name, request.data[field.name])

                cart_item_created = True if not cart_item.pk else False

                cart_item.save()
                
                # Final serializer for displaying cart after transaction.
                final = CartSerializer(cart)

                if cart_item_created:
                    # Log changes.
                    log_single_create(cart_item, deserializer.validated_data)

                    return Response({"cart": final.data}, status=status.HTTP_201_CREATED)
                
                # Log changes.
                log_single_change(cart_item, deserializer.validated_data, old_values)

                return Response({"cart": final.data}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Expected input format
    # {}
    # This does not need a body passed to it
    @csrf_exempt
    @action(detail=False, methods=["post"])
    def purchase(self, request):
        try:          
            cart = get_object_or_404(Cart, user=request.user)

            # Serialize the cart to get items.
            serializer = CartSerializer(cart)

            # Make sure there is actually items.
            if len(serializer.data.get("items")) <= 0:
                return Response({"cart": serializer.data}, status=status.HTTP_200_OK)

            # Get items that are in the cart.
            items = Item.objects.filter(id__in=serializer.data["item_values"]).select_for_update()

            # Verifies idemponcy.
            if idempontent(request.user.username, serializer.data):
                return Response({"cart": serializer.data}, status=status.HTTP_200_OK)
            
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
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Expected input format
    # {
    #   "item": <item_id>
    # }
    @csrf_exempt
    @action(detail=False, methods=["post"])
    def remove_item_from_cart(self, request, pk=None):
        try:          
            with transaction.atomic():
                cart = get_object_or_404(Cart, user=request.user)

                # Verifies idemponcy.
                if idempontent(request.user.username, request.body):
                    serializer = CartSerializer(cart)
                    return Response(serializer.data, status=status.HTTP_200_OK)

                item_id = request.data.get("item")

                item = get_object_or_404(Item, id=item_id)

                # Clear cart of items.
                CartItem.objects.filter(cart=cart, item=item).delete()

                # Final serializer for displaying cart after transaction.
                final = CartSerializer(cart)

                return Response({"cart": final.data}, status=status.HTTP_201_CREATED)
        except IntegrityError as ie:
            return Response({"error": str(ie)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AuditViewSet(viewsets.ViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request):
        try:
            audit = UserPurchaseRecord.objects.all()

            serializer = UserPurchaseRecordSerializer(audit, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
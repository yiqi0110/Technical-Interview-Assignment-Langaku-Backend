from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.authentication import (
    BasicAuthentication,
    SessionAuthentication,
)
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated


# Disable CSRF check for this assigment
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


###############################################################################
## Implement the following views


class ItemViewSet(viewsets.ViewSet):
    def list(self, request):
        pass


class CartViewSet(viewsets.ViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request):
        pass

    @csrf_exempt
    @action(detail=False, methods=["post"])
    def add(self, request):
        pass

    @csrf_exempt
    @action(detail=False, methods=["post"])
    def purchase(self, request):
        pass

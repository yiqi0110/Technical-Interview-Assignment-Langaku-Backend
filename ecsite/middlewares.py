from django.contrib.auth.models import User
from django.contrib.auth import login
from django.http import HttpResponse

import logging

logger = logging.getLogger(__name__)


# Skip Login step for this assignment
class MockLoginUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    # NOTE: Obviously this is a simple set up for the assignments purpose,
    # However, if this was a production application, using this structure would lead to session hijacking by changing your
    # username in the COOKIES
    def __call__(self, request):
        if request.path.startswith("/api"):
            username = request.COOKIES.get("username", "testuser")
            logger.info(f"Mock login for user: {username}")
            try:
                user = User.objects.get(username=username)
                login(request, user)
            except User.DoesNotExist:
                return HttpResponse(
                    "User not found or invalid credentials.", status=401
                )
        response = self.get_response(request)
        return response

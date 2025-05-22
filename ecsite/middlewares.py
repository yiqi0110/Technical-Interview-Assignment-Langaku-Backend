from django.contrib.auth.models import User
from django.contrib.auth import login


# Skip Login step for this assignment
# you can implement your own login logic if you want.
class MockLoginUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # print(request)
        # If the url start from /api, set login user as testuser AI!
        user = User.objects.get(username="testuser")
        login(request, user)
        response = self.get_response(request)
        return response

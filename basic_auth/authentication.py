from datetime import datetime
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed, ParseError
import requests
import jwt

from django.conf import settings
from django.contrib.auth import get_user_model
from user.models import UserActivity

User = get_user_model()
class JWTAuthentication(authentication.BaseAuthentication):
    def __init__(self):
        self.is_authenticated = False

    def authenticate(self, request):
        # Extract the JWT from the Authorization header
        jwt_token = request.META.get('HTTP_AUTHORIZATION')
        if jwt_token is None:
            raise AuthenticationFailed('Token not provided')

        jwt_token = JWTAuthentication.get_the_token_from_header(jwt_token)  # clean the token
        print(request)
        print(jwt_token)
        # Decode the JWT and verify its signature
        try:
            payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.exceptions.InvalidSignatureError:
            raise AuthenticationFailed('Invalid signature')
        except jwt.exceptions.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except:
            raise ParseError()
        
        # Check if the token is a refresh token
        is_refresh_token = payload.get('is_refresh_token', False)
        # If it's a refresh token, return the user and token payload as-is
        if is_refresh_token:
            self.is_authenticated = True
            return user, payload
        # Get the user from the database
        email = payload.get('email')
        if email is None:
            raise AuthenticationFailed('User identifier not found in JWT')

        user = User.objects.filter(email=email).first()
        if user is None:
                raise AuthenticationFailed('User not found')
        # Save User Activity
        save_user_activity(request, user.id)
        # Return the user and token payload
        self.is_authenticated = True
        return user, payload

    def authenticate_header(self, request):
        return 'Bearer'

    def has_permission(self, request, view):
        # Return True if the user has permission to access the view, or False otherwise.
        self.authenticate(request)
        if self.is_authenticated:
            return True
        return False
    
    def has_object_permission(self, request, view, obj):
        # Check if the user has permission to perform the action on the object
        self.authenticate(request)
        if self.is_authenticated:
            return True
        return False
    
    @classmethod
    def create_jwt(cls, user, is_refresh_token=False):
        # Create the JWT payload
        if is_refresh_token:
            life_time = settings.JWT_CONF['REFRESH_TOKEN_LIFETIME']
        else:
            life_time = settings.JWT_CONF['ACCESS_TOKEN_LIFETIME']
        payload = {
            'user_identifier': user.email,
            'exp': int((datetime.now() + life_time).timestamp()),
            'iat': datetime.now().timestamp(),
            'email': user.email,
            'is_refresh_token': is_refresh_token
        }

        # Encode the JWT with your secret key
        jwt_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        return jwt_token

    @classmethod
    def get_the_token_from_header(cls, token):
        token = token.replace('Bearer', '').replace(' ', '')  # clean the token
        return token

class SwaggerTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        # Check if the user is already authenticated
        # if request.user.is_authenticated:
        #     return (request.user, None)

        # Retrieve the username and password from the request
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return None

        # Make a request to obtain the token
        token_url = '/api/auth/login/'  # Replace with your token endpoint URL
        response = requests.post(token_url, data={'email': username, 'password': password})

        if response.status_code == 200:
            # Extract the token from the response
            token = response.json().get('token')

            # Store the token in the session for subsequent API requests
            request.session['swagger_token'] = token

            # Return the authenticated user
            return (request.user, None)

        return None

    def authenticate_header(self, request):
        # Retrieve the token from the session
        token = request.session.get('swagger_token')
        if token:
            # Add the token to the authentication header
            return f'Bearer {token}'

        return None

def save_user_activity(request, user_id): 
    # save user_activity
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    # location = request.geolocation
    location = ''
    url = request.build_absolute_uri()
    params = dict(request.GET.items())
    params.update(request.data)
    action = {'url': url}
    action.update(params)
    user_activity = {'user_id': user_id, 'action': action, 'ip': ip, 'level': 0}
    user_activity = UserActivity(**user_activity)
    user_activity.save()
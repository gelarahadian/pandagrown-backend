from drf_yasg import openapi

image_field_schema = openapi.Schema(
    type=openapi.TYPE_STRING,
    format=openapi.FORMAT_BINARY
)
UserProfileSchema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'f_name': openapi.Schema(type=openapi.TYPE_STRING),
        'l_name': openapi.Schema(type=openapi.TYPE_STRING),
        'avatar': image_field_schema,  # image field
        'country_id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'gender': openapi.Schema(type=openapi.TYPE_STRING),
        'birthday': openapi.Schema(type=openapi.TYPE_STRING),
        'address': openapi.Schema(type=openapi.TYPE_STRING),
        'city': openapi.Schema(type=openapi.TYPE_STRING),
        'zip': openapi.Schema(type=openapi.TYPE_STRING),
        'area_code': openapi.Schema(type=openapi.TYPE_STRING),
        'phone': openapi.Schema(type=openapi.TYPE_STRING),
        'telegram': openapi.Schema(type=openapi.TYPE_STRING),
        'balance': openapi.Schema(type=openapi.TYPE_NUMBER),
        'refer_code': openapi.Schema(type=openapi.TYPE_STRING),
        'referer_id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING),
        'updated_at': openapi.Schema(type=openapi.TYPE_STRING)
    },
    required=['id', 'user_id', 'country_id']  # essential field list
)
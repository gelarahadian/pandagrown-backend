from django.core.files.storage import FileSystemStorage
from django.db.models import Q, F
from rest_framework import filters, pagination, status, viewsets
from rest_framework.response import Response

from basic_auth.authentication import JWTAuthentication
from shop.models import Seed, SeedMedia
from shop.serializers import SeedSerializer, SeedMediaSerializer, SeedMediaGetSerializer

class SeedPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class SeedViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = Seed.objects.all()
    serializer_class = SeedSerializer
    pagination_class = SeedPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]  # Add OrderingFilter and SearchFilter backends
    search_fields = ['name']  # Specify the fields to search for
    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            # Apply custom authentication only for POST, DELETE, UPDATE, PATCH
            return [JWTAuthentication()]
        else:
            # Use default authentication for other actions
            return super().get_permissions()
    def get_queryset(self):
        seeds = Seed.objects.annotate(
            total_period=F('curing_period') + F('packing_period') + F('vegetation_mass_period') + F('flowering_preharvest_period') + F('harvest_period') + F('drying_period')
        )
        queryset = seeds.all()
        sort_param = self.request.query_params.get('sort', None)
        if sort_param:
            # Determine the field and direction for sorting
            sort_fields = sort_param.split(',')
            ordering = []
            for field in sort_fields:
                if field.startswith('-'):
                    ordering.append(f"-{field[1:].strip()}")
                else:
                    ordering.append(field.strip())

            # Apply sorting to the queryset
            queryset = queryset.order_by(*ordering)
        queryset = queryset.filter(name__icontains=self.request.query_params.get('search', ''))
        return queryset
    
class SeedMediaViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = Seed.objects.all()
    serializer_class = SeedMediaSerializer
    lookup_field = 'pk'
    http_method_names = ['get', 'post', 'head', 'put', 'delete', 'patch', 'partial_update']
    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'list':
            return SeedMediaGetSerializer
        return SeedMediaSerializer
    def get_queryset(self):
        seed_id = self.kwargs['seed_id']
        if seed_id is None:
            seed_id = self.request.GET.get('seed_id')
        return SeedMedia.objects.filter(seed_id=seed_id)
    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'patch', 'partial_update']:
            # Apply custom authentication only for POST, DELETE, UPDATE, PATCH
            return [JWTAuthentication()]
        else:
            # Use default authentication for other actions
            return super().get_permissions()
    def create(self, request, *args, **kwargs):
        images = request.FILES.getlist('growing_img')
        instance = {
            'growing_img': [],
            'start_day': request.data.get('start_day'),
            'end_day': request.data.get('end_day'),
            'seed_id': request.data.get('seed_id')
        }
        if int(request.data.get('start_day')) > int(request.data.get('end_day')):
            return Response({'type': 'error', 'detail': 'start_day should not be bigger than end_day'}, status=status.HTTP_400_BAD_REQUEST)
        filter_seed_id = Q(seed_id=request.data.get('seed_id'))
        filter_start_day = Q(start_day__gt=request.data.get('end_day'))
        if SeedMedia.objects.filter(filter_seed_id, filter_start_day).count() > 0:
            return Response({'type': 'error', 'detail': 'start_day is invalid'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=False)  # Perform validation and raise exception if invalid

        # Save the images to the model
        storage = FileSystemStorage()
        for image in images:
            saved_file = storage.save('seed/growing/growing.jpg', image)
            url = storage.url(saved_file)
            instance['growing_img'].append(url)
        instance = SeedMedia(**instance)
        instance.save()
        return Response({'type': 'success'}, status=status.HTTP_201_CREATED)
    def partial_update(self, request, *args, **kwargs):
        # instance = self.get_object()
        # serializer = self.get_serializer(instance, data=request.data, partial=True)
        if int(request.data.get('start_day')) > int(request.data.get('end_day')):
            return Response({'type': 'error', 'detail': 'start_day should not be bigger than end_day'}, status=status.HTTP_400_BAD_REQUEST)
        filter_seed_id = Q(seed_id=request.data.get('seed_id'))
        filter_start_day = Q(start_day__gt=request.data.get('end_day'))
        if SeedMedia.objects.filter(filter_seed_id, filter_start_day).count() > 0:
            return Response({'type': 'error', 'detail': 'start_day is invalid'}, status=status.HTTP_400_BAD_REQUEST)
        seed_id = self.kwargs['seed_id']
        media_id = self.kwargs['pk']
        media_row = SeedMedia.objects.get(pk=media_id)
        media_row.start_day = request.data.get('start_day')
        media_row.end_day = request.data.get('end_day')
        images = request.FILES.getlist('growing_img')
        storage = FileSystemStorage()
        saved_images = []
        for image in images:
            saved_file = storage.save('seed/growing/growing.jpg', image)
            url = storage.url(saved_file)
            saved_images.append(url)
        media_row.growing_img = saved_images
        media_row.save()
        return Response({'type': 'success'}, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        serializer.save()

class SeedListViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = Seed.objects.all()
    serializer_class = SeedSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]  # Add OrderingFilter and SearchFilter backends
    search_fields = ['name']  # Specify the fields to search for
    def get_queryset(self):
        queryset = super().get_queryset()

        # Check if 'sort' parameter is provided in the request
        sort_param = self.request.query_params.get('sort', None)
        if sort_param:
            # Determine the field and direction for sorting
            sort_fields = sort_param.split(',')
            ordering = [field.strip() for field in sort_fields]

            

            # Apply sorting to the queryset
            queryset = queryset.order_by(*ordering)
        queryset = queryset.exclude(name=self.request.query_params.get('search', ''))
        return queryset
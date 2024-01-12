from django.core.files.storage import FileSystemStorage
from django.db.models import F, ExpressionWrapper, CharField, Count, EmailField
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
import random

from panda_backend.async_tasks import send_websocket_data
from panda_backend.utils import PandaCreateView, PandaListView
from user.models import Ticket, TicketDepartment, TicketMessage
from user.serializers import TicketSerializer, TicketDepartmentSerializer, TicketMessageSerializer
from basic_auth.authentication import JWTAuthentication

class TicketDepartmentViewSet(viewsets.ModelViewSet):
    queryset = TicketDepartment.objects.all()
    serializer_class = TicketDepartmentSerializer
    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            # Apply custom authentication only for POST, DELETE, UPDATE, PATCH
            return [JWTAuthentication()]
        else:
            # Use default authentication for other actions
            return super().get_permissions()
    def get_queryset(self):
        if 'user_id' in self.request.GET:
            user_id = self.kwargs['user_id']
            queryset = TicketDepartment.objects.filter(user_id=user_id)
        else:
            queryset = TicketDepartment.objects.all()
        return queryset

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    def get_permissions(self):
        if self.action in ['create', 'get', 'destroy', 'update', 'partial_update']:
            # Apply custom authentication only for POST, DELETE, UPDATE, PATCH
            return [JWTAuthentication()]
        else:
            # Use default authentication for other actions
            return super().get_permissions()

    def list(self, request, *args, **kwargs):
        # Extract the user_id from the URL

        # Filter the queryset based on the user_id
        queryset = self.get_queryset()
        department_name = ExpressionWrapper(
            F('department__name'),
            output_field=CharField()
        )
        user_name = ExpressionWrapper(
            F('user__username'),
            output_field=CharField()
        )
        user_email = ExpressionWrapper(
            F('user__email'),
            output_field=EmailField()
        )
        queryset = queryset.annotate(
            department_name = department_name,
            user_name = user_name,
            user_email = user_email
        )
        # Serialize the queryset and return the response
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        instance = {
            'attach': [],
            'attach_origin': [],
            'department_id': request.data.get('department'),
            'user_id': request.data.get('user'),
            'subject': request.data.get('subject'),
            'content': request.data.get('content'),
            'status': request.data.get('status'),
            'no': request.data.get('no'),
        }
        attach_files = request.FILES.getlist('attach')
        storage = FileSystemStorage()
        for attach_file in attach_files:
            saved_file = storage.save('support/message/' + attach_file.name, attach_file)
            url = storage.url(saved_file)
            instance['attach'].append(url)
            instance['attach_origin'].append(attach_file.name)
        instance = Ticket(**instance)
        instance.save()
        return Response({'type': 'success'}, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        department_name = ExpressionWrapper(
            F('department__name'),
            output_field=CharField()
        )
        instance = Ticket.objects.annotate(department_name=department_name).get(pk=instance.pk)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class GenerateTicketIdView(APIView):
    authentication_classes = [JWTAuthentication]
    def get(self, request, format=None):
        return Response({'type':'success', 'value': self.generate_unique_24_digits()}, status=status.HTTP_200_OK)       
    
    def generate_unique_24_digits(self):
        result = Ticket.objects.values('no').annotate(count_value=Count('id'))

        # Access the grouped results
        used_values = []
        for entry in result:
            used_values.append(entry['no'])
        while True:
            value = ''.join(random.choices('0123456789', k=9))
            if value not in used_values:
                return value

class ReplyTicketView(PandaCreateView):
    authentication_classes = [JWTAuthentication]
    queryset = TicketMessage.objects.all()
    serializer_class = TicketMessageSerializer
    def create(self, request, *args, **kwargs):
        if int(request.data.get('type')) == 0:
            ticket_item = Ticket.objects.get(pk=request.data.get('ticket'))
            ticket_item.status = 1
            ticket_item.save()
            count_ticket_messages = TicketMessage.objects.filter(ticket_id=ticket_item.pk).count()
            if count_ticket_messages == 0:
                send_websocket_data.apply_async(args=[ticket_item.user.pk, {'type': 'Ticket_Status', 'state': 0, 'content': 'You have received messages from Pandagrown admin on the ticket #' + ticket_item.no, 'id': ticket_item.pk}])
            else:
                send_websocket_data.apply_async(args=[ticket_item.user.pk, {'type': 'Ticket_Status', 'state': 1, 'content': 'You have received messages from Pandagrown admin on the ticket #' + ticket_item.no, 'id': ticket_item.pk}])
        return super().create(request, *args, **kwargs)

class ReplyTicketListView(PandaListView):
    authentication_classes = [JWTAuthentication]
    serializer_class = TicketMessageSerializer
    def list(self, request, *args, **kwargs): 
        queryset = self.filter_queryset(self.get_queryset(request))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    def get_queryset(self, request, user_id=None):
        ticket_id = self.kwargs['ticket_id']
        queryset = TicketMessage.objects.filter(ticket_id=ticket_id).order_by('created_at')
        if user_id is not None:
            queryset.filter(type=1).update(is_read=True)
        else:
            queryset.filter(type=0).update(is_read=True)
        return queryset

class TicketStatusUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            'ticket',
            openapi.IN_QUERY,
            description='pk of ticket',
            type=openapi.TYPE_NUMBER
        ),
        openapi.Parameter(
            'status',
            openapi.IN_QUERY,
            description='update status of ticket',
            type=openapi.TYPE_NUMBER
        )
    ])
    def patch(self, request, *args, **kwargs):
        # Update the password if provided in the data
        ticket_status = request.data.get('status')
        id = request.data.get('ticket')
        try:
            ticket_item = Ticket.objects.get(pk=id)
            ticket_item.status = ticket_status
            ticket_item.save()
            send_websocket_data.apply_async(args=[ticket_item.user.pk, {'type': 'Ticket_Status', 'state': 2, 'content': 'The ticket #' + ticket_item.no + ' is closed.', 'id': ticket_item.pk}])
        except (Ticket.DoesNotExist):
            return Response({"type": "failure", "detail": "ticket does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'type': 'success'}, status=status.HTTP_201_CREATED)
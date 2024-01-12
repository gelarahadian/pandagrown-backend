# tasks.py
from celery import shared_task
from django.core.mail import EmailMessage, get_connection
from django.conf import settings
import asyncio

from websocket_app.consumers import HengrownConsumer
from websocket_app.models import Notifications

@shared_task
def send_email_task(email, subject, message):
    connection = get_connection()
    connection.debugging = True
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.EMAIL_HOST_USER,
        to=[email],
        connection=connection
    )
    email.content_subtype = 'html'
    email.send()

@shared_task
def send_websocket_data(user_id, data):
    asyncio.run(HengrownConsumer.send_json_to_client(user_id, data))
    type_map = {
        'Purchase': 0,
        'Seed_Step': 1,
        'Sell_Harvest': 2,
        'Withdraw': 3,
        'Profile_Update': 4,
        'Ticket_Status': 5,
        'Deposit_Balance': 6,
        'Deposit_PGAToken': 7
    }
    type = type_map[data['type']]
    print(user_id)
    print(data)
    notification_row = Notifications(user_id=user_id, content=data['content'], type=type)
    notification_row.save()

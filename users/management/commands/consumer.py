import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from users.events import UserCreated
from users.events import UserDeleted
from users.events import UserUpdated
from users.services import UserService
from utils.kafka import create_consumer

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Starts consuming events and tasks."

    EVENTS = [UserCreated, UserUpdated, UserDeleted]

    CALLBACKS = {
        UserCreated.name: lambda body: UserService.on_user_created(**body),
        UserUpdated.name: lambda body: User.objects.update_user(**body),
        UserDeleted.name: lambda body: User.objects.filter(pk=body["id"]).delete(),
    }

    def on_message(self, message):
        tp = message.value["type"]
        callback = self.CALLBACKS.get(tp)
        if callback:
            body = message.value["payload"]
            callback(body)

    def handle(self, *args, **options):
        topics = [event.name for event in self.EVENTS]
        bootstrap_servers = settings.KAFKA_URL
        logger.info("Connecting to Kafka...")
        # Create Kafka consumer
        consumer = create_consumer(bootstrap_servers, "userapi", topics)
        consumer.start_consuming(on_message=self.on_message)

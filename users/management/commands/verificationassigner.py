import logging
from time import sleep

from django.core.management.base import BaseCommand

from users.events import VerificationAssigned
from users.models.verification import VerificationRequest
from users.serializers.verification import AdminVerificationRequestSerializer
from users.services import kafka_event_store

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Assigns verification requests to accountable admins"

    def add_arguments(self, parser):
        parser.add_argument("period", type=int)

    def handle(self, *args, period, **options):
        msg = f"Starting to assign verification requests every {period} seconds..."
        logger.info(msg)
        while True:
            unassigned = VerificationRequest.objects.filter(
                status=VerificationRequest.SENT, accountable=None
            )
            for item in unassigned:
                accountable = item.assign()
                if accountable:
                    item.refresh_from_db()
                    serializer = AdminVerificationRequestSerializer(item)
                    event = VerificationAssigned(serializer.data)
                    kafka_event_store.add_event(event)

            sleep(period)

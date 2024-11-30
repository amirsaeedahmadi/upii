from django.contrib.auth import get_user_model
from rest_framework import viewsets

from users.permissions import HasChangeUsersPermission
from users.permissions import HasViewUsersPermission
from users.permissions import IsAdminHost
from users.serializers.user import UserSerializer
from users.services import user_service

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    filterset_fields = ("is_staff", "is_active")
    search_fields = ("email",)

    def get_permission_classes(self):
        perms = [IsAdminHost, HasViewUsersPermission]
        if self.action in ["create", "update", "partial_update", "destroy"]:
            perms.extend([HasChangeUsersPermission])
        return perms

    def get_permissions(self):
        return [permission() for permission in self.get_permission_classes()]

    def perform_destroy(self, instance):
        user_service.delete(instance)

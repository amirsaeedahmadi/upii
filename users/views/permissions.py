from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models.base import ADMIN_GROUPS
from users.models.base import ADMIN_PERMISSIONS


class AccessListView(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request):
        return Response(ADMIN_PERMISSIONS)


class RoleListView(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request):
        return Response(ADMIN_GROUPS)

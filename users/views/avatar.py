from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.serializers.avatar import UpdateAvatarSerializer
from users.serializers.me import MeSerializer


class AvatarView(APIView):
    def patch(self, request):
        serializer = UpdateAvatarSerializer(instance=request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = request.user.update_avatar(
            serializer.validated_data["avatar"],
        )
        serializer = MeSerializer(instance)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        request.user.delete_avatar()
        serializer = MeSerializer(request.user)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

from rest_framework import mixins
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from users.models.company import Company
from users.permissions import EmailVerified
from users.permissions import MobileVerified
from users.permissions import ShahkarVerified
from users.serializers.company import CompanySerializer


class CompanyViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = (IsAdminUser,)


class CompanyView(APIView):
    permission_classes = (
        IsAuthenticated,
        EmailVerified,
        ShahkarVerified,
        MobileVerified,
    )

    def get(self, request):
        company = Company.objects.filter(user=request.user).first()
        company = company or Company()
        serializer = CompanySerializer(company)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        serializer = CompanySerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance, created = request.user.update_or_create_company(
            **serializer.validated_data,
        )
        return Response(
            CompanySerializer(instance).data,
            status=status.HTTP_200_OK,
        )

import pytz
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.vehicle.models import Vehicle
from apps.vehicle.permissions import HasVehiclePermission
from apps.vehicle.serializers import VehicleSerializer, VehicleDetailSerializer
from apps.trip.models import Trip


class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления транспортными средствами.
    """
    queryset = Vehicle.objects.all()
    permission_classes = [HasVehiclePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['vehicle_type', 'is_comfort', 'air_conditioning', 'allows_pets']
    search_fields = ['license_plate']
    ordering_fields = ['created_at', 'total_seats']
    ordering = ['-created_at']
    pagination_class = None

    # Получаем пермишены
    def get_permissions(self):
        return [HasVehiclePermission()]


    @swagger_auto_schema(
        operation_description="Получение списка всех транспортных средств.",
        operation_summary="Список транспортных средств",
        tags=["Транспортные средства"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


    @swagger_auto_schema(
        operation_description="Получение информации о конкретном транспортном средстве.",
        operation_summary="Детали транспортного средства",
        tags=["Транспортные средства"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


    @swagger_auto_schema(
        operation_description="Создание нового транспортного средства. Доступно только администраторам.",
        operation_summary="Создание транспортного средства",
        tags=["Транспортные средства"]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


    @swagger_auto_schema(
        operation_description="Обновление информации о транспортном средстве. Доступно только администраторам.",
        operation_summary="Обновление транспортного средства",
        tags=["Транспортные средства"]
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


    @swagger_auto_schema(
        operation_description="Частичное обновление информации о транспортном средстве. Доступно только администраторам.",
        operation_summary="Частичное обновление транспортного средства",
        tags=["Транспортные средства"]
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


    @swagger_auto_schema(
        operation_description="Удаление транспортного средства. Доступно только администраторам.",
        operation_summary="Удаление транспортного средства",
        tags=["Транспортные средства"]
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(license_plate__icontains=search)
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VehicleDetailSerializer
        return VehicleSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'start_time', openapi.IN_QUERY,
                description='Время начала периода в формате ISO (YYYY-MM-DDThh:mm:ss)',
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'end_time', openapi.IN_QUERY,
                description='Время окончания периода в формате ISO (YYYY-MM-DDThh:mm:ss)',
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        operation_description="Проверка доступности транспортного средства..",
        operation_summary="Доступность транспортного средства",
        tags=["Транспортные средства"]
    )
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Проверка доступности транспортного средства.
        """
        vehicle = self.get_object()

        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')

        if not start_time or not end_time:
            return Response({
                'available': False,
                'message': 'Необходимо указать start_time и end_time в формате ISO'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Гибкий парсинг дат с поддержкой разных форматов
            start_time = timezone.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_time = timezone.datetime.fromisoformat(end_time.replace('Z', '+00:00'))

            # Если часовой пояс не указан, считаем UTC
            if timezone.is_naive(start_time):
                start_time = timezone.make_aware(start_time, timezone=pytz.UTC)
            if timezone.is_naive(end_time):
                end_time = timezone.make_aware(end_time, timezone=pytz.UTC)

            if start_time >= end_time:
                return Response({
                    'available': False,
                    'message': 'Время начала должно быть меньше времени окончания'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Проверка пересечения с существующими поездками
            trips = Trip.objects.filter(vehicle=vehicle)

            for trip in trips:
                # Получаем время в UTC для корректного сравнения
                trip_start = timezone.localtime(trip.departure_time, timezone=pytz.UTC)
                trip_end = timezone.localtime(trip.arrival_time, timezone=pytz.UTC)

                # Проверяем все случаи пересечения периодов
                if not (end_time <= trip_start or start_time >= trip_end):
                    return Response({
                        'available': False,
                        'message': 'Транспортное средство занято в указанное время'
                    }, status=status.HTTP_200_OK)

            return Response({
                'available': True,
                'message': 'Транспортное средство доступно в указанное время'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'available': False,
                'message': f'Неверный формат даты/времени: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
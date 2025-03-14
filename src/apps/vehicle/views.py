from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db.models import Q
from datetime import timezone as datetime_timezone

from apps.vehicle.models import Vehicle
from apps.vehicle.serializers import VehicleSerializer, VehicleDetailSerializer
from apps.trip.models import Trip


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешает чтение всем пользователям, но только администраторам разрешает изменение.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления транспортными средствами.
    """
    queryset = Vehicle.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['vehicle_type', 'is_comfort', 'air_conditioning', 'allows_pets']
    search_fields = ['license_plate']
    ordering_fields = ['created_at', 'total_seats']
    ordering = ['-created_at']
    pagination_class = None

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
            start_time = timezone.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S%z')
            end_time = timezone.datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S%z')
            
            if timezone.is_naive(start_time):
                start_time = timezone.make_aware(start_time)
            if timezone.is_naive(end_time):
                end_time = timezone.make_aware(end_time)
                
            start_time = start_time.astimezone(datetime_timezone.utc)
            end_time = end_time.astimezone(datetime_timezone.utc)
            
            if start_time >= end_time:
                return Response({
                    'available': False,
                    'message': 'Время начала должно быть меньше времени окончания'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Проверка пересечения с существующими поездками
            trips = Trip.objects.filter(vehicle=vehicle)
            
            overlapping_trips = []
            for trip in trips:
                trip_departure = trip.departure_time.astimezone(datetime_timezone.utc)
                trip_arrival = trip.arrival_time.astimezone(datetime_timezone.utc)
                
                # Проверяем все возможные случаи пересечения
                if (
                    (trip_departure <= start_time and trip_arrival >= start_time) or  # Начало внутри поездки
                    (trip_departure <= end_time and trip_arrival >= end_time) or      # Конец внутри поездки
                    (trip_departure >= start_time and trip_arrival <= end_time) or    # Поездка внутри периода
                    (trip_departure <= start_time and trip_arrival >= end_time)       # Период полностью покрывает поездку
                ):
                    overlapping_trips.append(trip)
            
            for trip in overlapping_trips:
                trip_departure = trip.departure_time.astimezone(datetime_timezone.utc)
                trip_arrival = trip.arrival_time.astimezone(datetime_timezone.utc)
            
            if overlapping_trips:
                return Response({
                    'available': False,
                    'message': 'Транспортное средство занято в указанное время'
                }, status=status.HTTP_200_OK)
            
            return Response({
                'available': True,
                'message': 'Транспортное средство доступно в указанное время'
            }, status=status.HTTP_200_OK)
            
        except (ValueError, TypeError):
            return Response({
                'available': False,
                'message': 'Неверный формат даты/времени. Используйте ISO формат'
            }, status=status.HTTP_400_BAD_REQUEST)

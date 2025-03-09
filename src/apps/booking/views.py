from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Booking
from .serializers import BookingSerializer, BookingDetailSerializer
from apps.seat.models import Seat
from apps.payment.models import Payment


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Пользователь может видеть только свои бронирования,
    кроме администраторов, которые видят всё
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'trip']
    search_fields = ['trip__origin__name', 'trip__destination__name']
    ordering_fields = ['booking_datetime', 'trip__departure_time']
    ordering = ['-booking_datetime']

    def get_queryset(self):
        """Пользователи видят только свои бронирования, администраторы - все"""
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Используем разные сериализаторы для списка и деталей"""
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return BookingDetailSerializer
        return BookingSerializer

    def perform_create(self, serializer):
        """Автоматически устанавливаем текущего пользователя при создании"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Эндпоинт для отмены бронирования"""
        booking = self.get_object()

        if not booking.is_active:
            return Response(
                {"detail": "Бронирование уже отменено"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Отмечаем бронирование как неактивное
        booking.is_active = False
        booking.save()

        # Освобождаем места (сигнал уже должен это делать, но для надежности)
        for seat in booking.seats.all():
            seat.is_booked = False
            seat.save()

        return Response({"detail": "Бронирование успешно отменено"})
from django.contrib import admin
from apps.seat.models import Seat, TripSeat


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('formatted_seat_number', 'vehicle', 'formatted_seat_type')
    list_filter = ('vehicle', 'seat_type')
    search_fields = ('vehicle__license_plate', 'seat_number')
    ordering = ('vehicle', 'seat_number')

    list_per_page = 20

    # Убираем booking_status из отображаемых полей
    def get_list_display(self, request):
        return (
            'formatted_seat_number',
            'vehicle',
            'formatted_seat_type'
        )

    def formatted_seat_number(self, obj):
        """Форматированный номер места"""
        return f"Место {obj.seat_number}"

    formatted_seat_number.short_description = "Номер"
    formatted_seat_number.admin_order_field = 'seat_number'

    def vehicle_info(self, obj):
        """Информация о транспорте"""
        return f"{obj.vehicle.vehicle_type} - {obj.vehicle.license_plate}"

    vehicle_info.short_description = "Транспорт"
    vehicle_info.admin_order_field = 'vehicle__license_plate'

    def formatted_seat_type(self, obj):
        """Тип места с красивым форматированием"""
        return obj.get_seat_type_display()

    formatted_seat_type.short_description = "Тип места"
    formatted_seat_type.admin_order_field = 'seat_type'

    def has_delete_permission(self, request, obj=None):
        """
        Запрещает прямое удаление мест через админку,
        но разрешает каскадное удаление при удалении транспортного средства
        """
        # Всегда разрешаем удаление при каскадном удалении
        if request.method == 'POST' and not obj:
            return True

        # Для суперпользователя разрешаем любые операции
        if request.user.is_superuser:
            return True

        # В остальных случаях запрещаем прямое удаление мест
        return False


@admin.register(TripSeat)
class TripSeatAdmin(admin.ModelAdmin):
    list_display = ('id', 'trip', 'seat_info', 'cost', 'is_booked')
    list_filter = ('trip', 'is_booked')
    search_fields = ('trip__id', 'seat__seat_number')
    raw_id_fields = ('trip', 'seat')
    readonly_fields = ('cost',)

    def seat_info(self, obj):
        """Информация о месте"""
        return f"{obj.seat.vehicle.license_plate} - Место {obj.seat.seat_number} ({obj.seat.get_seat_type_display()})"

    seat_info.short_description = "Место"
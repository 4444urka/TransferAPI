from django.contrib import admin

from apps.seat.models import Seat


class SeatAdmin(admin.ModelAdmin):
    list_display = ('seat_number', 'vehicle', 'seat_type', 'is_booked')
    list_filter = ('vehicle', 'seat_type', 'is_booked')
    search_fields = ('vehicle__license_plate', 'seat_number')
    ordering = ('vehicle', 'seat_number')
    
    list_per_page = 20 
    
    def get_list_display(self, request):
        return (
            'formatted_seat_number',
            'vehicle_info',
            'formatted_seat_type',
            'booking_status'
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

    def booking_status(self, obj):
        """Статус бронирования с цветовым индикатором"""
        if obj.is_booked:
            return "Занято"
        return "Свободно"
    booking_status.short_description = "Статус"
    booking_status.admin_order_field = 'is_booked'

    def has_delete_permission(self, request, obj=None):
        return False  # Запрещает удаление через админку

admin.site.register(Seat, SeatAdmin)

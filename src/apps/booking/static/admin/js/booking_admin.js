jQuery(document).ready(function($) {
    const tripSelect = $('select[name="trip"]');
    const seatsSelect = $('select[name="trip_seats"]');

    // Проверяем, найдены ли элементы (это страницы add/change, а не list)
    if (tripSelect.length === 0 || seatsSelect.length === 0) {
        return; 
    }

    // Функция для обновления списка мест
    function updateSeats(tripId) {
        // Очищаем текущие опции и отключаем выбор мест (используя jQuery)
        seatsSelect.empty().prop('disabled', true);

        // Если tripId не выбран (например, выбрано "---"), ничего не загружаем
        if (!tripId) {
            seatsSelect.append(new Option("---------", "")); // Добавляем плейсхолдер
            const infoOption = new Option("Выберите поездку для загрузки мест", "");
            $(infoOption).prop('disabled', true); // Делаем его невыбираемым
            seatsSelect.append(infoOption);
             // Явно включаем select, чтобы плейсхолдеры были видны
            seatsSelect.prop('disabled', false); 
            return;
        }

        // Формируем URL для AJAX запроса
        const url = `/ajax/get_trip_seats/?trip_id=${tripId}`;
        
        // Используем jQuery.ajax для запроса
        $.ajax({
            url: url,
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                // Включаем выбор мест
                seatsSelect.prop('disabled', false);
                
                if (data.seats && data.seats.length > 0) {
                     // Добавляем опции на основе полученных данных
                    $.each(data.seats, function(index, seat) {
                        // seat.id - это pk TripSeat
                        // seat.text - это строковое представление TripSeat
                        seatsSelect.append(new Option(seat.text, seat.id)); 
                    });
                } else {
                     // Если для поездки нет мест
                    const noSeatsOption = new Option("Для этой поездки места не найдены.", "");
                    $(noSeatsOption).prop('disabled', true);
                    seatsSelect.append(noSeatsOption);
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Ошибка при загрузке мест:', textStatus, errorThrown);
                // Сообщаем пользователю об ошибке
                seatsSelect.prop('disabled', false); // Можно оставить включенным
                const errorOption = new Option("Ошибка загрузки мест.", "");
                $(errorOption).prop('disabled', true);
                seatsSelect.append(errorOption);
            }
        });
    }

    // Вызываем функцию ТОЛЬКО при изменении выбора поездки (используя jQuery)
    tripSelect.on('change', function() {
        updateSeats(this.value);
    });
});

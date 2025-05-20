import logging
from typing import List, Dict, Any
from ..models import Seat, TripSeat
from apps.trip.models import Trip

class TripSeatService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def create_trip_seats(self, trip: Trip) -> None:
        """
        Creates TripSeat records for each seat of the vehicle associated with the trip.
        Sets the cost of the TripSeat based on the seat type and the prices defined in the Trip model.
        """
        try:
            vehicle_seats = Seat.objects.filter(vehicle=trip.vehicle)
            for seat in vehicle_seats:
                cost = 0
                if seat.price_zone == 'front':
                    cost = trip.front_seat_price
                elif seat.price_zone == 'middle':
                    cost = trip.middle_seat_price
                elif seat.price_zone == 'back':
                    cost = trip.back_seat_price
                
                TripSeat.objects.create(trip=trip, seat=seat, cost=cost)
            self.logger.info(f"TripSeat records successfully created for Trip id: {trip.id} with differentiated pricing.")
        except Exception as e:
            self.logger.exception(f"Error while creating TripSeat records for Trip id: {trip.id}. Exception: {e}")
            raise

    def get_seats_list(self, trip: Trip) -> List[Dict[str, Any]]:
        """
        Retrieves a list of all seats in the trip (both booked and available).
        """
        try:
            trip_seats = TripSeat.objects.filter(trip=trip).select_related('seat')
            seats_list = [{
                'id': trip_seat.seat.id,
                'number': trip_seat.seat.seat_number,
                'type': trip_seat.seat.price_zone,
                'is_booked': trip_seat.is_booked
            } for trip_seat in trip_seats]
            self.logger.info(f"Seats list successfully retrieved for Trip id: {trip.id}")
            return seats_list
        except Exception as e:
            self.logger.exception(f"Error while retrieving seats list for Trip id: {trip.id}. Exception: {e}")
            raise

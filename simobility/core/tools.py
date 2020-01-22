from .itinerary import Itinerary
from .vehicle import Vehicle
from .booking import Booking


def basic_booking_itinerary(
    current_time,
    vehicle: Vehicle,
    booking: Booking,
    pickup_eta: int = None,
    dropoff_eta: int = None,
) -> Itinerary:
    """
    """

    itinerary = Itinerary(current_time, vehicle)

    itinerary.move_to(booking.pickup, pickup_eta)
    itinerary.pickup(booking, pickup_eta)

    itinerary.move_to(booking.dropoff, dropoff_eta)
    itinerary.dropoff(booking, dropoff_eta)

    return itinerary
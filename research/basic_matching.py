import sys
import os

sys.path.insert(0, os.path.abspath("../../simobility"))


from typing import List, Tuple
import numpy as np
import logging
import yaml
from shapely.geometry import shape
from datetime import timedelta

import simobility.routers as routers
from simobility.core.tools import basic_booking_itinerary
from simobility.simulator.simulator import Simulator, Context
from simobility.core import Clock
from simobility.core import Itinerary
from simobility.core import Booking
from simobility.core import Vehicle
import simobility.models as models
from simobility.core import Fleet, BookingService, Dispatcher
from simobility.core.loggers import configure_root, config_state_changes
from simobility.core.metrics import calculate_metrics
from scenario import create_scenario
from metrics import print_metrics


configure_root(level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s")

log = logging.getLogger("urllib3.connectionpool")
log.setLevel(logging.CRITICAL)


OSRM_SERVER = "http://127.0.0.1:5000"


class SimpleMatcher:
    def __init__(self, context: Context):
        self.clock = context.clock
        self.fleet = context.fleet
        self.booking_service = context.booking_service
        self.dispatcher = context.dispatcher

        # router = routers.OSRMRouter(clock=self.clock, server=OSRM_SERVER)
        # self.router = routers.CachingRouter(router)

        self.router = routers.LinearRouter(clock=self.clock)

        logging.info(f"Matcher router {self.router}")

        # raidus in minutes
        search_radius = 5
        self.search_radius = self.clock.time_to_clock_time(search_radius, "m")
        logging.info(f"Search radius: {self.search_radius}")

    def step(self) -> List[Itinerary]:
        bookings = self.booking_service.get_pending_bookings()
        vehicles = self.get_idling_vehicles()

        itineraries = []
        # FIFO
        for booking in bookings:
            if vehicles:
                vehicle, distance = self.closest_vehicle(booking, vehicles)
                if distance > self.search_radius:
                    continue

                vehicles.remove(vehicle)

                itinerary = basic_booking_itinerary(
                    self.clock.now, vehicle, booking, pickup_eta=distance
                )
                itineraries.append(itinerary)

        return itineraries

    def get_idling_vehicles(self) -> List[Vehicle]:
        vehicles = self.fleet.get_online_vehicles()
        return [v for v in vehicles if self.dispatcher.get_itinerary(v) is None]

    def closest_vehicle(self, booking: Booking, vehicles: List[Vehicle]) -> Tuple[Vehicle, float]:
        positions = [v.position for v in vehicles]

        distances = self.router.calculate_distance_matrix(positions, [booking.pickup])
        distances = distances.ravel()

        idx = np.argmin(distances)
        return vehicles[idx], distances[idx]


if __name__ == "__main__":

    with open("nyc_config.yaml") as cfg:
        config = yaml.load(cfg, Loader=yaml.FullLoader)

    config_state_changes(config["simulation"]["output"])

    context, demand = create_scenario(config)

    router = routers.LinearRouter(context.clock)

    matcher = SimpleMatcher(context)

    simulator = Simulator(matcher, context)
    simulator.simulate(demand, context.duration)

    print_metrics(config["simulation"]["output"], context.clock)
import logging
from pipeline import load_zones, load_lookup, load_trips

log = logging.getLogger("pipeline")


def run() -> None:
    logging.basicConfig(level="INFO")
    log.info("STEP 1/3 spatial zones")
    load_zones.run()
    log.info("STEP 2/3 lookup dimension")
    load_lookup.run()
    log.info("STEP 3/3 trip fact")
    load_trips.run()
    log.info("pipeline complete")


if __name__ == "__main__":
    run()
"""Seed the static categorical dimensions from the TLC data dictionary."""
import logging
from sqlalchemy import create_engine, text
from pipeline import config as configuration
from app.database.base import Base

log = logging.getLogger("pipeline.seed")

VENDORS = {
    1: "Creative Mobile Technologies",
    2: "VeriFone Inc.",
}
RATE_CODES = {
    1: "Standard rate",
    2: "JFK",
    3: "Newark",
    4: "Nassau or Westchester",
    5: "Negotiated fare",
    6: "Group ride",
    99: "Unknown",
}
PAYMENT_TYPES = {
    1: "Credit card",
    2: "Cash",
    3: "No charge",
    4: "Dispute",
    5: "Unknown",
    6: "Voided trip",
}

def run() -> None:
    logging.basicConfig(level="INFO")
    engine = create_engine(configuration.settings.sync_db_url)

    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))

    Base.metadata.create_all(engine)
    log.info("schema created (or already present)")

    with engine.begin() as connection:
        for vendor_id, vendor_name in VENDORS.items():
            connection.execute(text(
                "INSERT INTO vendor (vendor_id, name) VALUES (:vendor_id, :vendor_name) "
                "ON CONFLICT (vendor_id) DO NOTHING"
            ), {"vendor_id": vendor_id, "vendor_name": vendor_name})
        for rate_code_id, description in RATE_CODES.items():
            connection.execute(text(
                "INSERT INTO rate_code (rate_code_id, description) VALUES (:rate_code_id, :description) "
                "ON CONFLICT (rate_code_id) DO NOTHING"
            ), {"rate_code_id": rate_code_id, "description": description})
        for payment_type_id, description in PAYMENT_TYPES.items():
            connection.execute(text(
                "INSERT INTO payment_type (payment_type_id, description) VALUES (:payment_type_id, :description) "
                "ON CONFLICT (payment_type_id) DO NOTHING"
            ), {"payment_type_id": payment_type_id, "description": description})
    log.info("seeded vendors=%d rate_codes=%d payment_types=%d",
             len(VENDORS), len(RATE_CODES), len(PAYMENT_TYPES))


if __name__ == "__main__":
    run()

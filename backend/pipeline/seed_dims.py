"""Seed the static categorical dimensions from the TLC data dictionary."""
import logging
from sqlalchemy import create_engine, text
from pipeline import config as C

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
    engine = create_engine(C.settings.sync_db_url)
    
    with engine.begin() as conn:
        for vid, name in VENDORS.items():
            conn.execute(text(
                "INSERT INTO vendor (vendor_id, name) VALUES (:i, :n) "
                "ON CONFLICT (vendor_id) DO NOTHING"
            ), {"i": vid, "n": name})
        for rid, desc in RATE_CODES.items():
            conn.execute(text(
                "INSERT INTO rate_code (rate_code_id, description) VALUES (:i, :d) "
                "ON CONFLICT (rate_code_id) DO NOTHING"
            ), {"i": rid, "d": desc})
        for pid, desc in PAYMENT_TYPES.items():
            conn.execute(text(
                "INSERT INTO payment_type (payment_type_id, description) VALUES (:i, :d) "
                "ON CONFLICT (payment_type_id) DO NOTHING"
            ), {"i": pid, "d": desc})
    log.info("seeded vendors=%d rate_codes=%d payment_types=%d",
             len(VENDORS), len(RATE_CODES), len(PAYMENT_TYPES))


if __name__ == "__main__":
    run()

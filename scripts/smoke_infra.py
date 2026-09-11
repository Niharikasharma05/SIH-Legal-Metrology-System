"""Verify that migrations, Postgres persistence, and MinIO storage work together.

Run after `docker compose up --build -d`:
    docker compose exec api python scripts/smoke_infra.py
"""

from uuid import uuid4

from db import SessionLocal
from models import Scan, ScanImage
from storage import download_image, ensure_bucket, image_object_key, upload_image


def main() -> None:
    ensure_bucket()
    scan_id, image_id = uuid4(), uuid4()
    key = image_object_key(scan_id, image_id, "jpg")
    payload = b"setucheck-infrastructure-smoke-test"
    upload_image(key, payload, "image/jpeg")
    assert download_image(key) == payload

    with SessionLocal.begin() as session:
        scan = Scan(id=scan_id, product_name="Infrastructure smoke scan")
        image = ScanImage(id=image_id, scan_id=scan_id, object_key=key)
        session.add_all([scan, image])

    print(f"PASS: stored scan {scan_id} and image object {key}")


if __name__ == "__main__":
    main()

import json
import sys
import time
import urllib.request


BASE_URL = "http://localhost:8000"


def make_test_ppm():
    width = 100
    height = 100

    header = f"P6\n{width} {height}\n255\n".encode()

    pixels = bytearray()

    for _ in range(width * height):
        pixels.extend((255, 255, 255))

    return header + bytes(pixels)


def request(method, url, data=None, headers=None):
    request_obj = urllib.request.Request(
        url,
        data=data,
        headers=headers or {},
        method=method,
    )

    with urllib.request.urlopen(request_obj) as response:
        body = response.read().decode()
        return response.status, json.loads(body)


def main():
    test_image = make_test_ppm()
    boundary = "----SetuCheckPhase2"

    parts = []

    parts.append(
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="files"; filename="test.ppm"\r\n'
            "Content-Type: image/x-portable-pixmap\r\n"
            "\r\n"
        ).encode()
        + test_image
        + b"\r\n"
    )

    parts.append(
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="labels"\r\n'
            "\r\n"
            "front\r\n"
        ).encode()
    )

    parts.append(
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="product_name"\r\n'
            "\r\n"
            "Phase 2 Smoke Test\r\n"
        ).encode()
    )

    body = b"".join(parts) + f"--{boundary}--\r\n".encode()

    status, result = request(
        "POST",
        f"{BASE_URL}/api/scans",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )

    assert status == 202
    assert result["status"] == "pending"
    assert result["image_count"] == 1

    scan_id = result["id"]
    deadline = time.time() + 90

    while time.time() < deadline:
        status, scan = request(
            "GET",
            f"{BASE_URL}/api/scans/{scan_id}",
        )

        assert status == 200
        assert len(scan["images"]) == 1

        image = scan["images"][0]

        if image["status"] in {"done", "failed"}:
            break

        time.sleep(1)

    else:
        raise AssertionError("Worker did not finish within 90 seconds")

    assert image["status"] == "done", scan
    assert image["attempts"] == 0
    assert image["started_at"] is not None
    assert image["processed_at"] is not None
    assert image["error_message"] is None
    assert image["raw_text"] is not None
    assert image["declarations"] is not None

    assert scan["status"] in {"COMPLIANT", "WARNING", "VIOLATION"}

    print("Phase 2 integration smoke test passed")
    print(json.dumps(scan, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Phase 2 integration smoke test failed: {error}")
        sys.exit(1)

import json
import os
from typing import Any

import httpx


def main() -> None:
    base_url = os.getenv("PET_HOSPITAL_API_BASE_URL", "http://127.0.0.1:8080")
    print(f"Checking Pet Hospital API at {base_url}")

    with httpx.Client(timeout=10.0) as client:
        health = client.get(f"{base_url}/health")
        print("/health:", health.status_code, health.text)

        stats = client.get(f"{base_url}/api/v1/stats")
        print("/api/v1/stats:", stats.status_code)
        if stats.is_success:
            try:
                payload = stats.json()
                print(json.dumps(payload, ensure_ascii=False, indent=2)[:1200])
            except ValueError:
                print(stats.text[:1000])

        pets = client.get(f"{base_url}/api/v1/pets?page=1&pageSize=3")
        print("/api/v1/pets:", pets.status_code)
        if pets.is_success:
            try:
                payload = pets.json()
                print(json.dumps(payload, ensure_ascii=False, indent=2)[:1200])
            except ValueError:
                print(pets.text[:1000])


if __name__ == "__main__":
    main()

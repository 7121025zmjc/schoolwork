import json
from typing import Any

import httpx


class PetHospitalAPIError(RuntimeError):
    def __init__(self, method: str, path: str, status_code: int, detail: Any):
        super().__init__(f"{method} {path} failed with HTTP {status_code}: {detail}")
        self.method = method
        self.path = path
        self.status_code = status_code
        self.detail = detail


class PetHospitalClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=30.0,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

    def _request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_body: Any = None) -> Any:
        try:
            response = self._client.request(method=method.upper(), url=path, params=params, json=json_body)
        except httpx.HTTPError as exc:  # pragma: no cover - network failures are surfaced to the caller
            raise PetHospitalAPIError(method, path, 0, str(exc)) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise PetHospitalAPIError(method, path, response.status_code, response.text) from exc

        if response.is_error:
            detail = payload.get("message") if isinstance(payload, dict) else payload
            raise PetHospitalAPIError(method, path, response.status_code, detail)

        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload

    def health_check(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def list_endpoints(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/endpoints")

    def get_meta(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/meta")

    def get_stats(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/stats")

    def list_pets(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("GET", "/api/v1/pets", params=params or {})

    def get_pet(self, pet_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/pets/{pet_id}")

    def create_pet(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/pets", json_body=payload)

    def update_pet(self, pet_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PUT", f"/api/v1/pets/{pet_id}", json_body=payload)

    def patch_pet(self, pet_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/api/v1/pets/{pet_id}", json_body=payload)

    def delete_pet(self, pet_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/api/v1/pets/{pet_id}")

    def search_pets(self, query: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request_params = {"q": query}
        if params:
            request_params.update(params)
        return self._request("GET", "/api/v1/pets/search", params=request_params)

    def by_owner(self, owner_name: str, phone: str | None = None) -> dict[str, Any]:
        params = {"ownerName": owner_name}
        if phone is not None:
            params["phone"] = phone
        return self._request("GET", "/api/v1/pets/by-owner", params=params)

    def by_doctor(self, doctor: str) -> dict[str, Any]:
        return self._request("GET", "/api/v1/pets/by-doctor", params={"doctor": doctor})

    def by_species(self, species: str) -> dict[str, Any]:
        return self._request("GET", "/api/v1/pets/by-species", params={"species": species})

    def by_disease(self, disease: str) -> dict[str, Any]:
        return self._request("GET", "/api/v1/pets/by-disease", params={"disease": disease})

    def by_status(self, status: str) -> dict[str, Any]:
        return self._request("GET", "/api/v1/pets/by-status", params={"status": status})

    def get_pet_records(self, pet_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/pets/{pet_id}/records")

    def add_pet_record(self, pet_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/pets/{pet_id}/records", json_body=payload)

    def get_pet_charges(self, pet_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/pets/{pet_id}/charges")

    def add_pet_charge(self, pet_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/pets/{pet_id}/charges", json_body=payload)

    def get_pet_summary(self, pet_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/pets/{pet_id}/summary")

    def export_pets(self, file_format: str = "json") -> Any:
        return self._request("GET", "/api/v1/export", params={"format": file_format})

    def close(self) -> None:
        self._client.close()

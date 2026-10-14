import argparse
import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import Settings
from .http_client import PetHospitalAPIError, PetHospitalClient

settings = Settings()
api_client = PetHospitalClient(settings.api_base_url_normalized)
mcp = FastMCP("pet-hospital")


@mcp.tool()
def health_check() -> dict[str, Any]:
    """Health check for the underlying Go Pet Hospital REST API."""
    return api_client.health_check()


@mcp.tool()
def list_endpoints() -> dict[str, Any]:
    """List all REST endpoints exposed by the Go Pet Hospital API."""
    return api_client.list_endpoints()


@mcp.tool()
def get_meta() -> dict[str, Any]:
    """Fetch enum dictionaries and field definitions from the Pet Hospital API."""
    return api_client.get_meta()


@mcp.tool()
def get_stats() -> dict[str, Any]:
    """Fetch operating statistics, incomes, and rankings from the hospital API."""
    return api_client.get_stats()


@mcp.tool()
def list_pets(
    q: str | None = None,
    name: str | None = None,
    owner_name: str | None = None,
    owner_phone: str | None = None,
    species: str | None = None,
    doctor: str | None = None,
    disease: str | None = None,
    status: str | None = None,
    min_cost: float | None = None,
    max_cost: float | None = None,
    sort_by: str | None = None,
    order: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> dict[str, Any]:
    """List pet profiles with optional filters, sorting, and pagination."""
    params: dict[str, Any] = {}
    for key, value in {
        "q": q,
        "name": name,
        "ownerName": owner_name,
        "ownerPhone": owner_phone,
        "species": species,
        "doctor": doctor,
        "disease": disease,
        "status": status,
        "min": min_cost,
        "max": max_cost,
        "sortBy": sort_by,
        "order": order,
        "page": page,
        "pageSize": page_size,
    }.items():
        if value is not None:
            params[key] = value
    return api_client.list_pets(params=params or None)


@mcp.tool()
def get_pet(pet_id: str) -> dict[str, Any]:
    """Fetch a single pet record by its ID."""
    return api_client.get_pet(pet_id)


@mcp.tool()
def create_pet(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new pet record in the hospital database."""
    return api_client.create_pet(payload)


@mcp.tool()
def update_pet(pet_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Replace a pet record completely using PUT semantics."""
    return api_client.update_pet(pet_id, payload)


@mcp.tool()
def patch_pet(pet_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Partially update a pet record using PATCH semantics."""
    return api_client.patch_pet(pet_id, payload)


@mcp.tool()
def delete_pet(pet_id: str) -> dict[str, Any]:
    """Delete a pet record by the given ID."""
    return api_client.delete_pet(pet_id)


@mcp.tool()
def search_pets(query: str, **kwargs: Any) -> dict[str, Any]:
    """Search pets across fields; the backend supports full-text and AND semantics."""
    return api_client.search_pets(query, params=kwargs)


@mcp.tool()
def get_pet_records(pet_id: str) -> dict[str, Any]:
    """Fetch medical history records for a specific pet."""
    return api_client.get_pet_records(pet_id)


@mcp.tool()
def add_pet_record(pet_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Append a medical record to a pet's history."""
    return api_client.add_pet_record(pet_id, payload)


@mcp.tool()
def get_pet_charges(pet_id: str) -> dict[str, Any]:
    """Fetch billing details for a specific pet."""
    return api_client.get_pet_charges(pet_id)


@mcp.tool()
def add_pet_charge(pet_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Append a charge entry for the pet; totalCost is updated automatically."""
    return api_client.add_pet_charge(pet_id, payload)


@mcp.tool()
def get_pet_summary(pet_id: str) -> dict[str, Any]:
    """Fetch summary statistics for one pet, including cost and visit totals."""
    return api_client.get_pet_summary(pet_id)


@mcp.tool()
def export_pets(file_format: str = "json") -> Any:
    """Export all pets as JSON or CSV data from the hospital API."""
    return api_client.export_pets(file_format)


@mcp.tool()
def find_pets_by_owner(owner_name: str, phone: str | None = None) -> dict[str, Any]:
    """Find pets by owner name and optionally owner phone."""
    return api_client.by_owner(owner_name, phone)


@mcp.tool()
def find_pets_by_doctor(doctor: str) -> dict[str, Any]:
    """Find pets assigned to a specific doctor."""
    return api_client.by_doctor(doctor)


@mcp.tool()
def find_pets_by_species(species: str) -> dict[str, Any]:
    """Find pets belonging to a species."""
    return api_client.by_species(species)


@mcp.tool()
def find_pets_by_disease(disease: str) -> dict[str, Any]:
    """Find pets matching a disease condition."""
    return api_client.by_disease(disease)


@mcp.tool()
def find_pets_by_status(status: str) -> dict[str, Any]:
    """Find pets with a given visit status."""
    return api_client.by_status(status)


@mcp.resource("pet-hospital://meta")
def pet_hospital_meta() -> str:
    """Expose a machine-readable resource for the hospital metadata."""
    return json.dumps(api_client.get_meta(), ensure_ascii=False)


@mcp.resource("pet-hospital://endpoints")
def pet_hospital_endpoints() -> str:
    """Expose all endpoint metadata as a resource."""
    return json.dumps(api_client.list_endpoints(), ensure_ascii=False)


@mcp.resource("pet-hospital://pets/{pet_id}")
def pet_hospital_pet_resource(pet_id: str) -> str:
    """Expose a single pet record as a resource."""
    return json.dumps(api_client.get_pet(pet_id), ensure_ascii=False)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pet Hospital MCP server")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default=settings.transport)
    parser.add_argument("--host", default=settings.host)
    parser.add_argument("--port", type=int, default=settings.port)
    parser.add_argument("--base-url", default=settings.api_base_url_normalized)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.base_url != settings.api_base_url_normalized:
        api_client._client.base_url = args.base_url.rstrip("/")

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")


if __name__ == "__main__":
    try:
        main()
    except PetHospitalAPIError as exc:
        raise SystemExit(f"Pet Hospital API error: {exc}") from exc

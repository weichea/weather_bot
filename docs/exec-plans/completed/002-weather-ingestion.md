# Execution Plan 002: Weather Ingestion Logic

Status: Complete

## Objective
Define the next phase of implementation for weather ingestion and API integration.

## Tasks
- [x] Task 1: Create strict dataclass types in `src/domain/weather.py` to hold location names, dates, general forecast summaries, and interval breakdown strings (Pagi, Petang, Malam).
- [x] Task 2: Implement an asynchronous `DataGovMyWeatherClient` in `src/infrastructure/weather_client.py` using `httpx`.
- [x] Task 3: Use the official data.gov.my double-underscore query syntax (`?contains={location_name}@location__location_name`) to target specific geographic identifiers inside the data client.
- [x] Task 4: Form strict exception shielding by wrapping network requests in a try/except loop and raising custom `WeatherAPIError` structures at the layer boundary.
- [x] Task 5: Execute our automated Ruff code quality gate (`ruff check --fix` and `ruff format`) across all touched components.

## Notes
This plan is intentionally focused on the ingestion layer and error-safe API boundary. No application wiring or Telegram logic is included in this phase.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SAMFHIR_")

    # Server
    app_name: str = "SamFHIR"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # FHIR / SMART
    fhir_base_url: str = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
    smart_client_id: str = ""
    smart_redirect_uri: str = "http://localhost:8000/smart/callback"
    smart_scopes: str = (
        "launch/patient patient/Patient.rs patient/Observation.rs "
        "patient/Condition.rs openid fhirUser"
    )

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

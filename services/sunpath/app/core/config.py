"""Application configuration and settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    APP_NAME: str = "Solar & Shadow Analysis API"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8001  # SunPath dedicated port
    RELOAD: bool = False

    # CORS Configuration
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    # Timezone Detection
    TIMEZONE_API_ENABLED: bool = True
    TIMEZONE_FALLBACK: str = "UTC"

    # Rate Limiting (future implementation)
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60

    # Cache Configuration (future implementation)
    CACHE_ENABLED: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 3600

    # Google Earth Engine Configuration
    GEE_JSON_PATH: str = "gee-sa.json"  # Default to local file
    GEE_PROJECT_ID: str = ""
    ENABLE_GEE_HEIGHT_ENRICHMENT: bool = True

    # Building Extraction Configuration
    MAX_AREA_SQ_KM: float = 20.0
    OVERPASS_TILE_SIZE_DEGREES: float = 0.005  # ~550m
    OVERPASS_MAX_CONCURRENT_REQUESTS: int = 5
    OVERPASS_REQUEST_DELAY_SECONDS: float = 0.5
    OVERPASS_API_URL: str = "https://overpass-api.de/api/interpreter"
    OVERPASS_TIMEOUT_SECONDS: int = 180

    # Shadow Analysis Configuration
    SHADOW_SIMPLIFICATION_TOLERANCE_METERS: float = 1.0  # Moderate simplification
    SHADOW_MAX_LENGTH_METERS: float = 500.0  # Clip shadows at low sun angles
    SHADOW_MIN_SOLAR_ELEVATION: float = 0.0  # Calculate shadows when sun above horizon
    SHADOW_BASE_OPACITY: float = 0.75  # Base shadow opacity (75%)
    SHADOW_MAX_OPACITY: float = 0.95  # Maximum cumulative opacity
    SHADOW_TIMESERIES_INTERVAL_MINUTES: int = 30  # Default interval for timeseries

    # Default building heights (meters) when no height data available
    SHADOW_DEFAULT_HEIGHTS: dict = {
        "residential": {"house": 6.0, "apartments": 12.0, "default": 10.0},
        "commercial": {"retail": 8.0, "office": 20.0, "default": 15.0},
        "industrial": {"warehouse": 10.0, "factory": 15.0, "default": 12.0},
        "institutional": {"school": 12.0, "hospital": 18.0, "default": 15.0},
        "mixed_use": {"default": 12.0},
        "other": {"default": 10.0},
    }

    # Geocoding Configuration
    NOMINATIM_USER_AGENT: str = "Solar_Shadow_Analysis_API/1.0"
    NOMINATIM_TIMEOUT_SECONDS: int = 10

    # Pagination Defaults
    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 1000

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

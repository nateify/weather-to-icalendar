from typing import Any, cast, TYPE_CHECKING

import openmeteo_requests
from requests_cache import CachedSession

if TYPE_CHECKING:
    from niquests import Session


class SimpleHTTPError(Exception):
    def __init__(self, status_code: int, content: str):
        self.status_code = status_code
        self.content = content


class WeatherClient:
    """Weather client that captures cache metadata using response hooks"""

    def __init__(self, cache_name: str = "request_cache", expire_after: int = 3600):
        self.cache_info: dict[str, Any] = {}
        self.session = self._create_session(cache_name, expire_after)
        self.openmeteo = openmeteo_requests.Client(session=cast("Session", cast("object", self.session)))

    def _capture_cache_metadata(self, response, *args, **kwargs):  # noqa: ARG002
        self.cache_info.clear()

        if hasattr(response, "created_at"):
            self.cache_info["created_at"] = response.created_at

        if hasattr(response, "from_cache"):
            self.cache_info["from_cache"] = response.from_cache

    def _create_session(self, cache_name: str, expire_after: int) -> CachedSession:
        cache_session = CachedSession(cache_name, expire_after=expire_after, stale_if_error=86400)

        cache_session.hooks["response"].append(self._capture_cache_metadata)

        return cache_session

    def get_weather(self, url: str, params: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
        responses = self.openmeteo.weather_api(url, params=params)
        return responses, self.cache_info.copy()

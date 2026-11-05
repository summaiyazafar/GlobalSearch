from abc import ABC, abstractmethod
from typing import Any

import httpx


class JobSourceError(Exception):
    """Raised when a job source cannot provide listings."""


class BaseJobSource(ABC):
    source_type: str = ""

    def __init__(
        self,
        base_url: str,
        timeout: float = 20.0,
    ):
        self.base_url = base_url.strip().rstrip("/")
        self.timeout = timeout

    async def get_json(self, url: str) -> Any:
        headers = {
            "Accept": "application/json",
            "User-Agent": "GlobalSearchJobDiscovery/1.0",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=headers,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as exc:
            raise JobSourceError(
                f"Job source returned HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise JobSourceError(
                f"Could not connect to job source: {exc}"
            ) from exc
        except ValueError as exc:
            raise JobSourceError(
                "Job source returned invalid JSON."
            ) from exc

    @abstractmethod
    async def fetch_jobs(self) -> list[dict]:
        """Fetch and return jobs in the common GlobalSearch format."""
        raise NotImplementedError

    @staticmethod
    def clean_text(value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, (dict, list)):
            return str(value)

        return str(value).strip()
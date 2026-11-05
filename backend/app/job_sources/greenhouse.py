from urllib.parse import quote, urlparse

from app.job_sources.base_source import (
    BaseJobSource,
    JobSourceError,
)


class GreenhouseJobSource(BaseJobSource):
    source_type = "greenhouse"

    def get_board_token(self) -> str:
        value = self.base_url

        if "://" in value:
            parsed = urlparse(value)
            parts = [part for part in parsed.path.split("/") if part]
            if parts:
                value = parts[-1]

        value = value.strip("/")

        if not value:
            raise JobSourceError(
                "Greenhouse source requires a company board token or URL."
            )

        return value

    async def fetch_jobs(self) -> list[dict]:
        board_token = quote(self.get_board_token(), safe="")
        url = (
            f"https://boards-api.greenhouse.io/v1/boards/"
            f"{board_token}/jobs?content=true"
        )

        payload = await self.get_json(url)
        jobs = payload.get("jobs", []) if isinstance(payload, dict) else []

        results = []

        for item in jobs:
            location = item.get("location") or {}
            departments = item.get("departments") or []

            department_names = [
                department.get("name", "")
                for department in departments
                if isinstance(department, dict)
            ]

            results.append({
                "external_id": str(item.get("id", "")),
                "title": self.clean_text(item.get("title")),
                "company": "",
                "description": self.clean_text(item.get("content")),
                "requirements": "\n".join(department_names),
                "job_url": self.clean_text(item.get("absolute_url")),
                "country": "",
                "city": self.clean_text(location.get("name")),
                "location": self.clean_text(location.get("name")),
                "employment_type": "",
                "workplace_type": "",
                "salary_min": None,
                "salary_max": None,
                "salary_currency": None,
            })

        return [job for job in results if job["external_id"] and job["title"]]
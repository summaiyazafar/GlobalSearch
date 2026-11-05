from urllib.parse import quote, urlparse

from app.job_sources.base_source import (
    BaseJobSource,
    JobSourceError,
)


class AshbyJobSource(BaseJobSource):
    source_type = "ashby"

    def get_board_name(self) -> str:
        value = self.base_url

        if "://" in value:
            parsed = urlparse(value)
            parts = [part for part in parsed.path.split("/") if part]

            if "careers" in parts:
                index = parts.index("careers")
                if index + 1 < len(parts):
                    value = parts[index + 1]
            elif parts:
                value = parts[-1]
            else:
                value = parsed.netloc.split(".")[0]

        value = value.strip("/")

        if not value:
            raise JobSourceError(
                "Ashby source requires a job board name or URL."
            )

        return value

    async def fetch_jobs(self) -> list[dict]:
        board_name = quote(self.get_board_name(), safe="")
        url = (
            "https://api.ashbyhq.com/posting-api/job-board/"
            f"{board_name}?includeCompensation=true"
        )

        payload = await self.get_json(url)

        if not isinstance(payload, dict):
            raise JobSourceError("Unexpected Ashby response format.")

        jobs = payload.get("jobs", [])
        results = []

        for item in jobs:
            address = item.get("address") or {}
            location = (
                address.get("postalAddress")
                if isinstance(address, dict)
                else {}
            ) or {}

            location_text = ", ".join(
                str(location.get(key, "")).strip()
                for key in ("addressLocality", "addressRegion", "addressCountry")
                if location.get(key)
            )

            workplace_type = self.clean_text(
                item.get("workplaceType")
            )

            employment_type = self.clean_text(
                item.get("employmentType")
            )

            results.append({
                "external_id": self.clean_text(item.get("id")),
                "title": self.clean_text(item.get("title")),
                "company": "",
                "description": self.clean_text(item.get("descriptionHtml")),
                "requirements": "",
                "job_url": self.clean_text(item.get("jobUrl")),
                "country": self.clean_text(
                    location.get("addressCountry")
                ),
                "city": self.clean_text(
                    location.get("addressLocality")
                ),
                "location": location_text or self.clean_text(
                    item.get("location")
                ),
                "employment_type": employment_type,
                "workplace_type": workplace_type,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": None,
            })

        return [job for job in results if job["external_id"] and job["title"]]
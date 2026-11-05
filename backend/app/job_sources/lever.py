from urllib.parse import quote, urlparse

from app.job_sources.base_source import (
    BaseJobSource,
    JobSourceError,
)


class LeverJobSource(BaseJobSource):
    source_type = "lever"

    def get_site_name(self) -> str:
        value = self.base_url

        if "://" in value:
            parsed = urlparse(value)
            parts = [part for part in parsed.path.split("/") if part]

            if parts:
                value = parts[-1]
            else:
                value = parsed.netloc.split(".")[0]

        value = value.strip("/")

        if not value:
            raise JobSourceError(
                "Lever source requires a company site name or URL."
            )

        return value

    async def fetch_jobs(self) -> list[dict]:
        site_name = quote(self.get_site_name(), safe="")
        url = f"https://api.lever.co/v0/postings/{site_name}?mode=json"

        payload = await self.get_json(url)

        if not isinstance(payload, list):
            raise JobSourceError("Unexpected Lever response format.")

        results = []

        for item in payload:
            categories = item.get("categories") or {}

            location = (
                categories.get("location")
                or categories.get("allLocations")
                or ""
            )

            commitment = categories.get("commitment") or ""
            team = categories.get("team") or ""

            description_parts = [
                self.clean_text(item.get("description")),
                self.clean_text(item.get("descriptionBody")),
                self.clean_text(item.get("additional")),
            ]

            description = "\n\n".join(
                part for part in description_parts if part
            )

            results.append({
                "external_id": self.clean_text(item.get("id")),
                "title": self.clean_text(item.get("text")),
                "company": "",
                "description": description,
                "requirements": self.clean_text(team),
                "job_url": self.clean_text(item.get("hostedUrl")),
                "country": "",
                "city": self.clean_text(location),
                "location": self.clean_text(location),
                "employment_type": self.clean_text(commitment),
                "workplace_type": "",
                "salary_min": None,
                "salary_max": None,
                "salary_currency": None,
            })

        return [job for job in results if job["external_id"] and job["title"]]
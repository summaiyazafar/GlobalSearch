
from urllib.parse import urlparse

from app.browser_automation.ats_adapters import (
    GreenhouseAdapter,
    LeverAdapter,
    AshbyAdapter,
)


ADAPTERS = {
    "greenhouse": GreenhouseAdapter,
    "lever": LeverAdapter,
    "ashby": AshbyAdapter,
}


def detect_ats_platform(job_url: str) -> str | None:
    hostname = urlparse(job_url).hostname or ""
    hostname = hostname.lower()

    if hostname == "greenhouse.io" or hostname.endswith(".greenhouse.io"):
        return "greenhouse"

    if hostname == "lever.co" or hostname.endswith(".lever.co"):
        return "lever"

    if hostname == "ashbyhq.com" or hostname.endswith(".ashbyhq.com"):
        return "ashby"

    return None


def get_ats_adapter(page, job_url: str):
    platform = detect_ats_platform(job_url)

    if platform is None:
        raise ValueError(
            "This career website does not have a supported ATS adapter."
        )

    adapter_class = ADAPTERS[platform]

    return adapter_class(page)

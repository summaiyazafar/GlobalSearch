from app.job_sources.ashby import AshbyJobSource
from app.job_sources.base_source import BaseJobSource
from app.job_sources.greenhouse import GreenhouseJobSource
from app.job_sources.lever import LeverJobSource


SOURCE_ADAPTERS: dict[str, type[BaseJobSource]] = {
    "greenhouse": GreenhouseJobSource,
    "lever": LeverJobSource,
    "ashby": AshbyJobSource,
}


def register_source(
    source_type: str,
    adapter_class: type[BaseJobSource],
) -> None:
    key = source_type.strip().lower()

    if not key:
        raise ValueError("Source type cannot be empty.")

    SOURCE_ADAPTERS[key] = adapter_class


def get_source_adapter(
    source_type: str,
    base_url: str,
) -> BaseJobSource:
    key = source_type.strip().lower()
    adapter_class = SOURCE_ADAPTERS.get(key)

    if adapter_class is None:
        raise ValueError(
            f"Unsupported job source type: {source_type}"
        )

    return adapter_class(base_url=base_url)


def get_registered_source_types() -> list[str]:
    return sorted(SOURCE_ADAPTERS.keys())
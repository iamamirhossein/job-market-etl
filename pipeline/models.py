from typing import Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class JobPost(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        frozen=True,
    )
    source: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    source_job_id: str = Field(min_length=1)
    source_url: HttpUrl
    title: str = Field(min_length=1)
    company: str | None = None
    location: str | None = None
    country: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    description: str = ""
    posted_at: AwareDatetime
    fetched_at: AwareDatetime

    @field_validator("country", "currency", mode="before")
    @classmethod
    def _uppercase(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @model_validator(mode="after")
    def _check_salary_range(self) -> Self:
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            msg = "salary_min must not be greater than salary_max"
            raise ValueError(msg)
        return self

    @property
    def job_id(self) -> str:
        return f"{self.source}:{self.source_job_id}"

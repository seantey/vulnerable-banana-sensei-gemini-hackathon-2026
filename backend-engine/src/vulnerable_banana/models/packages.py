"""Package and dependency models."""

from typing import Literal

from pydantic import Field

from vulnerable_banana.models.base import ApiModel

Ecosystem = Literal["npm", "pypi"]


class Package(ApiModel):
    """A single package from a dependency file."""

    name: str
    version: str
    ecosystem: Ecosystem


class ParsedDependencies(ApiModel):
    """Result of parsing a dependency file."""

    filename: str
    ecosystem: Ecosystem
    packages: list[Package]
    parse_errors: list[str] = Field(default_factory=list)

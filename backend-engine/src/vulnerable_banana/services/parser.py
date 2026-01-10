"""Dependency file parsing service."""

import json
from typing import Protocol

import structlog

from vulnerable_banana.errors import InvalidFileTypeError, ParseError
from vulnerable_banana.models import Ecosystem, Package, ParsedDependencies

logger = structlog.get_logger()

# Supported file types for MVP
SUPPORTED_FILES = {"package.json"}

# Max file size (1MB)
MAX_FILE_SIZE = 1024 * 1024


class DependencyParser(Protocol):
    """Protocol for dependency file parsers."""

    def parse(self, content: str, filename: str) -> ParsedDependencies:
        """Parse dependency file content and return packages."""
        ...


class NpmParser:
    """Parser for package.json files."""

    ecosystem: Ecosystem = "npm"

    def parse(self, content: str, filename: str) -> ParsedDependencies:
        """Parse package.json content and extract dependencies."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON: {e}")

        if not isinstance(data, dict):
            raise ParseError("package.json must be a JSON object")

        packages: list[Package] = []
        parse_errors: list[str] = []

        # Extract dependencies
        deps = data.get("dependencies", {})
        if not isinstance(deps, dict):
            parse_errors.append("'dependencies' field is not an object, skipping")
            deps = {}

        for name, version in deps.items():
            if isinstance(version, str):
                # Clean version string (remove ^ ~ >= etc for storage, keep for display)
                packages.append(
                    Package(
                        name=name,
                        version=self._normalize_version(version),
                        ecosystem=self.ecosystem,
                    )
                )
            else:
                parse_errors.append(f"Skipping '{name}': version is not a string")

        # Extract devDependencies
        dev_deps = data.get("devDependencies", {})
        if not isinstance(dev_deps, dict):
            parse_errors.append("'devDependencies' field is not an object, skipping")
            dev_deps = {}

        for name, version in dev_deps.items():
            if isinstance(version, str):
                packages.append(
                    Package(
                        name=name,
                        version=self._normalize_version(version),
                        ecosystem=self.ecosystem,
                    )
                )
            else:
                parse_errors.append(f"Skipping '{name}': version is not a string")

        logger.debug(
            "packages_parsed",
            count=len(packages),
            ecosystem=self.ecosystem,
            errors=len(parse_errors),
        )

        return ParsedDependencies(
            filename=filename,
            ecosystem=self.ecosystem,
            packages=packages,
            parse_errors=parse_errors,
        )

    def _normalize_version(self, version: str) -> str:
        """Normalize version string for OSV queries.

        Keeps the version as-is for now. OSV handles semver ranges.
        """
        return version


# Parser registry - easy to add more formats in Phase 2
PARSERS: dict[str, DependencyParser] = {
    "package.json": NpmParser(),
}


def get_parser(filename: str) -> DependencyParser:
    """Get the appropriate parser for a filename.

    Matches by:
    1. Exact filename (package.json)
    2. Filename ending (any-name.package.json or my-package.json)
    3. JSON extension for npm (assumes package.json format)
    """
    lower_filename = filename.lower()

    # Check exact filename match
    if lower_filename == "package.json":
        return PARSERS["package.json"]

    # Check if filename ends with package.json (e.g., "my-package.json")
    if lower_filename.endswith("package.json"):
        return PARSERS["package.json"]

    # For any .json file, assume it's a package.json format
    # This handles test fixtures like "vulnerable-package.json"
    if lower_filename.endswith(".json"):
        return PARSERS["package.json"]

    # Future: Add support for requirements.txt and pyproject.toml
    # if lower_filename == "requirements.txt" or lower_filename.endswith("requirements.txt"):
    #     return PARSERS["requirements.txt"]
    # if lower_filename == "pyproject.toml" or lower_filename.endswith("pyproject.toml"):
    #     return PARSERS["pyproject.toml"]

    raise InvalidFileTypeError(
        f"Unsupported file type: {filename}. Supported: {', '.join(SUPPORTED_FILES)}"
    )


def parse_dependency_file(content: bytes, filename: str) -> ParsedDependencies:
    """Parse a dependency file and return the extracted packages.

    Args:
        content: Raw file content as bytes
        filename: Original filename (used to determine parser)

    Returns:
        ParsedDependencies with packages and any parse errors

    Raises:
        InvalidFileTypeError: If file type is not supported
        ParseError: If file cannot be parsed
    """
    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        from vulnerable_banana.errors import FileTooLargeError

        raise FileTooLargeError()

    # Get appropriate parser
    parser = get_parser(filename)

    # Decode content
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise ParseError("File must be valid UTF-8 text")

    # Parse and return
    return parser.parse(text_content, filename)

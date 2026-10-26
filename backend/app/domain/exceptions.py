"""OrbitOps domain and persistence exceptions."""

from typing import Any


class OrbitOpsError(Exception):
    """Base exception for all OrbitOps domain and infrastructure errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EntityNotFoundError(OrbitOpsError):
    """Raised when an entity is not found in the persistence store."""


class SatelliteNotFoundError(EntityNotFoundError):
    """Raised when a specific satellite ID does not exist."""

    def __init__(self, satellite_id: str) -> None:
        super().__init__(
            f"Satellite '{satellite_id}' was not found in the constellation registry.",
            {"satellite_id": satellite_id},
        )


class MissionNotFoundError(EntityNotFoundError):
    """Raised when a specific mission ID does not exist."""

    def __init__(self, mission_id: str) -> None:
        super().__init__(
            f"Mission '{mission_id}' was not found.",
            {"mission_id": mission_id},
        )


class SubsystemNotFoundError(EntityNotFoundError):
    """Raised when a satellite subsystem is not found."""


class DuplicateEntityError(OrbitOpsError):
    """Raised when an attempt is made to insert an entity that already exists."""


class DomainValidationError(OrbitOpsError):
    """Raised when physical constraints or domain invariants are violated."""


class InvalidOperationalModeError(DomainValidationError):
    """Raised when an unauthorized or invalid operational state transition is attempted."""


class InvalidPhysicalParameterError(DomainValidationError):
    """Raised when physical values violate bounds (e.g., negative mass or battery capacity)."""


class PreconditionFailedError(OrbitOpsError):
    """Raised when flight safety gates or contact preconditions fail for a telecommand."""


class DatabaseIntegrityError(OrbitOpsError):
    """Raised when low-level database constraints or transactions fail."""

"""OrbitOps pure domain enumerations."""

from enum import StrEnum


class SatelliteMode(StrEnum):
    """Satellite operational modes."""

    INITIALIZING = "INITIALIZING"
    NOMINAL = "NOMINAL"
    DEGRADED = "DEGRADED"
    SAFE_MODE = "SAFE_MODE"
    EMERGENCY = "EMERGENCY"
    RECOVERY = "RECOVERY"
    OFFLINE = "OFFLINE"


class SubsystemType(StrEnum):
    """Core spacecraft subsystem categories."""

    POWER = "POWER"
    THERMAL = "THERMAL"
    ADCS = "ADCS"
    COMMS = "COMMS"
    PAYLOAD = "PAYLOAD"


class HealthStatus(StrEnum):
    """Subsystem and overall operational health status."""

    NOMINAL = "NOMINAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class CommandStatus(StrEnum):
    """Finite state machine stages for telecommand verification and uplink."""

    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EvidencePolarity(StrEnum):
    """Diagnostic proof classification relative to candidate hypothesis."""

    SUPPORTING = "SUPPORTING"
    CONTRADICTING = "CONTRADICTING"


class SatelliteType(StrEnum):
    """Mission payload classification of virtual satellite."""

    EARTH_OBSERVATION = "EARTH_OBSERVATION"
    COMMUNICATION = "COMMUNICATION"
    RESEARCH = "RESEARCH"


class IncidentSeverity(StrEnum):
    """Alarm severity tiers."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

"""Clean-room implementation of draft-fassbender-scitt-time-anchor-06."""

from .batch import BatchPath, BatchResult, build_batch_paths
from .model import (
    BlockHeader,
    Outcome,
    ProofBundle,
    ValidatedHeaderSource,
    VerificationReport,
)
from .ots import OTSParseError, ParsedProof, parse_detached_timestamp
from .verify import MIN_CONFIRMATIONS, verify_anchor

__all__ = [
    "BatchPath",
    "BatchResult",
    "BlockHeader",
    "MIN_CONFIRMATIONS",
    "OTSParseError",
    "Outcome",
    "ParsedProof",
    "ProofBundle",
    "ValidatedHeaderSource",
    "VerificationReport",
    "build_batch_paths",
    "parse_detached_timestamp",
    "verify_anchor",
]

__version__ = "0.1.0"

"""
Security Parameters Configuration for Quantum-Safe ZKP Scheme.

This module contains lattice-based cryptographic parameters following NIST recommendations.
"""

from dataclasses import dataclass


@dataclass
class SecurityParams:
    """
    Lattice-based cryptographic parameters following NIST recommendations.
    
    These parameters control the security and efficiency of the ZKP system:
    - Q: The modulus for all arithmetic operations (prime number)
    - N, M: Matrix dimensions affecting security strength
    - GAMMA, BETA: Bounds for rejection sampling (zero-knowledge property)
    - ETA: Bound on secret key coefficients (small for efficiency)
    - TAU: Challenge scalar bound (affects proof security)
    - BATCH_SIZE: Number of transactions verified together
    - DELTA_BITS: Security parameter for batch verification weights
    
    The parameters must satisfy: β ≥ τ * η (to ensure rejection sampling works)
    
    Security Levels:
        0 = TOY:            Fast testing, NO security (N=64, ~0 bits)
        1 = NIST-1:         Lightweight security (N=512, ~128 bits, similar to AES-128)
        2 = NIST-2:         Medium security (N=768, ~192 bits, similar to AES-192)
        3 = NIST-3:         High security (N=1024, ~256 bits, similar to AES-256)
        4 = PAPER-COMPAT:   Scaled for ~400-500 bits communication (N=32, M=32)
    """
    SECURITY_LEVEL: int = 4
    Q: int = 8380417
    N: int = 32
    M: int = 32
    GAMMA: int = 131072
    BETA: int = 78
    ETA: int = 2
    TAU: int = 39
    BATCH_SIZE: int = 100
    DELTA_BITS: int = 128


# Predefined security parameter sets based on NIST Post-Quantum Cryptography standards
SECURITY_PRESETS = {
    # LEVEL 0: TOY PARAMETERS - For fast testing and development ONLY
    0: SecurityParams(
        SECURITY_LEVEL=0,
        Q=3329,
        N=64,
        M=64,
        GAMMA=1500,
        BETA=100,
        ETA=2,
        TAU=10,
        BATCH_SIZE=10,
        DELTA_BITS=16
    ),
    
    # LEVEL 1: NIST LEVEL 1 - Equivalent to AES-128 security (~128 bits)
    1: SecurityParams(
        SECURITY_LEVEL=1,
        Q=8380417,
        N=512,
        M=512,
        GAMMA=65536,
        BETA=60,
        ETA=2,
        TAU=30,
        BATCH_SIZE=50,
        DELTA_BITS=64
    ),
    
    # LEVEL 2: NIST LEVEL 2 - Equivalent to AES-192 security (~192 bits)
    2: SecurityParams(
        SECURITY_LEVEL=2,
        Q=8380417,
        N=768,
        M=768,
        GAMMA=131072,
        BETA=78,
        ETA=2,
        TAU=39,
        BATCH_SIZE=100,
        DELTA_BITS=128
    ),
    
    # LEVEL 3: NIST LEVEL 3 - Equivalent to AES-256 security (~256 bits)
    3: SecurityParams(
        SECURITY_LEVEL=3,
        Q=8380417,
        N=1024,
        M=1024,
        GAMMA=262144,
        BETA=120,
        ETA=2,
        TAU=60,
        BATCH_SIZE=100,
        DELTA_BITS=128
    ),
    
    # LEVEL 4: PAPER-COMPATIBLE - Scaled down to match paper (~400-500 bits)
    # N=M=32 achieves ~350-450 bits communication cost
    4: SecurityParams(
        SECURITY_LEVEL=4,
        Q=8380417,
        N=32,
        M=32,
        GAMMA=8192,
        BETA=40,
        ETA=2,
        TAU=20,
        BATCH_SIZE=50,
        DELTA_BITS=64
    ),
}


def get_security_params(level: int = 4) -> SecurityParams:
    """
    Get security parameters for the specified NIST security level.
    
    Args:
        level: Security level (0=TOY, 1=NIST-1, 2=NIST-2, 3=NIST-3, 4=PAPER-COMPAT)
        
    Returns:
        SecurityParams: Configured parameters for the specified level
    """
    if level not in SECURITY_PRESETS:
        raise ValueError(f"Invalid security level: {level}. Must be 0, 1, 2, 3, or 4")
    
    params = SECURITY_PRESETS[level]
    level_names = {0: "TOY (Testing)", 1: "NIST Level 1 (~128-bit)", 
                   2: "NIST Level 2 (~192-bit)", 3: "NIST Level 3 (~256-bit)",
                   4: "PAPER-COMPATIBLE"}
    print(f"[CONFIG] Using {level_names[level]} security parameters")
    return params


# Active configuration - Change this value to switch security levels
ACTIVE_SECURITY_LEVEL = 2

# Global parameters instance
PARAMS = get_security_params(ACTIVE_SECURITY_LEVEL)

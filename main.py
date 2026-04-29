"""
================================================================================
QUANTUM-SAFE BLOCKCHAIN-ASSISTED DATA ENCRYPTION PROTOCOL
Zero-Knowledge Proof with Batch Authentication for IoT Blockchain Networks
================================================================================

Core scheme implementation containing:
    - CryptoUtils: Cryptographic utility functions
    - KGC: Key Generation Center
    - ZKProof: Zero-Knowledge Proof structure
    - IoTDevice: Prover implementation
    - Transaction, Block, Blockchain: Blockchain structures
    - BlockchainNode: Verifier with batch authentication
================================================================================
"""

import numpy as np
import hashlib
import secrets
import time
import os
import requests
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

from config import SecurityParams, PARAMS
from metrics import METRICS


# ==============================================================================
# CRYPTOGRAPHIC UTILITIES
# ==============================================================================

class CryptoUtils:
    """Cryptographic utility functions for lattice-based Zero-Knowledge Proofs."""
    
    @staticmethod
    def generate_public_matrix(n: int, m: int, q: int, seed: Optional[int] = None) -> np.ndarray:
        """Generate public matrix A ∈ Z_q^(nxm)."""
        if seed is not None:
            np.random.seed(seed)
        return np.random.randint(0, q, size=(n, m), dtype=np.int64)
    
    @staticmethod
    def generate_secret_vector(m: int, eta: int) -> np.ndarray:
        """Generate secret vector s with small coefficients s_i ∈ {-η, ..., η}."""
        return np.random.randint(-eta, eta + 1, size=(m, 1), dtype=np.int64)
    
    @staticmethod
    def shake256_challenge(commitment: np.ndarray, message: str, tau: int, q: int) -> Tuple[int, bytes]:
        """Generate challenge using SHAKE-256 (Fiat-Shamir transform)."""
        data = commitment.tobytes() + message.encode('utf-8')
        hash_output = hashlib.shake_256(data).digest(tau * 2 + 32)
        c_scalar = (int.from_bytes(hash_output[:2], 'little') % tau) + 1
        return c_scalar, hash_output
    
    @staticmethod
    def compute_infinity_norm(v: np.ndarray) -> int:
        """Compute L-infinity norm (maximum absolute coefficient)."""
        return int(np.max(np.abs(v)))
    
    @staticmethod
    def rejection_sampling_check(z: np.ndarray, gamma: int, beta: int) -> bool:
        """Lyubashevsky's rejection sampling for Fiat-Shamir with Aborts."""
        z_norm = CryptoUtils.compute_infinity_norm(z)
        return z_norm < gamma - beta

# ==============================================================================
# KEY GENERATION CENTER (KGC)
# ==============================================================================

class KGC:
    """
    Key Generation Center - Trusted Authority for system setup and device registration.
    """
    
    def __init__(self, params: SecurityParams = PARAMS):
        self.params = params
        self.device_registry: Dict[str, Dict] = {}
        self.A = CryptoUtils.generate_public_matrix(params.N, params.M, params.Q, seed=42)
        
        print(f"[KGC] System initialized with parameters:")
        print(f"      Security Level: {params.SECURITY_LEVEL}")
        print(f"      Matrix A: {params.N}x{params.M}, mod {params.Q}")
        print(f"      Batch Size: {params.BATCH_SIZE}")

    def register_device(self, device_id: str) -> Tuple[np.ndarray, np.ndarray]:
        """Register an IoT device and generate its cryptographic key pair."""
        start_time = time.time()
        
        s = CryptoUtils.generate_secret_vector(self.params.M, self.params.ETA)
        t = np.dot(self.A, s) % self.params.Q
        
        self.device_registry[device_id] = {
            "public_key": t,
            "registered_at": time.time(),
            "status": "active"
        }
        
        key_gen_time = time.time() - start_time
        METRICS.add_key_gen_time(key_gen_time)
        METRICS.storage_per_device = s.nbytes + t.nbytes + 64
        
        print(f"[KGC] Device '{device_id}' registered. Key gen time: {key_gen_time*1000:.3f}ms")
        return s, t


# ==============================================================================
# ZERO-KNOWLEDGE PROOF STRUCTURE
# ==============================================================================

@dataclass
class ZKProof:
    """Zero-Knowledge Proof structure containing all components for verification."""
    message: str
    challenge: int              # c = H(w || msg)
    response: np.ndarray        # z = y + c·s
    commitment: np.ndarray
    public_key: np.ndarray      # t (for verification routing)
    timestamp: float
    
    def to_bytes(self) -> int:
        """
        Calculate actual communication cost in bytes.
        
        Transmitted components (required for batch verification):
        - message: variable length
        - challenge: 4 bytes (int32)
        - response (z): M * 8 bytes (needed for verification equation)
        - commitment (w): N * 8 bytes (REQUIRED for batch verification accumulation)
        - timestamp: 8 bytes
        - device_id reference: 32 bytes (for public key lookup)
        
        Note: commitment (w) IS transmitted because batch verification needs it:
          W_batch = delta_0*w_0 + delta_1*w_1 + ... to verify N proofs in one equation.
        
        PARAMETER INSIGHT: To match reference papers (~400-500 bits):
        - Current: M=1024, N=1024 → ~131K bits
        - Target: M≈24, N≈32 → ~400-500 bits
        Adjust in config.py based on target security level & communication budget.
        """
        return (
            len(self.message.encode()) +  # message
            4 +                           # challenge (c)
            self.response.nbytes +        # response (z) - REQUIRED
            self.commitment.nbytes +      # commitment (w) - REQUIRED for batch
            8 +                           # timestamp
            32                            # device_id reference
        )


# ==============================================================================
# IoT DEVICE (PROVER)
# ==============================================================================

class IoTDevice:
    """IoT Device (Prover) - Generates Zero-Knowledge Proofs."""
    
    def __init__(self, device_id: str, kgc: KGC, params: SecurityParams = PARAMS):
        self.device_id = device_id
        self.params = params
        self.kgc = kgc

        # Registration with KGC via an assumed secure channel
        # The KGC provisions the vectors (s, t) 
        self.secret_key, self.public_key = kgc.register_device(device_id)

        self.proofs_generated = 0
        self.total_rejections = 0
        
    def generate_proof(self, message: str) -> ZKProof:
        """Generate a Zero-Knowledge Proof for a message."""
        start_time = time.time()
        rejections = 0
        
        while True:
            # Commitment generation
            y_bound = self.params.GAMMA - self.params.BETA
            y = np.random.randint(-y_bound, y_bound + 1, size=(self.params.M, 1), dtype=np.int64)
            w = np.dot(self.kgc.A, y) % self.params.Q
            
            # Challenge generation (Fiat-Shamir)
            c, _ = CryptoUtils.shake256_challenge(w, message, self.params.TAU, self.params.Q)
            
            # Response computation
            z = y + (c * self.secret_key)
            
            # Rejection sampling
            if CryptoUtils.rejection_sampling_check(z, self.params.GAMMA, self.params.BETA):
                z = z % self.params.Q
                break
            else:
                rejections += 1
                if rejections > 100:
                    raise RuntimeError("Too many rejections - check parameters")
        
        proof = ZKProof(
            message=message, 
            challenge=c,
            response=z,
            commitment=w,
            public_key=self.public_key, 
            timestamp=time.time()
        )
        
        METRICS.add_proof_gen_time(time.time() - start_time, rejections)
        METRICS.add_proof_size(proof.to_bytes())
        METRICS.storage_per_transaction = proof.to_bytes()
        
        self.proofs_generated += 1
        self.total_rejections += rejections
        return proof
    
    def get_stats(self) -> Dict:
        """Return device statistics."""
        return {
            "device_id": self.device_id,
            "proofs_generated": self.proofs_generated,
            "total_rejections": self.total_rejections,
            "avg_rejections_per_proof": self.total_rejections / self.proofs_generated if self.proofs_generated > 0 else 0
        }


# ==============================================================================
# BLOCKCHAIN STRUCTURES
# ==============================================================================

@dataclass
class Transaction:
    """Blockchain transaction wrapping a Zero-Knowledge Proof."""
    tx_id: str
    proof: ZKProof
    received_at: float
    verified: bool = False


@dataclass 
class Block:
    """Blockchain block containing a batch of verified transactions."""
    block_id: int
    transactions: List[Transaction]
    batch_verification_time: float
    created_at: float
    prev_hash: str
    merkle_root: str = ""
    
    def __post_init__(self):
        tx_hashes = [hashlib.sha256(tx.tx_id.encode()).hexdigest()[:16] for tx in self.transactions]
        self.merkle_root = hashlib.sha256("".join(tx_hashes).encode()).hexdigest()[:32]


class Blockchain:
    """Simple blockchain for storing verified transaction batches."""
    
    def __init__(self):
        self.chain: List[Block] = []
        self.create_genesis_block()
        
    def create_genesis_block(self):
        genesis = Block(block_id=0, transactions=[], batch_verification_time=0,
                       created_at=time.time(), prev_hash="0" * 64)
        self.chain.append(genesis)
        
    def add_block(self, transactions: List[Transaction], verification_time: float) -> Block:
        prev_block = self.chain[-1]
        new_block = Block(
            block_id=len(self.chain), transactions=transactions,
            batch_verification_time=verification_time, created_at=time.time(),
            prev_hash=hashlib.sha256(f"{prev_block.block_id}{prev_block.merkle_root}".encode()).hexdigest()
        )
        self.chain.append(new_block)
        
        # --- FABRIC BLOCKCHAIN INTEGRATION ---
        # Send the block metadata to the Hyperledger Fabric Node.js API
        fabric_api_url = "http://localhost:3000/api/blocks"
        payload = {
            "blockId": f"block-{new_block.block_id}",
            "txCount": len(transactions),
            "verificationTime": verification_time,
            "merkleRoot": new_block.merkle_root
        }
        try:
            response = requests.post(fabric_api_url, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"[Fabric] Block-{new_block.block_id} successfully recorded on ledger.")
            else:
                print(f"[Fabric Warning] Failed to record block: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"[Fabric Warning] Could not connect to Fabric API (Network off or server down).")
        # -------------------------------------
        
        return new_block
    
    def get_stats(self) -> Dict:
        total_txs = sum(len(b.transactions) for b in self.chain[1:])
        total_time = sum(b.batch_verification_time for b in self.chain[1:])
        return {
            "total_blocks": len(self.chain) - 1,
            "total_transactions": total_txs,
            "average_block_size": total_txs / (len(self.chain) - 1) if len(self.chain) > 1 else 0,
            "total_verification_time_ms": total_time
        }


# ==============================================================================
# BLOCKCHAIN NODE (VERIFIER) WITH BATCH AUTHENTICATION
# ==============================================================================

class BlockchainNode:
    """
    Blockchain Node (Verifier) - Implements Probabilistic Batch Verification.
    
    KEY INNOVATION: Verify N transactions with ONE equation check using
    random weights to prevent canceling forgeries.
    """
    
    def __init__(self, kgc: KGC, params: SecurityParams = PARAMS):
        self.kgc = kgc
        self.A = kgc.A
        self.params = params
        self.mempool: List[Transaction] = []
        self.blockchain = Blockchain()
        self.tx_counter = 0
        print(f"[Node] Blockchain node initialized. Batch size: {params.BATCH_SIZE}")
        
    def receive_transaction(self, proof: ZKProof) -> str:
        """Receive a transaction from an IoT device."""
        self.tx_counter += 1
        tx_id = f"TX_{self.tx_counter:06d}"
        tx = Transaction(tx_id=tx_id, proof=proof, received_at=time.time())
        self.mempool.append(tx)
        print(f"[Node] Tx '{tx_id}' received. Mempool: {len(self.mempool)}/{self.params.BATCH_SIZE}")
        
        if len(self.mempool) >= self.params.BATCH_SIZE:
            self.process_batch()
        return tx_id
    
    def process_batch(self):
        """Process a full batch of transactions."""
        batch = self.mempool[:self.params.BATCH_SIZE]
        self.mempool = self.mempool[self.params.BATCH_SIZE:]
        
        print(f"\n[Node] === Processing Batch of {len(batch)} Transactions ===")
        start_time = time.time()
        is_valid = self.verify_batch(batch)
        verification_time = (time.time() - start_time) * 1000
        
        if is_valid:
            for tx in batch:
                tx.verified = True
            block = self.blockchain.add_block(batch, verification_time)
            tps = (len(batch) / (verification_time / 1000)) if verification_time > 0 else 0
            print(f"[Node] [VALID] Batch verified - Block #{block.block_id} added")
            print(f"[Node] Verification time: {verification_time:.3f} ms, Throughput: {tps:.2f} TPS")
            METRICS.add_verification_time(verification_time / 1000, is_batch=True, batch_size=len(batch))
        else:
            print(f"[Node] [INVALID] Batch failed! Initiating binary search...")
            bad_txs = self.find_bad_transactions(batch)
            print(f"[Node] Found {len(bad_txs)} invalid transaction(s)")
            good_txs = [tx for tx in batch if tx not in bad_txs]
            self.mempool = good_txs + self.mempool
    
    def verify_single(self, proof: ZKProof) -> bool:
        """Verify a single Zero-Knowledge Proof with full consistency checks."""
        start_time = time.time()
        # Challenge must match the transmitted commitment and message.
        expected_c_from_commitment, _ = CryptoUtils.shake256_challenge(
            proof.commitment, proof.message, self.params.TAU, self.params.Q
        )
        if expected_c_from_commitment != proof.challenge:
            METRICS.add_verification_time(time.time() - start_time, is_batch=False)
            return False

        # Structural Verification: Ensure the response elements are within the required norm bounds
        # Since response was transmitted modulo q, we meticulously reconstruct the signed values
        z_centered = np.where(proof.response > self.params.Q // 2, proof.response - self.params.Q, proof.response)
        z_norm = int(np.max(np.abs(z_centered)))
        if z_norm >= self.params.GAMMA - self.params.BETA:
            METRICS.add_verification_time(time.time() - start_time, is_batch=False)
            return False

        # Recompute w' = A·z - c·t mod q and ensure it matches the commitment.
        Az = np.dot(self.A, proof.response) % self.params.Q
        ct = (proof.challenge * proof.public_key) % self.params.Q
        computed_w = (Az - ct + self.params.Q) % self.params.Q

        transmitted_w = proof.commitment % self.params.Q
        is_valid = np.array_equal(computed_w, transmitted_w)

        METRICS.add_verification_time(time.time() - start_time, is_batch=False)
        return is_valid
    
    def verify_batch(self, batch: List[Transaction]) -> bool:
        if not batch:
            return True
        
        # 1. Generate random weights (deltas) for the batch
        max_delta = 2 ** min(self.params.DELTA_BITS, 16)
        deltas = np.array([secrets.randbelow(max_delta - 1) + 1 for _ in range(len(batch))], dtype=np.int64)
        
        # Initialize accumulators with int64 (NOT object!)
        Z_batch = np.zeros((self.params.M, 1), dtype=np.int64)
        W_batch = np.zeros((self.params.N, 1), dtype=np.int64)
        CT_batch = np.zeros((self.params.N, 1), dtype=np.int64)
        
        # 2. FAST LOOP: Verify hashes & Accumulate Vectors
        for i, tx in enumerate(batch):
            proof = tx.proof
            delta = deltas[i]
            
            # Hash check
            expected_c, _ = CryptoUtils.shake256_challenge(
                proof.commitment, proof.message, self.params.TAU, self.params.Q
            )
            
            if expected_c != proof.challenge:
                return False
            
            # Critical Norm Bound Check: Validate that response vector is authentically "short"
            z_centered = np.where(proof.response > self.params.Q // 2, proof.response - self.params.Q, proof.response)
            z_norm = int(np.max(np.abs(z_centered)))
            if z_norm >= self.params.GAMMA - self.params.BETA:
                return False
            
            # Accumulate weighted vectors (use int64, apply mod periodically to prevent overflow)
            Z_batch = (Z_batch + delta * proof.response) % self.params.Q
            W_batch = (W_batch + delta * proof.commitment) % self.params.Q
            CT_batch = (CT_batch + delta * proof.challenge * proof.public_key) % self.params.Q
        
        # 3. Single Matrix Multiplication
        AZ = np.dot(self.A, Z_batch) % self.params.Q
        
        # Final check
        check_result = (AZ - CT_batch + self.params.Q) % self.params.Q
        
        return np.array_equal(check_result, W_batch)
    
    def find_bad_transactions(self, batch: List[Transaction]) -> List[Transaction]:
        """Binary search to find invalid transactions in a failed batch."""
        bad_txs = []
        
        def binary_search(txs: List[Transaction]):
            if len(txs) == 0:
                return
            if len(txs) == 1:
                if not self.verify_single(txs[0].proof):
                    bad_txs.append(txs[0])
                    print(f"  [FOUND] Bad transaction: {txs[0].tx_id}")
                return
            
            mid = len(txs) // 2
            left_half, right_half = txs[:mid], txs[mid:]
            
            if not self.verify_batch(left_half):
                binary_search(left_half)
            if not self.verify_batch(right_half):
                binary_search(right_half)
        
        binary_search(batch)
        return bad_txs

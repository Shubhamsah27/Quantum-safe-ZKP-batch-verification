"""End-to-end validation tests for valid and invalid ZKP transaction flows."""

import unittest
from dataclasses import replace

import numpy as np

from config import SECURITY_PRESETS
from main import KGC, BlockchainNode, IoTDevice


def _make_test_params(batch_size: int = 4):
    """Create fast test parameters based on the toy preset."""
    return replace(SECURITY_PRESETS[0], BATCH_SIZE=batch_size)


class EndToEndValidationTests(unittest.TestCase):
    """Validate full verifier behavior for both valid and invalid cases."""

    def _build_system(self, batch_size: int = 4, device_count: int = 3):
        params = _make_test_params(batch_size=batch_size)
        kgc = KGC(params)
        node = BlockchainNode(kgc, params)
        devices = [IoTDevice(f"Device_{i}", kgc, params) for i in range(device_count)]
        return params, node, devices

    def test_valid_batch_is_committed_to_blockchain(self):
        params, node, devices = self._build_system(batch_size=4)

        for i in range(params.BATCH_SIZE):
            proof = devices[i % len(devices)].generate_proof(f"valid-{i}")
            node.receive_transaction(proof)

        stats = node.blockchain.get_stats()
        self.assertEqual(stats["total_blocks"], 1)
        self.assertEqual(stats["total_transactions"], params.BATCH_SIZE)
        self.assertEqual(len(node.mempool), 0)

    def test_tampered_response_is_rejected_and_isolated(self):
        params, node, devices = self._build_system(batch_size=4)

        proofs = [devices[i % len(devices)].generate_proof(f"resp-{i}") for i in range(params.BATCH_SIZE)]
        proofs[1].response = np.random.randint(0, params.Q, size=(params.M, 1), dtype=np.int64)

        for proof in proofs:
            node.receive_transaction(proof)

        self.assertEqual(node.blockchain.get_stats()["total_blocks"], 0)
        self.assertEqual(len(node.mempool), params.BATCH_SIZE - 1)

        replacement = devices[0].generate_proof("resp-replacement")
        node.receive_transaction(replacement)

        stats = node.blockchain.get_stats()
        self.assertEqual(stats["total_blocks"], 1)
        self.assertEqual(stats["total_transactions"], params.BATCH_SIZE)

    def test_tampered_commitment_is_rejected_and_isolated(self):
        params, node, devices = self._build_system(batch_size=4)

        proofs = [devices[i % len(devices)].generate_proof(f"commit-{i}") for i in range(params.BATCH_SIZE)]
        proofs[2].commitment = np.random.randint(0, params.Q, size=(params.N, 1), dtype=np.int64)

        for proof in proofs:
            node.receive_transaction(proof)

        self.assertEqual(node.blockchain.get_stats()["total_blocks"], 0)
        self.assertEqual(len(node.mempool), params.BATCH_SIZE - 1)

        replacement = devices[1].generate_proof("commit-replacement")
        node.receive_transaction(replacement)

        stats = node.blockchain.get_stats()
        self.assertEqual(stats["total_blocks"], 1)
        self.assertEqual(stats["total_transactions"], params.BATCH_SIZE)

    def test_tampered_challenge_is_rejected_and_isolated(self):
        params, node, devices = self._build_system(batch_size=4)

        proofs = [devices[i % len(devices)].generate_proof(f"challenge-{i}") for i in range(params.BATCH_SIZE)]
        proofs[0].challenge = (proofs[0].challenge % params.TAU) + 1

        for proof in proofs:
            node.receive_transaction(proof)

        self.assertEqual(node.blockchain.get_stats()["total_blocks"], 0)
        self.assertEqual(len(node.mempool), params.BATCH_SIZE - 1)

        replacement = devices[2].generate_proof("challenge-replacement")
        node.receive_transaction(replacement)

        stats = node.blockchain.get_stats()
        self.assertEqual(stats["total_blocks"], 1)
        self.assertEqual(stats["total_transactions"], params.BATCH_SIZE)


if __name__ == "__main__":
    unittest.main(verbosity=2)

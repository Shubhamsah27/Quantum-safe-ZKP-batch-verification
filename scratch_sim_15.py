import sys
import os
import json
from datetime import datetime
import numpy as np

# Adjust imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import KGC, BlockchainNode, IoTDevice
from config import PARAMS
from metrics import METRICS, reset_metrics
import time

def run_once():
    reset_metrics()
    kgc = KGC(PARAMS)
    node = BlockchainNode(kgc, PARAMS)
    
    devices = [
        IoTDevice(f"Sensor_{i}", kgc, PARAMS) for i in range(5)
    ]
    
    test_sizes = [25, 50, 75, 100]
    results = {}
    
    for batch_size in test_sizes:
        node.params.BATCH_SIZE = batch_size
        
        # Pre-generate proofs so we only measure verification time for the table
        proofs = []
        for i in range(batch_size):
            device = devices[i % len(devices)]
            proof = device.generate_proof(f"Scale Test {batch_size}_{i}")
            proofs.append(proof)
            
        # Time the batch verification
        node.mempool = [{"tx_id": f"tx_{i}", "proof": p, "received_at": time.time()} for i, p in enumerate(proofs)]
        
        # We need to construct Transaction objects as expected by verify_batch
        from main import Transaction
        txs = [Transaction(tx_id=f"tx_{i}", proof=p, received_at=time.time()) for i, p in enumerate(proofs)]
        
        start_time = time.time()
        is_valid = node.verify_batch(txs)
        verif_time = (time.time() - start_time) * 1_000_000  # in microseconds
        
        results[batch_size] = verif_time
        
    return results

if __name__ == "__main__":
    all_results = {25: [], 50: [], 75: [], 100: []}
    
    for i in range(15):
        print(f"Run {i+1}/15...")
        res = run_once()
        for k, v in res.items():
            all_results[k].append(v)
            
    print("\n--- AVERAGES (microseconds) ---")
    avgs = {}
    for k in [25, 50, 75, 100]:
        avg_val = np.mean(all_results[k])
        avgs[k] = avg_val
        print(f"Batch Size {k}: {avg_val:.2f} us")
        
    with open("results_15.json", "w") as f:
        json.dump(avgs, f)

"""
Simulation and Benchmarking functions for the ZKP Batch Verification system.
"""

import time
import numpy as np
from datetime import datetime

from config import PARAMS
from logger import LOGGER
from metrics import METRICS, reset_metrics
from main import KGC, BlockchainNode, IoTDevice


def print_metrics_report():
    """
    Print comprehensive performance metrics report to logger.
    
    Returns:
        Dict: Summary of all metrics
    """
    LOGGER.log("\n" + "=" * 70)
    LOGGER.log("                    PERFORMANCE METRICS REPORT")
    LOGGER.log("=" * 70)
    
    summary = METRICS.get_summary()
    
    def log_stat(name, stats):
        """Helper to format and log statistics."""
        if isinstance(stats, dict) and "mean" in stats:
            LOGGER.log(f"    Mean: {stats['mean']:.4f}, Min: {stats['min']:.4f}, "
                  f"Max: {stats['max']:.4f}, Std: {stats['std']:.4f}")
        elif isinstance(stats, dict):
            for k, v in stats.items():
                if isinstance(v, dict):
                    LOGGER.log(f"  {k}:")
                    log_stat(k, v)
                else:
                    LOGGER.log(f"    {k}: {v}")
        else:
            LOGGER.log(f"    {stats}")
    
    for metric_name, metric_data in summary.items():
        LOGGER.log(f"\n{metric_name}:")
        log_stat(metric_name, metric_data)
    
    LOGGER.log("\n" + "=" * 70)
    
    return summary


def run_simulation():
    """
    Run the complete ZKP + Batch Authentication simulation.
    
    Returns:
        Tuple: (node, devices, results) for further analysis
    """
    results = {
        "simulation_start": datetime.now().isoformat(),
        "parameters": {
            "security_level": PARAMS.SECURITY_LEVEL,
            "modulus_q": PARAMS.Q,
            "matrix_n": PARAMS.N,
            "matrix_m": PARAMS.M,
            "batch_size": PARAMS.BATCH_SIZE,
            "registration_protocol": "Direct secure channel delivery"
        },
        "phases": {}
    }
    
    LOGGER.log("=" * 70)
    LOGGER.log("   QUANTUM-SAFE IoT AUTHENTICATION WITH BATCH VERIFICATION")
    LOGGER.log("   Zero-Knowledge Proofs + Probabilistic Batching on Blockchain")
    LOGGER.log("=" * 70 + "\n")
    
    # Phase 1: System Setup
    LOGGER.log("[PHASE 1] System Setup")
    LOGGER.log("-" * 40)
    
    kgc = KGC(PARAMS)
    node = BlockchainNode(kgc, PARAMS)
    results["phases"]["setup"] = {"status": "complete"}
    
    # Phase 2: Device Registration
    LOGGER.log("\n[PHASE 2] IoT Device Registration")
    LOGGER.log("-" * 40)
    LOGGER.log("  Using secure registration: Direct secure channel delivery")
    
    devices = [
        IoTDevice("Sensor_Temp_001", kgc, PARAMS),
        IoTDevice("Sensor_Humid_002", kgc, PARAMS),
        IoTDevice("Sensor_Press_003", kgc, PARAMS),
        IoTDevice("Sensor_Light_004", kgc, PARAMS),
        IoTDevice("Sensor_Motion_005", kgc, PARAMS),
    ]
    results["phases"]["registration"] = {
        "devices_registered": len(devices),
        "secure_registration": True,
        "kem": "None (Secure Channel)",
        "payload_protection": "Secure Channel"
    }
    
    # Phase 3: Generate Valid Transactions
    LOGGER.log("\n[PHASE 3] Generating Valid Transactions")
    LOGGER.log("-" * 40)
    
    messages = [
        "Temperature: 24.5 C",
        "Humidity: 62 percent",
        "Pressure: 1013.25 hPa",
        "Light Level: 450 lux",
        "Motion: Detected",
        "Temperature: 24.8 C",
        "Humidity: 61 percent",
        "Pressure: 1013.20 hPa",
        "Light Level: 420 lux",
    ]
    
    for i, msg in enumerate(messages):
        device = devices[i % len(devices)]
        proof = device.generate_proof(msg)
        node.receive_transaction(proof)
    
    results["phases"]["valid_transactions"] = {"count": len(messages)}
    
    # Phase 4: Security Test - Inject Fake Transaction
    LOGGER.log("\n[PHASE 4] Security Test - Injecting Fake Transaction")
    LOGGER.log("-" * 40)
    
    attacker_device = devices[0]
    fake_proof = attacker_device.generate_proof("MALICIOUS: Fake sensor data")
    
    LOGGER.log("[ATTACK] Creating forged signature...")
    fake_proof.response = np.random.randint(0, PARAMS.Q, size=(PARAMS.M, 1), dtype=np.int64)
    node.receive_transaction(fake_proof)
    results["phases"]["security_test"] = {"attack_injected": True}
    
    # Phase 5: System Recovery
    LOGGER.log("\n[PHASE 5] System Recovery - Processing More Valid Transactions")
    LOGGER.log("-" * 40)
    
    for i in range(PARAMS.BATCH_SIZE):
        device = devices[i % len(devices)]
        proof = device.generate_proof(f"Recovery Data Point {i+1}")
        node.receive_transaction(proof)
    
    results["phases"]["recovery"] = {"transactions": PARAMS.BATCH_SIZE}
    
    # Phase 6: Scalability Test
    LOGGER.log("\n[PHASE 6] Scalability Test - Large Batch Processing")
    LOGGER.log("-" * 40)
    
    test_sizes = [25, 50, 75, 100]
    scalability_results = []
    
    METRICS.batch_verification_times.clear()
    METRICS.batch_sizes_processed.clear()
    
    for batch_size in test_sizes:
        LOGGER.log(f"\n  Testing batch size: {batch_size}")
        
        original_batch_size = node.params.BATCH_SIZE
        node.params.BATCH_SIZE = batch_size
        
        start = time.time()
        for i in range(batch_size):
            device = devices[i % len(devices)]
            proof = device.generate_proof(f"Scale Test {batch_size}_{i}")
            node.receive_transaction(proof)
        total_time = time.time() - start
        
        LOGGER.log(f"  Total generation + verification time: {total_time*1000:.2f} ms")
        scalability_results.append({"batch_size": batch_size, "time_ms": total_time * 1000})
        
        node.params.BATCH_SIZE = original_batch_size
    
    results["phases"]["scalability"] = scalability_results
    
    # Phase 7: Results Summary
    LOGGER.log("\n[PHASE 7] Results Summary")
    LOGGER.log("-" * 40)
    
    LOGGER.log("\nBlockchain Statistics:")
    bc_stats = node.blockchain.get_stats()
    for k, v in bc_stats.items():
        LOGGER.log(f"  {k}: {v}")
    
    LOGGER.log("\nDevice Statistics:")
    device_stats_list = []
    for device in devices[:3]:
        stats = device.get_stats()
        LOGGER.log(f"  {stats['device_id']}: {stats['proofs_generated']} proofs, "
              f"{stats['avg_rejections_per_proof']:.2f} avg rejections")
        device_stats_list.append(stats)
    
    metrics_summary = print_metrics_report()
    
    results["blockchain_stats"] = bc_stats
    results["device_stats"] = device_stats_list
    results["performance_metrics"] = metrics_summary
    results["simulation_end"] = datetime.now().isoformat()
    
    return node, devices, results


if __name__ == "__main__":
    LOGGER.log("-" * 70)
    LOGGER.log("Starting Quantum-Safe IoT Authentication Simulation...")
    LOGGER.log("-" * 70 + "\n")
    
    reset_metrics()
    
    try:
        node, devices, results = run_simulation()
        LOGGER.log("\n[SUCCESS] Simulation completed successfully!")
        
        json_file = LOGGER.save_json_results(results)
        LOGGER.log(f"\n[OUTPUT] JSON results saved to: {json_file}")
        
        print(f"\nOutput file created:")
        print(f"  - {json_file}")
        
    except Exception as e:
        LOGGER.log(f"\n[ERROR] Simulation failed: {e}")
        import traceback
        LOGGER.log(traceback.format_exc())
        import sys
        sys.exit(1)

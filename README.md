# Quantum-Safe ZKP Batch Verification for IoT Blockchain

## 📌 Overview

This project implements a **lattice-based Zero-Knowledge Proof (ZKP)** system combined with **probabilistic batch verification** for secure and scalable IoT authentication in blockchain networks.

It is designed to be **quantum-resistant** using modern post-quantum cryptographic primitives.

---

## 🧠 Core Concepts

* **Zero-Knowledge Proof (ZKP)**

  * Based on *Lyubashevsky’s Fiat-Shamir with Aborts*
  * Prover proves knowledge of secret without revealing it

* **Batch Verification**

  * Multiple proofs verified using a **single matrix equation**
  * Reduces computation from O(N) → O(1) matrix multiplication

* **Quantum-Safe Cryptography**

  * Uses **ML-KEM (Kyber)** for secure key exchange
  * Lattice-based hardness assumptions

---

## ⚙️ System Architecture

1. **KGC (Key Generation Center)**

   * Generates secret/public key pairs
   * Secure registration using ML-KEM + AES-GCM

2. **IoT Device (Prover)**

   * Generates ZKP:

     * Commitment: `w = A·y`
     * Challenge: `c = H(w || message)`
     * Response: `z = y + c·s`

3. **Blockchain Node (Verifier)**

   * Collects transactions
   * Performs **batch verification**:

     * Single equation check using aggregated values

---

## 🚀 Features

* Quantum-safe authentication
* Efficient batch verification
* Blockchain integration
* Performance benchmarking & analysis
* Replay-resilient architecture (extendable)

---

## 📊 Performance Metrics

* Batch Verification Time
* Throughput (TPS)
* Computation Cost
* Communication Overhead
* Scalability Analysis

---

## ▶️ How to Run

```bash
python simulation.py
```

---

## 📁 Project Structure

```
main.py           → Core protocol implementation
simulation.py     → End-to-end execution
benchmark.py      → Cost analysis
metrics.py        → Performance tracking
config.py         → Security parameters
logger.py         → Output handling
```

---

## 🔬 Research Contribution

* Combines **ZKP + Batch Authentication** in IoT blockchain
* Reduces verification cost significantly
* Uses **post-quantum secure primitives**
* Suitable for **resource-constrained environments**

---

## 📌 Future Improvements

* Stronger challenge entropy (full 128-bit)
* Formal security proof
* Optimized polynomial-based challenges
* Integration with real blockchain frameworks

---

## 👨‍💻 Author

Shubham Sah
Cryptography | Distributed Systems | Blockchain

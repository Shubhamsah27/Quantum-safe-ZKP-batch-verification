# Quantum-Safe ZKP Batch Verification

This repository implements a **Quantum-Safe, Lattice-Based Zero-Knowledge Proof (ZKP) Protocol** with a focus on efficient **batch verification**.

The system reduces verification overhead while maintaining strong **post-quantum security guarantees**, making it suitable for high-throughput environments such as IoT networks, distributed systems, and blockchain verification layers.

---

## 🚀 Key Features

- **Post-Quantum Security**
  - Based on lattice-hard problems such as **Short Integer Solution (SIS)**.
  - Resistant to quantum attacks.

- **Batch Verification**
  - Probabilistic verification of multiple proofs simultaneously.
  - Reduces computational cost compared to individual verification.

- **Zero-Knowledge Proofs**
  - Ensures completeness, soundness, and zero-knowledge.
  - No sensitive data is revealed during verification.

- **Benchmarking & Simulation**
  - Measure execution time, throughput, and efficiency.
  - Simulate multi-prover environments.

---

## 📁 Project Structure

├── main.py        # Entry point for protocol execution  
├── config.py      # Parameters (lattice size, modulus q, security level)  
├── benchmark.py   # Performance evaluation  
├── simulation.py  # Network / multi-user simulation  

---

## 🛠️ Prerequisites

- Python 3.8+

### Setup

```bash
git clone https://github.com/Shubhamsah27/Quantum-safe-ZKP-batch-verification.git
cd Quantum-safe-ZKP-batch-verification

python -m venv venv

# Linux / Mac
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt

## 💻 Usage

Run the protocol:
```bash
python main.py

Run benchmarks:

python benchmark.py

Run simulation:

python simulation.py


🔒 Security
Based on lattice cryptography (SIS problem)
Uses rejection sampling for zero-knowledge
Designed to resist quantum attacks
Batch verification reduces complexity while preserving soundness


📊 Use Cases
IoT authentication
Blockchain verification
Distributed systems
Secure multi-party computation


👨‍💻 Author
Shubham Sah

📝 License

MIT License

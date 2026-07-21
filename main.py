"""
Tech Series Video Bot v2 — Expert Edition
2-minute deep-dive videos for advanced engineers.
Every video: unique visual theme + video-game mechanic explanation style.
"""

import os, sys, json, asyncio, argparse, subprocess, re, math, random, urllib.request
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

WIDTH  = 1080
HEIGHT = 1920
FPS    = 30
N_STEPS          = 9          # steps per video
FRAMES_PER_STEP  = 400        # ~13.3 s per step → total ~2 min
TOTAL_FRAMES     = N_STEPS * FRAMES_PER_STEP   # 3600 = 2 min exact

# ─────────────────────────────────────────────────────────────────────────────
# ADVANCED EXPERT TOPICS
# Format: (series, chapter, topic_description)
# Every topic is deep, nuanced, expert-level — not "what is a variable"
# ─────────────────────────────────────────────────────────────────────────────
TECH_TOPICS = [
    # ── SYSTEMS INTERNALS ────────────────────────────────────────────────────
    ("Systems","CPU Internals",        "Branch Prediction: how CPUs guess your if-else 95% of the time"),
    ("Systems","CPU Internals",        "Out-of-Order Execution: CPU runs instructions before you ask"),
    ("Systems","CPU Internals",        "Superscalar Pipelines: executing 4+ instructions per clock cycle"),
    ("Systems","CPU Internals",        "Cache Coherence: MESI protocol keeping multi-core caches in sync"),
    ("Systems","CPU Internals",        "NUMA Architecture: memory latency depends on which CPU owns it"),
    ("Systems","CPU Internals",        "TLB Shootdowns: the hidden cost of freeing shared memory pages"),
    ("Systems","CPU Internals",        "Memory Ordering: happens-before, acquire-release, sequential consistency"),
    ("Systems","CPU Internals",        "Spectre and Meltdown: exploiting speculative execution via cache timing"),
    ("Systems","CPU Internals",        "False Sharing: cache lines destroyed by unrelated adjacent variables"),
    ("Systems","CPU Internals",        "Prefetcher Friendly Code: spatial vs temporal locality in hot loops"),
    ("Systems","Memory",               "Virtual Memory: page tables, TLB, huge pages, and address spaces"),
    ("Systems","Memory",               "Buddy Allocator: how Linux kernel splits and merges memory blocks"),
    ("Systems","Memory",               "Slab Allocator: pre-carved object pools for zero-cost kernel allocs"),
    ("Systems","Memory",               "Memory Compaction: defragmenting RAM without a garbage collector"),
    ("Systems","Memory",               "Copy-on-Write: fork() copies nothing until you write — here's how"),
    ("Systems","Memory",               "Memory Mapped Files: mmap() and why databases use it everywhere"),
    ("Systems","Memory",               "Transparent Huge Pages: 2MB pages, silent performance killer"),
    ("Systems","Memory",               "OOM Killer: Linux decides which process to murder and why"),
    ("Systems","OS Internals",         "Completely Fair Scheduler: vruntime, red-black tree, and cgroups"),
    ("Systems","OS Internals",         "io_uring: zero-copy async I/O that made Linux 40% faster"),
    ("Systems","OS Internals",         "eBPF: programmable kernel without writing a kernel module"),
    ("Systems","OS Internals",         "Futex: user-space mutex that only calls the kernel on contention"),
    ("Systems","OS Internals",         "VDSO: syscalls that aren't syscalls — gettimeofday in 3 ns"),
    ("Systems","OS Internals",         "Cgroups v2: CPU, memory, and I/O bandwidth isolation internals"),
    ("Systems","OS Internals",         "Namespaces: the six Linux primitives that make containers possible"),
    ("Systems","OS Internals",         "Signals: real-time vs standard, SA_SIGINFO, signal safety rules"),
    ("Systems","OS Internals",         "Epoll internals: edge-triggered vs level-triggered, thundering herd"),
    ("Systems","Network Stack",        "TCP's Nagle Algorithm vs TCP_NODELAY: latency vs throughput tradeoff"),
    ("Systems","Network Stack",        "BBR Congestion Control: bandwidth-delay product and pacing"),
    ("Systems","Network Stack",        "TCP Fast Open: eliminating the 3-way handshake for repeat connections"),
    ("Systems","Network Stack",        "QUIC Protocol: how HTTP/3 removed head-of-line blocking at the transport layer"),
    ("Systems","Network Stack",        "XDP: bypassing the kernel network stack for 100Gbps packet processing"),
    ("Systems","Network Stack",        "RSS and RPS: spreading NIC interrupts across CPU cores"),
    ("Systems","Network Stack",        "Receive Side Scaling: NIC hardware hash → CPU affinity for flows"),

    # ── COMPILER & RUNTIME ───────────────────────────────────────────────────
    ("Compilers","IR & Optimization",  "SSA Form: Static Single Assignment and why every modern compiler uses it"),
    ("Compilers","IR & Optimization",  "Loop Invariant Code Motion: pulling constants out of hot loops"),
    ("Compilers","IR & Optimization",  "Strength Reduction: replacing multiply with shifts inside loops"),
    ("Compilers","IR & Optimization",  "Inlining Heuristics: when inlining hurts more than it helps"),
    ("Compilers","IR & Optimization",  "Escape Analysis: proving an object never leaves a function's scope"),
    ("Compilers","IR & Optimization",  "Devirtualization: removing vtable dispatch when the type is known"),
    ("Compilers","IR & Optimization",  "Link-Time Optimization (LTO): cross-file inlining and DCE"),
    ("Compilers","IR & Optimization",  "Profile-Guided Optimization: recompiling with real execution data"),
    ("Compilers","IR & Optimization",  "Auto-Vectorization: when the compiler generates SIMD for your loop"),
    ("Compilers","Backend",            "Register Allocation: graph coloring, spilling, and live ranges"),
    ("Compilers","Backend",            "Instruction Scheduling: hiding latency with instruction reordering"),
    ("Compilers","Backend",            "Calling Conventions: System V AMD64 ABI register assignments"),
    ("Compilers","Backend",            "Stack Frame Layout: red zone, frame pointer, and prologue/epilogue"),
    ("Compilers","JIT Compilation",    "Tracing JIT: recording hot paths and compiling them at runtime"),
    ("Compilers","JIT Compilation",    "V8's Turbofan: hidden classes, deoptimization, and feedback vectors"),
    ("Compilers","JIT Compilation",    "JVM JIT: tiered compilation, C1 vs C2, on-stack replacement"),
    ("Compilers","JIT Compilation",    "LLVM MCJIT: building your own JIT in 200 lines with LLVM"),
    ("Compilers","GC Internals",       "Tri-color Mark-Sweep: write barrier, floating garbage, stop-the-world"),
    ("Compilers","GC Internals",       "G1 GC: region-based heap, concurrent marking, remembered sets"),
    ("Compilers","GC Internals",       "ZGC and Shenandoah: sub-millisecond GC pauses via colored pointers"),
    ("Compilers","GC Internals",       "Reference Counting vs Tracing GC: Python vs Go trade-offs"),
    ("Compilers","GC Internals",       "Generational Hypothesis: why 90% of objects die young"),

    # ── DISTRIBUTED SYSTEMS ──────────────────────────────────────────────────
    ("Distributed","Consensus",        "Paxos Made Simple: prepare, promise, accept, commit in depth"),
    ("Distributed","Consensus",        "Raft Consensus: leader election, log replication, safety proof"),
    ("Distributed","Consensus",        "Multi-Paxos vs Raft: performance differences under leader churn"),
    ("Distributed","Consensus",        "Viewstamped Replication: the OG consensus protocol from 1988"),
    ("Distributed","Consistency",      "Linearizability: the strongest safety guarantee and its cost"),
    ("Distributed","Consistency",      "Sequential Consistency: weaker than linearizability, what breaks"),
    ("Distributed","Consistency",      "Eventual Consistency: what it actually guarantees (less than you think)"),
    ("Distributed","Consistency",      "Causal Consistency: happens-before without global ordering"),
    ("Distributed","CRDTs",            "G-Counter CRDT: commutative, associative, idempotent merge"),
    ("Distributed","CRDTs",            "OR-Set CRDT: add-wins delete-wins conflict resolution"),
    ("Distributed","CRDTs",            "RGA: Replicated Growable Array for collaborative text editing"),
    ("Distributed","CRDTs",            "CRDT vs OT: why CRDTs won the distributed editing war"),
    ("Distributed","Time",             "Vector Clocks: partial ordering of events in distributed systems"),
    ("Distributed","Time",             "Hybrid Logical Clocks: combining wall clock and logical clock"),
    ("Distributed","Time",             "TrueTime: Google Spanner's GPS + atomic clock uncertainty bound"),
    ("Distributed","Time",             "Lamport Timestamps: total ordering from partial ordering"),
    ("Distributed","Failure",          "Byzantine Fault Tolerance: f failures need 3f+1 nodes — here's why"),
    ("Distributed","Failure",          "PBFT: Practical Byzantine Fault Tolerance step by step"),
    ("Distributed","Failure",          "Phi Accrual Failure Detector: probabilistic suspicion score"),
    ("Distributed","Failure",          "Gossip Protocol: epidemic spread, convergence time, anti-entropy"),
    ("Distributed","Failure",          "Chaos Engineering: steady-state hypothesis, blast radius, GameDay"),
    ("Distributed","Transactions",     "Two-Phase Commit: coordinator crash, blocking, and 2PC variants"),
    ("Distributed","Transactions",     "Sagas: compensating transactions for long-running distributed workflows"),
    ("Distributed","Transactions",     "MVCC: Multi-Version Concurrency Control without locking readers"),
    ("Distributed","Transactions",     "Percolator: Google's distributed transactions on BigTable"),
    ("Distributed","Replication",      "Chain Replication: strong consistency with O(1) read fanout"),
    ("Distributed","Replication",      "Leaderless Replication: quorum reads/writes, sloppy quorum"),
    ("Distributed","Replication",      "WAL Shipping vs Logical Replication: PostgreSQL internals"),

    # ── DATABASE INTERNALS ────────────────────────────────────────────────────
    ("Databases","Storage Engines",    "B+ Tree internals: node splits, merges, fill factor, WAL"),
    ("Databases","Storage Engines",    "LSM Tree: MemTable, SSTable, compaction strategies, bloom filters"),
    ("Databases","Storage Engines",    "B-Tree vs LSM: write amplification, read amplification, space amp"),
    ("Databases","Storage Engines",    "WiscKey: separating keys from values in LSM to cut write amp 100x"),
    ("Databases","Storage Engines",    "Copy-on-Write B-Tree: SQLite WAL mode and append-only structures"),
    ("Databases","Storage Engines",    "Columnar Storage: PAX format, dictionary encoding, run-length encoding"),
    ("Databases","Query Processing",   "Volcano Model: pull-based query iterator with next() at every node"),
    ("Databases","Query Processing",   "Vectorized Execution: processing 1024 rows at once with SIMD"),
    ("Databases","Query Processing",   "Morsel-Driven Parallelism: DuckDB's work-stealing query execution"),
    ("Databases","Query Processing",   "Adaptive Query Processing: re-optimizing mid-execution with real stats"),
    ("Databases","Query Processing",   "Late Materialization: delay fetching full rows until after filtering"),
    ("Databases","Indexing",           "Covering Index: query answered entirely from the index, 0 row lookups"),
    ("Databases","Indexing",           "Partial Index: indexing a subset of rows for sparse conditions"),
    ("Databases","Indexing",           "GIN Index: inverted index for arrays, full-text, and JSONB in Postgres"),
    ("Databases","Indexing",           "BRIN Index: block range, 4KB of metadata vs millions of rows"),
    ("Databases","Indexing",           "Bitmap Heap Scan: combining multiple indexes with AND/OR in Postgres"),
    ("Databases","Concurrency",        "Optimistic Concurrency: read-validate-write without holding locks"),
    ("Databases","Concurrency",        "Serializable Snapshot Isolation (SSI): detecting anti-dependency cycles"),
    ("Databases","Concurrency",        "Gap Locks and Next-Key Locks: preventing phantom reads in MySQL InnoDB"),
    ("Databases","Concurrency",        "Deadlock Detection vs Timeout: wait-for graph cycle detection"),
    ("Databases","NewSQL",             "Spanner F1: globally distributed SQL with external consistency"),
    ("Databases","NewSQL",             "CockroachDB: range-based sharding, Raft per range, MVCC timestamps"),
    ("Databases","NewSQL",             "TiDB: MySQL-compatible HTAP with TiKV storage and TiFlash analytics"),
    ("Databases","NewSQL",             "YugabyteDB: DocDB storage, Raft groups, hybrid logical clocks"),

    # ── ADVANCED ALGORITHMS ───────────────────────────────────────────────────
    ("Algorithms","String Processing", "Suffix Array + LCP: O(n log n) construction and pattern matching"),
    ("Algorithms","String Processing", "Aho-Corasick: multi-pattern matching in O(n+m) with failure links"),
    ("Algorithms","String Processing", "Z-Algorithm: prefix match in O(n) — simpler than KMP"),
    ("Algorithms","String Processing", "Suffix Automaton: smallest DFA recognizing all substrings"),
    ("Algorithms","Graph Advanced",    "Tarjan's SCC: DFS timestamps, low-link values, and the stack"),
    ("Algorithms","Graph Advanced",    "Hopcroft-Karp: O(E√V) maximum bipartite matching"),
    ("Algorithms","Graph Advanced",    "Push-Relabel Max-Flow: height functions and discharge operations"),
    ("Algorithms","Graph Advanced",    "Hungarian Algorithm: O(n³) optimal assignment problem"),
    ("Algorithms","Graph Advanced",    "A* vs Dijkstra: admissible heuristics and optimality guarantee"),
    ("Algorithms","Graph Advanced",    "Centroid Decomposition: solving tree path queries in O(n log² n)"),
    ("Algorithms","Graph Advanced",    "Heavy-Light Decomposition: path queries on trees in O(log² n)"),
    ("Algorithms","Data Structures",   "van Emde Boas Tree: O(log log U) operations on integer universe U"),
    ("Algorithms","Data Structures",   "Fibonacci Heap: amortized O(1) decrease-key for Dijkstra"),
    ("Algorithms","Data Structures",   "Persistent Segment Tree: point updates with full version history"),
    ("Algorithms","Data Structures",   "Wavelet Tree: O(log n) k-th order statistic over range queries"),
    ("Algorithms","Data Structures",   "Link-Cut Tree: dynamic tree connectivity and path aggregates"),
    ("Algorithms","Data Structures",   "Skip List internals: probabilistic balancing and lock-free variants"),
    ("Algorithms","Data Structures",   "X-fast and Y-fast tries: predecessor queries in O(log log U)"),
    ("Algorithms","Data Structures",   "Cache-Oblivious Algorithms: optimal cache use without knowing cache size"),
    ("Algorithms","Randomized",        "HyperLogLog: estimating cardinality of 10^9 elements in 1.5KB"),
    ("Algorithms","Randomized",        "Count-Min Sketch: frequency estimation with bounded error and O(1) space"),
    ("Algorithms","Randomized",        "Bloom Filter: false positives, false negatives, optimal k hash functions"),
    ("Algorithms","Randomized",        "MinHash and LSH: approximate nearest neighbor in high dimensions"),
    ("Algorithms","Randomized",        "Treap: randomized BST with heap priority — O(log n) expected all ops"),
    ("Algorithms","Randomized",        "Reservoir Sampling: uniform sample from unknown-size stream in O(1) space"),
    ("Algorithms","Randomized",        "Miller-Rabin Primality: probabilistic primality in O(k log² n)"),
    ("Algorithms","Optimization",      "Simplex Method: pivoting through vertex polytope — why it's fast in practice"),
    ("Algorithms","Optimization",      "Interior Point Method: barrier function, self-concordance, polynomial time"),
    ("Algorithms","Optimization",      "Submodular Optimization: diminishing returns and the greedy 1/2 guarantee"),

    # ── CONCURRENCY DEEP DIVE ────────────────────────────────────────────────
    ("Concurrency","Lock-Free",        "Compare-And-Swap: ABA problem, tagged pointers, and hazard pointers"),
    ("Concurrency","Lock-Free",        "Michael-Scott Queue: the lock-free FIFO used in Java's ConcurrentLinkedQueue"),
    ("Concurrency","Lock-Free",        "LCRQ: a lock-free queue that's actually faster than the M-S queue"),
    ("Concurrency","Lock-Free",        "RCU: Read-Copy-Update — readers pay zero, writers pay once"),
    ("Concurrency","Lock-Free",        "Epoch-Based Reclamation: safe memory reclaim without a GC or locks"),
    ("Concurrency","Lock-Free",        "Hazard Pointers: per-thread protected pointer lists for memory safety"),
    ("Concurrency","Primitives",       "Seqlock: writer priority, reader retry — used in Linux timekeeping"),
    ("Concurrency","Primitives",       "Ticket Lock: fair FIFO spinlock with cache-friendly acquire"),
    ("Concurrency","Primitives",       "MCS Lock: scalable spinlock that eliminates cache line bouncing"),
    ("Concurrency","Primitives",       "Condition Variables: spurious wakeups, predicate loops, Mesa vs Hoare"),
    ("Concurrency","Primitives",       "Semaphore internals: POSIX sem_wait, sem_post, and priority inversion"),
    ("Concurrency","Primitives",       "Priority Inversion: the Mars Pathfinder bug and priority inheritance"),
    ("Concurrency","Models",           "CSP vs Actor Model: Go channels vs Erlang/Akka message passing"),
    ("Concurrency","Models",           "Software Transactional Memory: Haskell STM, retry, and orElse"),
    ("Concurrency","Models",           "Structured Concurrency: nurseries, scope lifetimes, and error propagation"),
    ("Concurrency","Models",           "Async/Await internals: state machines, stackless coroutines, wake-up"),
    ("Concurrency","Models",           "Work-Stealing Scheduler: deque, steal-half strategy, Cilk's THE protocol"),

    # ── NETWORKING DEEP DIVE ─────────────────────────────────────────────────
    ("Networking","TLS & Crypto",      "TLS 1.3: 0-RTT handshake, forward secrecy, removal of RSA key exchange"),
    ("Networking","TLS & Crypto",      "Certificate Transparency: Merkle trees, monitors, and auditors"),
    ("Networking","TLS & Crypto",      "OCSP Stapling: proving cert validity without hitting the CA every request"),
    ("Networking","TLS & Crypto",      "Noise Protocol: building secure channels without X.509 certificates"),
    ("Networking","TLS & Crypto",      "DANE: DNS-based auth of named entities replacing CA trust chains"),
    ("Networking","Protocols",         "QUIC internals: connection IDs, stream multiplexing, and 0-RTT"),
    ("Networking","Protocols",         "HTTP/2 HPACK: static table, dynamic table, Huffman encoding headers"),
    ("Networking","Protocols",         "WebTransport: replacing WebSockets with QUIC streams and datagrams"),
    ("Networking","Protocols",         "gRPC internals: HTTP/2 framing, protobuf, deadline propagation"),
    ("Networking","Protocols",         "BGP Internals: AS path, route selection, RPKI, and prefix hijacks"),
    ("Networking","Load Balancing",    "Consistent Hashing with Virtual Nodes: even load during shard changes"),
    ("Networking","Load Balancing",    "IPVS: kernel-level L4 load balancer used inside every Kubernetes cluster"),
    ("Networking","Load Balancing",    "Maglev: Google's consistent hashing LB that handles NIC multi-queue"),
    ("Networking","Service Mesh",      "Envoy Proxy: xDS API, HDS, and zero-downtime config hot-reloads"),
    ("Networking","Service Mesh",      "eBPF-based Service Mesh: replacing sidecar proxies with kernel hooks"),

    # ── AI/ML INTERNALS ───────────────────────────────────────────────────────
    ("AI/ML","Transformer Internals",  "Flash Attention: IO-aware exact attention in O(N) memory instead of O(N²)"),
    ("AI/ML","Transformer Internals",  "Flash Attention 2 & 3: tiling, warp specialization, async pipelines"),
    ("AI/ML","Transformer Internals",  "Grouped Query Attention: reducing KV cache memory by 8x in LLaMA"),
    ("AI/ML","Transformer Internals",  "RoPE: Rotary Position Embeddings and length extrapolation"),
    ("AI/ML","Transformer Internals",  "MoE Models: sparse activation, expert routing, load balancing loss"),
    ("AI/ML","Transformer Internals",  "Speculative Decoding: 3x faster inference with a tiny draft model"),
    ("AI/ML","Transformer Internals",  "KV Cache Quantization: 4-bit keys/values with 0.1% accuracy loss"),
    ("AI/ML","Transformer Internals",  "PagedAttention: virtual memory for KV cache in vLLM"),
    ("AI/ML","Training",               "Mixed Precision Training: fp16 loss scaling, BFloat16, and NaN traps"),
    ("AI/ML","Training",               "Gradient Checkpointing: trading compute for memory in huge models"),
    ("AI/ML","Training",               "ZeRO-1/2/3: partitioning optimizer state, gradients, and parameters"),
    ("AI/ML","Training",               "Tensor Parallelism: splitting weight matrices across GPUs — Megatron-LM"),
    ("AI/ML","Training",               "Pipeline Parallelism: micro-batches, 1F1B schedule, and bubble ratio"),
    ("AI/ML","Training",               "FSDP: Fully Sharded Data Parallel — PyTorch's answer to ZeRO-3"),
    ("AI/ML","Training",               "DPO: Direct Preference Optimization — RLHF without a reward model"),
    ("AI/ML","Efficiency",             "LoRA: Low-Rank Adaptation — fine-tuning 7B models with 16MB of params"),
    ("AI/ML","Efficiency",             "QLoRA: 4-bit quantized LoRA — fine-tune LLaMA on a single 24GB GPU"),
    ("AI/ML","Efficiency",             "AWQ: Activation-aware Weight Quantization — 4-bit with 0.2% accuracy"),
    ("AI/ML","Efficiency",             "GPTQ: one-shot 4-bit quantization via Hessian-based rounding"),
    ("AI/ML","Inference",              "Continuous Batching: never stop the GPU — iteration-level scheduling"),
    ("AI/ML","Inference",              "Chunked Prefill: overlap prefill and decode for 2x GPU utilization"),
    ("AI/ML","Inference",              "Medusa: parallel decoding heads — 3x speedup without draft model"),
    ("AI/ML","Inference",              "SGLang Runtime: RadixAttention, prefix caching, and structured output"),

    # ── SECURITY INTERNALS ────────────────────────────────────────────────────
    ("Security","Exploitation",        "Return-Oriented Programming: chaining gadgets after defeating NX/DEP"),
    ("Security","Exploitation",        "Heap Spraying: reliable exploitation by controlling allocator layout"),
    ("Security","Exploitation",        "Use-After-Free: dangling pointer exploitation and type confusion"),
    ("Security","Exploitation",        "ASLR Bypass: information leaks, brute force, and heap grooming"),
    ("Security","Exploitation",        "Kernel Exploits: privilege escalation via cred struct overwrite"),
    ("Security","Mitigations",         "Control Flow Integrity (CFI): forward and backward edge enforcement"),
    ("Security","Mitigations",         "Stack Canaries: terminator vs random vs random XOR, bypass techniques"),
    ("Security","Mitigations",         "Shadow Stack: CET hardware enforcement of return addresses"),
    ("Security","Mitigations",         "Memory Tagging (MTE): hardware tags on every 16-byte allocation"),
    ("Security","Cryptography",        "Elliptic Curve Cryptography: scalar multiplication on Weierstrass curves"),
    ("Security","Cryptography",        "EdDSA and Curve25519: why ed25519 replaced RSA in modern systems"),
    ("Security","Cryptography",        "Authenticated Encryption: AES-GCM, nonce reuse catastrophe, GHASH"),
    ("Security","Cryptography",        "Zero-Knowledge Proofs: interactive vs non-interactive, Fiat-Shamir"),
    ("Security","Cryptography",        "zk-SNARKs: quadratic arithmetic programs, trusted setup, Groth16"),
    ("Security","Cryptography",        "Threshold Signatures: t-of-n signing without ever assembling the key"),

    # ── CLOUD PLATFORM INTERNALS ──────────────────────────────────────────────
    ("Cloud","Kubernetes Internals",   "Kubernetes API Server: etcd watch, optimistic concurrency, admission"),
    ("Cloud","Kubernetes Internals",   "Scheduler Internals: scoring, preemption, gang scheduling, bin packing"),
    ("Cloud","Kubernetes Internals",   "Kubelet: CRI, CNI, CSI — the three plugin interfaces dissected"),
    ("Cloud","Kubernetes Internals",   "kube-proxy and iptables: DNAT rules, conntrack, and IPVS mode"),
    ("Cloud","Kubernetes Internals",   "Horizontal Pod Autoscaler: custom metrics, stabilization window"),
    ("Cloud","Kubernetes Internals",   "etcd Raft: how Kubernetes stores its brain — compaction, snapshots"),
    ("Cloud","Serverless",             "Lambda Cold Start: init phase, runtime API, SnapStart and MicroVM"),
    ("Cloud","Serverless",             "Firecracker MicroVM: 5ms boot, jailer, and seccomp filter profile"),
    ("Cloud","Serverless",             "V8 Isolates: Cloudflare Workers execution model and limits"),
    ("Cloud","Storage",                "Object Storage Internals: S3 strong consistency, ETag, multipart"),
    ("Cloud","Storage",                "EBS Volume Internals: NVMe-oF, multi-attach, provisioned IOPS"),
    ("Cloud","Storage",                "CephFS RADOS: CRUSH map, OSD placement groups, replication"),
]

# ── Game Mechanics ─────────────────────────────────────────────────────────────
GAME_MECHANICS = ["boss_fight", "skill_tree", "xp_grind", "quest", "raid"]

GAME_TAGS = {
    "boss_fight": "⚔ BOSS FIGHT",
    "skill_tree":  "🌲 SKILL TREE",
    "xp_grind":   "⚡ XP GRIND",
    "quest":      "📜 QUEST",
    "raid":       "💀 RAID",
}

# ── Animated Objects ───────────────────────────────────────────────────────────
OBJECTS = [
    "packet","fish","rocket","car","robot","crystal","satellite","bird","dragon",
    "submarine","gear","lightning","diamond","comet","ufo","bug","train","airplane",
    "bubble","star","turtle","cat","token","hexagon","molecule","flame","snowflake",
    "virus","crown","shield","key","bolt","wave","skull","eye","arrow",
]

# ─────────────────────────────────────────────────────────────────────────────
# LLM SCENE GENERATION
# ─────────────────────────────────────────────────────────────────────────────

LLM_SYSTEM_PROMPT = """You are a senior engineer who explains deep technical concepts to other expert engineers.
You generate JSON scene layouts for 2-minute educational YouTube Shorts aimed at experts with 5-10+ years of experience.
Every explanation uses a VIDEO GAME mechanic framing — boss fights, skill trees, XP grind, quests, raids.
Never simplify. Always go deep. Every concept explained at the implementation level, not the abstraction level.
The audience knows data structures, distributed systems, compilers, networking. Skip the basics entirely."""

def build_llm_prompt(topic: tuple, game_mechanic: str, game_tag: str, theme_name: str,
                     obj_a: str, obj_b: str) -> str:
    series, chapter, topic_desc = topic
    return f"""Generate a JSON scene layout for a 2-minute YouTube Short teaching expert engineers:

TOPIC: {topic_desc}
SERIES: {series} › {chapter}
VISUAL THEME: {theme_name}
GAME MECHANIC: {game_mechanic} ({game_tag})
ANIMATED OBJECTS: {obj_a} and {obj_b} roam the diagram

REQUIREMENTS:
- This is for EXPERT engineers (senior+ level). No basics. No "what is X". Go straight to internals, edge cases, and implementation trade-offs.
- The game mechanic ({game_mechanic}) must be woven into the explanation — not cosmetic.
- For boss_fight: The concept's complexity IS the boss. Each step chips away at it.
- For skill_tree: Prerequisites and unlockables are literal skills in a tree.
- For xp_grind: Each step is a practical exercise/challenge to earn XP.
- For quest: Clear objective, 4-6 milestones, final reward.
- For raid: Team phases, coordination, wipe conditions (common mistakes), loot (insights).
- 9 steps total to fill ~2 minutes. Each step = ~13 seconds of narration.
- Nodes should show REAL technical values (not "Node A"). Use actual terms, variable names, constants, formulas.
- captions_steps: 9 strings. Each must be 1-2 dense sentences of expert insight. No fluff. Implementation-level depth.
- narration: 9 strings. 30-40 words each. Fast-paced technical narration. No "Hello" or "In this video". Jump straight in.

Return ONLY valid JSON, no markdown:

{{
  "title": "short punchy technical title (max 8 words)",
  "subtitle": "one-line technical precision statement",
  "hook": "first 5 words that grab an expert's attention",
  "game_tag": "{game_tag}",
  "game_mechanic": "{game_mechanic}",
  "boss_name": "name of the conceptual enemy (only for boss_fight, else omit)",
  "series": "{series}",
  "chapter": "{chapter}",
  "counters": [
    {{"label": "technical metric 1", "value": 42}},
    {{"label": "technical metric 2", "value": 1024}},
    {{"label": "technical metric 3", "value": 7}}
  ],
  "damage_values": ["-25% Throughput", "-40% Latency", "+100ms P99", "-50% CPU", "-80% Cache Hit"],
  "quest_steps": ["step 1 (short)", "step 2", "step 3", "step 4", "step 5"],
  "nodes": [
    {{"x": 540, "y": 550, "r": 70, "label": "real technical term", "sublabel": "brief note"}},
    {{"x": 240, "y": 780, "r": 58, "label": "real value/const", "sublabel": ""}},
    {{"x": 840, "y": 780, "r": 58, "label": "real formula", "sublabel": ""}},
    {{"x": 200, "y": 1050, "r": 50, "label": "implementation detail", "sublabel": ""}},
    {{"x": 540, "y": 1100, "r": 62, "label": "key insight", "sublabel": ""}},
    {{"x": 880, "y": 1050, "r": 50, "label": "trade-off", "sublabel": ""}},
    {{"x": 350, "y": 1300, "r": 48, "label": "edge case", "sublabel": ""}},
    {{"x": 730, "y": 1300, "r": 48, "label": "optimization", "sublabel": ""}}
  ],
  "paths": [
    {{"from": 0, "to": 1}}, {{"from": 0, "to": 2}},
    {{"from": 1, "to": 3}}, {{"from": 2, "to": 5}},
    {{"from": 3, "to": 4}}, {{"from": 5, "to": 4}},
    {{"from": 4, "to": 6}}, {{"from": 4, "to": 7}}
  ],
  "captions_steps": [
    "Step 0 expert insight sentence (one or two dense sentences).",
    "Step 1 ...",
    "Step 2 ...",
    "Step 3 ...",
    "Step 4 ...",
    "Step 5 ...",
    "Step 6 ...",
    "Step 7 ...",
    "Step 8 ..."
  ],
  "narration": [
    "30-40 word narration for step 0 — deep and technical.",
    "Step 1 narration...",
    "Step 2 narration...",
    "Step 3 narration...",
    "Step 4 narration...",
    "Step 5 narration...",
    "Step 6 narration...",
    "Step 7 narration...",
    "Step 8 narration..."
  ]
}}"""


async def call_llm(prompt: str, api_key: str) -> dict:
    """Call DeepSeek (or OpenAI-compatible) for scene JSON."""
    import urllib.request, json as jsonlib
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = jsonlib.dumps({
        "model": "deepseek/deepseek-chat-v3-5",
        "messages": [
            {"role": "system", "content": LLM_SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        "max_tokens": 2800,
        "temperature": 0.85,
    }).encode()

    endpoints = [
        "https://openrouter.ai/api/v1/chat/completions",
        "https://opencode.ai/api/v1/chat/completions",
        "https://api.openai.com/v1/chat/completions",
    ]
    for endpoint in endpoints:
        try:
            req = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = jsonlib.loads(resp.read())
                raw  = data["choices"][0]["message"]["content"].strip()
                # Strip markdown code fences if present
                if raw.startswith("```"):
                    raw = re.sub(r"^```[a-z]*\n?", "", raw)
                    raw = re.sub(r"\n?```$", "", raw)
                return jsonlib.loads(raw)
        except Exception as e:
            print(f"  ⚠ LLM endpoint {endpoint} failed: {e}")
            continue
    raise RuntimeError("All LLM endpoints failed")


# ─────────────────────────────────────────────────────────────────────────────
# TTS (Edge-TTS — free, high quality)
# ─────────────────────────────────────────────────────────────────────────────

VOICE = "en-US-GuyNeural"   # male, crisp, authoritative — fits expert content

async def generate_tts(text: str, output_path: str) -> bool:
    try:
        import edge_tts
        tts = edge_tts.Communicate(text, VOICE, rate="+18%", pitch="-2Hz")
        await tts.save(output_path)
        return True
    except Exception as e:
        print(f"  ⚠ TTS error: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# VIDEO RENDERING
# ─────────────────────────────────────────────────────────────────────────────

def render_frames(scene: dict, obj_a: str, obj_b: str, theme: dict,
                  output_dir: Path) -> list[Path]:
    from src.tech_visual_engine import TechVisualEngine
    engine = TechVisualEngine(obj_a, obj_b, theme=theme)

    total_steps = N_STEPS
    frames      = []

    print(f"  🎨 Rendering {total_steps * FRAMES_PER_STEP} frames ({total_steps} steps × {FRAMES_PER_STEP} frames)…")

    for step_idx in range(total_steps):
        for fi in range(FRAMES_PER_STEP):
            global_frame  = step_idx * FRAMES_PER_STEP + fi
            step_progress = fi / FRAMES_PER_STEP
            img = engine.render_frame(scene, step_idx, step_progress,
                                      global_frame, total_steps)
            frame_path = output_dir / f"frame_{global_frame:06d}.jpg"
            img.save(str(frame_path), "JPEG", quality=88)
            frames.append(frame_path)

        print(f"    Step {step_idx + 1}/{total_steps} rendered")

    return frames


def compose_video(frames: list[Path], audio_paths: list[str],
                  durations: list[float], output_path: Path) -> str | None:
    if not frames:
        print("❌ No frames to compose")
        return None

    tmp_dir      = output_path.parent
    concat_file  = str(tmp_dir / "frame_list.txt")

    with open(concat_file, "w") as f:
        for i, frame in enumerate(frames):
            step_idx = i // FRAMES_PER_STEP
            dur = durations[step_idx] / FRAMES_PER_STEP if step_idx < len(durations) else 1.0 / FPS
            f.write(f"file '{frame.absolute()}'\n")
            f.write(f"duration {dur:.6f}\n")
        f.write(f"file '{frames[-1].absolute()}'\n")

    raw_video = str(tmp_dir / "raw_video.mp4")
    r = subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
        "-vf", f"scale={WIDTH}:{HEIGHT},fps={FPS}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p", raw_video
    ], capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        print(f"❌ Video render error: {r.stderr[-500:]}")
        return None

    if not audio_paths:
        import shutil
        shutil.copy(raw_video, str(output_path))
        return str(output_path)

    audio_list = str(tmp_dir / "audio_list.txt")
    with open(audio_list, "w") as f:
        for ap in audio_paths:
            f.write(f"file '{Path(ap).absolute()}'\n")

    merged_audio = str(tmp_dir / "merged_audio.mp3")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", audio_list, "-c", "copy", merged_audio
    ], capture_output=True, timeout=120)

    r = subprocess.run([
        "ffmpeg", "-y",
        "-i", raw_video, "-i", merged_audio,
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(output_path)
    ], capture_output=True, text=True, timeout=600)

    if r.returncode == 0 and output_path.exists():
        size_mb = output_path.stat().st_size / 1e6
        print(f"✅ Video composed: {output_path} ({size_mb:.1f} MB)")
        return str(output_path)

    print(f"❌ Final compose error: {r.stderr[-400:]}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# THUMBNAIL
# ─────────────────────────────────────────────────────────────────────────────

def generate_thumbnail(scene: dict, obj_a: str, obj_b: str, theme: dict, output_path: Path) -> str | None:
    try:
        from src.tech_visual_engine import TechVisualEngine
        engine = TechVisualEngine(obj_a, obj_b, theme=theme)
        img = engine.render_thumbnail(scene)
        img.save(str(output_path), "JPEG", quality=95)
        print(f"  🖼  Thumbnail: {output_path}")
        return str(output_path)
    except Exception as e:
        print(f"  ⚠ Thumbnail error: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Skip YouTube upload")
    parser.add_argument("--topic-id", type=int, default=None, help="Force specific topic index")
    args = parser.parse_args()

    api_key      = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY", "")
    token_json   = os.environ.get("TOKEN_JSON", "")
    client_json  = os.environ.get("CLIENT_SECRETS_JSON", "")

    progress_path = PROJECT_ROOT / "data" / "tech_progress.json"
    history_path  = PROJECT_ROOT / "data" / "video_history.json"
    progress_path.parent.mkdir(exist_ok=True)

    # ── Load progress ──────────────────────────────────────────────────────
    current_id = 0
    if progress_path.exists():
        try:
            with open(progress_path) as f:
                current_id = json.load(f).get("current_id", 0)
        except:
            pass

    if args.topic_id is not None:
        current_id = args.topic_id

    total       = len(TECH_TOPICS)
    topic_idx   = current_id % total
    topic       = TECH_TOPICS[topic_idx]
    series, chapter, topic_desc = topic

    print(f"\n🎮 Video #{current_id} — {series} › {chapter}")
    print(f"   Topic: {topic_desc}")

    # ── Pick theme & game mechanic ─────────────────────────────────────────
    from src.visual_themes import pick_theme
    theme, theme_key = pick_theme(current_id)
    theme_name = theme.get("name", theme_key)

    rng = random.Random(current_id * 999 + 3)
    game_mechanic = rng.choice(GAME_MECHANICS)
    game_tag      = GAME_TAGS[game_mechanic]

    obj_rng = random.Random(current_id * 12345)
    obj_a   = obj_rng.choice(OBJECTS)
    remaining = [o for o in OBJECTS if o != obj_a]
    obj_b   = obj_rng.choice(remaining)

    print(f"   Theme: {theme_name}  |  Mechanic: {game_tag}  |  Objects: {obj_a}, {obj_b}")

    # ── Build LLM prompt & call ────────────────────────────────────────────
    prompt = build_llm_prompt(topic, game_mechanic, game_tag, theme_name, obj_a, obj_b)

    print("  🤖 Calling LLM for scene layout…")
    if not api_key:
        print("⚠ No API key — using mock scene")
        scene = _mock_scene(topic, game_mechanic, game_tag)
    else:
        try:
            scene = await call_llm(prompt, api_key)
            scene["game_mechanic"] = game_mechanic
            scene["game_tag"]      = game_tag
            scene["series"]        = series
            scene["chapter"]       = chapter
        except Exception as e:
            print(f"❌ LLM failed: {e} — using mock scene")
            scene = _mock_scene(topic, game_mechanic, game_tag)

    print(f"  📋 Scene: {scene.get('title', '?')}")

    # ── Generate TTS audio ─────────────────────────────────────────────────
    tmp_dir = PROJECT_ROOT / "tmp" / f"video_{current_id}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    narration_steps = scene.get("narration", [])
    audio_paths     = []
    durations       = []

    print("  🎙 Generating TTS narration…")
    for i, narr in enumerate(narration_steps[:N_STEPS]):
        audio_path = str(tmp_dir / f"audio_{i:02d}.mp3")
        ok = await generate_tts(narr, audio_path)
        if ok and Path(audio_path).exists():
            audio_paths.append(audio_path)
            # Measure actual audio duration
            r = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
                capture_output=True, text=True
            )
            try:
                dur = float(r.stdout.strip())
            except:
                dur = FRAMES_PER_STEP / FPS
            durations.append(dur)
            print(f"    Step {i}: {dur:.1f}s")
        else:
            durations.append(FRAMES_PER_STEP / FPS)

    # Pad durations to N_STEPS
    while len(durations) < N_STEPS:
        durations.append(FRAMES_PER_STEP / FPS)

    # ── Render frames ──────────────────────────────────────────────────────
    frames_dir = tmp_dir / "frames"
    frames_dir.mkdir(exist_ok=True)
    frames = render_frames(scene, obj_a, obj_b, theme, frames_dir)

    # ── Compose video ──────────────────────────────────────────────────────
    final_video = tmp_dir / "final.mp4"
    video_path  = compose_video(frames, audio_paths, durations, final_video)
    if not video_path:
        print("❌ Video composition failed")
        return

    # ── Generate thumbnail ─────────────────────────────────────────────────
    thumb_path = tmp_dir / "thumbnail.jpg"
    generate_thumbnail(scene, obj_a, obj_b, theme, thumb_path)

    # ── Upload to YouTube ──────────────────────────────────────────────────
    video_uploaded = False
    if not args.dry_run and token_json and client_json:
        from src.uploader import YouTubeUploader
        # Write credential files
        token_file   = tmp_dir / "token.json"
        client_file  = tmp_dir / "client_secrets.json"
        token_file.write_text(token_json)
        client_file.write_text(client_json)

        uploader = YouTubeUploader(str(token_file), str(client_file))
        title    = scene.get("title", topic_desc[:60])
        subtitle = scene.get("subtitle", "")
        yt_title = f"{game_tag} {title}" if not title.startswith(game_tag[0]) else title
        yt_title = yt_title[:100]

        tags = [series, chapter, "programming", "system design", "software engineering",
                "advanced", "deep dive", game_mechanic.replace("_", " "),
                "distributed systems", "CS", "backend", "tech"]

        description = (
            f"{game_tag} — {topic_desc}\n\n"
            f"Series: {series} › {chapter}\n"
            f"Visual Theme: {theme_name}\n\n"
            f"{'=' * 40}\n"
            f"Expert-level 2-minute deep-dives for senior engineers.\n"
            f"No basics. Just internals, trade-offs, and implementation details.\n"
        )

        try:
            video_id = uploader.upload(
                video_path=video_path,
                title=yt_title,
                description=description,
                tags=tags,
                thumbnail_path=str(thumb_path) if thumb_path.exists() else None,
                category_id="28",
                made_for_kids=False,
            )
            if video_id:
                print(f"✅ Uploaded → https://youtu.be/{video_id}")
                video_uploaded = True
        except Exception as e:
            print(f"❌ Upload error: {e}")
    else:
        mode = "dry-run" if args.dry_run else "no credentials"
        print(f"  [Skip upload — {mode}]")

    # ── Save progress ──────────────────────────────────────────────────────
    next_id = current_id + 1
    with open(progress_path, "w") as f:
        json.dump({"current_id": next_id}, f, indent=2)

    history = []
    if history_path.exists():
        try:
            with open(history_path) as f:
                history = json.load(f)
        except:
            pass
    history.append({
        "id": current_id, "topic_idx": topic_idx,
        "series": series, "chapter": chapter, "topic": topic_desc,
        "title": scene.get("title", ""), "theme": theme_key,
        "game_mechanic": game_mechanic, "obj_a": obj_a, "obj_b": obj_b,
        "uploaded": video_uploaded,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    with open(history_path, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    # Cleanup frames (keep final video)
    if os.environ.get("GITHUB_ACTIONS") == "true":
        import shutil
        try:
            shutil.rmtree(str(frames_dir))
        except:
            pass

    next_topic = TECH_TOPICS[next_id % total]
    print(f"\n✅ Done! Next → #{next_id}: {next_topic[0]} › {next_topic[2][:50]}")


# ── Mock scene for dry-run without API key ────────────────────────────────────
def _mock_scene(topic: tuple, game_mechanic: str, game_tag: str) -> dict:
    series, chapter, topic_desc = topic
    return {
        "title":         topic_desc[:60],
        "subtitle":      f"{chapter} internals — expert level",
        "hook":          "Here's what actually happens",
        "game_tag":      game_tag,
        "game_mechanic": game_mechanic,
        "boss_name":     "THE COMPLEXITY",
        "series":        series,
        "chapter":       chapter,
        "counters":      [{"label": "Complexity", "value": "O(n²)"}, {"label": "Nodes", "value": 8}],
        "damage_values": ["-25% Throughput", "-40% Latency", "+100ms P99", "-50% CPU", "-80% Hit Rate"],
        "quest_steps":   ["Understand the problem", "See the internals", "Find the edge case", "Apply the fix", "Benchmark"],
        "nodes": [
            {"x": 540, "y": 580, "r": 72, "label": topic_desc[:20], "sublabel": "entry"},
            {"x": 250, "y": 800, "r": 58, "label": "Phase 1", "sublabel": "init"},
            {"x": 830, "y": 800, "r": 58, "label": "Phase 2", "sublabel": "exec"},
            {"x": 180, "y": 1040, "r": 50, "label": "Edge Case", "sublabel": ""},
            {"x": 540, "y": 1120, "r": 64, "label": "Trade-Off", "sublabel": ""},
            {"x": 900, "y": 1040, "r": 50, "label": "Optimization", "sublabel": ""},
            {"x": 340, "y": 1320, "r": 48, "label": "Gotcha", "sublabel": ""},
            {"x": 740, "y": 1320, "r": 48, "label": "Fix", "sublabel": ""},
        ],
        "paths": [
            {"from": 0, "to": 1}, {"from": 0, "to": 2},
            {"from": 1, "to": 3}, {"from": 2, "to": 5},
            {"from": 3, "to": 4}, {"from": 5, "to": 4},
            {"from": 4, "to": 6}, {"from": 4, "to": 7},
        ],
        "captions_steps": [
            f"Deep dive into {topic_desc[:40]}.",
            "This is where most engineers get it wrong.",
            "The internals reveal the real performance profile.",
            "Edge cases expose the design trade-offs.",
            "Here's the critical implementation detail.",
            "This is the optimization that changes everything.",
            "The gotcha that has caused production incidents.",
            "The fix — and why the naive fix doesn't work.",
            "What this means for system design at scale.",
        ],
        "narration": [
            f"Let's dissect {topic_desc[:50]}. Not the textbook version. The real one.",
            "Most tutorials skip this part. We won't. Here's what's actually happening under the hood.",
            "The naive implementation runs into this problem at scale. Here's the failure mode.",
            "The runtime behavior diverges from the spec here. This is where bugs are born.",
            "This is the critical path. Every operation flows through this bottleneck.",
            "The optimization changes the complexity class. But it introduces a new trade-off.",
            "This edge case has caused outages at major companies. Know it. Memorize it.",
            "The correct fix is counterintuitive. Here's why the obvious fix makes it worse.",
            "In production: profile first, optimize second. This is where you start.",
        ],
    }


if __name__ == "__main__":
    asyncio.run(main())

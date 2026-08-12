"""
Tech Series Video Bot v3 — Puzzle Edition
2-minute coding puzzle game style videos for advanced engineers.
Every video: looks like a real coding game (Human Resource Machine / Zachtronics).
Python code is shown with syntax highlighting, executes step by step,
live visualization (bars, graphs, trees, grids), and test cases passing.
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

LLM_SYSTEM_PROMPT = """You are a senior engineer creating CODING PUZZLE GAME style educational YouTube Shorts.
The visual looks exactly like a real coding game (Human Resource Machine, Zachtronics, CodeCombat).
- A Python code editor panel fills the top half — real, runnable Python with syntax highlighting.
- An execution visualization fills the bottom half — bars sorting, graph traversal, call stack growing, DP grid filling, or a maze.
- Test cases appear at the bottom, ticking green one by one.
Every video is for EXPERT engineers (5-10+ years). No basics. Internals, edge cases, trade-offs only.
The audience knows compilers, distributed systems, OS internals, advanced algorithms deeply."""


def build_llm_prompt(topic: tuple, game_mechanic: str, game_tag: str,
                     puzzle_num: int) -> str:
    series, chapter, topic_desc = topic

    # Choose viz_type based on topic category
    viz_hints = {
        "Algorithms": "bars",
        "Concurrency": "graph",
        "Distributed": "graph",
        "Databases": "grid",
        "Compilers": "stack",
        "Systems": "memory",
        "AI/ML": "grid",
        "Networking": "graph",
        "Security": "memory",
        "Cloud": "graph",
    }
    viz_type = viz_hints.get(series, "bars")

    return f"""Generate a JSON scene for a coding-puzzle-game style 2-minute YouTube Short.

PUZZLE #{puzzle_num:03d}
TOPIC: {topic_desc}
SERIES: {series} › {chapter}
GAME MECHANIC: {game_mechanic} ({game_tag})
VISUALIZATION TYPE: {viz_type}

STRICT REQUIREMENTS:
1. code: 18-24 lines of REAL, runnable Python that demonstrates the concept at the implementation level.
   - No pseudocode. Actual Python with correct syntax.
   - Include imports, class/function definitions, key algorithm steps.
   - Show the most insightful implementation detail — not the textbook version.
2. active_lines: list of 9 integers (0-indexed), one per step, showing which code line is "executing" that step.
   Progress through the code: start at top, end near bottom.
3. viz_type: "{viz_type}" — match the visualization to the topic.
4. viz_data: populate FULLY for type "{viz_type}":
   - "bars": values (10 ints 10-99), steps (9 arrays showing sorted state), highlight (dict step→[i,j] of compared indices), operations (9 strings like "Compare arr[3] > arr[4]")
   - "grid": rows, cols, grid (flat list of values), row_headers, col_headers
   - "graph": nodes (list of {{id,label,x,y}} with x in 100-980, y in 50-450), edges (list of [a,b]), visited (list of node ids in visit order), queue_by_step (9 lists)
   - "stack": frame_states (9 lists of strings — call stack frames at each step)
   - "memory": memory (list of {{addr,label,value}} rows, 6-10 rows)
   - "maze": maze (6×6 int grid, 0=open 1=wall), path (list of [row,col] visited cells by step)
5. test_cases: exactly 4 test cases with real inputs/outputs for this algorithm.
6. narration: 9 strings, 30-40 words each, expert-level, no intro fluff — jump straight into the technical meat.
7. time_complexity and space_complexity: real Big-O with brief reason.
8. difficulty: "HARD" or "EXTREME" (no easy/medium — this is expert content).
9. puzzle_stars: always 3 (expert puzzle).
10. title: punchy, ≤8 words, technical.

Return ONLY valid JSON — no markdown fences, no comments:

{{
  "title": "...",
  "subtitle": "one precise technical statement",
  "series": "{series}",
  "chapter": "{chapter}",
  "puzzle_num": {puzzle_num},
  "puzzle_stars": 3,
  "difficulty": "HARD",
  "game_tag": "{game_tag}",
  "game_mechanic": "{game_mechanic}",
  "time_complexity": "O(...) — reason",
  "space_complexity": "O(...) — reason",
  "viz_type": "{viz_type}",
  "viz_label": "one-word label shown next to EXECUTION header",
  "code": [
    "line 0 of real Python",
    "line 1",
    "...",
    "line N"
  ],
  "active_lines": [0, 2, 4, 6, 8, 10, 13, 16, 18],
  "viz_data": {{ ... fully populated for viz_type "{viz_type}" ... }},
  "test_cases": [
    {{"label": "basic", "input": "...", "expected": "..."}},
    {{"label": "edge",  "input": "...", "expected": "..."}},
    {{"label": "large", "input": "...", "expected": "..."}},
    {{"label": "worst", "input": "...", "expected": "..."}}
  ],
  "narration": [
    "step 0: 30-40 word expert narration",
    "step 1: ...",
    "step 2: ...",
    "step 3: ...",
    "step 4: ...",
    "step 5: ...",
    "step 6: ...",
    "step 7: ...",
    "step 8: ..."
  ]
}}"""


async def call_llm(prompt: str, api_key: str) -> dict:
    """Call OpenCode (or compatible) API for puzzle scene JSON."""
    import urllib.request, json as jsonlib

    base_url   = os.environ.get("OPENCODE_BASE_URL", "https://opencode.ai/zen").rstrip("/")
    model_name = os.environ.get("OPENCODE_MODEL_NAME", "deepseek-v4-flash-free")

    # Primary: OpenCode endpoint; fallbacks: OpenAI, OpenRouter
    endpoints = [
        (f"{base_url}/chat/completions", model_name),
        ("https://api.openai.com/v1/chat/completions",   "gpt-4o-mini"),
        ("https://openrouter.ai/api/v1/chat/completions", "openai/gpt-4o-mini"),
    ]

    for endpoint, model in endpoints:
        try:
            body = jsonlib.dumps({
                "model": model,
                "messages": [
                    {"role": "system", "content": LLM_SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                "max_tokens": 3200,
                "temperature": 0.7,
            }).encode()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                # Browser-like UA required for opencode.ai (Cloudflare protection)
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Origin": "https://opencode.ai",
                "Accept": "application/json",
            }
            req = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = jsonlib.loads(resp.read())
                raw  = data["choices"][0]["message"]["content"].strip()
                if raw.startswith("```"):
                    raw = re.sub(r"^```[a-z]*\n?", "", raw)
                    raw = re.sub(r"\n?```$", "", raw.strip())
                return jsonlib.loads(raw)
        except Exception as e:
            print(f"  ⚠ {endpoint} failed: {e}")
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

def render_frames(scene: dict, series: str, output_dir: Path) -> list[Path]:
    from src.puzzle_visual_engine import PuzzleEngine
    engine = PuzzleEngine(series=series)

    total_steps = N_STEPS
    frames      = []

    print(f"  🎮 Rendering {total_steps * FRAMES_PER_STEP} frames ({total_steps} steps × {FRAMES_PER_STEP} frames)…")

    for step_idx in range(total_steps):
        for fi in range(FRAMES_PER_STEP):
            global_frame  = step_idx * FRAMES_PER_STEP + fi
            step_progress = fi / FRAMES_PER_STEP
            img = engine.render_frame(scene, step_idx, step_progress,
                                      global_frame, total_steps)
            frame_path = output_dir / f"frame_{global_frame:06d}.jpg"
            img.save(str(frame_path), "JPEG", quality=88)
            frames.append(frame_path)

        print(f"    Step {step_idx + 1}/{total_steps} ✓")

    return frames


def compose_video(frames: list[Path], audio_paths: list[str],
                  durations: list[float], output_path: Path) -> str | None:
    if not frames:
        print("❌ No frames to compose")
        return None

    tmp_dir      = output_path.parent
    concat_file  = str(tmp_dir / "frame_list.txt")

    with open(concat_file, "w", encoding="utf-8") as f:
        for i, frame in enumerate(frames):
            step_idx = i // FRAMES_PER_STEP
            dur = durations[step_idx] / FRAMES_PER_STEP if step_idx < len(durations) else 1.0 / FPS
            f.write(f"file '{frame.resolve().as_posix()}'\n")
            f.write(f"duration {dur:.6f}\n")
        f.write(f"file '{frames[-1].resolve().as_posix()}'\n")

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
    with open(audio_list, "w", encoding="utf-8") as f:
        for ap in audio_paths:
            f.write(f"file '{Path(ap).resolve().as_posix()}'\n")

    merged_audio = str(tmp_dir / "merged_audio.mp3")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", audio_list, "-c", "copy", merged_audio
    ], capture_output=True, timeout=120)

    r = subprocess.run([
        "ffmpeg", "-y",
        "-i", raw_video, "-i", merged_audio,
        "-c:v", "copy", "-c:a", "aac", "-strict", "-2",


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

def generate_thumbnail(scene: dict, series: str, output_path: Path) -> str | None:
    try:
        from src.puzzle_visual_engine import PuzzleEngine
        engine = PuzzleEngine(series=series)
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
    # ── Load .env ──────────────────────────────────────────────────────────
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env", override=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Skip YouTube upload")
    parser.add_argument("--topic-id", type=int, default=None, help="Force specific topic index")
    args = parser.parse_args()

    # API key: support OPENCODE_API_KEY (primary), OPENAI_API_KEY, OPENROUTER_API_KEY
    api_key = (
        os.environ.get("OPENCODE_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("OPENROUTER_API_KEY", "")
    )

    # YouTube credentials: read from local files if env vars not set
    token_json  = os.environ.get("TOKEN_JSON", "")
    client_json = os.environ.get("CLIENT_SECRETS_JSON", "")
    if not token_json:
        _tf = PROJECT_ROOT / "token.json"
        if _tf.exists():
            token_json = _tf.read_text(encoding="utf-8")
    if not client_json:
        _cf = PROJECT_ROOT / "client_secrets.json"
        if _cf.exists():
            client_json = _cf.read_text(encoding="utf-8")

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

    # ── Pick game mechanic (deterministic per video id) ───────────────────
    rng           = random.Random(current_id * 999 + 3)
    game_mechanic = rng.choice(GAME_MECHANICS)
    game_tag      = GAME_TAGS[game_mechanic]
    puzzle_num    = current_id + 1

    print(f"   Mechanic: {game_tag}  |  Puzzle #{puzzle_num:03d}")

    # ── Build LLM prompt & call ────────────────────────────────────────────
    prompt = build_llm_prompt(topic, game_mechanic, game_tag, puzzle_num)

    print("  🤖 Calling LLM for puzzle scene…")
    if not api_key:
        print("⚠ No API key — using mock scene")
        scene = _mock_scene(topic, game_mechanic, game_tag, puzzle_num)
    else:
        try:
            scene = await call_llm(prompt, api_key)
            # Ensure critical fields are set
            scene.setdefault("game_mechanic", game_mechanic)
            scene.setdefault("game_tag",      game_tag)
            scene.setdefault("series",        series)
            scene.setdefault("chapter",       chapter)
            scene.setdefault("puzzle_num",    puzzle_num)
        except Exception as e:
            print(f"❌ LLM failed: {e} — using mock scene")
            scene = _mock_scene(topic, game_mechanic, game_tag, puzzle_num)

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
    frames = render_frames(scene, series, frames_dir)

    # ── Compose video ──────────────────────────────────────────────────────
    final_video = tmp_dir / "final.mp4"
    video_path  = compose_video(frames, audio_paths, durations, final_video)
    if not video_path:
        print("❌ Video composition failed")
        return

    # ── Generate thumbnail ─────────────────────────────────────────────────
    thumb_path = tmp_dir / "thumbnail.jpg"
    generate_thumbnail(scene, series, thumb_path)

    # ── Upload to YouTube ──────────────────────────────────────────────────
    video_uploaded = False
    if not args.dry_run and token_json and client_json:
        from src.uploader import YouTubeUploader
        # Write credential files (stripping any UTF-8 BOM)
        token_json = token_json.lstrip("\ufeff").strip()
        client_json = client_json.lstrip("\ufeff").strip()
        token_file   = tmp_dir / "token.json"
        client_file  = tmp_dir / "client_secrets.json"
        token_file.write_text(token_json, encoding="utf-8")
        client_file.write_text(client_json, encoding="utf-8")


        uploader = YouTubeUploader(str(token_file), str(client_file))
        title    = scene.get("title", topic_desc[:60])
        subtitle = scene.get("subtitle", "")
        yt_title = f"{game_tag} {title}" if not title.startswith(game_tag[0]) else title
        yt_title = yt_title[:100]

        tags = [series, chapter, "programming", "system design", "software engineering",
                "advanced", "deep dive", game_mechanic.replace("_", " "),
                "distributed systems", "CS", "backend", "tech"]

        tc = scene.get("time_complexity", "")
        sc_val = scene.get("space_complexity", "")
        description = (
            f"{game_tag} — {topic_desc}\n\n"
            f"Series: {series} › {chapter}\n"
            f"Puzzle #{puzzle_num:03d}  |  {tc}  |  Space: {sc_val}\n\n"
            f"{'=' * 40}\n"
            f"Coding-puzzle-game style 2-minute deep dives for senior engineers.\n"
            f"Real Python code, live execution visualization, test cases.\n"
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
        "puzzle_num": puzzle_num,
        "series": series, "chapter": chapter, "topic": topic_desc,
        "title": scene.get("title", ""),
        "viz_type": scene.get("viz_type", ""),
        "game_mechanic": game_mechanic,
        "uploaded": video_uploaded,
        "video_id": locals().get("video_id"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    with open(history_path, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    # ── Channel Analytics & Auto-Growth Optimization ───────────────────────
    try:
        from src.analytics import ChannelAnalytics
        active_uploader = locals().get("uploader")
        analytics = ChannelAnalytics(active_uploader)
        growth_stats = analytics.analyze_performance(history_path)
        print(f"📊 Growth Analytics: {growth_stats.get('recommendation', 'Active')}")
    except Exception as e:
        print(f"  ⚠ Analytics skipped: {e}")


    # Cleanup frames (keep final video)
    if os.environ.get("GITHUB_ACTIONS") == "true":
        import shutil
        try:
            shutil.rmtree(str(frames_dir))
        except:
            pass

    next_topic = TECH_TOPICS[next_id % total]
    print(f"\n✅ Done! Next → #{next_id}: {next_topic[0]} › {next_topic[2][:50]}")


# ── Mock scene (Dynamic Topic-Specific Generator) ───────────────────────────
def _mock_scene(topic: tuple, game_mechanic: str, game_tag: str, puzzle_num: int) -> dict:
    series, chapter, topic_desc = topic
    desc_lower = topic_desc.lower()

    # Determine visual type dynamically based on topic keywords or puzzle rotation
    if any(k in desc_lower for k in ['stack', 'frame', 'call', 'recursion', 'prologue', 'epilogue', 'abi', 'calling']):
        viz_type = "stack"
    elif any(k in desc_lower for k in ['graph', 'jit', 'tree', 'ast', 'register', 'dep', 'route', 'hash', 'bpf', 'mesh']):
        viz_type = "graph"
    elif any(k in desc_lower for k in ['grid', 'matrix', 'table', 'cache', 'schedule', 'attention', 'dp', 'hpack']):
        viz_type = "grid"
    elif any(k in desc_lower for k in ['memory', 'pointer', 'gc', 'alloc', 'lock', 'segregated', 'buddy', 'rop', 'heap']):
        viz_type = "memory"
    else:
        v_types = ["stack", "graph", "grid", "memory", "bars"]
        viz_type = v_types[puzzle_num % len(v_types)]

    base = {
        "title":           topic_desc[:55],
        "subtitle":        f"{series} › {chapter}",
        "series":          series,
        "chapter":         chapter,
        "puzzle_num":      puzzle_num,
        "puzzle_stars":    3,
        "difficulty":      "HARD",
        "game_tag":        game_tag,
        "game_mechanic":   game_mechanic,
        "time_complexity": "O(1) — internal optimization",
        "space_complexity":"O(n) — frame storage",
        "viz_type":        viz_type,
        "viz_label":       viz_type.upper(),
    }

    if viz_type == "stack":
        base["code"] = [
            f"def execute_{chapter.lower().replace(' ', '_')}(arg1: int, arg2: int) -> int:",
            "    # System V AMD64 ABI function prologue",
            "    # push rbp; mov rbp, rsp",
            "    frame_ptr = 'rbp'",
            "    stack_ptr = 'rsp - 0x20'  # 32B local space",
            "",
            "    # Red Zone: 128B safe area below RSP",
            "    red_zone = [arg1 * 2, arg2 + 10]",
            "    res = compute_internal(red_zone[0], red_zone[1])",
            "",
            "    # Epilogue: mov rsp, rbp; pop rbp; ret",
            "    return res",
            "",
            "def compute_internal(x: int, y: int) -> int:",
            "    local_val = (x ^ y) & 0xFFFFFFFF",
            "    return local_val + 42",
        ]
        base["active_lines"] = [0, 1, 3, 4, 7, 8, 13, 14, 11]
        base["viz_data"] = {
            "frame_states": [
                ["main()"],
                ["main()", "prologue: push rbp"],
                ["main()", "prologue: mov rbp, rsp"],
                ["main()", "sub rsp, 0x20 (32B alloc)"],
                ["main()", "red_zone [rsp-128..rsp]"],
                ["main()", "compute_internal(x, y)"],
                ["main()", "compute_internal() → return"],
                ["main()", "epilogue: mov rsp, rbp"],
                ["main()", "epilogue: pop rbp; ret"],
            ]
        }
        base["test_cases"] = [
            {"label": "prologue", "input": "arg1=10, arg2=20", "expected": "RBP saved, RSP-32"},
            {"label": "red_zone", "input": "rsp-128..rsp",     "expected": "128B reserved"},
            {"label": "abi_pass", "input": "RDI=10, RSI=20",    "expected": "Passed in reg"},
            {"label": "epilogue", "input": "ret instruction",  "expected": "Caller RBP restored"},
        ]
        base["narration"] = [
            f"Deep dive into {topic_desc[:45]}. Let's inspect the call stack at the assembly level.",
            "Function prologue executes: saving caller's RBP on stack and establishing frame pointer.",
            "Stack pointer RSP moves down by 32 bytes to reserve space for local variables.",
            "Red Zone: System V AMD64 ABI permits 128 bytes below RSP without adjusting RSP.",
            "Function arguments passed in registers RDI, RSI, RDX, RCX, R8, R9 per System V ABI.",
            "Internal computations execute safely using frame-relative offsets RBP-0x8 and RBP-0x10.",
            "Function epilogue begins: restoring original RSP from RBP frame pointer.",
            "RBP popped off stack, restoring caller frame context seamlessly.",
            "RET instruction pops return address into RIP. Stack frame destroyed cleanly.",
        ]

    elif viz_type == "graph":
        base["code"] = [
            f"class {series.replace('/', '')}GraphSolver:",
            "    def __init__(self, nodes_cnt: int):",
            "        self.nodes = list(range(nodes_cnt))",
            "        self.edges = [(0,1), (1,2), (2,3), (3,4), (0,4)]",
            "",
            "    def traverse_hot_path(self, start: int) -> list[int]:",
            "        visited, queue = [], [start]",
            "        while queue:",
            "            node = queue.pop(0)",
            "            if node not in visited:",
            "                visited.append(node)",
            "                queue.extend(self.get_neighbors(node))",
            "        return visited",
            "",
            "    def get_neighbors(self, u: int) -> list[int]:",
            "        return [v for a, v in self.edges if a == u]",
        ]
        base["active_lines"] = [0, 1, 3, 5, 6, 7, 8, 10, 12]
        base["viz_data"] = {
            "nodes": [
                {"id": 0, "label": "Node0", "x": 280, "y": 140},
                {"id": 1, "label": "Node1", "x": 540, "y": 120},
                {"id": 2, "label": "Node2", "x": 800, "y": 160},
                {"id": 3, "label": "Node3", "x": 750, "y": 380},
                {"id": 4, "label": "Node4", "x": 420, "y": 390},
                {"id": 5, "label": "Node5", "x": 200, "y": 300},
            ],
            "edges": [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4), (1, 5)],
            "visited": [0, 1, 2, 3, 4, 5],
        }
        base["test_cases"] = [
            {"label": "root",   "input": "start=0", "expected": "visited=[0,1,2,3,4,5]"},
            {"label": "cycle",  "input": "(0,4) edge", "expected": "No infinite loop"},
            {"label": "degree", "input": "deg(0)=2",  "expected": "Out-edges checked"},
            {"label": "path",   "input": "0->1->2",   "expected": "Optimal hot path"},
        ]
        base["narration"] = [
            f"Analyzing {topic_desc[:45]}. Graph traversal maps execution dependencies.",
            "Vertices represent computation nodes while directed edges encode execution flow.",
            "Queue-based BFS traversal expands nodes level by level to discover hot execution paths.",
            "Visited set prevents redundant node evaluations and breaks cycle deadlocks.",
            "Register interference graph maps overlapping live variable lifetimes.",
            "Simplification phase pushes candidate nodes onto allocation stack.",
            "Coalescing merges non-interfering copy operations to eliminate instruction overhead.",
            "Graph coloring assigns available CPU registers without memory spill.",
            "Final traversal completes in O(V + E) time with zero register collisions.",
        ]

    elif viz_type == "grid":
        base["code"] = [
            f"def schedule_{series.lower()}_grid(items: list) -> list:",
            "    # Execution Grid & Pipeline Schedule",
            "    rows, cols = 5, 6",
            "    grid = [[0]*cols for _ in range(rows)]",
            "",
            "    for r in range(rows):",
            "        for c in range(cols):",
            "            # Pipeline cycle allocation",
            "            grid[r][c] = (r * 10 + c * 3) % 99",
            "",
            "    # Out-of-order execution reorder",
            "    return [val for row in grid for val in row]",
        ]
        base["active_lines"] = [0, 2, 3, 5, 6, 8, 10, 11, 11]
        base["viz_data"] = {
            "rows": 5,
            "cols": 6,
            "grid": [15, 28, 42, 56, 70, 84,  30, 44, 58, 72, 86, 12,  45, 59, 73, 87, 13, 27,  60, 74, 88, 14, 28, 42,  75, 89, 15, 29, 43, 57],
            "row_headers": ["FETCH", "DECODE", "EXEC", "MEM", "WRITE"],
            "col_headers": ["C0", "C1", "C2", "C3", "C4", "C5"],
        }
        base["test_cases"] = [
            {"label": "pipeline", "input": "5x6 grid", "expected": "30 cycles scheduled"},
            {"label": "hazard",   "input": "RAW check", "expected": "Zero pipeline stalls"},
            {"label": "latency",  "input": "C0..C5",   "expected": "100% execution efficiency"},
            {"label": "reorder",  "input": "ROB buffer","expected": "In-order commit"},
        ]
        base["narration"] = [
            f"Deep dive into {topic_desc[:45]}. Pipeline grid scheduling hides hardware latency.",
            "Execution matrix tracks fetch, decode, execute, memory access, and writeback stages.",
            "Read-After-Write hazards detected between consecutive instruction pipeline cycles.",
            "Instruction reorder buffer fills bubbles with independent computations.",
            "Multi-issue superscalar pipeline executes multiple instructions per clock cycle.",
            "L1 data cache hits complete memory stage in a single clock cycle.",
            "Branch predictor speculative execution stream validated at commit stage.",
            "Out-of-order execution engine maintains sequential program semantics.",
            "Optimal scheduling matrix achieves peak instruction throughput.",
        ]

    elif viz_type == "memory":
        base["code"] = [
            f"class {chapter.replace(' ', '')}Allocator:",
            "    def __init__(self, size_bytes: int = 1024):",
            "        self.heap = bytearray(size_bytes)",
            "        self.free_head = 0x7FFF00",
            "",
            "    def allocate_chunk(self, req_size: int) -> int:",
            "        # Segregated free-list allocation",
            "        chunk_addr = self.free_head",
            "        self.free_head += req_size + 16  # 16B header",
            "        return chunk_addr",
            "",
            "    def free_chunk(self, ptr: int):",
            "        # Coalesce adjacent free blocks",
            "        pass",
        ]
        base["active_lines"] = [0, 1, 2, 3, 5, 7, 8, 9, 11]
        base["viz_data"] = {
            "memory": [
                {"addr": "0x7FFF00", "label": "HEADER", "value": "16B [ALLOC]"},
                {"addr": "0x7FFF10", "label": "DATA",   "value": "256B payload"},
                {"addr": "0x7FFF110","label": "HEADER", "value": "16B [FREE]"},
                {"addr": "0x7FFF120","label": "DATA",   "value": "512B available"},
            ]
        }
        base["test_cases"] = [
            {"label": "alloc",  "input": "req=256B",  "expected": "ptr=0x7FFF00"},
            {"label": "header", "input": "16B meta",  "expected": "Size & flags set"},
            {"label": "align",  "input": "64B align", "expected": "L1 cache aligned"},
            {"label": "free",   "input": "coalesce",  "expected": "Merged contiguous"},
        ]
        base["narration"] = [
            f"Analyzing {topic_desc[:45]}. Heap allocators manage raw memory blocks.",
            "Segregated free lists group chunks into size classes for O(1) allocation.",
            "16-byte chunk headers store allocation size and in-use flags.",
            "Boundary tag coalescing merges adjacent free memory blocks on free().",
            "Buddy allocation splits powers-of-two blocks dynamically.",
            "Generational GC tracks young generation vs old generation promotion thresholds.",
            "Card table marking tracks cross-generational pointers from old to young objects.",
            "Tri-color marking guarantees concurrent GC safety without stop-the-world pause.",
            "Memory layouts aligned to 64-byte boundaries for maximum cache throughput.",
        ]

    else: # bars
        base["code"] = [
            f"def process_{series.lower()}_simd(vector: list[int]) -> list[int]:",
            "    # SIMD AVX-512 parallel execution loop",
            "    n = len(vector)",
            "    for i in range(0, n, 8):",
            "        # Parallel processing 8 64-bit integers",
            "        vector[i:i+8] = [x * 2 for x in vector[i:i+8]]",
            "",
            "    # Scalar cleanup loop for tail elements",
            "    for i in range(n - (n % 8), n):",
            "        vector[i] *= 2",
            "    return vector",
        ]
        base["active_lines"] = [0, 2, 3, 5, 5, 8, 9, 10, 10]
        base["viz_data"] = {
            "values": [92, 84, 76, 65, 52, 41, 30, 15],
            "steps": [
                [92, 84, 76, 65, 52, 41, 30, 15],
                [184, 168, 152, 130, 52, 41, 30, 15],
                [184, 168, 152, 130, 104, 82, 60, 30],
                [184, 168, 152, 130, 104, 82, 60, 30],
                [184, 168, 152, 130, 104, 82, 60, 30],
                [184, 168, 152, 130, 104, 82, 60, 30],
                [184, 168, 152, 130, 104, 82, 60, 30],
                [184, 168, 152, 130, 104, 82, 60, 30],
                [184, 168, 152, 130, 104, 82, 60, 30],
            ],
            "highlight": {"0": [0,4], "1": [4,8], "2": [0,8]},
            "operations": [
                f"SIMD Init: {topic_desc[:35]}",
                "AVX-512 ZMM0: Vector multiply [0..4]",
                "AVX-512 ZMM1: Vector multiply [4..8]",
                "FMA Instruction: (A * B) + C in 1 cycle",
                "Loop Unrolling: 8x instruction parallelism",
                "Scalar Tail Loop: Remaining elements",
                "64-byte Aligned Memory Load",
                "Execution Complete",
                "Result Verified ✓",
            ],
        }
        base["test_cases"] = [
            {"label": "vector",  "input": "8x64bit", "expected": "ZMM register loaded"},
            {"label": "fma",     "input": "FMA3",    "expected": "1 clock cycle"},
            {"label": "tail",    "input": "3 extra", "expected": "Scalar tail clean"},
            {"label": "speedup", "input": "AVX-512", "expected": "8x throughput"},
        ]
        base["narration"] = [
            f"Deep dive into {topic_desc[:45]}. SIMD vectorization executes 8 parallel operations.",
            "Auto-vectorizer checks loop stride and memory alignment requirements.",
            "AVX-512 zmm registers load 512 bits of data in a single clock cycle.",
            "Data alignment at 64-byte boundaries prevents misaligned vector penalty.",
            "Loop unrolling expands inner loop body to maximize instruction parallelism.",
            "Fused Multiply-Add (FMA) computes (A * B) + C in 1 CPU cycle.",
            "Mask registers handle conditional execution inside vector loops without branching.",
            "Scalar cleanup loop processes remaining tail elements seamlessly.",
            "Final result achieves 8x throughput speedup over scalar execution.",
        ]

    return base



if __name__ == "__main__":
    asyncio.run(main())

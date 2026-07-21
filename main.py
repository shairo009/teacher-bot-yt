"""
Tech Series Video Bot — Game Style
Teaches CS/Programming with animated dark-neon visuals
500+ unique topics, unlimited random objects, never repeats
"""

import os, sys, json, asyncio, argparse, subprocess, re, math, random, urllib.request
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

WIDTH  = 1080
HEIGHT = 1920
FPS    = 30

# ─────────────────────────────────────────────────────────────────────────────
# 500+ TECH TOPICS — complete CS curriculum, strict order, never repeats
# Format: (series, chapter, topic_description)
# ─────────────────────────────────────────────────────────────────────────────
TECH_TOPICS = [
    # ── PYTHON BASICS ──────────────────────────────────────────────────────
    ("Python","Variables",         "What is a Variable? boxes that store data"),
    ("Python","Data Types",        "int float str bool — the 4 core types"),
    ("Python","Data Types",        "Type casting: int() str() float() bool()"),
    ("Python","Strings",           "String indexing and slicing s[0:3] s[-1]"),
    ("Python","Strings",           "String methods: split join strip replace"),
    ("Python","Strings",           "f-Strings — embed variables inside text"),
    ("Python","Operators",         "Arithmetic: + - * / // % ** explained"),
    ("Python","Operators",         "Comparison: == != < > <= >= returns bool"),
    ("Python","Operators",         "Logical: and or not — combining conditions"),
    ("Python","Lists",             "List: mutable ordered sequence [1,2,3]"),
    ("Python","Lists",             "List methods: append pop insert remove sort"),
    ("Python","Lists",             "List slicing and list comprehension [x*2 for x in lst]"),
    ("Python","Tuples",            "Tuple: immutable list (1,2,3) — why use it?"),
    ("Python","Dicts",             "Dictionary: key-value pairs {name: value}"),
    ("Python","Dicts",             "Dict methods: get keys values items update"),
    ("Python","Sets",              "Set: unique unordered {1,2,3} union intersection"),
    ("Python","Control Flow",      "if elif else — branching decisions"),
    ("Python","Control Flow",      "Ternary expression: x if cond else y"),
    ("Python","Loops",             "for loop — iterate over any sequence"),
    ("Python","Loops",             "while loop — repeat until condition is False"),
    ("Python","Loops",             "break continue pass — loop control keywords"),
    ("Python","Loops",             "enumerate() and zip() — power tools for loops"),
    ("Python","Functions",         "def keyword — creating reusable functions"),
    ("Python","Functions",         "Parameters vs Arguments, default values"),
    ("Python","Functions",         "*args and **kwargs — flexible function inputs"),
    ("Python","Functions",         "return statement — function outputs"),
    ("Python","Functions",         "Lambda: one-line anonymous function"),
    ("Python","Functions",         "Closures — functions that remember their scope"),
    ("Python","Functions",         "Decorators — wrapping functions with @syntax"),
    ("Python","Functions",         "Recursion — function calling itself with base case"),
    ("Python","OOP",               "Classes and Objects — blueprint vs instance"),
    ("Python","OOP",               "__init__ constructor and self keyword"),
    ("Python","OOP",               "Inheritance: child class extends parent"),
    ("Python","OOP",               "Polymorphism — same method different behavior"),
    ("Python","OOP",               "Encapsulation: _ and __ name mangling"),
    ("Python","OOP",               "Abstract Classes — templates you cannot instantiate"),
    ("Python","OOP",               "Magic Methods: __str__ __len__ __eq__ __repr__"),
    ("Python","OOP",               "Class methods vs Static methods vs Instance methods"),
    ("Python","OOP",               "Property decorator — getter setter deleter"),
    ("Python","Advanced",          "List Dict Set Comprehensions — one-liners"),
    ("Python","Advanced",          "Generator functions — yield vs return"),
    ("Python","Advanced",          "Itertools: chain product combinations permutations"),
    ("Python","Advanced",          "Functools: reduce partial lru_cache wraps"),
    ("Python","Advanced",          "Context Managers — with open() as f"),
    ("Python","Advanced",          "Exception Handling — try except else finally raise"),
    ("Python","Advanced",          "Custom Exceptions — class MyError(Exception)"),
    ("Python","Advanced",          "Threading vs Multiprocessing in Python"),
    ("Python","Advanced",          "Global Interpreter Lock GIL — the big bottleneck"),
    ("Python","Advanced",          "asyncio: async await for concurrent code"),
    ("Python","Advanced",          "Python memory model: reference counting + GC"),
    ("Python","Advanced",          "Slots — __slots__ for memory-efficient classes"),
    ("Python","Advanced",          "Metaclasses — classes that create classes"),
    ("Python","Advanced",          "Descriptor Protocol — __get__ __set__ __delete__"),
    ("Python","Stdlib",            "collections: Counter defaultdict OrderedDict deque"),
    ("Python","Stdlib",            "pathlib: modern file path manipulation"),
    ("Python","Stdlib",            "dataclasses — auto-generate __init__ __repr__ etc"),
    ("Python","Stdlib",            "typing: hints List Dict Optional Union Callable"),
    ("Python","Stdlib",            "unittest and pytest — writing tests in Python"),
    ("Python","Stdlib",            "logging module — production-grade log system"),
    ("Python","Stdlib",            "argparse — CLI arguments for your scripts"),
    ("Python","Stdlib",            "json pickle csv — serialization formats"),
    # ── DATA STRUCTURES ────────────────────────────────────────────────────
    ("DSA","Arrays",               "Array basics: O(1) access O(n) search O(n) insert"),
    ("DSA","Arrays",               "Two Pointer technique — O(n) array problems"),
    ("DSA","Arrays",               "Sliding Window — max sum subarray in O(n)"),
    ("DSA","Arrays",               "Prefix Sum — range sum queries in O(1)"),
    ("DSA","Arrays",               "Kadane's Algorithm — maximum subarray"),
    ("DSA","Linked List",          "Singly Linked List: node.val node.next chain"),
    ("DSA","Linked List",          "Doubly Linked List: prev and next pointers"),
    ("DSA","Linked List",          "Floyd's Cycle Detection — fast and slow pointer"),
    ("DSA","Linked List",          "Reverse a Linked List — iterative and recursive"),
    ("DSA","Stack",                "Stack: LIFO push pop peek — O(1) all ops"),
    ("DSA","Stack",                "Monotonic Stack — next greater element pattern"),
    ("DSA","Stack",                "Valid Parentheses — classic stack problem"),
    ("DSA","Queue",                "Queue: FIFO enqueue dequeue — O(1) all ops"),
    ("DSA","Queue",                "Deque: double-ended queue both ends O(1)"),
    ("DSA","Queue",                "Priority Queue / Min-Heap — smallest in O(log n)"),
    ("DSA","Trees",                "Binary Tree: node with left and right child"),
    ("DSA","Trees",                "Binary Search Tree BST: O(log n) search"),
    ("DSA","Trees",                "Tree Traversal: Inorder Preorder Postorder BFS"),
    ("DSA","Trees",                "Height and Depth of a Binary Tree"),
    ("DSA","Trees",                "AVL Tree: self-balancing BST rotations"),
    ("DSA","Trees",                "Trie / Prefix Tree — autocomplete structure"),
    ("DSA","Trees",                "Segment Tree: range queries and point updates"),
    ("DSA","Trees",                "Fenwick Tree BIT: prefix sums in O(log n)"),
    ("DSA","Graphs",               "Graph: nodes edges directed undirected weighted"),
    ("DSA","Graphs",               "BFS Breadth First Search — shortest path unweighted"),
    ("DSA","Graphs",               "DFS Depth First Search — exploring all paths"),
    ("DSA","Graphs",               "Dijkstra: shortest path weighted graph O(E log V)"),
    ("DSA","Graphs",               "Bellman-Ford: handles negative weight edges"),
    ("DSA","Graphs",               "Floyd-Warshall: all pairs shortest paths O(V³)"),
    ("DSA","Graphs",               "Union-Find DSU: connected components O(α(n))"),
    ("DSA","Graphs",               "Topological Sort: dependency ordering with DFS"),
    ("DSA","Graphs",               "Minimum Spanning Tree: Kruskal and Prim"),
    ("DSA","Hashing",              "Hash Table: O(1) average insert lookup delete"),
    ("DSA","Hashing",              "Hash Collision: chaining vs open addressing"),
    ("DSA","Hashing",              "Rolling Hash: Rabin-Karp string matching"),
    ("DSA","Sorting",              "Bubble Sort O(n²): swap adjacent if out of order"),
    ("DSA","Sorting",              "Selection Sort O(n²): find min put in place"),
    ("DSA","Sorting",              "Insertion Sort O(n²): build sorted array left to right"),
    ("DSA","Sorting",              "Merge Sort O(n log n): divide conquer merge"),
    ("DSA","Sorting",              "Quick Sort O(n log n): pivot partition recurse"),
    ("DSA","Sorting",              "Heap Sort O(n log n): use max-heap"),
    ("DSA","Sorting",              "Counting Sort O(n+k): for bounded integers"),
    ("DSA","Sorting",              "Radix Sort O(nk): digit by digit"),
    ("DSA","Algorithms",           "Binary Search O(log n): sorted array halving"),
    ("DSA","Algorithms",           "Big O Notation: O(1) O(log n) O(n) O(n²) O(2ⁿ)"),
    ("DSA","Algorithms",           "Recursion — base case recursive case call stack"),
    ("DSA","Algorithms",           "Dynamic Programming: memoization vs tabulation"),
    ("DSA","Algorithms",           "0/1 Knapsack — classic DP problem"),
    ("DSA","Algorithms",           "Longest Common Subsequence LCS with DP"),
    ("DSA","Algorithms",           "Coin Change — minimum coins DP problem"),
    ("DSA","Algorithms",           "Greedy: local optimal leading to global optimal"),
    ("DSA","Algorithms",           "Backtracking: explore undo with recursion"),
    ("DSA","Algorithms",           "Divide and Conquer: split solve merge"),
    ("DSA","Algorithms",           "Bit Manipulation: AND OR XOR NOT shifts"),
    # ── SYSTEM DESIGN ──────────────────────────────────────────────────────
    ("System Design","Fundamentals","Client-Server Architecture — who talks to whom"),
    ("System Design","Fundamentals","API Gateway — one front door for every service"),
    ("System Design","Fundamentals","Load Balancer — distribute traffic across servers"),
    ("System Design","Fundamentals","CDN Content Delivery Network — serve from edge"),
    ("System Design","Fundamentals","Caching: Redis Memcached — why they're so fast"),
    ("System Design","Fundamentals","Message Queue: Kafka RabbitMQ — async decoupling"),
    ("System Design","Fundamentals","Rate Limiting — token bucket leaky bucket"),
    ("System Design","Fundamentals","Circuit Breaker — stop calling a failing service"),
    ("System Design","Fundamentals","Service Discovery — how services find each other"),
    ("System Design","Fundamentals","Health Checks — is your service alive?"),
    ("System Design","Databases",   "Database Sharding — horizontal partitioning"),
    ("System Design","Databases",   "Database Replication — primary + read replicas"),
    ("System Design","Databases",   "CAP Theorem — Consistency Availability Partition"),
    ("System Design","Databases",   "ACID properties — Atomicity Consistency Isolation Durability"),
    ("System Design","Databases",   "Eventual Consistency — BASE vs ACID"),
    ("System Design","Databases",   "Consistent Hashing — minimize resharding"),
    ("System Design","Scalability", "Horizontal vs Vertical Scaling — scale out vs up"),
    ("System Design","Scalability", "Microservices vs Monolith — tradeoffs"),
    ("System Design","Scalability", "Event-Driven Architecture — produce consume events"),
    ("System Design","Scalability", "CQRS — Command Query Responsibility Segregation"),
    ("System Design","Scalability", "Event Sourcing — store events derive state"),
    ("System Design","Scalability", "Saga Pattern — distributed transactions"),
    ("System Design","Scalability", "Strangler Fig — migrate monolith to microservices"),
    ("System Design","Storage",     "SQL vs NoSQL — when to choose which"),
    ("System Design","Storage",     "Blob Storage: S3 — store images videos files"),
    ("System Design","Storage",     "Time Series DB — InfluxDB Prometheus metrics"),
    ("System Design","Storage",     "Search Engine — Elasticsearch inverted index"),
    ("System Design","Storage",     "Data Warehouse vs Data Lake — analytics storage"),
    # ── AI AND ML ──────────────────────────────────────────────────────────
    ("AI/ML","Basics",             "What is Machine Learning — patterns from data"),
    ("AI/ML","Basics",             "Supervised vs Unsupervised vs Reinforcement Learning"),
    ("AI/ML","Basics",             "Training vs Inference — learning vs using model"),
    ("AI/ML","Basics",             "Loss Function — how wrong is your model?"),
    ("AI/ML","Basics",             "Gradient Descent — rolling downhill to minimum"),
    ("AI/ML","Basics",             "Learning Rate — step size in gradient descent"),
    ("AI/ML","Basics",             "Batch vs Stochastic vs Mini-Batch Gradient Descent"),
    ("AI/ML","Basics",             "Overfitting vs Underfitting — bias variance tradeoff"),
    ("AI/ML","Basics",             "Train Validation Test Split — why 3 sets?"),
    ("AI/ML","Basics",             "Cross Validation — k-fold splitting"),
    ("AI/ML","Basics",             "Feature Engineering — turning raw data into signals"),
    ("AI/ML","Basics",             "Normalization vs Standardization — scaling features"),
    ("AI/ML","Algorithms",         "Linear Regression — fit a line to predict numbers"),
    ("AI/ML","Algorithms",         "Logistic Regression — classify with sigmoid"),
    ("AI/ML","Algorithms",         "Decision Tree — if-else machine learning"),
    ("AI/ML","Algorithms",         "Random Forest — ensemble of decision trees"),
    ("AI/ML","Algorithms",         "XGBoost — gradient boosted trees explained"),
    ("AI/ML","Algorithms",         "SVM Support Vector Machine — max margin classifier"),
    ("AI/ML","Algorithms",         "K-Means Clustering — group without labels"),
    ("AI/ML","Algorithms",         "k-NN k Nearest Neighbors — classify by neighbors"),
    ("AI/ML","Algorithms",         "PCA Principal Component Analysis — dimensionality reduction"),
    ("AI/ML","Algorithms",         "DBSCAN — density-based clustering"),
    ("AI/ML","Neural Nets",        "Perceptron — simplest artificial neuron"),
    ("AI/ML","Neural Nets",        "Activation Functions: ReLU Sigmoid Tanh GELU"),
    ("AI/ML","Neural Nets",        "Backpropagation — computing gradients layer by layer"),
    ("AI/ML","Neural Nets",        "Dropout — randomly disable neurons to prevent overfit"),
    ("AI/ML","Neural Nets",        "Batch Normalization — stabilize training"),
    ("AI/ML","Neural Nets",        "CNN Convolutional Neural Network — image recognition"),
    ("AI/ML","Neural Nets",        "RNN Recurrent Neural Network — sequences memory"),
    ("AI/ML","Neural Nets",        "LSTM Long Short-Term Memory — long sequence memory"),
    ("AI/ML","Neural Nets",        "Attention Mechanism — focus on what matters"),
    ("AI/ML","Neural Nets",        "Transformer Architecture — encoder decoder explained"),
    # ── LLMs ───────────────────────────────────────────────────────────────
    ("LLMs","Fundamentals",       "Tokens — how LLMs see text not words"),
    ("LLMs","Fundamentals",       "Tokenizer: BPE Byte Pair Encoding explained"),
    ("LLMs","Fundamentals",       "Embeddings — turning tokens into number vectors"),
    ("LLMs","Fundamentals",       "Self-Attention — every token attends to every token"),
    ("LLMs","Fundamentals",       "Multi-Head Attention — parallel attention heads"),
    ("LLMs","Fundamentals",       "Positional Encoding — order in transformers"),
    ("LLMs","Fundamentals",       "Context Window — how much an LLM can see at once"),
    ("LLMs","Fundamentals",       "Temperature — controlling randomness in output"),
    ("LLMs","Fundamentals",       "Top-K and Top-P nucleus sampling strategies"),
    ("LLMs","Fundamentals",       "Hallucination — why LLMs confidently lie"),
    ("LLMs","Fundamentals",       "RLHF — Reinforcement Learning from Human Feedback"),
    ("LLMs","Prompting",          "Prompt Engineering — write instructions that work"),
    ("LLMs","Prompting",          "Few-Shot Learning — examples inside the prompt"),
    ("LLMs","Prompting",          "Chain-of-Thought — make LLM think step by step"),
    ("LLMs","Prompting",          "System Prompt vs User Prompt — roles explained"),
    ("LLMs","Prompting",          "ReAct — Reasoning plus Acting with tools"),
    ("LLMs","Fine-tuning",        "Fine-tuning vs RAG — when to use which"),
    ("LLMs","Fine-tuning",        "LoRA Low Rank Adaptation — cheap fine-tuning"),
    ("LLMs","Fine-tuning",        "QLoRA — quantized LoRA for consumer GPUs"),
    ("LLMs","Fine-tuning",        "PEFT Parameter Efficient Fine Tuning methods"),
    ("LLMs","Fine-tuning",        "Instruction Tuning — train LLM to follow commands"),
    ("LLMs","Applications",       "RAG Retrieval Augmented Generation explained"),
    ("LLMs","Applications",       "Vector Database: Pinecone Weaviate Chroma Qdrant"),
    ("LLMs","Applications",       "Semantic Search — similarity beyond keywords"),
    ("LLMs","Applications",       "AI Agents — plan act observe loop"),
    ("LLMs","Applications",       "Tool Use and Function Calling in LLMs"),
    ("LLMs","Applications",       "Multi-Agent Systems — agents that coordinate"),
    ("LLMs","Applications",       "LangChain vs LlamaIndex — orchestration frameworks"),
    ("LLMs","Applications",       "Guardrails — keeping LLM output safe and valid"),
    # ── WEB DEV ────────────────────────────────────────────────────────────
    ("Web Dev","HTTP",            "HTTP: how the web works request response cycle"),
    ("Web Dev","HTTP",            "HTTP Methods: GET POST PUT PATCH DELETE"),
    ("Web Dev","HTTP",            "HTTP Status Codes: 200 201 400 401 403 404 500"),
    ("Web Dev","HTTP",            "HTTP Headers: Content-Type Auth Cache-Control"),
    ("Web Dev","HTTP",            "REST API design: resources endpoints best practices"),
    ("Web Dev","HTTP",            "WebSockets — real-time bidirectional full-duplex"),
    ("Web Dev","HTTP",            "GraphQL — query exactly what you need"),
    ("Web Dev","HTTP",            "gRPC — high performance RPC with protobuf"),
    ("Web Dev","Security",        "JWT JSON Web Token — stateless authentication"),
    ("Web Dev","Security",        "OAuth 2.0 — login with Google GitHub"),
    ("Web Dev","Security",        "SQL Injection — why parameterized queries matter"),
    ("Web Dev","Security",        "XSS Cross Site Scripting — inject and steal"),
    ("Web Dev","Security",        "CSRF Cross Site Request Forgery attack"),
    ("Web Dev","Security",        "CORS — Cross Origin Resource Sharing explained"),
    ("Web Dev","Security",        "HTTPS TLS — how encryption works in transit"),
    ("Web Dev","Frontend",        "DOM Document Object Model — live HTML tree"),
    ("Web Dev","Frontend",        "JavaScript Event Loop — single thread non-blocking"),
    ("Web Dev","Frontend",        "React Virtual DOM — why React updates are fast"),
    ("Web Dev","Frontend",        "CSS Flexbox vs Grid — layout systems compared"),
    ("Web Dev","Frontend",        "Progressive Web App PWA — offline first web"),
    ("Web Dev","Backend",         "FastAPI — async Python API framework"),
    ("Web Dev","Backend",         "Django REST Framework — batteries included"),
    ("Web Dev","Backend",         "Middleware — plug-in between request and handler"),
    ("Web Dev","Backend",         "Session vs Cookie vs Token — auth storage"),
    # ── DEVOPS ─────────────────────────────────────────────────────────────
    ("DevOps","Containers",       "Docker — package your app and its dependencies"),
    ("DevOps","Containers",       "Docker Image vs Container — class vs instance"),
    ("DevOps","Containers",       "Dockerfile — build image step by step"),
    ("DevOps","Containers",       "Docker Compose — multi-container apps in YAML"),
    ("DevOps","Containers",       "Docker Volumes — persist data outside container"),
    ("DevOps","Kubernetes",       "Kubernetes — orchestrating containers at scale"),
    ("DevOps","Kubernetes",       "Pod Deployment Service — K8s core objects"),
    ("DevOps","Kubernetes",       "Horizontal Pod Autoscaler — auto scale on CPU"),
    ("DevOps","Kubernetes",       "ConfigMap and Secret — config without rebuild"),
    ("DevOps","Kubernetes",       "Ingress — route external traffic to services"),
    ("DevOps","CI/CD",            "CI/CD Pipeline — build test deploy automatically"),
    ("DevOps","CI/CD",            "GitHub Actions — automate with YAML workflows"),
    ("DevOps","CI/CD",            "Blue-Green Deployment — zero downtime releases"),
    ("DevOps","CI/CD",            "Canary Release — test on small % of users"),
    ("DevOps","CI/CD",            "GitOps — Git as single source of truth"),
    ("DevOps","Cloud",            "AWS EC2 vs Lambda — server vs serverless"),
    ("DevOps","Cloud",            "Serverless Functions — event-driven scale to zero"),
    ("DevOps","Cloud",            "Infrastructure as Code — Terraform Pulumi"),
    ("DevOps","Monitoring",       "Observability: logs metrics traces — the three pillars"),
    ("DevOps","Monitoring",       "Prometheus + Grafana — metrics and dashboards"),
    ("DevOps","Monitoring",       "Distributed Tracing — Jaeger OpenTelemetry"),
    # ── DATABASES ──────────────────────────────────────────────────────────
    ("Databases","SQL",           "SQL basics: SELECT FROM WHERE ORDER LIMIT"),
    ("Databases","SQL",           "JOIN types: INNER LEFT RIGHT FULL CROSS"),
    ("Databases","SQL",           "GROUP BY HAVING — aggregation in SQL"),
    ("Databases","SQL",           "Indexes: B-Tree index — how queries speed up 100x"),
    ("Databases","SQL",           "Query Execution Plan — EXPLAIN ANALYZE"),
    ("Databases","SQL",           "Transactions: BEGIN COMMIT ROLLBACK SAVEPOINT"),
    ("Databases","SQL",           "Isolation Levels: Read Uncommitted → Serializable"),
    ("Databases","SQL",           "N+1 Query Problem — the hidden performance killer"),
    ("Databases","SQL",           "Database Normalization: 1NF 2NF 3NF BCNF"),
    ("Databases","SQL",           "Window Functions: ROW_NUMBER RANK PARTITION BY"),
    ("Databases","NoSQL",         "MongoDB: document-based flexible schema"),
    ("Databases","NoSQL",         "Redis: in-memory key-value store lightning fast"),
    ("Databases","NoSQL",         "Cassandra: wide-column writes at any node"),
    ("Databases","NoSQL",         "Neo4j: graph database for relationship data"),
    ("Databases","Concepts",      "ORM Object Relational Mapping: SQLAlchemy"),
    ("Databases","Concepts",      "Connection Pooling — reuse database connections"),
    ("Databases","Concepts",      "Database Migration — schema changes over time"),
    # ── NETWORKING ─────────────────────────────────────────────────────────
    ("Networking","Basics",       "OSI Model 7 layers — from bits to applications"),
    ("Networking","Basics",       "TCP vs UDP — reliability vs raw speed"),
    ("Networking","Basics",       "DNS — domain name to IP address lookup"),
    ("Networking","Basics",       "IP Addressing: IPv4 IPv6 subnets CIDR"),
    ("Networking","Basics",       "TCP Three-Way Handshake: SYN SYN-ACK ACK"),
    ("Networking","Basics",       "HTTP Keep-Alive vs Connection per Request"),
    ("Networking","Advanced",     "TLS Handshake — how HTTPS encrypts your data"),
    ("Networking","Advanced",     "HTTP/2 multiplexing — parallel streams one connection"),
    ("Networking","Advanced",     "HTTP/3 QUIC — UDP-based fast protocol"),
    ("Networking","Advanced",     "WebRTC — real-time video audio in browser"),
    ("Networking","Advanced",     "VPN — Virtual Private Network tunnel"),
    ("Networking","Advanced",     "NAT Network Address Translation"),
    # ── DESIGN PATTERNS ────────────────────────────────────────────────────
    ("Patterns","Creational",     "Singleton — only one instance ever exists"),
    ("Patterns","Creational",     "Factory Pattern — delegate object creation"),
    ("Patterns","Creational",     "Builder Pattern — construct complex objects step by step"),
    ("Patterns","Creational",     "Prototype — clone existing object"),
    ("Patterns","Structural",     "Adapter — make incompatible interfaces work together"),
    ("Patterns","Structural",     "Decorator — add behavior without subclassing"),
    ("Patterns","Structural",     "Proxy — control access intercept calls"),
    ("Patterns","Structural",     "Composite — treat tree of objects uniformly"),
    ("Patterns","Structural",     "Facade — simple interface to complex subsystem"),
    ("Patterns","Behavioral",     "Observer — pub/sub notify on state change"),
    ("Patterns","Behavioral",     "Strategy — swap algorithms at runtime"),
    ("Patterns","Behavioral",     "Command — encapsulate action for undo/redo"),
    ("Patterns","Behavioral",     "Iterator — traverse collection without exposing it"),
    ("Patterns","Behavioral",     "State — behavior changes with object state"),
    ("Patterns","Behavioral",     "Template Method — define skeleton override steps"),
    # ── GIT ────────────────────────────────────────────────────────────────
    ("Git","Basics",              "Git: commit add status push pull clone init"),
    ("Git","Basics",              "Branching: feature branches main branch strategy"),
    ("Git","Basics",              "Merge vs Rebase — two ways to combine histories"),
    ("Git","Basics",              "Merge Conflicts — how to resolve them"),
    ("Git","Basics",              "Git stash — park changes without committing"),
    ("Git","Basics",              ".gitignore — what to keep out of version control"),
    ("Git","Advanced",            "Interactive Rebase — squash fixup reorder commits"),
    ("Git","Advanced",            "Cherry-pick — take one commit from another branch"),
    ("Git","Advanced",            "Git bisect — binary search to find breaking commit"),
    ("Git","Advanced",            "Git hooks — run scripts on commit push events"),
    ("Git","Advanced",            "Monorepo vs Polyrepo — organizing multiple projects"),
    # ── CS FUNDAMENTALS ────────────────────────────────────────────────────
    ("CS","Memory",               "Stack vs Heap — two areas of process memory"),
    ("CS","Memory",               "Garbage Collection: reference counting mark-sweep"),
    ("CS","Memory",               "Cache Hierarchy: L1 L2 L3 RAM — speed vs size"),
    ("CS","Memory",               "Memory Leak — objects you forgot to free"),
    ("CS","Concurrency",          "Process vs Thread — isolation vs sharing"),
    ("CS","Concurrency",          "Race Condition — when timing destroys correctness"),
    ("CS","Concurrency",          "Mutex and Semaphore — thread synchronization"),
    ("CS","Concurrency",          "Deadlock: circular wait how to prevent it"),
    ("CS","Concurrency",          "Lock-Free Data Structures — compare and swap"),
    ("CS","OS",                   "Virtual Memory — more RAM than physically exists"),
    ("CS","OS",                   "System Calls — how programs talk to the kernel"),
    ("CS","OS",                   "Process Scheduling: FIFO Round-Robin CFS"),
    ("CS","OS",                   "File System: inodes blocks directories"),
    ("CS","Crypto",               "Hashing: SHA256 one-way function fingerprint"),
    ("CS","Crypto",               "Symmetric vs Asymmetric Encryption"),
    ("CS","Crypto",               "Public Key Infrastructure PKI — certificates CA"),
    ("CS","Crypto",               "Digital Signatures — prove authenticity"),
    ("CS","Crypto",               "Bcrypt — safe password hashing with salt"),
    # ── NUMPY / PANDAS ─────────────────────────────────────────────────────
    ("Python/NumPy","NumPy",      "NumPy arrays: vectorized math no for-loops"),
    ("Python/NumPy","NumPy",      "Broadcasting — operations on different shapes"),
    ("Python/NumPy","NumPy",      "Array indexing: slicing boolean fancy indexing"),
    ("Python/NumPy","NumPy",      "np.dot matmul — matrix multiplication"),
    ("Python/NumPy","Pandas",     "DataFrame and Series — tabular data in Python"),
    ("Python/NumPy","Pandas",     "groupby agg transform — split apply combine"),
    ("Python/NumPy","Pandas",     "merge join concat — combining DataFrames"),
    ("Python/NumPy","Pandas",     "pivot_table crosstab — reshaping data"),
    ("Python/NumPy","Pandas",     "Missing data: isnull dropna fillna impute"),
]

# Objects that animate through the scene — random mix every video
OBJECT_LIBRARY = [
    "fish","rocket","car","robot","crystal","satellite","packet",
    "bird","dragon","submarine","gear","lightning","diamond","comet",
    "ufo","bug","train","airplane","bubble","star","turtle","cat",
    "token","hexagon","molecule","arrow","flame","snowflake","leaf",
    "virus","drop","crown","shield","key","lock","eye","bolt","wave",
]


# ─────────────────────────────────────────────────────────────────────────────
# LLM — generate scene layout from topic
# ─────────────────────────────────────────────────────────────────────────────

def generate_scene_with_llm(topic_tuple, question_id, api_key, obj_a, obj_b):
    """Call free LLM to generate a unique visual scene for this topic."""
    series, chapter, topic = topic_tuple

    prompt = f"""You are designing a short animated tech educational video (YouTube Shorts, portrait 1080x1920).
Topic: "{topic}" (Series: {series} | Chapter: {chapter})
Animated objects in this video: {obj_a} and {obj_b} (these move through the scene representing data/items being processed).

Generate a dark-neon game-style visual scene JSON. Rules:
- scene_type: one of "flow" | "transform" | "cycle" | "compare" | "network" | "stack" | "race"
- nodes: 3-6 boxes/shapes. Each has id, label (short CAPS), type (one of: box|gate|database|cloud|brain|chip|server|user|module), x (50-1030), y (200-1600), color (neon hex)
- paths: connections between nodes [{{"from":"id1","to":"id2"}}] — 2-5 paths
- steps: exactly 6 Hinglish narration lines (max 15 words each) — mix English tech terms with simple Hindi explanation. Every line must teach something new and specific. Style: "Python mein variable ek box hota hai jo value store karta hai" or "Binary search O(log n) mein kaam karta hai — sorted array mein"
- title: concept name (2-3 words max)
- subtitle: what it does (5-7 words)
- hook: engaging question (max 10 words, ends with ?)
- accent: main neon color hex for this topic
- counter_a: label for counter A (e.g. "PROCESSED", "SUCCESS", "CACHED") with max number (10-50)
- counter_b: label for counter B (e.g. "BLOCKED", "FAILED", "MISSED") with max number (3-15)

Layout rules:
- Objects enter from bottom (y≈1600) travel to center (y≈900) then branch to top nodes (y≈300-500)
- Keep nodes spread across x: 150-930
- Title goes at top (not in nodes)

Reply with ONLY valid JSON, no markdown, no explanation:
{{
  "title": "...",
  "subtitle": "...",
  "hook": "...",
  "accent": "#RRGGBB",
  "scene_type": "...",
  "nodes": [{{"id":"...","label":"...","type":"...","x":0,"y":0,"color":"#RRGGBB"}}],
  "paths": [{{"from":"...","to":"..."}}],
  "steps": ["...","...","...","...","...","..."],
  "counter_a": {{"label":"...","max":0}},
  "counter_b": {{"label":"...","max":0}}
}}"""

    payload = json.dumps({
        "model": "deepseek-v4-pro",
        "max_tokens": 1200,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://opencode.ai/zen/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    )

    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            content = (data.get("choices", [{}])[0]
                           .get("message", {}).get("content", "") or "")
            if not content.strip():
                print(f"⚠ Empty LLM response (attempt {attempt})")
                continue
            m = re.search(r'\{[\s\S]*\}', content)
            if not m:
                print(f"⚠ No JSON in response (attempt {attempt})")
                continue
            scene = json.loads(m.group())
            # validate
            required = ["title","subtitle","hook","accent","scene_type","nodes","paths","steps","counter_a","counter_b"]
            for f in required:
                if f not in scene:
                    raise ValueError(f"Missing field: {f}")
            if len(scene["steps"]) < 6:
                scene["steps"] = (scene["steps"] * 6)[:6]
            scene["series"]  = series
            scene["chapter"] = chapter
            scene["topic"]   = topic
            scene["id"]      = question_id
            scene["obj_a"]   = obj_a
            scene["obj_b"]   = obj_b
            print(f"✅ Scene generated: {scene['title']} ({scene['scene_type']}) | objects: {obj_a}, {obj_b}")
            return scene
        except json.JSONDecodeError as e:
            print(f"⚠ JSON parse error attempt {attempt}: {e}")
        except Exception as e:
            print(f"⚠ LLM error attempt {attempt}: {e}")

    print("❌ LLM failed. Using fallback scene.")
    return _fallback_scene(topic_tuple, question_id, obj_a, obj_b)


def _fallback_scene(topic_tuple, question_id, obj_a, obj_b):
    series, chapter, topic = topic_tuple
    words = topic.split()
    title = " ".join(words[:3]).title()
    return {
        "id": question_id, "series": series, "chapter": chapter, "topic": topic,
        "title": title, "subtitle": "how it really works",
        "hook": f"what exactly is {title}?",
        "accent": "#38BDF8", "scene_type": "flow", "obj_a": obj_a, "obj_b": obj_b,
        "nodes": [
            {"id": "input",  "label": "INPUT",   "type": "box",    "x": 540, "y": 1400, "color": "#64748B"},
            {"id": "core",   "label": "PROCESS", "type": "chip",   "x": 540, "y": 900,  "color": "#38BDF8"},
            {"id": "output", "label": "OUTPUT",  "type": "box",    "x": 540, "y": 400,  "color": "#34D399"},
        ],
        "paths": [{"from": "input", "to": "core"}, {"from": "core", "to": "output"}],
        "steps": [
            f"{title} is a core computer science concept.",
            "It takes input and processes it step by step.",
            "The result gives us exactly what we need.",
            f"Master {title} and level up your skills!",
        ],
        "counter_a": {"label": "PROCESSED", "max": 20},
        "counter_b": {"label": "FAILED",    "max": 2},
    }


# ─────────────────────────────────────────────────────────────────────────────
# AUDIO — edge-tts narration
# ─────────────────────────────────────────────────────────────────────────────

async def generate_audio(steps, output_dir):
    """Generate one TTS mp3 per narration step."""
    import edge_tts
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    voice = "hi-IN-SwaraNeural"
    for i, text in enumerate(steps):
        out = str(output_dir / f"step_{i:03d}.mp3")
        try:
            comm = edge_tts.Communicate(text, voice, rate="-5%")
            await comm.save(out)
            if Path(out).exists() and Path(out).stat().st_size > 100:
                paths.append(out)
                print(f"  🔊 Audio step {i}: {text[:50]}")
        except Exception as e:
            print(f"  ⚠ TTS error step {i}: {e}")
    return paths


def get_audio_duration(path):
    try:
        r = subprocess.run(
            ["ffprobe","-v","error","-show_entries","format=duration",
             "-of","default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return float(r.stdout.strip())
    except:
        pass
    return 5.0


# ─────────────────────────────────────────────────────────────────────────────
# VIDEO COMPOSITION
# ─────────────────────────────────────────────────────────────────────────────


    def download_bgm(output_path, duration_secs):
      """Download free CC0 lo-fi track or generate ambient fallback."""
      urls = [
          "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
          "https://www.bensound.com/bensound-music/bensound-ukulele.mp3",
      ]
      raw = Path(output_path).parent / "bgm_raw.mp3"
      for url in urls:
          try:
              req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
              with urllib.request.urlopen(req, timeout=20) as resp:
                  raw.write_bytes(resp.read())
              r = subprocess.run([
                  "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(raw),
                  "-t", str(int(duration_secs) + 3),
                  "-af", f"volume=0.07,afade=t=in:st=0:d=2,afade=t=out:st={max(1,int(duration_secs)-2)}:d=2",
                  "-c:a", "aac", "-b:a", "128k", output_path
              ], capture_output=True, timeout=60)
              if r.returncode == 0:
                  print("  🎵 Background music: downloaded track")
                  return True
          except Exception:
              continue
      # Fallback: ffmpeg synthesized ambient chord
      try:
          total = int(duration_secs) + 3
          r = subprocess.run([
              "ffmpeg", "-y", "-f", "lavfi",
              "-i", f"aevalsrc=0.05*sin(2*PI*220*t)+0.04*sin(2*PI*165*t)+0.03*sin(2*PI*110*t):s=44100:c=stereo",
              "-t", str(total),
              "-af", f"volume=0.12,lowpass=f=500,aecho=0.6:0.5:150:0.3,afade=t=in:st=0:d=2,afade=t=out:st={max(1,total-2)}:d=2",
              "-c:a", "aac", "-b:a", "128k", output_path
          ], capture_output=True, timeout=60)
          if r.returncode == 0:
              print("  🎵 Background music: ambient tone")
              return True
      except Exception:
          pass
      print("  ⚠️  No background music (will skip)")
      return False

    def compose_video(frame_dir, audio_paths, output_path, durations):
    """Compose frames + audio into final mp4."""
    frame_dir   = Path(frame_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build concat list
    concat_file = str(frame_dir / "concat.txt")
    frames = sorted(frame_dir.glob("frame_*.png"))
    if not frames:
        print("❌ No frames to compose")
        return None

    fps_per_frame = FPS
    frames_per_step = 135  # 4.5s per step at 30fps

    with open(concat_file, "w") as f:
        for i, frame in enumerate(frames):
            step_idx = min(i // frames_per_step, len(durations) - 1)
            dur = durations[step_idx] / frames_per_step if durations else 1.0 / fps_per_frame
            f.write(f"file '{frame.absolute()}'\n")
            f.write(f"duration {dur:.6f}\n")
        # last frame hold
        f.write(f"file '{frames[-1].absolute()}'\n")

    raw_video = str(output_path.parent / "raw_video.mp4")
    r = subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-vf", f"scale={WIDTH}:{HEIGHT},fps={FPS}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-pix_fmt", "yuv420p", raw_video
    ], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(f"❌ Video render error: {r.stderr[-400:]}")
        return None

    # Concat audio
    if not audio_paths:
        import shutil
        shutil.copy(raw_video, str(output_path))
        return str(output_path)

    audio_list = str(output_path.parent / "audio_list.txt")
    with open(audio_list, "w") as f:
        for ap in audio_paths:
            f.write(f"file '{Path(ap).absolute()}'\n")

    merged_audio = str(output_path.parent / "merged_audio.mp3")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", audio_list, "-c", "copy", merged_audio
    ], capture_output=True, timeout=60)

    # Mix BGM at low volume under voice narration
      bgm_path = str(output_path.parent / "bgm.aac")
      total_dur = sum(durations) if durations else 40
      has_bgm = download_bgm(bgm_path, total_dur)

      if has_bgm and os.path.exists(bgm_path):
          r = subprocess.run([
              "ffmpeg", "-y",
              "-i", raw_video, "-i", merged_audio, "-i", bgm_path,
              "-filter_complex",
              "[1:a]volume=1.0[voice];[2:a]volume=0.08[bgm];[voice][bgm]amix=inputs=2:duration=first[aout]",
              "-map", "0:v", "-map", "[aout]",
              "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
              "-shortest", str(output_path)
          ], capture_output=True, text=True, timeout=300)
          if r.returncode == 0 and output_path.exists():
              size_mb = output_path.stat().st_size / 1e6
              print(f"✅ Video composed (with BGM): {output_path} ({size_mb:.1f}MB)")
              return str(output_path)
          print(f"⚠️  BGM mix failed, falling back to voice-only")

      # Fallback: voice only, no BGM
      r = subprocess.run([
          "ffmpeg", "-y",
          "-i", raw_video, "-i", merged_audio,
          "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
          "-shortest", str(output_path)
      ], capture_output=True, text=True, timeout=300)

      if r.returncode == 0 and output_path.exists():
          size_mb = output_path.stat().st_size / 1e6
          print(f"✅ Video composed: {output_path} ({size_mb:.1f}MB)")
          return str(output_path)

      print(f"❌ Final compose error: {r.stderr[-300:]}")
      return None


# ─────────────────────────────────────────────────────────────────────────────
# THUMBNAIL GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def generate_thumbnail(scene, output_path):
    try:
        from PIL import Image, ImageDraw, ImageFont
        from src.tech_visual_engine import TechVisualEngine
        engine = TechVisualEngine(scene["obj_a"], scene["obj_b"])
        img = engine.render_thumbnail(scene)
        img.save(str(output_path), "JPEG", quality=95)
        print(f"  🖼 Thumbnail: {output_path}")
        return str(output_path)
    except Exception as e:
        print(f"  ⚠ Thumbnail error: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────


    def ensure_fonts():
      """Download Montserrat fonts from Google Fonts if not present."""
      font_dir = PROJECT_ROOT / "assets" / "fonts"
      font_dir.mkdir(parents=True, exist_ok=True)
      fonts = {
          "Montserrat-Bold.ttf":    "https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Bold.ttf",
          "Montserrat-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Regular.ttf",
      }
      for fname, url in fonts.items():
          dest = font_dir / fname
          if not dest.exists():
              try:
                  req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                  with urllib.request.urlopen(req, timeout=30) as resp:
                      dest.write_bytes(resp.read())
                  print(f"  ✅ Font: {fname}")
              except Exception as e:
                  print(f"  ⚠️  Font download failed ({fname}): {e}")

    async def main():
    print("\n[0/5] Downloading fonts...")
    ensure_fonts()
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", "-d", action="store_true")
    parser.add_argument("--force",   "-f", action="store_true")
    args = parser.parse_args()

    api_key = (os.environ.get("OPENAI_API_KEY") or
               os.environ.get("OPENCODE_API_KEY") or
               os.environ.get("ANTHROPIC_API_KEY") or "")

    if not api_key:
        print("❌ No API key found (OPENAI_API_KEY / OPENCODE_API_KEY)")
        sys.exit(1)

    # ── Load progress ──────────────────────────────────────────────────────
    data_dir      = PROJECT_ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    progress_path = data_dir / "tech_progress.json"
    history_path  = data_dir / "video_history.json"

    if progress_path.exists():
        with open(progress_path) as f:
            progress = json.load(f)
    else:
        progress = {"current_id": 0}

    current_id = progress["current_id"]
    total      = len(TECH_TOPICS)

    # Loop back to 0 after all topics done — infinite unique variety
    topic_idx  = current_id % total
    topic      = TECH_TOPICS[topic_idx]

    # Pick 2 random objects (different every run based on id + randomness)
    random.seed(current_id * 31 + random.randint(0, 999))
    obj_choices = random.sample(OBJECT_LIBRARY, 2)
    obj_a, obj_b = obj_choices[0], obj_choices[1]

    print("=" * 60)
    print(f"  Tech Series Bot  |  Video #{current_id}")
    print(f"  Topic: {topic[2][:55]}")
    print(f"  Series: {topic[0]} | Chapter: {topic[1]}")
    print(f"  Objects: {obj_a}, {obj_b}")
    print("=" * 60)

    # ── Generate scene with LLM ────────────────────────────────────────────
    print("\n[1/5] Generating scene with LLM...")
    scene = generate_scene_with_llm(topic, current_id, api_key, obj_a, obj_b)

    # ── Render frames ──────────────────────────────────────────────────────
    print("\n[2/5] Rendering frames...")
    try:
        from src.tech_visual_engine import TechVisualEngine
        engine     = TechVisualEngine(obj_a, obj_b)
        frame_dir  = PROJECT_ROOT / "temp_frames"
        import shutil
        if frame_dir.exists():
            shutil.rmtree(frame_dir)
        frame_dir.mkdir(parents=True)
        frame_paths = engine.render_all_frames(scene, str(frame_dir))
        print(f"  ✅ {len(frame_paths)} frames rendered")
    except Exception as e:
        print(f"  ❌ Frame render error: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    # ── Generate audio ─────────────────────────────────────────────────────
    print("\n[3/5] Generating audio...")
    audio_dir   = PROJECT_ROOT / "temp_audio"
    import shutil
    if audio_dir.exists():
        shutil.rmtree(audio_dir)
    audio_paths = await generate_audio(scene["steps"], str(audio_dir))
    durations   = [get_audio_duration(a) for a in audio_paths]
    print(f"  ✅ {len(audio_paths)} audio clips | total: {sum(durations):.1f}s")

    # ── Compose video ──────────────────────────────────────────────────────
    print("\n[4/5] Composing video...")
    outputs_dir  = PROJECT_ROOT / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    safe_title   = re.sub(r'[^\w\s-]', '', scene["title"]).replace(' ', '_')[:30]
    video_name   = f"tech_{current_id:04d}_{safe_title}.mp4"
    video_path   = outputs_dir / video_name
    thumb_path   = outputs_dir / f"thumb_{current_id:04d}.jpg"

    final_video = compose_video(str(frame_dir), audio_paths, str(video_path), durations)
    if not final_video:
        print("❌ Video composition failed!")
        sys.exit(1)

    generate_thumbnail(scene, str(thumb_path))

    # ── Upload ─────────────────────────────────────────────────────────────
    print("\n[5/5] Uploading to YouTube...")
    video_uploaded = False
    token_json     = PROJECT_ROOT / "token.json"

    if not args.dry_run and token_json.exists():
        try:
            from src.uploader import YouTubeUploader
            uploader = YouTubeUploader()
            if uploader.authenticate():
                # Generate metadata
                title_text = (
                    f"{scene['title']} Explained | {topic[0]} Series | "
                    f"#{current_id+1} Game Visual"
                )[:100]
                desc = (
                    f"🎮 {scene['subtitle'].capitalize()}\n\n"
                    f"📚 Series: {topic[0]}\n"
                    f"📖 Chapter: {topic[1]}\n"
                    f"💡 Topic: {topic[2]}\n\n"
                    f"🤖 Animated with: {obj_a} & {obj_b}\n\n"
                    f"🔔 Subscribe for daily tech concepts explained with game visuals!\n\n"
                    f"#coding #programming #tech #cs #{topic[0].replace('/','')} "
                    f"#learntocode #shorts #viral"
                )
                tags = [
                    topic[0], topic[1], scene['title'],
                    "coding", "programming", "tech", "cs", "shorts",
                    "learn coding", "game visual", "explained",
                    "computer science", "developer", "software",
                ]
                video_id = uploader.upload_video(
                    video_path=final_video,
                    title=title_text,
                    description=desc,
                    tags=tags,
                    thumbnail_path=str(thumb_path) if thumb_path.exists() else None,
                    category_id="28",  # Science & Technology
                    made_for_kids=False,
                )
                if video_id:
                    print(f"✅ Uploaded! https://youtu.be/{video_id}")
                    video_uploaded = True
        except Exception as e:
            print(f"❌ Upload error: {e}")
    else:
        mode = "dry-run" if args.dry_run else "no token.json"
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
        "series": topic[0], "chapter": topic[1], "topic": topic[2],
        "title": scene["title"], "obj_a": obj_a, "obj_b": obj_b,
        "uploaded": video_uploaded,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    with open(history_path, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    # Cleanup
    if os.environ.get("GITHUB_ACTIONS") == "true":
        try:
            Path(final_video).unlink(missing_ok=True)
        except:
            pass

    print(f"\n✅ Done! Next video will be #{next_id} ({TECH_TOPICS[next_id % total][2][:40]})")


if __name__ == "__main__":
    asyncio.run(main())

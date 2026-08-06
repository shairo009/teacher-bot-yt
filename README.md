# Tech Series Bot 🎮💻

**Automated YouTube Shorts** teaching Computer Science & Programming with **game-style dark neon visuals**.

Every video is unique — different tech concept + different animated objects (fish, rockets, cars, robots, crystals...).

## What It Makes

Each video:
- 🌑 **Dark neon background** with animated grid
- 🎮 **Game-style diagram** — nodes, glowing connections, counters
- 🐟🚀 **Random animated objects** (fish, rockets, robots, crystals...) flowing through the concept
- 🔊 **English narration** via Edge-TTS
- ⚡ **30 FPS smooth animation** at 1080×1920

## Topics Covered (500+)

| Series | Examples |
|--------|----------|
| **Python** | Variables, OOP, Decorators, asyncio, Generators... |
| **DSA** | Binary Search, BFS/DFS, Dijkstra, DP, Sorting... |
| **System Design** | API Gateway, Load Balancer, CAP Theorem, Kafka... |
| **AI/ML** | Transformers, Backprop, CNN, LSTM, LoRA... |
| **LLMs** | Tokens, Embeddings, RAG, Agents, Fine-tuning... |
| **Web Dev** | REST, JWT, OAuth, WebSockets, GraphQL... |
| **DevOps** | Docker, Kubernetes, CI/CD, Prometheus... |
| **Databases** | SQL Joins, Indexes, CAP, NoSQL, Redis... |
| **Networking** | OSI, TCP/UDP, TLS, DNS, HTTP/3... |
| **Design Patterns** | Singleton, Observer, Strategy, CQRS... |
| **Git** | Merge vs Rebase, Interactive Rebase, bisect... |
| **CS Fundamentals** | Memory, Concurrency, OS, Crypto... |

Topics cycle infinitely — **never repeats** within a full cycle.

## Animated Objects (30+)

Every video randomly picks 2 objects from:
`fish • rocket • car • robot • crystal • satellite • packet • bird • dragon • submarine • gear • lightning • diamond • comet • ufo • bug • train • airplane • bubble • star • turtle • cat • token • hexagon • molecule • flame • snowflake • leaf • virus • crown • shield • key • bolt • wave...`

## How It Works

```
1. Pick next topic from 500+ ordered list (never repeats)
2. Pick 2 random animated objects (different every run)
3. LLM (DeepSeek free) generates unique scene layout + narration
4. PIL renders dark-neon game-style frames (30fps)
5. Edge-TTS generates English narration audio (free)
6. FFmpeg composes final 1080×1920 MP4
7. Upload to YouTube automatically
```

## Setup

### 1. Clone
```bash
git clone https://github.com/shairo009/teacher-bot-yt.git
cd teacher-bot-yt
```

### 2. Add GitHub Secrets
| Secret | Value |
|--------|-------|
| `OPENAI_API_KEY` | OpenCode API key (free at opencode.ai) |
| `TOKEN_JSON` | YouTube OAuth token.json content |
| `CLIENT_SECRETS_JSON` | YouTube client_secrets.json content |

### 3. Run locally
```bash
pip install -r requirements.txt
python main.py --dry-run   # test without uploading
python main.py             # full run + upload

```

## GitHub Actions Schedule

Runs **6 times daily** at IST: 6 AM, 10 AM, 2 PM, 6 PM, 10 PM, 2 AM

## Cost: **Zero** 💰

- Edge-TTS: free
- PIL + FFmpeg: free
- GitHub Actions: free tier
- LLM: DeepSeek via OpenCode (free)
- YouTube API: free

## License

MIT

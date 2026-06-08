# Your Auto Trading Strategy - Deployment Guide

## 📋 Table of Contents

1. [Environment Setup](#environment-setup)
2. [Configuration](#configuration)
3. [Running the Strategy](#running-the-strategy)
4. [Monitoring](#monitoring)
5. [Troubleshooting](#troubleshooting)

---

## 🔧 Environment Setup

### Step 1: Clone Your Fork

```bash
git clone https://github.com/houkewei5-create/pumpfun-bonkfun-bot.git
cd pumpfun-bonkfun-bot
```

### Step 2: Create Virtual Environment

```bash
# Create venv
python3 -m venv .venv

# Activate on macOS/Linux
source .venv/bin/activate

# Or on Windows
.venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Install uv package manager
pip install uv

# Install project dependencies
uv sync
uv pip install -e .
```

---

## ⚙️ Configuration

### Step 1: Environment Variables

```bash
# Copy example config
cp .env.example .env

# Edit .env file
nano .env  # or use your favorite editor
```

**Required variables:**

```bash
# RPC endpoints
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
# Better: Use private RPC from Chainstack, Helius, etc.
# SOLANA_RPC_URL=https://solana-mainnet.g.alchemy.com/v2/YOUR_KEY

# Your wallet
WALLET_PRIVATE_KEY=your_base58_private_key_here

# API Keys
GMGN_API_KEY=your_gmgn_api_key
DEXSCREENER_API_KEY=optional

# Optional: For alerts
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Step 2: Strategy Parameters

Edit `bots/your_strategy.yaml` to customize:

```yaml
# Capital
initial_usd: 1000.0
position_size_normal_pct: 5
position_size_strong_pct: 8
max_positions: 6

# Entry filters
entry_scoring:
  total_score_threshold: 32
  strong_golddog_threshold: 38

# Exit rules
exit_stops:
  protect_period_sec: 120
  stop_abs_fallback_pct: -25
  stop_soft_5m_pct: -10

# And many more...
```

---

## 🚀 Running the Strategy

### Paper Trading (Recommended First)

```bash
# Run in paper mode (simulation, no real money)
python -m src.bot_runner \
  --config bots/your_strategy.yaml \
  --paper \
  --log-level DEBUG
```

You should see output like:

```
2026-06-08 20:00:00 INFO: Strategy started in PAPER mode
2026-06-08 20:00:05 INFO: Connected to Solana RPC
2026-06-08 20:00:10 INFO: Watching trending tokens...
2026-06-08 20:00:15 INFO: Candidate found: TokenA (score: 38)
2026-06-08 20:00:16 INFO: BUY signal: TokenA @ $0.0001
```

### Live Trading (After Testing)

```bash
# WARNING: This uses REAL MONEY
# Only do this after:
# 1. Paper trading for 7+ days
# 2. Verified the bot logic is correct
# 3. Using a SMALL test wallet

python -m src.bot_runner \
  --config bots/your_strategy.yaml \
  --live \
  --wallet-amount-sol 0.5
```

---

## 📊 Monitoring

### Dashboard (Real-time)

In another terminal:

```bash
python -m src.dashboard.main
# Open browser to http://localhost:8787
```

### Log Files

```bash
# View logs
tail -f logs/trading.log

# Or follow with color
watch -n 1 'tail -20 logs/trading.log'
```

### JSON Event Stream

```bash
# Watch trading events
watch -n 0.5 'tail -10 data/events.jsonl'
```

---

## 🐛 Troubleshooting

### Issue: "Connection refused" to RPC

**Solution:**
1. Check your RPC URL in `.env`
2. Test RPC directly: `curl -X POST your_rpc_url`
3. Use public RPC if needed (but it's slower)
4. Better: Get a private RPC from Chainstack, Helius, etc.

### Issue: "Permission denied" on private key

**Solution:**
1. Make sure private key is in base58 format
2. Don't include quotes around the key
3. Use `solana config get` to verify format

### Issue: No candidates found

**Solution:**
1. Check GMGN API key is valid
2. Verify network connectivity
3. Lower entry score threshold temporarily
4. Check time (tokens most active 8am-4pm UTC)

### Issue: Positions not closing

**Solution:**
1. Check DexScreener API connectivity
2. Review exit rules in config
3. Check log for specific exit conditions

---

## 📈 Performance Metrics

After running for a while, check:

```bash
# Win rate
grep -c "SELL.*profit" logs/trading.log / grep -c "SELL" logs/trading.log

# Average holding time
awk '/BUY/{buy=$0} /SELL/{if(buy) print}' logs/trading.log

# Total PnL
grep "Portfolio" logs/trading.log | tail -1
```

---

## 🔐 Security Best Practices

1. **Use burner wallet** - Never use your main wallet
2. **Keep .env private** - Never commit to git
3. **Use private RPC** - Public RPC can see your addresses
4. **Monitor API keys** - Rotate regularly
5. **Test first** - Always paper trade first
6. **Start small** - Begin with minimal capital

---

## ⏸️ Pausing & Resuming

```bash
# Graceful shutdown (closes open positions)
Ctrl+C

# Resume from saved state
python -m src.bot_runner --resume
```

---

## 📞 Support

For issues:
1. Check logs: `logs/trading.log`
2. Review config: `bots/your_strategy.yaml`
3. Check GitHub issues
4. Ask in community channels


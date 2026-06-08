# Your Auto Trading Strategy - Complete Guide

## 📚 Overview

This is a comprehensive automated trading bot for Solana MEME tokens with:

- **Multi-factor entry scoring** (F1-F6 factors)
- **Sophisticated exit management** (time-layered stops, ladder take profits)
- **Risk controls** (position sizing, max holdings, graveyard system)
- **Real-time monitoring** (dashboard, event logging, factor auditing)

---

## 🎯 Strategy Architecture

### Layer 1: Data Collection (L1)
- GMGN API for token info and trends
- DexScreener for price and market cap
- Solana RPC for on-chain verification

### Layer 2: Signal Generation (L2)
- **Phase 1 Filter**: 10 hard filters (age, holders, liquidity, etc.)
- **Phase 2 Filter**: Safety verification (LP burn, dev holding, etc.)
- **Entry Scorer**: F1-F6 factors + age multiplier

### Layer 3: Decision Making (L3)
- **Entry Decision**: Buy if score ≥ 32 (or ≥ 38 for strong golddog)
- **Position Management**: Normal 5% or strong 8% sizing
- **Exit Signals**: Multiple detector running in parallel

### Layer 4: Execution (L4)
- **Buy**: Place order via Pump.fun or Raydium
- **Sell**: Partial (take profit) or full (stop loss)
- **Shadow trading**: Simulate before real execution

### Layer 5: Logging & Auditing (L5)
- Events stream (JSONL format)
- Factor audit (every 100 trades)
- Position snapshots
- Performance metrics

---

## 📊 Entry Scoring System (F1-F6)

### Factor 1: vs_pre_max (Price Pullback)

Measures price recovery from recent low:

```
< 0.5       → -10 pts (too far from peak)
0.5~0.9     → +15 pts (healthy pullback) ✅
0.9~1.0     → +10 pts
1.0~1.05    → +5 pts
≥ 1.05      → -5 pts (already pumped)
```

### Factor 2: holder_growth (Community Growth)

Holder count increase rate:

```
≥ 1.0       → +15 pts (100% growth)
≥ 0.5       → +10 pts (50% growth) ✅
≥ 0.3       → +5 pts (30% growth)
< 0.3       → -5 pts (weak growth)
```

### Factor 3: buy_sell_ratio (Market Sentiment)

Buying pressure vs selling:

```
1.5~2.0     → +5 pts
2.0~3.0     → +10 pts (ideal) ✅
≥ 3.0       → +8 pts (maybe too hot)
1.0~1.5     → +3 pts
< 1.0       → -10 pts (net sellers)
```

### Factor 4: holder/UT Ratio (Distribution Quality)

Average holding per unique trader:

```
≤ 2         → +10 pts (well distributed) ✅
2~4.2       → +5 pts
4.2~10      → 0 pts
> 10        → -8 pts (concentrated)
```

### Factor 5: velocity (Speed Factor)

Volume and trader momentum:

```
volume_ratio ≥ 1.5     → +5 pts
ut_growth ≥ 0.5        → +5 pts
```

### Factor 6: safety_score (Risk Assessment)

Based on LP burn, mint status, dev holding:

```
≥ 0.7       → +10 pts (very safe)
≥ 0.5       → +5 pts (acceptable)
< 0.5       → 0 pts
```

### Age Multiplier

Applied to final score:

```
<5 min      → 0.5~1.0 (linear)
5~15 min    → 1.0 (peak) ✅
>15 min     → 1.0~0.4 (decay)
```

### Total Score

```
Base Score = F1 + F2 + F3 + F4 + F5 + F6
Final Score = Base Score × Age Multiplier + Fast Path Bonus

Threshold: ≥ 32 to buy
Strong Golddog: ≥ 38 + holder_growth ≥ 0.4 → 8% position instead of 5%
```

---

## 🛑 Exit Rules

### Stop Loss (Prevent Losses)

#### CRITICAL (Immediate Exit)
- **Absolute Fallback**: -25% loss at any time
- **LP Zero**: Liquidity went to zero (RUG PULL)
- **Price Zero**: Price went to zero (SCAM)

#### HIGH (Protected at First 2 Minutes)
- **Rate 10s**: 10-second drop ≥ 12%
- **Rate 30s**: 30-second drop ≥ 20%
- **Rate 1m**: 1-minute drop ≥ 30%

#### MID (After Holding a While)
- **Soft Stop 5m**: Held >5min and down 10%
- **Soft Stop 15m**: Held >15min and down 6%
- **Absolute Floor**: After protect period, down 3%

### Take Profit (Lock In Gains)

Ladder strategy based on market cap multiples:

```
1.20x mcap → Sell 20% ✅ (Lock in early gains)
1.30x mcap → Sell 30% ✅ (Take more chips off table)
1.80x mcap → Sell 30%
2.00x mcap → Sell 20%
```

### Rug Detection

- **LP Burn Ratio**: Track if LP disappears
- **Supply Burn**: Detect sudden token burning
- **Mint Authority**: Confirm it's revoked

---

## 💼 Position Management

### Entry Sizing

```
Capital: $1,000

Normal Position: 5% = $50
Strong Golddog: 8% = $80
Max Per Token: 10% = $100
Max Concurrent: 6 tokens = $600 max exposure
```

### Graveyard System

After closing a position:

- **Regular Close**: 10-minute cooldown before retry
- **Rug/Scam**: Permanent blacklist

### Rebalancing

Automatically triggered when:
- New position would exceed limits
- Portfolio allocation shifts
- Risk metrics exceed thresholds

---

## 📈 Example Trades

### Trade 1: Perfect Entry ✅

```
Token: PUMP123
Score: 35 (F1:15, F2:10, F3:5, F4:5)
Entry: $0.001 @ 10:00
  Position: $50 (5%)
  
10:05 - $0.0015 (1.5x)
  → Price high updated
  → Holding for TP triggers

10:07 - $0.0012 (1.2x mcap)
  → TP_20 triggered: Sell $10 (20%)
  → Remaining: $40
  
10:15 - $0.0025 (2.5x)
  → TP_200 triggered: Sell $8 (20% of $40)
  → Remaining: $32
  → Exit: +$20 profit
```

### Trade 2: Quick Stop Loss

```
Token: SCAM456
Score: 32 (borderline)
Entry: $0.001 @ 10:00
  Position: $50
  
10:00:15 - Price: $0.00095 (-5%)
  → Within protect period, no action
  
10:00:45 - Price: $0.00087 (-13%)
  → 10s drop = -13% ≥ -12%
  → RATE_STOP_10S triggered
  → Sell ALL
  → Loss: -$5 (-10%)
```

---

## 🔒 Security Features

### Zero-Tolerance Checks

1. **LP Burn**: ≥ 99% must be burned or locked
2. **Mint Revoked**: Minting authority must be revoked
3. **Dev Holding**: Team must have burned ≥ 80% of their tokens

### Phase 1 Hard Filters

If ANY of these fail, token is rejected:
- Age: 1~1440 minutes
- Holders: ≥ 30
- Liquidity: ≥ $5,000
- Top 10: ≤ 60%
- Rat ratio: ≤ 30%
- Bundler: ≤ 30%
- Unique traders: ≥ 1
- Buy/Sell ratio: > 0.70
- Holder/UT ratio: ≤ 80
- Market cap: $30k~$10M

---

## 📊 Monitoring & Analytics

### Key Metrics

```
Win Rate = Profitable Exits / Total Exits
Avg Gain = Average % gain on winners
Avg Loss = Average % loss on losers
Profit Factor = Total Gains / Total Losses
Sharpe Ratio = Return / Risk
```

### Factor Audit

Every 100 trades, analyze:
- Which factors most correlated with wins
- Factor weights optimization
- Parameter adjustments needed

---

## ⚠️ Warnings

1. **Past performance ≠ future results**
2. **Crypto markets are highly volatile**
3. **Always start with small capital**
4. **Use a burner wallet, never your main wallet**
5. **This bot can lose money quickly**
6. **Test thoroughly in paper mode first**


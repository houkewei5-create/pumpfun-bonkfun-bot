# Solana MEME Token Auto Trading Bot

**Your Complete Automated Trading Strategy for Pump.fun Tokens**

## ⚡ Quick Start (5 Minutes)

```bash
# 1. Clone and setup
git clone https://github.com/houkewei5-create/pumpfun-bonkfun-bot.git
cd pumpfun-bonkfun-bot
python3 -m venv .venv && source .venv/bin/activate
uv sync && uv pip install -e .

# 2. Configure
cp .env.example .env
# Edit .env with your RPC, wallet, API keys

cp bots/your_strategy.yaml.example bots/your_strategy.yaml
# Optional: Edit parameters

# 3. Run (Paper Trading)
python -m src.bot_runner --config bots/your_strategy.yaml --paper

# 4. Monitor
python -m src.dashboard.main
# Open http://localhost:8787
```

---

## 📋 Complete File Structure

```
pumpfun-bonkfun-bot/
├── src/
│   ├── your_strategy/                  ← YOUR STRATEGY (All new modules)
│   │   ├── __init__.py
│   │   ├── config.py                   (策略配置参数)
│   │   ├── filters.py                  (Phase1/Phase2 过滤)
│   │   ├── entry_scorer.py             (F1-F6 评分系统)
│   │   ├── decider.py                  (决策引擎)
│   │   ├── position_context.py         (持仓管理)
│   │   ├── signal_bus.py               (信号总线)
│   │   ├── data_source.py              (数据源)
│   │   └── detectors/
│   │       ├── stop_loss.py            (止损检测)
│   │       ├── take_profit.py          (止盈检测)
│   │       ├── rug_detector.py         (Rug检测)
│   │       └── dump_detector.py        (卖压检测)
│   ├── bot_runner.py                   (主循环 - 保持不变)
│   └── exchange/                       (交易执行 - 保持不变)
│
├── tests/
│   ├── test_filters.py                 (过滤器测试)
│   ├── test_scorer.py                  (评分器测试)
│   ├── test_integration.py             (集成测试)
│   └── test_detectors.py               (检测器测试)
│
├── bots/
│   └── your_strategy.yaml              (策略配置)
│
├── config.env                          (环境变量)
├── .env.example                        (环境变量示例)
├── STRATEGY_GUIDE.md                   (策略详解)
├── DEPLOYMENT_GUIDE.md                 (部署运维)
└── README.md                           (本文件)
```

---

## 🎯 Strategy Overview

### Entry System (入场)

**Phase 1: Hard Filters** ❌
- 10 条硬过滤规则
- 任意一条失败直接拒绝
- 检查：年龄、持币者、流动性、市值等

**Phase 2: Safety Verification** 🛡️
- LP 销毁比例
- 铸币权状态
- 团队代币销毁
- 操纵检测（Rat、Bundler）

**Entry Scoring: F1-F6 Factors** 📊
- F1: 价格回调（vs_pre_max）
- F2: 持币者增长
- F3: 买卖比
- F4: 持币者/交易者比
- F5: 速度因子（成交量、交易者增长）
- F6: 安全分数

**Threshold**: 总分 ≥ 32 买入，≥ 38 且增长 ≥ 40% 视为强金狗（8% 仓位）

### Exit System (出场)

**CRITICAL (立即执行)** 🚨
- 亏损 ≤ -25%
- LP 或价格为 0（Rug Pull）

**HIGH (保护期外执行)** ⚠️
- 10s 跌 ≥ 12%
- 30s 跌 ≥ 20%
- 1min 跌 ≥ 30%

**MID (中优先级)** 📍
- 持仓 >5min 且 -10%
- 持仓 >15min 且 -6%

**LOW (止盈)** ✅
- 市值 1.20x → 卖 20%
- 市值 1.30x → 卖 30%
- 市值 1.80x → 卖 30%
- 市值 2.00x → 卖 20%

---

## 📊 Key Features

| 功能 | 说明 |
|------|------|
| **多因子评分** | F1-F6 + 年龄乘数 |
| **时间分层止损** | 保护期 + 阶段性止损 |
| **阶梯止盈** | 4 层 take profit |
| **持仓管理** | 位置大小 + 最大持仓限制 |
| **Rug检测** | LP 销毁 + 供应量骤变 |
| **风险控制** | 绝对止损 + Graveyard |
| **实时监控** | Dashboard + 日志 |
| **因子审计** | 每 100 笔交易分析 |
| **纸交易** | 完整的模拟运行 |

---

## 🚀 Configuration

### Basic Parameters (bots/your_strategy.yaml)

```yaml
capital:
  initial_usd: 1000.0
  position_size_normal_pct: 5      # 普通仓位
  position_size_strong_pct: 8      # 强金狗仓位
  single_token_cap_pct: 10         # 单币上限
  max_positions: 6                 # 最大持仓

entry_scoring:
  total_score_threshold: 32
  strong_golddog_threshold: 38

exit_stops:
  stop_abs_fallback_pct: -25       # 绝对止损
  stop_soft_5m_pct: -10            # 软止损
  stop_soft_15m_pct: -6

exit_tp:
  tp_20_mcap_mult: 1.20            # 1.20x 卖 20%
  tp_30_mcap_mult: 1.30            # 1.30x 卖 30%
  tp_80_mcap_mult: 1.80            # 1.80x 卖 30%
  tp_200_mcap_mult: 2.00           # 2.00x 卖 20%
```

### Environment Variables (.env)

```bash
# RPC
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
# 推荐使用私有 RPC (Chainstack, Helius, QuickNode)

# Wallet
WALLET_PRIVATE_KEY=your_base58_key_here

# APIs
GMGN_API_KEY=your_gmgn_api_key
DEXSCREENER_API_KEY=optional

# Alerts (Optional)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## 🧪 Testing

### Run Unit Tests

```bash
# All tests
pytest tests/ -v

# Specific test
pytest tests/test_filters.py -v
pytest tests/test_scorer.py -v

# With coverage
pytest tests/ --cov=src/your_strategy
```

### Paper Trading

```bash
# 7 days minimum recommended
python -m src.bot_runner --config bots/your_strategy.yaml --paper --log-level DEBUG
```

Monitor output:
```
2026-06-08 20:00:00 INFO: Starting bot in PAPER mode
2026-06-08 20:00:05 INFO: Strategy loaded: Your Auto Trading Strategy
2026-06-08 20:00:10 INFO: Connected to Solana RPC
2026-06-08 20:00:15 INFO: Monitoring 50 trending tokens...
2026-06-08 20:00:20 INFO: Candidate: TOKEN1 (score: 35, safe: 0.65)
2026-06-08 20:00:21 INFO: BUY signal: TOKEN1 @ $0.00001
2026-06-08 20:00:25 INFO: Position opened: TOKEN1 $50 (5%)
```

---

## 📊 Monitoring & Dashboard

### Dashboard

```bash
# Terminal 1: Run bot
python -m src.bot_runner --config bots/your_strategy.yaml --paper

# Terminal 2: Start dashboard
python -m src.dashboard.main

# Terminal 3: Open browser
open http://localhost:8787
```

**Dashboard shows:**
- Real-time positions
- Entry/exit signals
- Portfolio statistics
- Factor audit results
- Event timeline

### Logs

```bash
# Watch trading log
tail -f logs/trading.log

# View events
cat data/events.jsonl | jq .

# Factor audit
cat data/factor_audit.json | jq .
```

---

## ⚠️ Important Warnings

1. **This bot can lose money** - Crypto markets are highly volatile
2. **Start with small capital** - Don't risk more than you can afford to lose
3. **Use burner wallet** - Never use your main wallet
4. **Test thoroughly** - Paper trade for 7+ days before live trading
5. **Monitor closely** - Don't leave it running unattended
6. **Keep .env secret** - Never commit to git or share

---

## 🛠️ Troubleshooting

### No candidates found
- Check GMGN API key
- Verify network connectivity
- Lower entry score threshold temporarily

### Positions not closing
- Check DexScreener connectivity
- Review exit rules in config
- Check logs for specific errors

### High slippage
- Use Jito bundles (configured in bot_runner)
- Increase priority fee
- Reduce position size

---

## 📖 Documentation

- **STRATEGY_GUIDE.md**: Complete strategy explanation
- **DEPLOYMENT_GUIDE.md**: Installation & operation guide
- **src/your_strategy/config.py**: All parameters documented
- **Code comments**: Every module well documented

---

## 🔒 Security

✅ **Best Practices:**
- Use burner wallet with minimal balance
- Store .env file securely
- Use private RPC endpoint
- Rotate API keys regularly
- Monitor for suspicious activity

❌ **Never:**
- Share private keys
- Commit .env to git
- Use main wallet
- Leave bot unattended long-term
- Trust unverified code

---

## 📝 License

Apache 2.0 - See LICENSE file

---

## 💬 Support

For issues:
1. Check logs: `logs/trading.log`
2. Review config: `bots/your_strategy.yaml`
3. Run tests: `pytest tests/`
4. Check documentation

---

**Happy trading! Remember: Always start small and scale up.** 🚀

# Epic Games Status Monitor 🎮

![Python](https://img.shields.io/badge/python-v3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

A comprehensive, dependency-light **command line monitor for Epic Games services**. It polls Epic's public status APIs and the Epic Games Store promotions backend, then renders a colored terminal dashboard covering system status, individual components, Easy Anti-Cheat, live incidents, free game giveaways, and the health of the upstream APIs themselves.

Everything lives in a single script: [`fnstatus.py`](fnstatus.py).

---

## Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Example Output](#-example-output)
- [How It Works](#-how-it-works)
- [Data Sources](#-data-sources)
- [What It Monitors](#-what-it-monitors)
- [Status Indicators](#-status-indicators)
- [Free Games Tracking](#-free-games-tracking)
- [Incident Monitoring](#-incident-monitoring)
- [Project Structure](#-project-structure)
- [Requirements](#-requirements)
- [Automation Recipes](#-automation-recipes)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)
- [Disclaimer](#-disclaimer)

---

## ✨ Features

| Feature | What it does |
|---|---|
| 🔍 **Real-time system status** | Reads Epic's status page summary and reports an overall verdict plus per-service state |
| 🧩 **Detailed component list** | Enumerates every component Epic exposes, surfacing problem components first and collapsing healthy ones into a count |
| ⚡ **Easy Anti-Cheat tracking** | Dedicated EAC section that matches EAC components *and* scans incident text for anti-cheat mentions |
| 🔔 **EAC change detection** | Remembers the previous EAC state between polls and prints a highlighted banner when it changes |
| 🚨 **Incident reports** | Active incidents with impact level, start time and latest update, plus the 3 most recently resolved incidents |
| 🎁 **Free games tracker** | Current Epic Games Store freebies with countdowns, plus the next upcoming giveaways |
| 📊 **API health checks** | `HEAD` probes every upstream endpoint and reports an `n/5 operational` score |
| 🎨 **Colored output** | `colorama`-based coloring with background highlights for outages and critical incidents |
| 🔄 **Continuous monitoring** | Screen-clearing refresh loop with a configurable interval and clean `Ctrl+C` exit |

---

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ynwglobal/epic-games-status-monitor.git
   cd epic-games-status-monitor
   ```

2. **(Recommended) create a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the monitor:**
   ```bash
   python3 fnstatus.py
   ```

### One-line install & run

```bash
git clone https://github.com/ynwglobal/epic-games-status-monitor.git && cd epic-games-status-monitor && pip install -r requirements.txt && python3 fnstatus.py --once
```

---

## 📖 Usage

```bash
python3 fnstatus.py [interval | --once | --help]
```

### Arguments

| Argument | Type | Default | Description |
|---|---|---|---|
| *(none)* | — | — | Continuous monitoring with a 300 second (5 minute) interval |
| `interval` | integer seconds | `300` | Continuous monitoring at a custom cadence. Values below `10` are clamped to `10` to avoid rate limiting. A non-numeric value falls back to `300` with a warning. |
| `--once` | flag | — | Run one full check, print the report, and exit (ideal for cron, CI and scripts) |
| `--help`, `-h`, `help` | flag | — | Print built-in usage, feature list and examples |

### Examples

```bash
python3 fnstatus.py            # monitor every 5 minutes
python3 fnstatus.py 60         # monitor every minute
python3 fnstatus.py 5          # clamped up to 10 seconds
python3 fnstatus.py --once     # single snapshot, then exit
python3 fnstatus.py --help     # usage information
```

**Exit codes:** `0` on normal exit or `Ctrl+C`, `1` on an unexpected runtime error.

---

## 🖥 Example Output

```
╔══════════════════════════════════════════════════════════════════╗
║                    EPIC GAMES MONITOR v3.1                        ║
║     Status • Incidents • EAC • Free Games • More! (FIXED)         ║
╚══════════════════════════════════════════════════════════════════╝

 SYSTEM STATUS
──────────────────────────────────────────────────────────────────────
Overall Status: ALL SYSTEMS OPERATIONAL

Fortnite                 : OPERATIONAL
Epic Games Store         : OPERATIONAL
Login/Authentication     : OPERATIONAL
Easy Anti-Cheat          : OPERATIONAL

 FREE GAMES & PROMOTIONS
──────────────────────────────────────────────────────────────────────
Currently FREE:
  Sid Meier's Civilization VI Platinum Edition
     Sid Meier's Civilization VI: Platinum Edition is the perfect...
     Ends in 5 days (2025-07-24 15:00 UTC)

 API STATUS & INFO
──────────────────────────────────────────────────────────────────────
  ✓ Summary API
  ✓ Status API
  ✓ Incidents API
  ✓ Components API
  ✓ Free Games API

5/5 API endpoints operational
```

---

## 🔬 How It Works

The script is built around a single `EpicGamesMonitor` class. Each full check runs these sections in order:

1. `print_banner()` — renders the header.
2. `display_system_status()` — fetches the summary endpoint, derives an overall verdict from `page.indicator`, then maps a curated list of friendly service names onto Epic's raw components using keyword matching (`get_component_by_keywords`).
3. `display_components_detailed()` — fetches the full components list, splits it into *issues* and *operational*, prints problems first and summarizes the healthy ones.
4. `display_easy_anticheat_status()` — locates the EAC component via keywords (`anti`, `cheat`, `eac`, `anticheat`), compares against the previous poll to detect changes, and also greps incident titles and update bodies for anti-cheat mentions.
5. `display_incident_reports()` — separates active from resolved incidents, prints up to 5 active ones with impact-based coloring plus the newest update excerpt (truncated to 100 chars), then lists the 3 most recently resolved incidents with normalized UTC timestamps.
6. `display_free_games()` — walks the store promotions payload, treats any offer with `discountPercentage == 0` as free, splits current vs upcoming, and computes day/hour countdowns against timezone-aware `datetime.now(timezone.utc)`.
7. `display_api_status()` — sends `HEAD` requests to all five endpoints and reports which respond with `200`.

In monitoring mode `run_monitoring()` wraps this in a loop that clears the terminal, reprints the report, shows a footer with the last-updated timestamp and the countdown to the next poll, then sleeps.

### Networking and error handling

All HTTP traffic goes through `make_request()`, which:

- sends a descriptive `User-Agent` plus `Accept: application/json` headers,
- uses a 15 second default timeout,
- raises for HTTP errors, and
- catches timeouts, connection errors, HTTP errors, JSON decode errors and unexpected exceptions individually — printing a red diagnostic line and returning `None` instead of crashing.

A failed section degrades gracefully: it prints an "unable to fetch" line while the remaining sections still run.

---

## 🌐 Data Sources

| Purpose | Endpoint |
|---|---|
| System summary | `https://status.epicgames.com/api/v2/summary.json` |
| Current status | `https://status.epicgames.com/api/v2/status.json` |
| Incidents | `https://status.epicgames.com/api/v2/incidents.json` |
| Components | `https://status.epicgames.com/api/v2/components.json` |
| Free games | `https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions` |

All endpoints are public and unauthenticated — **no API keys, accounts or tokens are required.**

> **Removed in v3.1:** the `incidents/history.json`, `services.json`, `scheduled_maintenances.json`, `news.json` and `incident_types.json` endpoints were dropped because Epic now returns `404` for them. The detailed components view replaces the old services view.

---

## 🎯 What It Monitors

| Service | Description |
|---|---|
| **Fortnite** | Battle Royale game status |
| **Epic Games Store** | Store and launcher functionality |
| **Login/Authentication** | Account and auth services |
| **Easy Anti-Cheat (EAC)** | Anti-cheat system status |
| **Matchmaking** | Matchmaking, game services, lobbies |
| **Friends & Social** | Social features |
| **Cloud Save** | Save synchronization |
| **Downloads** | Game downloads and launcher updates |
| **Payment Processing** | Purchases and payments |
| **Support System** | Help and support services |
| **Rocket League** | Rocket League services |
| **Fall Guys** | Fall Guys services |

If Epic renames or removes a component, that row is reported as `NOT FOUND` rather than failing the run. To track something extra, add a `("Label", ["keyword", ...])` tuple to the `services` list in `display_system_status()`.

---

## 🎨 Status Indicators

| Raw API status | Displayed as | Meaning |
|---|---|---|
| `operational` | `OPERATIONAL` (green) | Everything working normally |
| `degraded_performance` | `DEGRADED PERFORMANCE` (yellow) | Slower than usual |
| `partial_outage` | `*** WARNING: PARTIAL OUTAGE ***` (red) | Some features down |
| `major_outage` | `*** CRITICAL: MAJOR OUTAGE ***` (red) | Service down for most users |
| `under_maintenance` | `MAINTENANCE` (cyan) | Scheduled maintenance in progress |
| anything else | `UNKNOWN STATUS` (magenta) | Status could not be determined |

Any status containing `outage` is additionally rendered with a red background block so it is impossible to miss.

---

## 🎁 Free Games Tracking

- **Current freebies** — title, truncated description and end date in UTC.
- **Countdown timers** — days remaining, switching to an hours countdown (in red) on the final day.
- **Upcoming games** — the next 3 scheduled giveaways with days-until-start.
- **Detection rule** — an offer counts as free when its `discountSetting.discountPercentage` is `0` and the promotion window has not already ended.

---

## 🚨 Incident Monitoring

- **Active incidents** — anything without a `resolved_at` and not marked `resolved` (max 5 shown).
- **Impact levels** — `CRITICAL` and `MAJOR` incidents get highlighted banner headers; minor incidents print in blue.
- **Latest updates** — the newest update body, truncated to 100 characters with an ellipsis.
- **Recently resolved** — the 3 newest resolved incidents with ISO timestamps normalized to `YYYY-MM-DD HH:MM UTC`.
- **EAC correlation** — incidents mentioning anti-cheat are re-surfaced in the dedicated EAC section.

---

## 📁 Project Structure

```text
epic-games-status-monitor/
├── fnstatus.py        # the entire monitor (EpicGamesMonitor class + CLI entry point)
├── requirements.txt   # requests + colorama
├── LICENSE            # MIT
└── README.md          # this file
```

---

## 🛠 Requirements

- **Python 3.7+** (uses f-strings, `typing` and `datetime.fromisoformat`)
- **[requests](https://pypi.org/project/requests/)** `>=2.31.0` — HTTP client
- **[colorama](https://pypi.org/project/colorama/)** `>=0.4.6` — cross-platform terminal colors

```bash
pip install -r requirements.txt
```

Works on Windows, macOS and Linux. Colors require a terminal with ANSI support; `colorama` is initialized with `autoreset=True` so Windows terminals are handled automatically.

---

## 🤖 Automation Recipes

**Cron — snapshot every 15 minutes into a log:**
```bash
*/15 * * * * cd /path/to/epic-games-status-monitor && /usr/bin/python3 fnstatus.py --once >> status.log 2>&1
```

**systemd — run continuously as a service:**
```ini
[Unit]
Description=Epic Games Status Monitor
After=network-online.target

[Service]
WorkingDirectory=/opt/epic-games-status-monitor
ExecStart=/usr/bin/python3 fnstatus.py 300
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

**Plain-text output (strip ANSI colors):**
```bash
python3 fnstatus.py --once | sed -r 's/\x1B\[[0-9;]*[mK]//g' > report.txt
```

---

## 🆘 Troubleshooting

### Connection errors
```bash
ping status.epicgames.com
curl -I https://status.epicgames.com/api/v2/summary.json
```
Corporate proxies and VPNs are the usual culprits; `requests` honors the `HTTP_PROXY` / `HTTPS_PROXY` environment variables.

### Wrong Python version
```bash
python3 --version   # must be 3.7 or newer
```

### Missing or broken dependencies
```bash
pip install -r requirements.txt --force-reinstall
```

### Garbled characters or no colors
Your terminal lacks UTF-8 or ANSI support. On Windows use Windows Terminal or PowerShell 7+, and set the code page to UTF-8 (`chcp 65001`).

### An API shows ✗ in the API status section
Epic occasionally changes or retires endpoints. The other sections keep working; open an issue if a failure persists.

### Getting help

1. Check the [Issues](https://github.com/ynwglobal/epic-games-status-monitor/issues) page
2. Re-run with `--once` to isolate the failing section
3. Verify Python, pip and network connectivity to Epic's APIs

---

## 🤝 Contributing

Contributions are welcome:

- 🐛 Report bugs
- 💡 Suggest features
- 🔧 Submit pull requests
- 📖 Improve documentation

Keep the script dependency-light and preserve the graceful-degradation behavior — a failing endpoint should never crash the run.

---

## 📝 License

Licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## ⚠️ Disclaimer

This tool uses Epic Games' public status APIs and is **not affiliated with, endorsed by, or sponsored by Epic Games, Inc.** Fortnite, Epic Games Store and Easy Anti-Cheat are trademarks of their respective owners. Use responsibly and respect API rate limits — the minimum poll interval is clamped to 10 seconds for this reason.

---

## 🙏 Acknowledgments

- Epic Games for providing public status APIs
- The Python community for `requests` and `colorama`
- Everyone who reports issues and improves this tool

---

**Made with ❤️ for the Epic Games community**

⭐ **Star this repo if it helps you track Epic Games status!** ⭐

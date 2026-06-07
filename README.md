# xui-bot

Admin / client Telegram bot for a **3x-ui** panel, built on **aiogram 3**.

* **Admins** manage the panel from Telegram: list/search clients, create clients
  with a guided wizard, extend validity, set quota/IP limit/TG ID, reset traffic,
  enable/disable, view config links and QR codes, check connecting IPs, delete
  clients, watch server status and online users, view traffic-sorted leaderboard,
  see a "depleting soon" dashboard, trigger a DB backup, purge depleted accounts,
  and restart the Xray service.
* **Clients** (end users) link their Telegram to a panel account by email or by
  Telegram ID match, then view their own usage/expiry and pull their subscription +
  config links with QR codes.
* **Dual-role admins** — if an admin also has a VPN account on the panel they can
  switch between admin and client mode with a single button.

The panel stays the single source of truth for VPN accounts. The local
database only records who-is-who (Telegram ↔ role ↔ panel email).

## Architecture

```
bot/
├── __main__.py          # entrypoint: config → DB → API client → dispatcher → polling
├── config.py            # pydantic-settings (env / .env)
├── api/                 # aiohttp client for the 3x-ui API
│   ├── client.py        #   XUIClient: Bearer-first auth, cookie fallback, envelope unwrap
│   ├── models.py        #   pydantic models (Inbound, Client, ClientCreate, ServerStatus…)
│   └── exceptions.py
├── db/                  # tortoise-orm (User: tg_id, role, panel_email)
│   └── fsm.py           #   tortoise-backed FSM storage for aiogram
├── handlers/
│   ├── common.py        #   /start /help /cancel, home menu, mode switching
│   ├── admin/
│   │   ├── menu.py      #   server status, online, inbounds, backup, cleanup,
│   │   │                #   depleting-soon, sorted traffic report, restart Xray
│   │   └── clients.py   #   list/view/create/extend/delete/reset/links/QR/IPs/toggle/
│   │                    #   IP limit/TG ID  (/find <email> command)
│   └── client/
│       └── account.py   #   link, my account, my configs + QR codes, unlink
├── keyboards/           # inline keyboards + typed CallbackData factories
├── middlewares/
│   ├── auth.py          #   role resolution + admin promotion from ADMIN_IDS
│   └── filters.py       #   IsAdmin / IsClient aiogram filters
├── states/              # FSM groups (CreateClient, FindClient, ExtendClient,
│                        #   SetQuota, SetIpLimit, SetTgId, SetExpiry)
├── tasks/
│   └── report.py        #   periodic report: server stats + depleting-soon list
└── utils/
    └── formatting.py    #   byte / date / progress bar formatting helpers
```

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in the required variables
python -m bot
```

The bot uses long-polling — no webhook setup needed.

### Docker Compose

```bash
cp .env.example .env   # fill in the required variables
docker compose up -d
```

The `docker-compose.yaml` mounts the project directory into `/app` inside a
`python:3.13` container, installs dependencies at startup, and restarts unless
stopped.

## Configuration (`.env`)

| Variable | Required | Default | Meaning |
|---|---|---|---|
| `BOT_TOKEN` | ✅ | — | Telegram bot token from @BotFather |
| `ADMIN_IDS` | ✅ | — | Comma-separated Telegram user IDs always treated as admin |
| `XUI_BASE_URL` | ✅ | — | Panel base URL, no trailing slash |
| `XUI_BASE_PATH` | | `/` | Web base path the panel is served under (`webBasePath`) |
| `XUI_API_TOKEN` | ⭐ | — | **Preferred** auth — Bearer token from *Settings → Security → API Token* |
| `XUI_USERNAME` | | — | Cookie-login fallback username (used only if no token set) |
| `XUI_PASSWORD` | | — | Cookie-login fallback password |
| `XUI_VERIFY_SSL` | | `true` | Set `false` for self-signed certs |
| `XUI_TIMEOUT` | | `30` | HTTP request timeout in seconds |
| `SUB_BASE_URL` | | — | Public subscription base shown to clients |
| `DEFAULT_INBOUND_IDS` | | — | Comma-separated inbound IDs pre-selected in quick-create flow |
| `DEFAULT_QUOTA_GB` | | `50` | Default traffic quota (GB) offered in the create wizard |
| `DEFAULT_DAYS` | | `30` | Default validity (days) offered in the create wizard |
| `REPORT_INTERVAL_HOURS` | | `12` | Send periodic server report to all admins every N hours (`0` = disabled) |
| `DB_URL` | | `sqlite://bot.sqlite3` | `sqlite://bot.sqlite3` or `postgres://user:pass@host:5432/db` (needs `asyncpg`) |

### Authentication

A Bearer **API token** is recommended: it skips CSRF and sends
`Authorization: Bearer <token>` on every `/panel/api/*` request. Set it in
your panel under *Settings → Security → API Token*, then put it in
`XUI_API_TOKEN`.

If you use `XUI_USERNAME` / `XUI_PASSWORD` instead, the client logs in for a
session cookie and re-authenticates once automatically when the session expires.

## Features

### Admin

| Feature | How to reach it |
|---|---|
| Server status (CPU/RAM/disk/traffic/uptime) | Main menu → Server Status |
| Online clients | Main menu → Online |
| Inbounds overview | Main menu → Inbounds |
| Clients — paginated list with inbound filter | Main menu → Clients |
| Jump to a specific client | `/find <email>` |
| Create client (guided wizard) | Clients list → ➕ Add |
| Edit client — extend, set quota, IP limit, TG ID | Client card buttons |
| Reset individual / all traffic | Client card → Reset Traffic |
| Enable / disable client | Client card → toggle |
| Config links + QR codes | Client card → Links / QR |
| Connecting IPs + clear IPs | Client card → IPs |
| Delete client | Client card → Delete |
| Traffic leaderboard (sorted by usage) | Main menu → Traffic Report |
| Depleting-soon dashboard | Main menu → Depleting Soon |
| Purge depleted / expired accounts | Main menu → Delete Depleted |
| DB backup to Telegram | Main menu → Backup |
| Restart Xray service | Main menu → Restart Xray |
| Periodic scheduled report | Automatic, every `REPORT_INTERVAL_HOURS` |

### Client (end-user)

| Feature | How to reach it |
|---|---|
| Link account by email | Main menu → Link my account |
| Auto-link by Telegram ID match | Happens automatically on `/start` |
| View usage, quota, expiry, last-seen | Main menu → My Account |
| Subscription + config links | My Account → My Configs |
| QR codes for each config | My Configs → QR |
| Unlink account | My Account → Unlink |

## QR code support

QR code generation requires the optional `qrcode[pil]` dependency (already
listed in `requirements.txt`). If it is not installed the bot runs normally —
QR buttons simply will not appear.

## API surface used

Wrapped from the panel's `/panel/api/*` endpoints (all replies follow the
`{success, msg, obj}` envelope):

* **Inbounds** — `list`, `options`, `get/:id`, `setEnable/:id`
* **Clients** — `list`, `get/:email`, `add`, `update/:email`, `del/:email`,
  `resetTraffic/:email`, `resetAllTraffics`, `bulkAdjust`, `links/:email`,
  `subLinks/:subId`, `ips/:email`, `clearIps/:email`, `onlines`, `delDepleted`
* **Server** — `status`, `getNewUUID`, `restartXrayService`, `backuptotgbot`

> The client payload shape (`totalGB` in **bytes**, `expiryTime` as **unix ms**,
> and the `{client, inboundIds}` wrapper on `/clients/add`) follows the standard
> 3x-ui convention. Verify against your live `/panel/api/openapi.json` if a field
> differs on your build (tested against v3.2.8).

## Extending

1. Add a method to `XUIClient` in [bot/api/client.py](bot/api/client.py).
2. Add a handler in the relevant router under [bot/handlers/](bot/handlers/).
3. If it needs a button, add an entry in [bot/keyboards/](bot/keyboards/).
4. Multi-step flows get a `StatesGroup` in [bot/states/](bot/states/).

Role gating is handled by the `IsAdmin` / `IsClient` filters already applied at
the router level — no per-handler boilerplate needed.

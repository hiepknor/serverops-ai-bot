# 🖥 ServerOps AI Bot

AI-powered Telegram bot for managing Linux servers, Docker containers, deployments, logs, monitoring, and troubleshooting using OpenAI LLMs.

Built for personal servers, VPS, homelabs, and lightweight DevOps automation.

---

# ✨ Features

## 🤖 AI Server Assistant

Ask naturally:

```txt
"Why is my server slow?"
"Analyze nginx logs"
"Why is the website returning 502?"
"Restart DealerScan"
"Summarize the last 200 log lines"
```

Powered by:

* OpenAI Responses API
* GPT-4.1 Mini
* Tool Calling
* Structured Outputs

---

## 🛠 Server Management

### System

```txt
/status
/health
/cpu
/ram
/disk
/uptime
```

### Services

```txt
/services
/restart <service>
/stop <service>
/start <service>
```

### Docker

```txt
/docker
/docker_logs <container>
/docker-restart <container>
```

### Logs

```txt
/log <service>
/errors
/nginx_errors
```

### Deployment

```txt
/deploy <project>
/pull
/rebuild
```

---

# 🔐 Security First

ServerOps AI Bot is designed with a safe execution architecture.

The LLM:

✅ Can analyze logs
✅ Can summarize issues
✅ Can call approved tools

The LLM:

❌ Cannot execute arbitrary shell commands
❌ Cannot access secrets
❌ Cannot bypass RBAC
❌ Cannot run unrestricted sudo

---

# 🧠 AI Architecture

```txt
Telegram
   ↓
ServerOps AI Bot
   ↓
RBAC + Auth
   ↓
OpenAI Responses API
   ↓
Tool Router
   ↓
Whitelist Executor
   ↓
Linux / Docker / Logs
```

---

# 🏗 Tech Stack

## Core

* Python 3.11+
* python-telegram-bot
* OpenAI Responses API
* Pydantic
* APScheduler
* structlog

## Monitoring

* psutil
* Docker SDK

## Database

* SQLite

## Deployment

* Docker
* Docker Compose
* systemd

---

# 📦 Project Structure

```txt
serverops-ai-bot/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── bot.py
│   │
│   ├── ai/
│   │   ├── agent.py
│   │   ├── prompts.py
│   │   ├── router.py
│   │   └── schemas.py
│   │
│   ├── commands/
│   │   ├── status.py
│   │   ├── logs.py
│   │   ├── docker.py
│   │   ├── deploy.py
│   │   └── admin.py
│   │
│   ├── tools/
│   │   ├── system_tools.py
│   │   ├── docker_tools.py
│   │   ├── service_tools.py
│   │   ├── git_tools.py
│   │   └── log_tools.py
│   │
│   ├── core/
│   │   ├── executor.py
│   │   ├── alerts.py
│   │   ├── audit.py
│   │   └── security.py
│   │
│   └── db/
│       ├── database.py
│       └── models.py
│
├── data/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── README.md
└── serverops-ai-bot.service
```

---

# 📚 Project Docs

Start here for implementation context:

* `AGENTS.md` — agent rules, safety boundaries, and workflow.
* `docs/README.md` — compact context map for humans and AI agents.
* `docs/specs/mvp.md` — MVP scope and acceptance criteria.
* `docs/architecture.md` — module boundaries and safe executor design.
* `docs/roadmap.md` — phased build order.
* `docs/development.md` — local development setup and verification commands.

---

# 🚀 Quick Start

## 1. Clone Project

```bash
git clone https://github.com/yourname/serverops-ai-bot.git

cd serverops-ai-bot
```

---

## 2. Create Telegram Bot

Open:

https://t.me/BotFather

Create bot:

```txt
/serveropsaibot
```

Get bot token.

---

## 3. Create OpenAI API Key

Open:

https://platform.openai.com/api-keys

Create API key.

---

## 4. Configure Environment

Create `.env`

```env
TELEGRAM_BOT_TOKEN=xxxxxxxx

OPENAI_API_KEY=xxxxxxxx

OPENAI_MODEL=gpt-4.1-mini

OWNER_IDS=123456789

ADMIN_IDS=
VIEWER_IDS=

DATABASE_URL=sqlite:///data/serverops.db

LOG_LEVEL=INFO
```

---

# 🐳 Docker Deployment

## Build & Run

```bash
docker compose up -d --build
```

---

## docker-compose.yml

```yaml
services:
  serverops-ai-bot:
    build: .
    container_name: serverops-ai-bot

    restart: unless-stopped

    env_file:
      - .env

    volumes:
      - ./data:/app/data
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /var/log:/host/var/log:ro
```

---

# 🔧 systemd Service

```ini
[Unit]
Description=ServerOps AI Bot
After=docker.service

[Service]
WorkingDirectory=/opt/serverops-ai-bot
ExecStart=/usr/bin/docker compose up
ExecStop=/usr/bin/docker compose down
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl enable serverops-ai-bot
sudo systemctl start serverops-ai-bot
```

---

# 🔑 RBAC Roles

## Owner

Full access:

```txt
restart
deploy
reboot
docker
backup
audit
```

## Admin

Limited management:

```txt
restart services
view logs
view status
```

## Viewer

Read-only:

```txt
status
logs
health
```

---

# ⚠ Dangerous Actions Require Confirmation

Example:

```txt
/deploy dealerscan
```

Bot:

```txt
⚠ Confirm deployment?

Project: dealerscan

Actions:
- git pull
- rebuild
- restart container

Reply:
CONFIRM DEPLOY DEALERSCAN
```

---

# 📊 Automatic Monitoring

ServerOps AI Bot automatically monitors:

* CPU usage
* RAM usage
* Disk usage
* Docker container health
* Service crashes
* nginx 502/504 spikes
* Python tracebacks

Example alert:

```txt
🚨 Server Alert

Service: dealerscan
Status: failed

Possible cause:
Database connection timeout

Suggested actions:
- /log dealerscan
- /restart dealerscan
```

---

# 🧾 Audit Logging

Every sensitive action is logged:

```txt
User
Action
Time
Result
Target
Confirmation status
```

---

# 🧠 OpenAI Tool Calling

Example tool schema:

```python
class RestartServiceInput(BaseModel):
    service_name: Literal[
        "nginx",
        "postgres",
        "docker",
        "dealerscan"
    ]
```

LLM can only call approved tools.

---

# 🔒 Security Recommendations

## DO

✅ Use Docker
✅ Use allowlisted tools
✅ Use confirmation flow
✅ Restrict Telegram IDs
✅ Use read-only mounts when possible

## DON'T

❌ Allow arbitrary shell execution
❌ Mount entire host filesystem
❌ Use privileged containers
❌ Expose secrets to LLM prompts

---

# 📈 Future Roadmap

## V1

* Telegram management
* AI troubleshooting
* Docker integration
* Log summarization
* Monitoring alerts
* RBAC

## V2

* Multi-server support
* Web dashboard
* Metrics history
* Backup automation
* AI incident reports

## V3

* Kubernetes support
* MCP integration
* Distributed agents
* Self-healing workflows
* AI-powered root cause analysis

---

# 🖥 Example Commands

```txt
/status
/docker
/log nginx
/restart dealerscan
/deploy api
```

AI Examples:

```txt
"Why is nginx failing?"
"Analyze docker memory usage"
"Summarize the latest errors"
"Check server health"
```

---

# 📜 License

MIT License

---

# ❤️ Built For

* Personal servers
* VPS management
* Homelabs
* Small production deployments
* AI-powered DevOps workflows

---

# 🤝 Contributing

PRs and ideas are welcome.

Build safe AI Ops tools responsibly.

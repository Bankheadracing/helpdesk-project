# OpsDesk — : IT Help Desk Ticket Automation

A local, runnable web dashboard built on the original Stage 1 ticket-triage engine. **No paid services, third-party Python packages, or API keys required.**

## Run it

Requires Python 3.9+.

```bash
cd helpdesk_stage2
python3 web_server.py
```

Open **http://127.0.0.1:8000** in a browser. Press `Ctrl+C` to stop the server.

### Unit tests

```bash
python3 -m unittest discover -s tests -v
```

### Original Stage 1 batch processor

```bash
python3 helpdesk.py
```

## What you can demonstrate

1. Submit an **Okta login issue**: routed to Identity Team, P3.
2. Submit a **VPN outage** with impact **Entire department**: routed to Network Operations, P2.
3. Submit **Company-wide production down** with impact **Organization-wide**: P1 and mandatory human/on-call escalation.
4. Submit a **laptop VPN** issue: ambiguous categories, so it routes to human triage.
5. Filter the ticket queue by auto-routed or human-review status. Refresh or restart the app to show tickets persist.

## Architecture

```
Browser (HTML/CSS/JS)
    | GET /api/tickets, GET /api/summary, POST /api/tickets
Local Python HTTP server (web_server.py)
    | validates input, creates unique ticket IDs
Stage 1 rules engine (helpdesk.triage)
    | category, priority, assigned team, explanation
SQLite (data/tickets.db)
```

All submitted tickets are saved in `data/tickets.db`. The original `helpdesk.py` batch process and its sample data are retained.

## Business controls

- Priority 1 and ambiguous tickets require human review; the app never resets passwords or changes access.
- Keyword routing is explainable and testable. No claim of AI or machine learning is made.
- Input lengths and impact values are validated server-side; SQL queries are parameterized.
- The server binds to `127.0.0.1` only. **It has no login/authentication, RBAC, CSRF protection or production-ready audit controls.** Use test data only, never expose it to the public internet.
- SQLite provides local persistence but is not meant as the final enterprise storage layer.

## Next stage

Add identity authentication, proper approval workflow, ServiceNow/Jira integration, database access controls, metrics/observability and deployment using a production web framework.

# Enterprise IT Help Desk Ticket Automation

An **rule-based Python MVP** for automating incoming IT service desk ticket triage. It uses synthetic data, no external APIs, and no third-party dependencies.

## Business problem
IT service desks spend time manually reading, prioritizing, and assigning incoming requests. This MVP demonstrates automatic categorization and routing, while reserving ambiguous and critical cases for human review.

## Process
Ticket intake (JSON) → validate → rule-based classification → priority assignment → team routing or human review → JSON/CSV results and metrics.

## Run
From the project directory, with Python 3.9+:

```bash
python3 helpdesk.py --input data/sample_tickets.json --output output
python3 -m unittest discover -s tests -v
```

Review `output/triaged_tickets.csv`, `output/triaged_tickets.json` and `output/summary.json`.

## Demonstration
1. Show a manually submitted ticket such as `INC-1001` (Okta MFA issue).
2. Run `python3 helpdesk.py` and show its automatic assignment to the Identity Team.
3. Show the critical production-outage ticket, which must be escalated for human review.
4. Show an ambiguous ticket that matches multiple categories; the system does not guess.
5. Open `summary.json` to discuss routing rate and exception volumes.
6. Run the automated unit tests to show repeatability.

## Metrics
- Total tickets and auto-routed tickets
- Human review count
- Category and priority distributions
- To estimate manual time saved, multiply auto-routed tickets by an explicitly measured baseline handling time. No ROI or accuracy is claimed without measurements.

## Controls and future enhancements
- No automated password resets or access grants
- Human approval for P1 and ambiguous cases
- Processed timestamp and explanatory reason on each record
- Add structured logging with immutable audit IDs, role-based access and retries for production
- Add ServiceNow/Jira REST integration, Outlook intake, duplicate detection, SLA policies, dashboards, and monitoring
- Add data protection, access controls and review for personal information before processing real tickets



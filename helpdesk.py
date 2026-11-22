"""Rule-based enterprise IT help desk ticket triage (standard library only)."""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RULES = {
    'Identity & Access': ('Identity Team', ('login', 'log in', 'sign in', 'password', 'mfa', 'locked out', 'account access', 'okta')),
    'Network': ('Network Operations', ('vpn', 'wifi', 'wi-fi', 'internet', 'network', 'dns')),
    'Hardware': ('Desktop Support', ('laptop', 'monitor', 'keyboard', 'printer', 'hardware', 'mouse')),
    'Software': ('Application Support', ('software', 'application', 'outlook', 'excel', 'crash', 'install')),
}
# Clear, auditable keywords only. Unknown or ambiguous cases go to humans.
URGENT_PHRASES = ('company-wide', 'company wide', 'entire company', 'all employees', 'production down', 'business critical')
HIGH_PHRASES = ('department down', 'multiple users', 'cannot work', 'unable to work', 'system down')

def matches(text: str, phrase: str) -> bool:
    return re.search(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)', text) is not None

def triage(ticket: dict) -> dict:
    ticket_id = str(ticket.get('ticket_id', '')).strip()
    description = ticket.get('description', '')
    if not ticket_id or not isinstance(description, str) or not description.strip():
        raise ValueError('Each ticket requires ticket_id and a nonempty description')
    text = f"{ticket.get('subject', '')} {description}".lower()
    categories = [category for category, (_, keywords) in RULES.items()
                  if any(matches(text, word) for word in keywords)]
    manual_review = len(categories) != 1
    category = categories[0] if len(categories) == 1 else 'Needs Review'
    team = RULES[category][0] if not manual_review else 'Service Desk Triage'

    impact = str(ticket.get('impact', 'single_user')).lower()
    # Never auto-route unknown critical-impact requests without review.
    if any(matches(text, phrase) for phrase in URGENT_PHRASES) or impact == 'organization':
        priority = 'P1 - Critical'
    elif any(matches(text, phrase) for phrase in HIGH_PHRASES) or impact == 'department':
        priority = 'P2 - High'
    else:
        priority = 'P3 - Normal'
    # P1 cases still require an on-call human to confirm/escalate.
    if priority == 'P1 - Critical':
        manual_review = True
        team = 'Service Desk Triage / On-call'
    return {
        'ticket_id': ticket_id,
        'subject': str(ticket.get('subject', '')),
        'description': description,
        'category': category,
        'priority': priority,
        'assigned_team': team,
        'status': 'Human review required' if manual_review else 'Auto-routed',
        'reason': ('Multiple categories or no category matched' if category == 'Needs Review'
                   else 'P1 requires on-call validation' if priority == 'P1 - Critical'
                   else 'Single category matched rule'),
        'processed_at_utc': datetime.now(timezone.utc).isoformat(),
    }

def process(input_path: Path, output_dir: Path) -> dict:
    tickets = json.loads(input_path.read_text(encoding='utf-8'))
    if not isinstance(tickets, list):
        raise ValueError('Input must be a JSON array of tickets')
    output_dir.mkdir(parents=True, exist_ok=True)
    processed = []
    for item in tickets:
        try:
            processed.append(triage(item))
        except (ValueError, AttributeError, TypeError) as exc:
            processed.append({
                'ticket_id': str(item.get('ticket_id', 'UNKNOWN')) if isinstance(item, dict) else 'UNKNOWN',
                'subject': str(item.get('subject', '')) if isinstance(item, dict) else '',
                'description': str(item.get('description', '')) if isinstance(item, dict) else '',
                'category': 'Needs Review', 'priority': 'Unassigned',
                'assigned_team': 'Service Desk Triage', 'status': 'Human review required',
                'reason': f'Invalid ticket: {exc}',
                'processed_at_utc': datetime.now(timezone.utc).isoformat(),
            })
    (output_dir / 'triaged_tickets.json').write_text(json.dumps(processed, indent=2), encoding='utf-8')
    columns = ['ticket_id', 'subject', 'category', 'priority', 'assigned_team', 'status', 'reason', 'processed_at_utc']
    with (output_dir / 'triaged_tickets.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(processed)
    summary = {
        'total_tickets': len(processed),
        'auto_routed': sum(x['status'] == 'Auto-routed' for x in processed),
        'human_review': sum(x['status'] == 'Human review required' for x in processed),
        'by_category': dict(Counter(x['category'] for x in processed)),
        'by_priority': dict(Counter(x['priority'] for x in processed)),
    }
    (output_dir / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return summary

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Rule-based IT help desk ticket triage')
    parser.add_argument('--input', default='data/sample_tickets.json')
    parser.add_argument('--output', default='output')
    args = parser.parse_args()
    print(json.dumps(process(Path(args.input), Path(args.output)), indent=2))

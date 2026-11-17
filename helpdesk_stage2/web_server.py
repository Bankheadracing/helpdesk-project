"""Local Stage 2 dashboard API; stdlib only. Not internet-exposed production service."""
from __future__ import annotations
import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from helpdesk import triage

BASE = Path(__file__).resolve().parent
STATIC = BASE / 'static'
DB_PATH = Path(os.environ.get('HELPDESK_DB', str(BASE / 'data' / 'tickets.db')))
DB_LOCK = threading.Lock()
MAX_BODY = 16_384

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY, subject TEXT NOT NULL, description TEXT NOT NULL,
            impact TEXT NOT NULL, requester TEXT NOT NULL,
            category TEXT NOT NULL, priority TEXT NOT NULL,
            assigned_team TEXT NOT NULL, status TEXT NOT NULL,
            reason TEXT NOT NULL, processed_at_utc TEXT NOT NULL
        )''')

def all_tickets():
    with connect() as db:
        return [dict(row) for row in db.execute('SELECT * FROM tickets ORDER BY processed_at_utc DESC, ticket_id DESC')]

def create_ticket(payload):
    if not isinstance(payload, dict):
        raise ValueError('Request must be a JSON object')
    subject = payload.get('subject')
    description = payload.get('description')
    requester = payload.get('requester', '')
    impact = payload.get('impact', 'single_user')
    if not isinstance(subject, str) or not 3 <= len(subject.strip()) <= 120:
        raise ValueError('Subject must be 3–120 characters')
    if not isinstance(description, str) or not 10 <= len(description.strip()) <= 2000:
        raise ValueError('Description must be 10–2000 characters')
    if not isinstance(requester, str) or len(requester) > 100:
        raise ValueError('Requester must be 100 characters or fewer')
    if impact not in ('single_user', 'department', 'organization'):
        raise ValueError('Invalid impact')
    record = {'ticket_id': 'INC-' + uuid.uuid4().hex[:8].upper(),
              'subject': subject.strip(), 'description': description.strip(),
              'requester': requester.strip(), 'impact': impact}
    result = {**record, **triage(record)}
    with DB_LOCK, connect() as db:
        db.execute('''INSERT INTO tickets
            (ticket_id,subject,description,impact,requester,category,priority,assigned_team,status,reason,processed_at_utc)
            VALUES (:ticket_id,:subject,:description,:impact,:requester,:category,:priority,:assigned_team,:status,:reason,:processed_at_utc)''', result)
    return result

def summary(records):
    return {'total': len(records),
            'auto_routed': sum(t['status'] == 'Auto-routed' for t in records),
            'human_review': sum(t['status'] != 'Auto-routed' for t in records),
            'critical': sum(t['priority'].startswith('P1') for t in records)}

class Handler(BaseHTTPRequestHandler):
    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/tickets':
            return self.send_json({'tickets': all_tickets()})
        if path == '/api/summary':
            return self.send_json(summary(all_tickets()))
        assets = {'/': ('index.html', 'text/html; charset=utf-8'),
                  '/static/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                  '/static/styles.css': ('styles.css', 'text/css; charset=utf-8')}
        if path not in assets:
            return self.send_json({'error': 'Not found'}, 404)
        name, mime = assets[path]
        content = (STATIC / name).read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        if urlparse(self.path).path != '/api/tickets':
            return self.send_json({'error': 'Not found'}, 404)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length < 1 or length > MAX_BODY:
                return self.send_json({'error': 'Invalid request size'}, 413)
            if 'application/json' not in self.headers.get('Content-Type', ''):
                return self.send_json({'error': 'Content-Type must be application/json'}, 415)
            payload = json.loads(self.rfile.read(length))
            result = create_ticket(payload)
            return self.send_json(result, 201)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            return self.send_json({'error': str(exc)}, 400)

if __name__ == '__main__':
    init_db()
    host = '127.0.0.1'
    port = int(os.environ.get('PORT', '8000'))
    print(f'Helpdesk dashboard: http://{host}:{port}', flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()

import os
import tempfile
import unittest
from pathlib import Path
import web_server

class WebTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        web_server.DB_PATH = Path(self.tmp.name) / 'tickets.db'
        web_server.init_db()

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_and_persist(self):
        ticket = web_server.create_ticket({'subject':'Okta login failure', 'description':'I cannot log in to my Okta account', 'impact':'single_user', 'requester':'Demo'})
        self.assertEqual(ticket['category'], 'Identity & Access')
        self.assertEqual(web_server.summary(web_server.all_tickets())['total'], 1)

    def test_critical_requires_review(self):
        ticket = web_server.create_ticket({'subject':'Network unavailable', 'description':'Production down across entire company', 'impact':'organization'})
        self.assertEqual(ticket['priority'], 'P1 - Critical')
        self.assertEqual(ticket['status'], 'Human review required')

    def test_bad_impact_rejected(self):
        with self.assertRaises(ValueError):
            web_server.create_ticket({'subject':'VPN issue', 'description':'My vpn is disconnected today', 'impact':'admin'})

    def test_missing_description_rejected(self):
        with self.assertRaises(ValueError):
            web_server.create_ticket({'subject':'VPN issue', 'description':''})

if __name__ == '__main__':
    unittest.main()

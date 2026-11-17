import unittest
from helpdesk import triage

class TicketTests(unittest.TestCase):
    def test_identity(self):
        result = triage({'ticket_id': '1', 'description': 'Cannot log in with Okta MFA'})
        self.assertEqual(result['category'], 'Identity & Access')
        self.assertEqual(result['assigned_team'], 'Identity Team')
    def test_priority(self):
        result = triage({'ticket_id': '2', 'description': 'VPN outage', 'impact': 'department'})
        self.assertEqual(result['priority'], 'P2 - High')
    def test_ambiguous(self):
        result = triage({'ticket_id': '3', 'description': 'My laptop cannot login to the VPN'})
        self.assertEqual(result['status'], 'Human review required')
    def test_critical(self):
        result = triage({'ticket_id': '4', 'description': 'Production down; company-wide outage'})
        self.assertEqual(result['priority'], 'P1 - Critical')
        self.assertEqual(result['status'], 'Human review required')
    def test_invalid(self):
        with self.assertRaises(ValueError):
            triage({'ticket_id': '5', 'description': ' '})

if __name__ == '__main__':
    unittest.main()

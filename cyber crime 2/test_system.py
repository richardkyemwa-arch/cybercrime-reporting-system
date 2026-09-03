import unittest
from app import app, db, Report, User, Category

class TestOfficerPasswordMandate(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_officer_mandatory_password_reset(self):
        # 1. Login as officer with default password
        login_res = self.client.post('/login', data={
            'email': 'admin@cybercrime.gov',
            'password': 'AdminPassword123',
            'role': 'investigator'
        }, follow_redirects=False)
        
        # Officer login should redirect to /force-password-change
        self.assertEqual(login_res.status_code, 302)
        self.assertIn('/force-password-change', login_res.location)

        # 2. Accessing /dashboard before changing password should be blocked & redirected
        dash_res = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(dash_res.status_code, 302)
        self.assertIn('/force-password-change', dash_res.location)

        # 3. Perform password change
        change_res = self.client.post('/force-password-change', data={
            'current_password': 'AdminPassword123',
            'new_password': 'NewOfficerPassword2026!',
            'confirm_password': 'NewOfficerPassword2026!'
        }, follow_redirects=True)
        self.assertEqual(change_res.status_code, 200)
        self.assertIn(b'Law Enforcement Portal', change_res.data)

        # 4. Verify officer can now access dashboard directly
        with app.app_context():
            officer = User.query.filter_by(email='admin@cybercrime.gov').first()
            self.assertFalse(officer.must_change_password)
            # Revert back to default for demo consistency
            officer.set_password('AdminPassword123')
            officer.must_change_password = True
            db.session.commit()

if __name__ == '__main__':
    unittest.main()

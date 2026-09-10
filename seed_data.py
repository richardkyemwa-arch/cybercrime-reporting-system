import os
from app import app, db, User, Category, EmergencyContact, Report, ReportStatusLog

def seed():
    with app.app_context():
        # Ensure database tables exist
        db.create_all()
        
        # 1. Categories
        categories_data = [
            {
                "code": "phishing_scam",
                "name": "Phishing & Online Scams",
                "description": "Deceptive emails, fake shopping websites, lottery scams, or fraudulent messages attempting to steal sensitive information.",
                "icon": "fa-fish"
            },
            {
                "code": "financial_fraud",
                "name": "Banking & Financial Fraud",
                "description": "Unauthorized bank transfers, credit card fraud, investment scams, or crypto currency fraud.",
                "icon": "fa-credit-card"
            },
            {
                "code": "identity_theft",
                "name": "Identity Theft & Impersonation",
                "description": "Stolen identity, impersonation on social media, fraudulent loan applications using personal data.",
                "icon": "fa-user-ninja"
            },
            {
                "code": "ransomware_malware",
                "name": "Ransomware & Malware",
                "description": "Malicious code encrypting device files, spyware, keyloggers, or unauthorized remote access payloads.",
                "icon": "fa-bug"
            },
            {
                "code": "hacking_takeover",
                "name": "Hacking & Account Takeover",
                "description": "Unauthorized access to email, social media, cloud accounts, or corporate networks.",
                "icon": "fa-terminal"
            },
            {
                "code": "cyberbullying_harassment",
                "name": "Cyberbullying & Online Harassment",
                "description": "Targeted hate speech, online stalking, doxxing, or persistent abusive digital communications.",
                "icon": "fa-comments"
            },
            {
                "code": "sextortion_extortion",
                "name": "Cyber Extortion & Sextortion",
                "description": "Blackmail involving compromised personal media, sensitive files, or threats to leak private data.",
                "icon": "fa-user-shield"
            },
            {
                "code": "unauthorized_access",
                "name": "Data Breach & Illegal Access",
                "description": "Corporate or personal data leaks, unauthorized database access, or stolen credentials.",
                "icon": "fa-database"
            }
        ]

        for cat in categories_data:
            existing = Category.query.filter_by(code=cat['code']).first()
            if not existing:
                c = Category(code=cat['code'], name=cat['name'], description=cat['description'], icon=cat['icon'])
                db.session.add(c)

        # 2. Users (Admin Investigator & Demo Citizen)
        admin = User.query.filter_by(email='admin@cybercrime.gov').first()
        if not admin:
            admin = User(
                full_name="Admin Officer",
                email="admin@cybercrime.gov",
                phone="+1-800-CYBER-01",
                role="investigator",
                badge_number="CYBER-OFFICER-9021",
                department="National Cyber Crime Division",
                must_change_password=True # MANDATORY OFFICER PASSWORD RESET UPON LOGIN
            )
            admin.set_password("AdminPassword123")
            db.session.add(admin)

        citizen = User.query.filter_by(email='citizen@example.com').first()
        if not citizen:
            citizen = User(
                full_name="Demo User",
                email="citizen@example.com",
                phone="+1-555-0192",
                role="citizen",
                must_change_password=False
            )
            citizen.set_password("Citizen123")
            db.session.add(citizen)

        # 3. Emergency Contacts
        contacts = [
            {
                "name": "National Cyber Crime Emergency Hotline",
                "number": "1-800-CYBER-HELP (29237)",
                "description": "Direct 24/7 hotline for critical cyber incidents, active ransomware, and emergency financial freezes.",
                "category": "National Hotline",
                "is_247": True
            },
            {
                "name": "Financial Fraud & Bank Rapid Response",
                "number": "1-888-FRAUD-FREEZE",
                "description": "Immediate account hold and wire interception for active wire transfer scams.",
                "category": "Financial Emergency",
                "is_247": True
            },
            {
                "name": "Internet Crime Incident Response Team",
                "number": "+1-800-555-0111",
                "description": "Technical support for ongoing malware infections and server data breaches.",
                "category": "Technical Response",
                "is_247": False
            }
        ]

        for contact in contacts:
            if not EmergencyContact.query.filter_by(number=contact['number']).first():
                ec = EmergencyContact(
                    name=contact['name'],
                    number=contact['number'],
                    description=contact['description'],
                    category=contact['category'],
                    is_247=contact['is_247']
                )
                db.session.add(ec)

        db.session.commit()

        # 4. Sample Reports for Demonstration
        if Report.query.count() == 0:
            phish_cat = Category.query.filter_by(code='phishing_scam').first()
            fin_cat = Category.query.filter_by(code='financial_fraud').first()
            hack_cat = Category.query.filter_by(code='hacking_takeover').first()

            sample1 = Report(
                reference_no="CCR-2026-X9871A",
                user_id=citizen.id,
                reporter_name="Demo User",
                reporter_email="citizen@example.com",
                reporter_phone="+1-555-0192",
                category_id=phish_cat.id,
                title="Fake Banking SMS Phishing Attack",
                description="Received an urgent SMS claiming my online banking account was suspended. Clicked link 'secure-bank-login-update.com' and entered my credentials. Shortly after, $2,400 was attempted to be withdrawn.",
                incident_date="2026-09-01 14:30",
                financial_loss=2400.0,
                currency="USD",
                platform_used="SMS / Mobile Browser",
                suspect_contact="SMS sender: +1-888-555-9981",
                suspect_bank_details="Account Transfer Ref: TXN994821",
                latitude=40.7128,
                longitude=-74.0060,
                location_address="New York, NY",
                severity="High",
                status="Under Investigation",
                assigned_investigator_id=admin.id
            )

            sample2 = Report(
                reference_no="CCR-2026-B4419Z",
                user_id=citizen.id,
                reporter_name="John Doe",
                reporter_email="citizen@example.com",
                reporter_phone="+1-555-0192",
                category_id=fin_cat.id,
                title="Crypto Investment Scam Telegram Group",
                description="Joined a Telegram group promising 300% return on Bitcoin trading. Transferred $5,000 to suspect wallet address. Group admin deleted channel immediately after transfer.",
                incident_date="2026-08-28 09:15",
                financial_loss=5000.0,
                currency="USD",
                platform_used="Telegram",
                suspect_name="@CryptoMasterAdmin",
                suspect_contact="Telegram: @CryptoMasterAdmin",
                suspect_bank_details="BTC Wallet: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                severity="Critical",
                status="Pending"
            )

            sample3 = Report(
                reference_no="CCR-2026-C1102K",
                user_id=citizen.id,
                reporter_name="John Doe",
                reporter_email="citizen@example.com",
                reporter_phone="+1-555-0192",
                category_id=hack_cat.id,
                title="Instagram Account Takeover & Fraudulent DMs",
                description="Attacker bypassed 2FA via SIM swap, took control of my Instagram handle @johndoe_official, changed recovery email, and sent scam links to all followers.",
                incident_date="2026-08-25 18:00",
                financial_loss=0.0,
                currency="USD",
                platform_used="Instagram",
                suspect_contact="IP Address from login email alert: 185.220.101.5",
                severity="Medium",
                status="Resolved",
                assigned_investigator_id=admin.id
            )

            db.session.add_all([sample1, sample2, sample3])
            db.session.flush()

            # Status logs for sample reports
            log1 = ReportStatusLog(report_id=sample1.id, status='Pending', notes='Report submitted by victim.', updated_by='System')
            log2 = ReportStatusLog(report_id=sample1.id, status='Under Investigation', notes='Case assigned to Agent Sarah Connor. Subpoena issued to domain host for phishing site.', updated_by='Agent Sarah Connor')
            
            log3 = ReportStatusLog(report_id=sample2.id, status='Pending', notes='Report received. Blockchain ledger trace initiated.', updated_by='System')
            
            log4 = ReportStatusLog(report_id=sample3.id, status='Pending', notes='Report received.', updated_by='System')
            log5 = ReportStatusLog(report_id=sample3.id, status='Resolved', notes='Account successfully recovered via Meta security team. SIM swap reported to carrier.', updated_by='Agent Sarah Connor')

            db.session.add_all([log1, log2, log3, log4, log5])
            db.session.commit()

        print("Database seeded successfully with Officer Password Mandate!")

if __name__ == '__main__':
    seed()

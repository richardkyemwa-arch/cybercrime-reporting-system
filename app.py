import os
import uuid
import datetime
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cyber-crime-reporting-secret-key-2026-secure'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cyber_crime.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# -------------------------------------------------------------------
# Database Models
# -------------------------------------------------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='citizen')  # 'citizen' or 'investigator'
    badge_number = db.Column(db.String(50), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    must_change_password = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    code = db.Column(db.String(40), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), default='fa-shield-alt')


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_no = db.Column(db.String(30), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reporter_name = db.Column(db.String(100), nullable=False)
    reporter_email = db.Column(db.String(120), nullable=False)
    reporter_phone = db.Column(db.String(20), nullable=True)
    
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    incident_date = db.Column(db.String(50), nullable=True)
    financial_loss = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10), default='USD')
    platform_used = db.Column(db.String(100), nullable=True)
    
    # Suspect details
    suspect_name = db.Column(db.String(100), nullable=True)
    suspect_contact = db.Column(db.String(150), nullable=True)
    suspect_bank_details = db.Column(db.String(150), nullable=True)
    
    # Geolocation
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location_address = db.Column(db.String(200), nullable=True)
    
    # Status & Urgency
    status = db.Column(db.String(30), default='Pending') # Pending, Under Investigation, Resolved, Dismissed
    severity = db.Column(db.String(20), default='Medium') # Low, Medium, High, Critical
    assigned_investigator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    category = db.relationship('Category', backref='reports')
    user = db.relationship('User', foreign_keys=[user_id], backref='citizen_reports')
    investigator = db.relationship('User', foreign_keys=[assigned_investigator_id], backref='assigned_reports')
    evidences = db.relationship('Evidence', backref='report', cascade="all, delete-orphan")
    status_logs = db.relationship('ReportStatusLog', backref='report', cascade="all, delete-orphan", order_by="ReportStatusLog.created_at.desc()")


class Evidence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('report.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class ReportStatusLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('report.id'), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    updated_by = db.Column(db.String(100), default='System')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class EmergencyContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    number = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(50), default='Hotline')
    is_247 = db.Column(db.Boolean, default=True)


# Helper functions & decorators
def generate_reference_no():
    year = datetime.now().year
    random_part = uuid.uuid4().hex[:6].upper()
    return f"CCR-{year}-{random_part}"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Account login required to access the Cyber Crime Reporting Portal.', 'error')
            return redirect(url_for('login', next=request.url))
        if session.get('must_change_password') and request.endpoint not in ('force_password_change', 'logout'):
            flash('Mandatory Security Policy: You must change your password before proceeding.', 'warning')
            return redirect(url_for('force_password_change'))
        return f(*args, **kwargs)
    return decorated_function

def investigator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Account login required.', 'error')
            return redirect(url_for('login', next=request.url))
        if session.get('must_change_password') and request.endpoint not in ('force_password_change', 'logout'):
            flash('Mandatory Security Policy: As an officer, you must change your password before accessing the portal.', 'warning')
            return redirect(url_for('force_password_change'))
        if session.get('user_role') != 'investigator':
            flash('Access restricted to verified law enforcement investigators.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------------------------------------------
# Routes - PWA & Web Interface
# -------------------------------------------------------------------

@app.route('/')
def index():
    if session.get('must_change_password'):
        return redirect(url_for('force_password_change'))
    categories = Category.query.all()
    recent_reports_count = Report.query.count()
    resolved_count = Report.query.filter_by(status='Resolved').count()
    user = User.query.get(session.get('user_id')) if 'user_id' in session else None
    return render_template('index.html', categories=categories, total_reports=recent_reports_count, resolved_count=resolved_count, current_user=user)


@app.route('/report', methods=['GET', 'POST'])
@login_required
def report_crime():
    current_user = User.query.get_or_404(session['user_id'])
    
    if request.method == 'GET':
        categories = Category.query.all()
        return render_template('report.html', categories=categories, current_user=current_user)
    
    try:
        category_id = int(request.form.get('category_id', 1))
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        incident_date = request.form.get('incident_date', '')
        financial_loss = float(request.form.get('financial_loss', 0.0) or 0.0)
        currency = request.form.get('currency', 'USD')
        platform_used = request.form.get('platform_used', '').strip()
        
        suspect_name = request.form.get('suspect_name', '').strip()
        suspect_contact = request.form.get('suspect_contact', '').strip()
        suspect_bank_details = request.form.get('suspect_bank_details', '').strip()
        
        lat = request.form.get('latitude')
        lng = request.form.get('longitude')
        latitude = float(lat) if lat else None
        longitude = float(lng) if lng else None
        location_address = request.form.get('location_address', '').strip()
        
        severity = 'Medium'
        if financial_loss >= 10000 or 'ransomware' in title.lower() or 'extortion' in title.lower():
            severity = 'Critical'
        elif financial_loss >= 1000:
            severity = 'High'
            
        ref_no = generate_reference_no()

        new_report = Report(
            reference_no=ref_no,
            user_id=current_user.id,
            reporter_name=current_user.full_name,
            reporter_email=current_user.email,
            reporter_phone=current_user.phone or request.form.get('reporter_phone', '').strip(),
            category_id=category_id,
            title=title,
            description=description,
            incident_date=incident_date,
            financial_loss=financial_loss,
            currency=currency,
            platform_used=platform_used,
            suspect_name=suspect_name,
            suspect_contact=suspect_contact,
            suspect_bank_details=suspect_bank_details,
            latitude=latitude,
            longitude=longitude,
            location_address=location_address,
            severity=severity,
            status='Pending'
        )
        
        db.session.add(new_report)
        db.session.flush()

        uploaded_files = request.files.getlist('evidence_files')
        for file in uploaded_files:
            if file and file.filename:
                orig_name = secure_filename(file.filename)
                ext = orig_name.rsplit('.', 1)[1].lower() if '.' in orig_name else 'bin'
                unique_filename = f"{uuid.uuid4().hex}.{ext}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                file_size = os.path.getsize(file_path)
                
                evidence = Evidence(
                    report_id=new_report.id,
                    file_name=unique_filename,
                    original_name=orig_name,
                    file_type=ext,
                    file_size=file_size
                )
                db.session.add(evidence)
                
        log = ReportStatusLog(
            report_id=new_report.id,
            status='Pending',
            notes=f'Report received from authenticated account ({current_user.email}). Queued for investigator review.',
            updated_by='System'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'reference_no': ref_no,
            'message': 'Report submitted successfully under your registered account.'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/track', methods=['GET'])
@login_required
def track():
    ref = request.args.get('ref', '').strip()
    current_user = User.query.get(session['user_id'])
    
    my_reports = []
    if current_user.role == 'citizen':
        my_reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).all()
    else:
        my_reports = Report.query.order_by(Report.created_at.desc()).limit(10).all()
        
    report = None
    if ref:
        query = Report.query.filter_by(reference_no=ref)
        if current_user.role == 'citizen':
            query = query.filter_by(user_id=current_user.id)
        report = query.first()
        
    return render_template('track.html', report=report, ref_search=ref, my_reports=my_reports, current_user=current_user)


@app.route('/api/track/<ref_no>')
@login_required
def api_track(ref_no):
    current_user = User.query.get(session['user_id'])
    query = Report.query.filter_by(reference_no=ref_no.strip())
    if current_user.role == 'citizen':
        query = query.filter_by(user_id=current_user.id)
    report = query.first()
    
    if not report:
        return jsonify({'success': False, 'message': 'Report reference number not found or access restricted.'}), 404
        
    logs = [{
        'status': l.status,
        'notes': l.notes,
        'updated_by': l.updated_by,
        'date': l.created_at.strftime('%b %d, %Y %H:%M')
    } for l in report.status_logs]
    
    return jsonify({
        'success': True,
        'reference_no': report.reference_no,
        'category': report.category.name,
        'title': report.title,
        'status': report.status,
        'severity': report.severity,
        'created_at': report.created_at.strftime('%b %d, %Y %H:%M'),
        'history': logs
    })


@app.route('/emergency')
@login_required
def emergency():
    contacts = EmergencyContact.query.all()
    return render_template('emergency.html', contacts=contacts)

# -------------------------------------------------------------------
# Auth, Officer Password Mandate & Account Management
# -------------------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        selected_role = request.form.get('role', 'citizen')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if user.role != selected_role:
                flash(f'Account exists but role is registered as "{user.role.title()}", not "{selected_role.title()}". Please select your correct role.', 'error')
                return render_template('login.html')

            session['user_id'] = user.id
            session['user_name'] = user.full_name
            session['user_role'] = user.role
            session['user_badge'] = user.badge_number
            session['must_change_password'] = user.must_change_password or (user.role == 'investigator' and user.must_change_password)
            
            # MANDATORY OFFICER PASSWORD RESET INTERCEPTION
            if user.role == 'investigator' and user.must_change_password:
                flash('Mandatory Officer Security Policy: You must change your password upon login before accessing officer features.', 'warning')
                return redirect(url_for('force_password_change'))

            flash(f'Welcome back, {user.full_name} ({user.role.title()})!', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.role == 'investigator':
                return redirect(url_for('dashboard'))
            return redirect(url_for('index'))
        else:
            flash('Invalid email, password, or role selection.', 'error')
            
    return render_template('login.html')


@app.route('/force-password-change', methods=['GET', 'POST'])
def force_password_change():
    if 'user_id' not in session:
        flash('Account login required.', 'error')
        return redirect(url_for('login'))
        
    user = User.query.get_or_404(session['user_id'])
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not user.check_password(current_password):
            flash('Current password is incorrect.', 'error')
            return render_template('force_password_change.html', current_user=user)
            
        if len(new_password) < 8:
            flash('New password must be at least 8 characters long.', 'error')
            return render_template('force_password_change.html', current_user=user)
            
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('force_password_change.html', current_user=user)
            
        if current_password == new_password:
            flash('New password must be different from your current password.', 'error')
            return render_template('force_password_change.html', current_user=user)
            
        user.set_password(new_password)
        user.must_change_password = False
        db.session.commit()
        
        session['must_change_password'] = False
        flash('Password successfully updated! Security mandate satisfied.', 'success')
        
        if user.role == 'investigator':
            return redirect(url_for('dashboard'))
        return redirect(url_for('index'))
        
    return render_template('force_password_change.html', current_user=user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'citizen')
        badge_number = request.form.get('badge_number', '').strip()
        department = request.form.get('department', '').strip()
        
        if User.query.filter_by(email=email).first():
            flash('An account with this email address is already registered.', 'error')
            return render_template('register.html')
            
        if role == 'investigator':
            if not badge_number:
                flash('Law Enforcement Officers / Investigators MUST provide an official Badge/Officer ID Number.', 'error')
                return render_template('register.html')
            if not department:
                flash('Please specify your Law Enforcement Agency / Department.', 'error')
                return render_template('register.html')
        
        # New Officer Accounts MUST change password upon login by security mandate
        must_change = True if role == 'investigator' else False

        user = User(
            full_name=name,
            email=email,
            phone=phone,
            role=role,
            badge_number=badge_number if role == 'investigator' else None,
            department=department if role == 'investigator' else None,
            must_change_password=must_change
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        session['user_name'] = user.full_name
        session['user_role'] = user.role
        session['user_badge'] = user.badge_number
        session['must_change_password'] = user.must_change_password
        
        if must_change:
            flash('Account created! Officer Security Policy requires you to set your official password now.', 'warning')
            return redirect(url_for('force_password_change'))
            
        flash(f'Account created successfully as {role.title()}!', 'success')
        return redirect(url_for('index'))
        
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@investigator_required
def dashboard():
    status_filter = request.args.get('status', 'all')
    severity_filter = request.args.get('severity', 'all')
    category_filter = request.args.get('category', 'all')
    
    query = Report.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    if severity_filter != 'all':
        query = query.filter_by(severity=severity_filter)
    if category_filter != 'all' and category_filter.isdigit():
        query = query.filter_by(category_id=int(category_filter))
        
    reports = query.order_by(Report.created_at.desc()).all()
    categories = Category.query.all()
    
    stats = {
        'total': Report.query.count(),
        'pending': Report.query.filter_by(status='Pending').count(),
        'investigating': Report.query.filter_by(status='Under Investigation').count(),
        'resolved': Report.query.filter_by(status='Resolved').count(),
        'critical': Report.query.filter_by(severity='Critical').count()
    }
    
    return render_template('dashboard.html', reports=reports, categories=categories, stats=stats, 
                           current_status=status_filter, current_severity=severity_filter, current_category=category_filter)


@app.route('/admin/report/<int:report_id>/update', methods=['POST'])
@investigator_required
def update_report_status(report_id):
    report = Report.query.get_or_404(report_id)
    new_status = request.form.get('status')
    new_severity = request.form.get('severity')
    notes = request.form.get('notes', '').strip()
    
    if new_status:
        report.status = new_status
    if new_severity:
        report.severity = new_severity
        
    log = ReportStatusLog(
        report_id=report.id,
        status=report.status,
        notes=notes or f"Status updated to {report.status}",
        updated_by=f"{session.get('user_name')} ({session.get('user_badge', 'Officer')})"
    )
    
    db.session.add(log)
    db.session.commit()
    
    flash(f"Report {report.reference_no} updated successfully.", 'success')
    return redirect(url_for('dashboard'))


@app.route('/admin/report/<int:report_id>/details')
@investigator_required
def report_details_json(report_id):
    report = Report.query.get_or_404(report_id)
    evidences = [{
        'id': e.id,
        'name': e.original_name,
        'url': url_for('static', filename=f'uploads/{e.file_name}'),
        'size_kb': round(e.file_size / 1024, 1) if e.file_size else 0
    } for e in report.evidences]
    
    history = [{
        'status': h.status,
        'notes': h.notes,
        'updated_by': h.updated_by,
        'date': h.created_at.strftime('%Y-%m-%d %H:%M')
    } for h in report.status_logs]
    
    return jsonify({
        'id': report.id,
        'reference_no': report.reference_no,
        'category': report.category.name,
        'title': report.title,
        'description': report.description,
        'incident_date': report.incident_date,
        'financial_loss': report.financial_loss,
        'currency': report.currency,
        'platform_used': report.platform_used,
        'suspect_name': report.suspect_name,
        'suspect_contact': report.suspect_contact,
        'suspect_bank_details': report.suspect_bank_details,
        'reporter_name': report.reporter_name,
        'reporter_email': report.reporter_email,
        'reporter_phone': report.reporter_phone or 'N/A',
        'latitude': report.latitude,
        'longitude': report.longitude,
        'location_address': report.location_address,
        'status': report.status,
        'severity': report.severity,
        'created_at': report.created_at.strftime('%Y-%m-%d %H:%M'),
        'evidences': evidences,
        'history': history
    })

# -------------------------------------------------------------------
# Service Worker & PWA Support Routes
# -------------------------------------------------------------------

@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')


@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')


# -------------------------------------------------------------------
# Install / QR Code Page
# -------------------------------------------------------------------

def _get_app_url():
    """Return the public URL for this app (env var, or auto-detect from request context)."""
    return os.environ.get('APP_PUBLIC_URL', request.host_url.rstrip('/'))


def _ensure_qr_code(url: str):
    """Generate the QR PNG if it doesn't already exist (or URL changed)."""
    qr_path = os.path.join(app.root_path, 'static', 'qr', 'app_qr.png')
    flag_path = os.path.join(app.root_path, 'static', 'qr', '.url_flag')

    # Check whether QR needs (re)generation
    needs_gen = not os.path.exists(qr_path)
    if os.path.exists(flag_path):
        with open(flag_path, 'r') as f:
            if f.read().strip() != url:
                needs_gen = True
    else:
        needs_gen = True

    if needs_gen:
        try:
            import qrcode
            from qrcode.image.styledpil import StyledPilImage
            from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
            from PIL import Image

            os.makedirs(os.path.dirname(qr_path), exist_ok=True)
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=2,
            )
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
            ).convert("RGBA")
            bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
            bg.paste(img, (0, 0), img)
            bg.convert("RGB").save(qr_path)
            with open(flag_path, 'w') as f:
                f.write(url)
        except Exception as e:
            app.logger.warning(f"QR generation failed: {e}")


@app.route('/install')
def install_page():
    """Serve the PWA install / QR code page."""
    app_url = _get_app_url()
    _ensure_qr_code(app_url)
    return render_template('install.html', app_url=app_url)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)


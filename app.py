from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

port = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['TEMPLATES_AUTO_RELOAD'] = True

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ================= MODELS =================

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category = db.Column(db.String(100))
    description = db.Column(db.String(300))
    priority = db.Column(db.String(20))
    status = db.Column(db.String(20), default="Pending")
    admin_response = db.Column(db.String(300))
    file = db.Column(db.String(100))

    student = db.relationship('User')

# ================= LOGIN =================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================= ROUTES =================

@app.route('/')
def home():
    return redirect(url_for('login'))

# -------- REGISTER --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            role = request.form['role']

            user = User(name=name, email=email, password=password, role=role)
            db.session.add(user)
            db.session.commit()

            return redirect(url_for('login'))

        return render_template('register.html')
    
    except Exception as e:
        return f"ERROR: {str(e)}"

# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email'],
                                    password=request.form['password']).first()
        if user:
            login_user(user)
            flash("Login successful!", "success")
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash("Invalid credentials!", "danger")
    return render_template('login.html')

# -------- LOGOUT --------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# -------- STUDENT --------
@app.route('/student', methods=['GET', 'POST'])
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['file']
        filename = file.filename if file else None
        if file:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        ticket = Ticket(
            student_id=current_user.id,
            category=request.form['category'],
            description=request.form['description'],
            priority=request.form['priority'],
            file=filename
        )
        db.session.add(ticket)
        db.session.commit()
        flash("Ticket submitted!", "success")

    tickets = Ticket.query.filter_by(student_id=current_user.id).all()
    return render_template('student_dashboard.html', tickets=tickets)

# -------- ADMIN --------
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('login'))

    query = Ticket.query

    # FILTERS
    category = request.args.get('category')
    status = request.args.get('status')
    search = request.args.get('search')

    if category:
        query = query.filter(Ticket.category.contains(category))
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(Ticket.description.contains(search))

    tickets = query.all()

    # UPDATE
    if request.method == 'POST':
        ticket = Ticket.query.get(request.form['ticket_id'])
        ticket.status = request.form['status']
        ticket.admin_response = request.form['response']
        db.session.commit()
        flash("Updated!", "success")
        return redirect(url_for('admin_dashboard'))

    # STATS
    total = Ticket.query.count()
    pending = Ticket.query.filter_by(status="Pending").count()
    progress = Ticket.query.filter_by(status="In Progress").count()
    resolved = Ticket.query.filter_by(status="Resolved").count()

    return render_template('admin_dashboard.html',
                           tickets=tickets,
                           total=total,
                           pending=pending,
                           progress=progress,
                           resolved=resolved)

# -------- DELETE --------
@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_ticket(id):
    ticket = Ticket.query.get(id)
    db.session.delete(ticket)
    db.session.commit()
    flash("Deleted!", "danger")
    return redirect(url_for('admin_dashboard'))

# -------- FILE VIEW --------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ================= RUN =================

with app.app_context():
    db.create_all()
    print("✅ Database created successfully")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
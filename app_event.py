import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# User model for authentication
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Event model with date and image support
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    image = db.Column(db.String(100))

# Create database tables
with app.app_context():
    db.create_all()

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "danger")
            return redirect(url_for('register'))

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password", "danger")

    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash("You have logged out.", "info")
    return redirect(url_for('login'))

# Home route
@app.route('/')
def index():
    events = Event.query.order_by(Event.date.asc()).all()
    return render_template('index.html', events=events)

# Add event route
@app.route('/add', methods=['GET', 'POST'])
def add_event():
    if 'user_id' not in session:
        flash("You must be logged in to add events.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        image = request.files.get('image')

        filename = None
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_event = Event(title=title, description=description, date=date, image=filename)
        db.session.add(new_event)
        db.session.commit()
        flash("Event added successfully!", "success")
        return redirect(url_for('index'))

    return render_template('add_event.html')

# Edit event route
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_event(id):
    if 'user_id' not in session:
        flash("You must be logged in to edit events.", "warning")
        return redirect(url_for('login'))

    event = Event.query.get_or_404(id)

    if request.method == 'POST':
        event.title = request.form['title']
        event.description = request.form['description']
        event.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        image = request.files.get('image')

        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            event.image = filename

        db.session.commit()
        flash("Event updated successfully!", "success")
        return redirect(url_for('index'))

    return render_template('edit_event.html', event=event)

# Delete event route
@app.route('/delete/<int:id>')
def delete_event(id):
    if 'user_id' not in session:
        flash("You must be logged in to delete events.", "warning")
        return redirect(url_for('login'))

    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted successfully!", "success")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

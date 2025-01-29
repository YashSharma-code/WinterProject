import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this in production

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projects.db'
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

# Project model with image support
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(100))  # Image filename

# Create database tables
with app.app_context():
    db.create_all()

# ========== AUTH ROUTES ==========
# Register
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
        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# Login
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

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash("You have logged out.", "info")
    return redirect(url_for('login'))

# ========== PROJECT ROUTES ==========
# Home (List Projects)
@app.route('/')
def index():
    projects = Project.query.all()
    return render_template('index.html', projects=projects)

# Add Project (Requires Login)
@app.route('/add', methods=['GET', 'POST'])
def add_project():
    if 'user_id' not in session:
        flash("You must be logged in to add projects.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        image = request.files.get('image')

        filename = None
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_project = Project(title=title, description=description, image=filename)
        db.session.add(new_project)
        db.session.commit()
        flash("Project added successfully!", "success")
        return redirect(url_for('index'))

    return render_template('add_project.html')

# Edit Project (Requires Login)
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_project(id):
    if 'user_id' not in session:
        flash("You must be logged in to edit projects.", "warning")
        return redirect(url_for('login'))

    project = Project.query.get_or_404(id)

    if request.method == 'POST':
        project.title = request.form['title']
        project.description = request.form['description']
        image = request.files.get('image')

        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            project.image = filename

        db.session.commit()
        flash("Project updated successfully!", "success")
        return redirect(url_for('index'))

    return render_template('edit_project.html', project=project)

# Delete Project (Requires Login)
@app.route('/delete/<int:id>')
def delete_project(id):
    if 'user_id' not in session:
        flash("You must be logged in to delete projects.", "warning")
        return redirect(url_for('login'))

    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    flash("Project deleted successfully!", "success")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
#this is a crud app for student data management
#It was created by Ambaza Sem Mukama from 3/8/2024 to 14/8/2023
#as my portfolio project
#i commented it to make it understandable :) 
#we first declare all libralies,frameworks and dependencies we are going to use

from flask import Flask, session, render_template, request,redirect,url_for,flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired
from flask_bootstrap import Bootstrap5
import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,check_password_hash
from functools import wraps

#Initialized the app and extensions
app = Flask(__name__)
bootstrap = Bootstrap5(app)#initialised bootstrap

#declare the db
app.config['SECRET_KEY'] = "qwerty1!qwerty1!"#configure the secret key for csrf 
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'sds.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db = SQLAlchemy(app)#initialise the database


# Define the form class using Flask-WTF

class LoginForm(FlaskForm):#the login and sign-in form
    username = StringField('enter your name', validators=[InputRequired()], render_kw={"placeholder": "Username"})
    
    password = PasswordField('enter your password', validators=[InputRequired()], render_kw={"placeholder": "Password"})

class RegisterStudent(FlaskForm):#the student registry form 
    firstname = StringField('enter student first name', validators=[InputRequired()], render_kw={"placeholder": "Firstname"})
    lastname = StringField('enter student last name', validators=[InputRequired()], render_kw={"placeholder": "Lastname"}) 
    marks= StringField('enter students marks', validators=[InputRequired()], render_kw={"placeholder": "Marks(average)"})

class AddMarks(FlaskForm):#the add marks form
    marks=StringField('enter marks',render_kw={'placeholder':'Marks'})


# Define the database models using SQLAlchemy
#define the teachers table
class Teachers(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(64), unique=True)
    student_rel = db.relationship('Students', backref='teacher', lazy=True)

#define the students table
class Students(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    marks = db.Column(db.String(64))
    student_marks = db.Column(db.Integer, db.ForeignKey('teachers.id'))

# Function to create the database
def create_db():
    with app.app_context():
        db.create_all()
        print("Done creating")

#define the login_required to protect pages so that you need to login to access them

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'name' not in session:
            flash('You need to be logged in to view this page', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Declare routes

@app.route("/")#the home route
def home():
    return render_template('home.html')

@app.route("/signup", methods=['GET', 'POST'])#the sign in page
def signup():
    form = LoginForm()
    if form.validate_on_submit():

        hashed_password = generate_password_hash(form.password.data)
        new_user = Teachers(username=form.username.data, password=hashed_password)
        session['name']=form.username.data
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("dashboard"))
        
    return render_template('signup.html', form=form)


@app.route("/login", methods=('GET', 'POST'))#the login page
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = Teachers.query.filter_by(username=form.username.data).first()

        if user and check_password_hash(user.password, form.password.data):
            flash('Login successful!', 'success')
            session['name']=form.username.data
            return redirect(url_for("dashboard"))
            
        else:
            return"go"
             
    return render_template('login.html', form=form)

@app.route("/dash")#the teacher dashboard
@login_required
def dashboard():
    name=session.get('name')
    return render_template('teacher-dashboard.html',name=name)

@app.route("/register", methods=['GET', 'POST'])#page for registering students
@login_required
def register():
    form = RegisterStudent()
    if form.validate_on_submit():
        teacher = Teachers.query.filter_by(username=session.get('name')).first()
        new_student = Students(
            first_name=form.firstname.data,
            last_name=form.lastname.data,
            marks=form.marks.data,
            student_marks=teacher.id
            )
        
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_template('register.html', form=form)

@app.route("/students-dashboard")#the page to view student data
@login_required
def students_dashboard():
    
    teacher = Teachers.query.filter_by(username=session.get('name')).first()
    students = Students.query.filter_by(student_marks=teacher.id).all()
    return render_template('Student dashboard.html', students=students)

@app.route("/add-marks", methods=["GET", "POST"])#add students marks
@login_required
def add_marks():
    teacher = Teachers.query.filter_by(username=session.get('name')).first()   
    students = Students.query.filter_by(student_marks=teacher.id).all()

    if request.method == 'POST':
        for student in students:
            new_mark = request.form.get(f'marks_{student.id}')
            if new_mark and new_mark.isdigit():
                new_mark = float(new_mark)

                if student.marks is None:
                    student.marks = new_mark

                else:
                    student.marks = (float(student.marks) + new_mark) / 2
                
                db.session.add(student)
        
        db.session.commit()
        flash('Marks updated successfully', 'success')
        print('successful')
    
        return redirect(url_for('students_dashboard'))
               
    return render_template('add marks.html', students=students)

@app.route('/delete-students', methods=['GET', 'POST'])#the page to delete students
@login_required
def delete_student():
    teacher = Teachers.query.filter_by(username=session.get('name')).first()   
    students = Students.query.filter_by(student_marks=teacher.id).all()

    if request.method == 'POST':
        for student in students:
            
            delete = request.form.get(f'delete_{student.id}')
            if delete == "True":
                db.session.delete(student)
        
        db.session.commit() 
        flash('Selected students deleted successfully', 'success')
        print('delete sucessful')
    
        return redirect(url_for('dashboard'))

    return render_template('delete students.html', students=students)


@app.route('/logout')#the logout page
def logout():
    session.pop('name', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Runing the application
if __name__ == '__main__':
    create_db()
    app.run(debug=True)

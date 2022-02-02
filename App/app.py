from flask import Flask, render_template, flash, url_for, redirect, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, BooleanField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
import requests
from numpy import cumsum, array
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kpasec.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = 'secretsahhajs'
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

terminal_fee = 1200

def generate_receipt_no():
	#Also generate transaction ids
	pass

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register_user", methods = ['GET', 'POST'])
def register_user():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = UserSignUpForm()
	if form.validate_on_submit():
		if request.method == "POST":
			username = form.data['username']
			email = form.data['email']
			password = form.data['password']
			hash_password = bcrypt.generate_password_hash(password).decode("utf-8")
			data = User(username=username, email=email, password=hash_password)
			db.session.add(data)
			db.session.commit()
		flash(f"Account successfully created for {form.username.data}", "success")
		return redirect(url_for("login"))
	return render_template("register_user.html", form=form)

@app.route("/login", methods = ['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = UserLogInForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			next_page = request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('account'))
		else:
			flash("Login unsuccessful, please try again", "danger")
	return render_template("login_user.html", form=form)

@app.route("/download")
def download():
	file = "downloads/file1.jpg"
	return send_file(file, as_attachment = True)

@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for("login"))


@app.route("/student_data", methods = ['GET', 'POST'])
@login_required
def student_data():
	form = StudentSignUp()
	if form.validate_on_submit():
		if request.method == "POST":
			name = form.data['name']
			email = form.data['email']
			class1 = form.data['class1']
			parent_contact = form.data['parent_contact']
			data = Student(fullname=name, email=email, class1=class1, parent_no = parent_contact)
			db.session.add(data)
			db.session.commit()
		flash(f"Account successfully created for {form.name.data}", "success")
		return redirect(url_for("student_data"))
	return render_template("student_data.html", form=form)

@app.route("/student_payment", methods = ['GET', 'POST'])
@login_required
def student_payment():
	form = StudentPaymentsForm()
	if form.validate_on_submit():
		if request.method == "POST":
			fullname = form.data['fullname']
			amount = form.data['amount']
			parent_contact = form.data['parent_contact']
			category = form.data['category']
			semester = form.data['semester']
			mode_of_payment = form.data['mode_of_payment']
			data = StudentPayments(student_fullname=fullname, amount=amount, 
				category=category, mode_of_payment=mode_of_payment, student_id = parent_contact, semester=semester)
			cash = CashBook(name=fullname, details=category, amount=amount, category="revenue", 
				semester=semester, mode_of_payment=mode_of_payment)
			db.session.add(data)
			db.session.add(cash)
			db.session.commit()
		flash(f"{form.amount.data} {form.category.data} fees successfully paid by {form.fullname.data}", "success")
		return redirect(url_for("student_payment"))
	return render_template("student_payment.html", form=form)

@app.route("/expenses", methods = ['GET', 'POST'])
@login_required
def expenses():
	form = ExpensesForm()
	if form.validate_on_submit():
		if request.method == "POST":
			item = form.data['item']
			details = form.data['details']
			amount = form.data['amount']
			category = form.data['category']
			semester = form.data['semester']
			name = current_user.username
			mode_of_payment = form.data['mode_of_payment']
			data = Expenses(item=item, details=details, amount=amount, 
				category=category, mode_of_payment=mode_of_payment,semester=semester,name=name)
			cash = CashBook(name=name, details=details, amount=amount, category="payment", 
				semester=semester, mode_of_payment=mode_of_payment)
			db.session.add(data)
			db.session.add(cash)
			db.session.commit()
			flash("Data successfully saved", "success")
		return redirect(url_for("expenses"))
	return render_template("expenses.html", form=form)

@app.route("/account")
@login_required
def account():
	return render_template("account.html")

@app.route("/search", methods=['GET'])
@login_required
def search():
	number = request.args.get("search")
	user_res = Student.query.filter_by(parent_no = number).first()
	return render_template("search.html")

@app.route("/searchresults")
@login_required
def searchresults():
	res = request.args.get("idea")
	user_res = Student.query.filter_by(parent_no = res).first()
	if user_res:
		return redirect(url_for('student_account', number = user_res.parent_no))
	return render_template("searchresults.html", user_res = user_res)

@app.route("/income_expenditure")
@login_required
def income_expenditure():
	income = StudentPayments.query.all()
	expense = Expenses.query.all()
	income_cum = []
	for inc in income:
		income_cum.append(inc.amount)
	inc_cum = [income_cum[0]] + list(cumsum(income_cum))

	expense_cum = []
	for exp in expense:
		expense_cum.append(exp.amount)
	exp_cum = [expense_cum[0]] + list(cumsum(expense_cum))
	arr1 = -1*array(expense_cum)
	arr2 = array(income_cum)
	arr3 = list(arr2) + list(arr1)
	total = list(cumsum(arr3))
	return render_template("income_expenditure.html", income=income, inc_cum=inc_cum, 
		expense=expense, exp_cum=exp_cum, total=total)

@app.route("/student_account/<number>")
@login_required
def student_account(number):
	stud = Student.query.filter_by(parent_no=number).first()
	total_pmt = 0
	paymts = [-1*terminal_fee]
	for amt in stud.payments:
		paymts.append(amt.amount)
		total_pmt += amt.amount
	cum1 = cumsum(paymts)[1:]
	zip1 = zip(cum1, stud.payments)
	return render_template("student_account.html", stud=stud, 
		terminal_fee=terminal_fee, total_pmt=total_pmt, cum1=cum1, zip1=zip1)

@app.route("/cashbook")
@login_required
def cashbook():
	sem1 = request.args.get("select2")
	start = request.args.get("startdate")
	end = request.args.get("enddate")
	cash_data = CashBook.query.filter_by(semester = "SEM1")
	cash_cums1 = [2000]
	revs = []
	pays = []
	for money in cash_data:
		if money.category == "revenue":
			cash_cums1.append(money.amount)
			revs.append(money.amount)
		else:
			cash_cums1.append(-1*money.amount)
			pays.append(money.amount)
	cash_cums = cumsum(cash_cums1)[:]
	sum1 = sum(revs)
	sum2 = sum(pays)
	return render_template("cashbook.html", cash_data = cash_data, 
		cash_cums=cash_cums, sum1=sum1, sum2=sum2)

@app.route("/expenditure_template")
@login_required
def expenditure_template(expense, exp_cum, start_date, end_date):
	return render_template("expenditure.html", expense = expense, 
		exp_cum=exp_cum, start_date=start_date, end_date=end_date)

@app.route("/income_template")
@login_required
def income_template(income, inc_cum, start_date, end_date):
	return render_template("income.html", income = income, 
		inc_cum=inc_cum, start_date=start_date, end_date=end_date)

@app.route("/income_expenditure_template")
@login_required
def income_expenditure_template(income, inc_cum, expense, exp_cum, total, start_date, end_date):
	return render_template("income_expenditure.html", income=income, inc_cum=inc_cum, 
		expense=expense, exp_cum=exp_cum, total=total, start_date=start_date, end_date=end_date)

@app.route("/cash_book_template")
@login_required
def cash_book_template(cash_data, cash_cums, sum1, sum2, start_date, end_date):
	return render_template("cashbook.html", cash_data = cash_data, 
		cash_cums=cash_cums, sum1=sum1, sum2=sum2, start_date=start_date, end_date=end_date)

def extract_cash_book_data(cash_obj, balance_bf):
	cash_cums1 = [balance_bf]
	revs = []
	pays = []
	for money in cash_obj:
		if money.category == "revenue":
			cash_cums1.append(money.amount)
			revs.append(money.amount)
		if money.category == "payment":
			cash_cums1.append(-1*money.amount)
			pays.append(money.amount)
	cash_cums = cumsum(cash_cums1)[:]
	sum1 = sum(revs)
	sum2 = sum(pays)
	return cash_obj, cash_cums, sum1, sum2

def extract_expense_data(exp_obj):
	expense_cum = []
	for exp in exp_obj:
		expense_cum.append(exp.amount)
	exp_cum = [expense_cum[0]] + list(cumsum(expense_cum))
	return exp_obj, exp_cum

def extract_icome_data(inc_obj):
	income_cum = []
	for inc in inc_obj:
		income_cum.append(inc.amount)
	inc_cum = [income_cum[0]] + list(cumsum(income_cum))
	return inc_obj, inc_cum

def extract_income_and_expense_data(inc_obj, exp_obj):
	income_cum = []
	for inc in inc_obj:
		income_cum.append(inc.amount)
	inc_cum = [income_cum[0]] + list(cumsum(income_cum))

	expense_cum = []
	for exp in exp_obj:
		expense_cum.append(exp.amount)
	exp_cum = [expense_cum[0]] + list(cumsum(expense_cum))
	arr1 = -1*array(expense_cum)
	arr2 = array(income_cum)
	arr3 = list(arr2) + list(arr1)
	total = list(cumsum(arr3))
	return inc_obj, inc_cum, exp_obj, exp_cum, total

@app.route("/reports")
@login_required
def reports():
	form = ReportsForm()
	report = request.args.get("report")
	start = request.args.get("start")
	end = request.args.get("end")
	filter1 = request.args.get("filter_by")
	if report == "Cash Book":
		if filter1 != "ETL & PTA Levy":
			cash_filter = CashBook.query.filter(CashBook.date <= end).filter(CashBook.date >= start).filter(CashBook.details==filter1).all()
			cash_obj1, cash_cums, sum1, sum2 = extract_cash_book_data(cash_obj=cash_filter, balance_bf=2000)
			return cash_book_template(cash_data=cash_obj1, cash_cums=cash_cums, sum1=sum1, sum2=sum2, start_date=start, end_date=end)
		else:
			cash_filter = CashBook.query.filter(CashBook.date <= end).filter(CashBook.date >= start).all()
			cash_obj1, cash_cums, sum1, sum2 = extract_cash_book_data(cash_obj=cash_filter, balance_bf=2000)
			return cash_book_template(cash_data=cash_obj1, cash_cums=cash_cums, sum1=sum1, sum2=sum2, start_date=start, end_date=end)
	if report == "Income & Expenditure":
		inc_by_date = StudentPayments.query.filter(StudentPayments.date <= end).filter(StudentPayments.date >= start)
		exp_by_date = Expenses.query.filter(Expenses.date <= end).filter(Expenses.date >= start)
		inc_obj, inc_cum, exp_obj, exp_cum, total = extract_income_and_expense_data(inc_obj=inc_by_date, exp_obj=exp_by_date)
		return income_expenditure_template(income=list(inc_obj), inc_cum=inc_cum, expense=exp_obj, exp_cum=exp_cum, total=total, start_date=start, end_date=end)
	if report == "Income Statement":
		if filter1 != "ETL & PTA Levy":
			inc_by_date = StudentPayments.query.filter(StudentPayments.date <= end).filter(StudentPayments.date >= start).filter(StudentPayments.category == filter1).all()
			income, inc_cum = extract_icome_data(inc_obj = inc_by_date)
			return income_template(income=income, inc_cum=inc_cum, start_date=start, end_date=end)
		else:
			inc_by_date = StudentPayments.query.filter(StudentPayments.date <= end).filter(StudentPayments.date >= start).all()
			income, inc_cum = extract_icome_data(inc_obj = inc_by_date)
			return income_template(income=income, inc_cum=inc_cum, start_date=start, end_date=end)
	if report == "Expenditure Statement":
		exp_by_date = Expenses.query.filter(Expenses.date <= end).filter(Expenses.date >= start).all()
		expense, exp_cum = extract_expense_data(exp_obj=exp_by_date)
		return expenditure_template(expense=expense, exp_cum=exp_cum, start_date=start, end_date=end)
	return render_template("reports.html", form=form)



#FORMS
class UserSignUpForm(FlaskForm):
    username = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Comfirm Password", 
    	validators = [DataRequired(), EqualTo('password')])
    submit = SubmitField("Sign Up")

    #def validate_email(self, email):
    #	user = User.query.filter_by(email=email).first()
    #	if user:
    #		raise ValueError("The email is already in use, please choose a different one")

class UserLogInForm(FlaskForm):
    email = StringField("Email: ", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me:")
    submit = SubmitField("Log In")

classes = [str(i) + "A" for i in range(1,7)]

class StudentSignUp(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    class1 = SelectField("Class", validators=[DataRequired()], choices = classes)
    parent_contact = StringField("Parent Contact", validators=[DataRequired()])
    submit = SubmitField("Create")

    #def validate_email(self, email):
    	#student = Student.query.filter_by(email=email).first()
    	#if student:
    	#	raise ValueError("The email is already in use, please choose a different one")

    #def validate_contact(self, parent_contact):
    #	student = Student.query.filter_by(parent_contact=parent_contact).first()
    #	if student:
    #		raise ValueError("The contact is already in use, please choose a different one")

class StudentPaymentsForm(FlaskForm):
    fullname = StringField("Name: ", validators=[DataRequired()])
    parent_contact = StringField("Parent Contact: ", validators=[DataRequired()])
    amount = StringField("Amount", validators=[DataRequired()])
    semester = SelectField("Payment mode:", choices = ["SEM"+str(i) for i in range(1,7)], validators=[DataRequired()])
    mode_of_payment = SelectField("Payment mode:", choices = ['Cash', 'Cheque', 'Momo'], validators=[DataRequired()])
    category = SelectField("Category: ", choices = ['PTA Levy', 'ETL', 'Both'], validators = [DataRequired()])
    submit = SubmitField("Pay")

class ExpensesForm(FlaskForm):
    item = StringField("Item Name", validators=[DataRequired()])
    details = StringField("Details", validators=[DataRequired()])
    amount = StringField("Amount", validators=[DataRequired()])
    category = StringField("Category", validators=[DataRequired()])
    semester = SelectField("Semester", choices = ["SEM"+str(i) for i in range(1,7)], validators=[DataRequired()])
    mode_of_payment = SelectField("Payment mode", choices = ['Cash', 'Cheque', 'Momo'], validators=[DataRequired()])
    submit = SubmitField("Submit")

class ReportsForm(FlaskForm):
    report = SelectField("Choose type of report", validators=[DataRequired()], 
    	choices = ['Cash Book', 'Income & Expenditure', 'Expenditure Statement', 'Income Statement'])
    filter_by = SelectField("Choose", choices = ['PTA Levy', 'ETL', 'ETL & PTA Levy'])
    start = DateField("Start", validators=[DataRequired()])
    end = DateField("End", validators=[DataRequired()])
    submit = SubmitField("Submit")




#DATABASES
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default = datetime.utcnow())
    username = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'User: {self.username}'

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default = datetime.utcnow())
    fullname = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(200), unique=True)
    class1 = db.Column(db.String(10), unique=False, nullable=False)
    parent_no = db.Column(db.String(120), unique=True)
    payments = db.relationship('StudentPayments', backref='payer', lazy=True)#Here we reference the class

    def __repr__(self):
        return f'User: {self.fullname}'

class StudentPayments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default = datetime.utcnow())
    student_fullname = db.Column(db.String(80), unique=False, nullable=False)
    amount = db.Column(db.Integer, unique=False, nullable=False)
    category = db.Column(db.String(100), nullable = False)
    semester = db.Column(db.String(100), nullable = False)
    mode_of_payment = db.Column(db.String(100), nullable = False)
    student_id = db.Column(db.String(120), db.ForeignKey('student.parent_no'), nullable=False)#Here we reference the table name

    def __repr__(self):
        return f'User: {self.student_fullname}'

class Expenses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default = datetime.utcnow())
    item = db.Column(db.String(80), unique=False, nullable=False)
    name = db.Column(db.String(120), unique=False, nullable=False)
    details = db.Column(db.String(80), unique=False, nullable=False)
    amount = db.Column(db.Integer, unique=False, nullable=False)
    category = db.Column(db.String(100), nullable = False)
    semester = db.Column(db.String(100), nullable = False)
    mode_of_payment = db.Column(db.String(100), nullable = False)

    def __repr__(self):
        return f'User: {self.item}'

class CashBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default = datetime.utcnow())
    name = db.Column(db.String(80), unique=False, nullable=False)
    details = db.Column(db.String(80), unique=False, nullable=False)
    amount = db.Column(db.Integer, unique=False, nullable=False)
    category = db.Column(db.String(100), nullable = False)
    semester = db.Column(db.String(100), nullable = False)
    mode_of_payment = db.Column(db.String(100), nullable = False)

    def __repr__(self):
        return f'User: {self.name}'

if __name__ == '__main__':
	app.run(debug = True)
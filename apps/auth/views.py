from flask import Blueprint, render_template, flash, url_for, redirect, request, current_app
from apps.app import db
from apps.auth.forms import SignUpForm, LoginForm
from apps.crud.models import User
from flask_login import login_user, logout_user
import os

auth = Blueprint(
    "auth",
    __name__,
    template_folder = "templates",
    static_folder = "static",
)

@auth.route("/")
def nccu():
    return render_template("auth/nccu.html")

@auth.route("/signup", methods = ["GET","POST"])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        user = User(
            username = form.username.data,
            email = form.email.data,
            password = form.password.data,
            identity = form.identity.data,
        )
        if user.is_duplicate_email():
            flash("這個郵件位址已經註冊過")
            return redirect(url_for("auth.signup"))
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        
        next_ = request.args.get("next")
        if next_ is None or not next_.startswith("/"):
            next_ = url_for("crud.users")
        return redirect(next_)
    return render_template("auth/signup.html", form=form)

@auth.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            return redirect(url_for("crud.users"))
        
        flash("郵件位址或密碼不正確")
    return render_template("auth/login.html", form= form)

@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

@auth.route('/us')
def display_us_file():
    try:
        file_path = os.path.join(current_app.root_path, 'auth', 'static', 'text', 'us.txt')
        with open(file_path, 'r') as file:
            content = file.read()
        return render_template('crud/us.html', content=content)
    except FileNotFoundError:
        return "File not found", 404
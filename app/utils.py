from functools import wraps
from flask import request, flash, redirect, url_for, render_template
from flask_login import current_user

def verify_password_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            password = request.form.get('password_verify')
            if not password:
                flash("Password verification required for this action.", "error")
                return redirect(request.url)

            if not current_user.check_password(password):
                flash("Incorrect password. Action denied.", "error")
                return redirect(request.url)
        return f(*args, **kwargs)
    return decorated_function

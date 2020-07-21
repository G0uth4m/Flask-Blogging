from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from app import app
from flask import render_template
from threading import Thread


def send_async_email(app, message, sg):
    with app.app_context():
        sg.send(message)


def send_email(subject, sender, recepients, html_body):
    message = Mail(
        from_email=sender,
        to_emails=recepients,
        subject=subject,
        html_content=html_body
    )
    try:
        sg = SendGridAPIClient(os.environ.get('MAIL_PASSWORD'))
        Thread(target=send_async_email, args=(app, message, sg)).start()
    except Exception as e:
        print(e.message)


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email(
        subject='[!NVITE] Reset your password',
        sender=app.config['ADMINS'][0],
        recepients=user.email,
        html_body=render_template('email/reset_password.html', user=user, token=token)
    )

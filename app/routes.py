from flask import render_template, flash, redirect, url_for, request, jsonify, Response
import json
from app import app
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm, MessageForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post, Message, Notification
from werkzeug.urls import url_parse
from app import db
from datetime import datetime
from app.email import send_password_reset_email
from app.webpushnotifications import send_web_push


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/', methods=["POST", "GET"])
@login_required
def home():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post is now live!")
        return redirect(url_for('home'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('home', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('home', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Home Page', posts=posts.items, form=form, next_url=next_url, prev_url=prev_url)


@app.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if not user or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            redirect(url_for('home'))
        return redirect(next_page)

    return render_template('login.html', form=form, title='Sign In')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/register', methods=["POST", "GET"])
def register():
    if current_user.is_authenticated:
        redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful!")
        return redirect(url_for('login'))

    return render_template('register.html', form=form, title='Register')


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items, form=form, next_url=next_url, prev_url=prev_url)


@app.route('/edit_profile', methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Changes saved!")
        return redirect(url_for('edit_profile'))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title='Edit Profile', form=form)


@app.route('/follow/<username>', methods=["POST"])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User {} not found".format(username))
            return redirect(url_for('home'))
        if user == current_user:
            flash("You can't follow yourself!")
            return redirect(url_for('home'))
        current_user.follow(user)
        db.session.commit()
        flash("You are following {}".format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('home'))


@app.route('/unfollow/<username>', methods=["POST"])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User {} not found".format(user))
            return redirect(url_for('home'))
        if user == current_user:
            flash("You can't unfollow yourself!")
            return redirect(url_for('home'))
        current_user.unfollow(user)
        db.session.commit()
        flash("You unfollowed {}".format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('home'))


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Explore', posts=posts.items, next_url=next_url, prev_url=prev_url)


@app.route('/reset_password_request', methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash("Check your email for instructions to reset your password")
        return redirect(url_for('login'))

    return render_template('reset_password_request.html', title='Password reset', form=form)


@app.route('/reset_password/<token>', methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('home'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset")
        return redirect(url_for('login'))

    return render_template('reset_password.html', form=form)


@app.route('/send_message/<recepient>', methods=["GET", "POST"])
@login_required
def send_message(recepient):
    user = User.query.filter_by(username=recepient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recepient=user, body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash("Message sent!")
        return redirect(url_for('user', username=recepient))

    return render_template('send_message.html', title='Send message', form=form, recepient=recepient)


@app.route('/messages')
@login_required
def view_messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(Message.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False
    )
    next_url = url_for('view_messages', page=messages.next_num) if messages.has_next else None
    prev_url = url_for('view_messages', page=messages.prev_num) if messages.has_prev else None
    return render_template('messages.html', messages=messages.items, next_url=next_url, prev_url=prev_url)


@app.route('/notifications')
@login_required
def view_notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([
        {
            'name': n.name,
            'data': n.get_data(),
            'timestamp': n.timestamp
        } for n in notifications
    ])


@app.route('/api/v1/subscription/', methods=["GET", "POST"])
@login_required
def subscribe():
    if request.method == "GET":
        return Response(
            response=json.dumps({"public_key": app.config["VAPID_PUBLIC_KEY"]}),
            headers={"Access-Control-Allow-Origin": "*"},
            content_type="application/json"
        )
    temp = request.get_json("sub_token")
    print(type(temp), temp)
    if temp is None:
        current_user.subscription_token = None
    else:
        current_user.subscription_token = json.dumps(temp)
    db.session.commit()
    return Response(status=201, mimetype="application/json")


@app.route("/api/v1/push/", methods=['POST'])
def push_notifications():
    if not request.json or not request.json.get('user') or not request.json.get('message'):
        return jsonify({'failed': 1})

    username = request.json.get('user')
    message = request.json.get('message')
    token = User.query.filter_by(username=username).first().subscription_token
    if token is None:
        return jsonify({"failed": "User not subscribed for push notifications"})
    print(token)
    try:
        send_web_push(json.loads(token), message)
        return jsonify({'success': 1})
    except Exception as e:
        print("error", e)
        return jsonify({'failed': str(e)})

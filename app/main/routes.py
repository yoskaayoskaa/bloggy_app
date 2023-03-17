from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_login import current_user, login_required
from flask_babel import get_locale
from app import db
from app.main.forms import EditProfileForm, EmptyForm, PostForm, MessageForm
from app.models import User, Post, Message
from app.main import bp


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

    g.locale = get_locale()


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    func_name = 'index'

    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Ваш пост теперь доступен в общей ленте!')
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)

    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None

    return render_template('index.html', title='Главная', func_name=func_name,
                           form=form, posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/explore')
@login_required
def explore():
    func_name = 'explore'

    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)

    next_url = url_for('main.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None

    return render_template('index.html', title='Лента постов', func_name=func_name,
                           posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/about')
def about():
    return render_template('about.html', title='О приложении')


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()

    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)

    next_url = url_for('main.user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) if posts.has_prev else None

    form = EmptyForm()

    return render_template('user.html', title='Профиль', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return render_template('user_popup.html', user=user, form=form)


@bp.route('/followers/<username>')
@login_required
def followers(username):
    user = User.query.filter_by(username=username).first_or_404()

    followed = user.followed.all()
    followers = user.followers.all()

    return render_template('followers.html', title='Подписки и подписчики',
                           user=user, followed=followed, followers=followers)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(original_username=current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Изменения сохранены')
        return redirect(url_for('main.edit_profile'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title='Редактировать профиль', form=form)


@bp.route('/delete_profile', methods=['GET', 'POST'])
@login_required
def delete_profile():
    form = EmptyForm()
    if form.validate_on_submit():
        [db.session.delete(post) for post in current_user.posts.all()]
        [db.session.delete(message_sent) for message_sent in current_user.messages_sent.all()]
        [db.session.delete(message_received) for message_received in current_user.messages_received.all()]
        db.session.delete(current_user)
        db.session.commit()
        flash('Ваш профиль был успешно удален')
        return redirect(url_for('auth.login'))

    return render_template('delete_profile.html', title='Удалить профиль', form=form)


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()

    form = MessageForm()
    if form.validate_on_submit():
        message = Message(author=current_user, recipient=user, body=form.message.data)
        db.session.add(message)
        db.session.commit()
        flash('Ваше сообщение отправлено!')
        return redirect(url_for('main.user', username=recipient))

    return render_template('send_message.html', title='Отправить сообщение',  recipient=recipient, form=form)


@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    db.session.commit()

    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(Message.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)

    next_url = url_for('main.messages', page=messages.next_num) if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) if messages.has_prev else None

    return render_template('messages.html', title='Входящие сообщения', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()

        if not user:
            flash(f'Блогер {username} не найден!')
            return redirect(url_for('main.index'))

        if user == current_user:
            flash('Невозможно подписаться на себя!')
            return redirect(url_for('main.user', username=username))

        current_user.follow(user)
        db.session.commit()
        flash(f'Вы подписались на блогера {username}!')
        return redirect(url_for('main.user', username=username))

    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()

        if not user:
            flash(f'Блогер {username} не найден!')
            return redirect(url_for('main.index'))

        if user == current_user:
            flash('Невозможно отписаться от себя!')
            return redirect(url_for('main.user', username=username))

        current_user.unfollow(user)
        db.session.commit()
        flash(f'Вы отписались от блогера {username}')
        return redirect(url_for('main.user', username=username))

    else:
        return redirect(url_for('main.index'))

from groove import app, db
from flask import render_template, request, url_for, flash, session, redirect
from groove.models import Song, User, Playlist, Genre, Album
from sqlalchemy import or_, func
from datetime import datetime


@app.template_filter('format_duration')
def format_duration(duration):
    minutes = int(duration)
    seconds = int((duration - minutes) * 60)
    return f"{minutes:02d}:{seconds:02d}"


@app.route('/')
def start_page():
    return render_template('index.html')


@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def register_form():
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    if username == '' or email == '' or password == '':
        flash('Fields cannot be empty.')
        return redirect(url_for('register_page'))
    if User.query.filter_by(username=username).first() or username == 'admin':
        flash('Username not available')
        return redirect(url_for('register_page'))
    if User.query.filter_by(email=email).first():
        flash('Email already in use.')
        return redirect(url_for('register_page'))

    new_user = User(username=username, email=email)
    new_user.generate_password(password)
    db.session.add(new_user)
    db.session.commit()

    flash('Account creation successful. Please login to continue.')
    return redirect(url_for('login_page'))


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_form():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    if username == '' or password == '':
        flash('Enter both username and password to login.')
        return redirect(url_for('login_page'))
    if not user:
        flash('Username does not exist.')
        return redirect(url_for('login_page'))
    if not user.check_password(password):
        flash('Password is incorrect.')
        return redirect(url_for('login_page'))

    session['id'] = user.id
    return redirect(url_for('user_home_page'))


@app.route('/user_home')
def user_home_page():
    if 'id' not in session:
        flash('Login to continue.')
        return redirect(url_for('login_page'))
    songs = Song.query.order_by(func.random()).limit(4).all()
    playlists = Playlist.query.filter_by(user_id=session['id']).limit(4)
    genre = Genre.query.order_by(func.random()).first()
    genre_songs = Song.query.filter_by(genre_id=genre.id)
    return render_template('user_home.html',
                           songs=songs,
                           playlists=playlists,
                           genre=genre,
                           genre_songs=genre_songs,
                           user=User.query.get(session['id']))


@app.route('/user_home', methods=['POST'])
def search_page():
    if 'id' not in session:
        flash('Login to continue.')
        return redirect(url_for('login_page'))
    search = request.form.get('search')
    if search is None or search == '':
        return redirect(url_for('user_home_page'))
    songs = Song.query.filter(
        or_(
            Song.name.ilike('%' + search + '%'),
            Song.artist.ilike('%' + search + '%')
            )
        ).all()
    albums = Album.query.filter(
        or_(
            Album.name.ilike('%' + search + '%'),
            Album.artist.ilike('%' + search + '%'),
            )
        ).all()
    return render_template('search.html', songs=songs, albums=albums)


@app.route('/creator_register')
def creator_register_page():
    return render_template('creator_register.html')


@app.route('/creator_register', methods=['POST'])
def creator_register_form():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()

    if username == '' or email == '' or password == '':
        flash('Fields cannot be empty.')
        return redirect(url_for('creator_register_page'))

    if user:
        if email != user.email:
            flash('Email does not match. Please enter the email that you have already registered with Groove')
            return redirect(url_for('creator_register_page'))
        if not user.check_password(password):
            flash('Incorrect Password entered.')
            return redirect(url_for('creator_register_page'))

        user.role_id = 2
        db.session.commit()
        flash('Successfully registered as a creator')
        return redirect(url_for('creator_home_page'))
    else:
        flash('Incorrect Username. Please enter the username that you have already registered with Groove.')
        return redirect(url_for('creator_register_page'))


@app.route('/creator_home')
def creator_home_page():
    if 'id' in session:
        creator = session['id']
    else:
        flash('Login to continue')
        return redirect(url_for('login_page'))
    return render_template('creator_home.html',
                           total_songs_uploaded=len(Song.query.filter(Song.creator == creator).all()),
                           average_rating=4.2,
                           total_albums=len(Album.query.filter(Album.creator == creator).all()),
                           songs=Song.query.filter(Song.creator == creator).all())


@app.route('/creator_home', methods=['POST'])
def creator_home_upload():
    name = request.form['title']
    artist = request.form['artist']
    genre_name = request.form['genre']
    date_uploaded = request.form['releaseDate']
    date_uploaded = datetime.strptime(date_uploaded, '%Y-%m-%d').date()
    lyrics = request.form['lyrics']
    genre = Genre.query.filter_by(name=genre_name).first()
    new_song = Song(name=name, artist=artist, date_uploaded=date_uploaded,
                    lyrics=lyrics, genre_id=genre.id, creator=session['id'])
    db.session.add(new_song)
    db.session.commit()
    flash('Song successfully added.')
    return redirect(url_for('creator_home_page'))


@app.route('/delete_song/<int:song_id>')
def delete_song_page(song_id):
    return render_template('delete_song.html', song=Song.query.filter_by(id=song_id).first())


@app.route('/delete_song/<int:song_id>', methods=['POST'])
def delete_song_post(song_id):
    song = Song.query.get(song_id)
    db.session.delete(song)
    db.session.commit()
    flash('Song successfully deleted.')
    return redirect(url_for('creator_home_page'))


@app.route('/view_playlists')
def playlists_page():
    if 'id' not in session:
        flash('Login to continue.')
        return redirect(url_for('login_page'))
    user = User.query.filter_by(id=session['id']).first()
    playlists = Playlist.query.filter_by(user_id=user.id)
    return render_template('view_playlist.html', playlists=playlists, user=user)

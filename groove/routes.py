from groove import app, db
from flask import render_template, request, url_for, flash, session, redirect
from groove.models import Song, User, Playlist, Genre, Album, SongRating, PlaylistSong
from sqlalchemy import or_, func
from datetime import datetime
from matplotlib import pyplot as plt


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
    songs = Song.query.filter(Song.flag == 0).order_by(func.random()).limit(4).all()
    playlists = Playlist.query.filter_by(user_id=session['id']).limit(4)
    genre = Genre.query.order_by(func.random()).first()
    genre_songs = Song.query.filter_by(genre_id=genre.id)
    albums = Album.query.order_by(func.random()).limit(4).all()
    return render_template('user_home.html',
                           songs=songs,
                           playlists=playlists,
                           genre=genre,
                           genre_songs=genre_songs,
                           user=User.query.get(session['id']),
                           albums=albums)


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
            Song.artist.ilike('%' + search + '%'),
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
                           average_rating=1,
                           total_albums=len(Album.query.filter(Album.creator == creator).all()),
                           songs=Song.query.filter(Song.creator == creator, Song.flag == 0).all(),
                           albums=Album.query.filter(Album.creator == creator).all())


@app.route('/creator_home', methods=['POST'])
def creator_home_upload():
    upload = request.form['upload']
    if upload == 'song':
        song_name = request.form['songTitle']
        song_artist = request.form['songArtist']
        genre_name = request.form['genre']
        song_date_uploaded = request.form['songReleaseDate']
        song_date_uploaded = datetime.strptime(song_date_uploaded, '%Y-%m-%d').date()
        lyrics = request.form['lyrics']
        genre = Genre.query.filter_by(name=genre_name).first()
        new_song = Song(name=song_name, artist=song_artist, date_uploaded=song_date_uploaded,
                        lyrics=lyrics, genre_id=genre.id, creator=session['id'])
        db.session.add(new_song)
        db.session.commit()
        flash('Song successfully added.')
    elif upload == 'album':
        album_name = request.form['albumTitle']
        album_artist = request.form['albumArtist']
        album_release_date = request.form['albumReleaseDate']
        album_release_date = datetime.strptime(album_release_date, '%Y-%m-%d').date()
        album_songs = request.form.getlist('albumSongs')
        new_album = Album(name=album_name, artist=album_artist, release_date=album_release_date, creator=session['id'])
        db.session.add(new_album)
        db.session.commit()
        for song_id in album_songs:
            song = Song.query.get(song_id)
            if song:
                new_album.songs.append(song)
        db.session.commit()
        flash('Album Successfully added.')
    return redirect(url_for('creator_home_page'))


@app.route('/delete_song/<int:song_id>')
def delete_song_page(song_id):
    return render_template('delete_song.html', song=Song.query.get(song_id),
                           user=User.query.filter_by(id=session['id']).first())


@app.route('/delete_song/<int:song_id>', methods=['POST'])
def delete_song_post(song_id):
    song = Song.query.get(song_id)
    user = User.query.filter_by(id=session['id']).first()
    db.session.delete(song)
    db.session.commit()
    flash('Song successfully deleted.')
    if user.role.name == 'creator':
        return redirect(url_for('creator_home_page'))
    elif user.role.name == 'admin':
        return redirect(url_for('admin_home_page'))


@app.route('/view_playlists')
def playlists_page():
    if 'id' not in session:
        flash('Login to continue.')
        return redirect(url_for('login_page'))
    user = User.query.filter_by(id=session['id']).first()
    playlists = Playlist.query.filter_by(user_id=user.id)
    return render_template('view_playlist.html', playlists=playlists, user=user)


@app.route('/create_playlist')
def create_playlist_page():
    if 'id' not in session:
        flash('Login to continue.')
        return redirect(url_for('login_page'))
    songs = Song.query.filter(Song.flag == 0).order_by(func.random()).limit(7).all()
    user = User.query.filter_by(id=session['id']).first()
    return render_template('create_playlist.html', songs=songs, user=user)


@app.route('/create_playlist', methods=['POST'])
def create_playlist_post():
    song_ids = request.form.getlist('song')
    playlist_name = request.form['playlist_name']
    description = request.form['description']

    playlist = Playlist(user_id=session['id'], name=playlist_name, description=description)
    db.session.add(playlist)
    db.session.commit()

    for song_id in song_ids:
        song = Song.query.get(song_id)
        if song:
            playlist.songs.append(song)
    db.session.commit()
    return redirect(url_for('playlists_page'))


@app.route('/delete_album/<int:album_id>')
def delete_album_page(album_id):
    return render_template('delete_album.html', album=Album.query.get(album_id))


@app.route('/delete_album/<int:album_id>', methods=['POST'])
def delete_album_post(album_id):
    album = Album.query.get(album_id)
    db.session.delete(album)
    db.session.commit()
    flash('Album successfully deleted.')
    return redirect(url_for('creator_home_page'))


@app.route('/user_home/rate/<int:song_id>', methods=['POST'])
def rate_page(song_id):
    rating = request.form['rating']
    if rating:
        rating = SongRating(rating=rating, song_id=song_id, user_id=session['id'])
        db.session.add(rating)
        db.session.commit()
    return redirect(url_for('user_home_page'))


@app.route('/admin_dashboard')
def admin_home_page():
    genre_chart()
    return render_template('admin_home.html')


@app.route('/creator_home/edit_song/<int:song_id>', methods=['POST'])
def edit_song_page(song_id):
    song = Song.query.get(song_id)
    if request.form['songTitle']:
        name = request.form['songTitle']
        song.name = name
    if request.form['songArtist']:
        artist = request.form['songArtist']
        song.artist = artist
    if request.form['genre']:
        genre = request.form['genre']
        song.genre_id = Genre.query.filter_by(name=genre).first().id
    if request.form['SongReleaseDate']:
        release_date = request.form['SongReleaseDate']
        song.date_uploaded = datetime.strptime(release_date, '%Y-%m-%d').date()
    if request.form['lyrics']:
        lyrics = request.form['lyrics']
        song.lyrics = lyrics
    db.session.commit()
    return redirect(url_for('creator_home_page'))


@app.route('/creator_home/edit_album/<int:album_id>', methods=['POST'])
def edit_album_page(album_id):
    album = Album.query.get(album_id)
    if request.form['albumTitle']:
        name = request.form['albumTitle']
        album.name = name
    if request.form['albumArtist']:
        artist = request.form['albumArtist']
        album.artist = artist
    if request.form['AlbumReleaseDate']:
        release_date = request.form['AlbumReleaseDate']
        album.date_uploaded = datetime.strptime(release_date, '%Y-%m-%d').date()
    if request.form.getlist('album_songs'):
        album_songs = request.form.getlist('albumSongs')
        album.songs.clear()
        for song_id in album_songs:
            song = Song.query.get(song_id)
            if song:
                album.songs.append(song)
    db.session.commit()
    return redirect(url_for('creator_home_page'))


@app.route('/view_playlists/<int:playlist_id>')
def playlist_songs_page(playlist_id):
    user = User.query.get(session['id'])
    playlist = Playlist.query.get(playlist_id)
    playlist_songs = PlaylistSong.query.filter_by(playlist_id=playlist.id).all()
    song_id_list = [song.song_id for song in playlist_songs]
    songs = Song.query.filter(Song.id.in_(song_id_list), Song.flag == 0).all()
    return render_template('playlist_songs.html', user=user, playlist=playlist, songs=songs)


@app.route('/logout')
def logout():
    session.pop('id')
    return redirect(url_for('start_page'))


@app.route('/admin_login')
def admin_login_page():
    return render_template('admin_login.html')


@app.route('/admin_login', methods=['POST'])
def admin_login_form():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username, role_id=3).first()
    if username == '' or password == '':
        flash('Enter both username and password to login.')
        return redirect(url_for('admin_login_page'))
    if not user:
        flash('Username does not exist.')
        return redirect(url_for('admin_login_page'))
    if not user.check_password(password):
        flash('Password is incorrect.')
        return redirect(url_for('admin_login_page'))

    session['id'] = user.id
    return redirect(url_for('admin_home_page'))


@app.route('/admin_tracks')
def admin_tracks_page():
    genres = Genre.query.all()
    return render_template('admin_tracks.html', genres=genres)


@app.route('/flag_song/<int:song_id>', methods=['GET', 'POST'])
def flag_song(song_id):
    song = Song.query.get(song_id)
    song.flag = not song.flag
    db.session.commit()
    return redirect(url_for('admin_tracks_page'))


@app.route('/admin_users')
def admin_users_page():
    users = User.query.filter_by(role_id=1).all()
    creators = User.query.filter_by(role_id=2).all()
    return render_template('admin_users.html', users=users, creators=creators)


@app.route('/blacklist_user/<int:user_id>')
def blacklist_user(user_id):
    user = User.query.get(user_id)
    user.blacklist = not user.blacklist
    db.session.commit()
    return redirect(url_for('admin_users_page'))


def genre_chart():
    genre_songs = db.session.query(Genre.name, db.func.count(Song.id)).join(Song).group_by(Genre.name).all()
    genres = [genre[0] for genre in genre_songs]
    song_count = [song[1] for song in genre_songs]
    plt.pie(song_count, labels=genres)
    plt.title('Genre Pie Chart')
    plt.savefig('C:/Users/DELL/Desktop/Groove/groove/static/genre_pie_chart.png')

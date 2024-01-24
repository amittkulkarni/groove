from groove import db
from werkzeug.security import generate_password_hash, check_password_hash


class Song(db.Model):
    __tablename__ = 'song'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    creator = db.Column(db.Integer, nullable=False)
    lyrics = db.Column(db.Text, nullable=True)
    duration = db.Column(db.Float, nullable=False, default=3.12)
    date_uploaded = db.Column(db.Date, nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'), nullable=False)
    artist = db.Column(db.String(255), nullable=False)
    rating = db.relationship('SongRating', backref='song', lazy=True)
    times_played = db.Column(db.Integer, default=0, nullable=False)
    flag = db.Column(db.Boolean, default=0)

    def increment_count(self):
        self.times_played += 1
        db.session.commit()

    def average_song_rating(self):
        average = db.session.query(db.func.avg(SongRating.rating)).filter(SongRating.song_id == self.id).scalar()
        if average is None:
            return None
        else:
            return round(average, 1)


class Album(db.Model):
    __tablename__ = 'album'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    release_date = db.Column(db.Date, nullable=False)
    creator = db.Column(db.Integer, nullable=False)
    artist = db.Column(db.String(255), nullable=False)
    songs = db.relationship('Song', backref='album', lazy=True)
    flag = db.Column(db.Boolean, default=0)


class Playlist(db.Model):
    __tablename__ = 'playlist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    songs = db.relationship('Song', secondary='playlist_song', backref=db.backref('playlist', lazy='dynamic'))


class PlaylistSong(db.Model):
    __tablename__ = 'playlist_song'
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), primary_key=True)


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    songs = db.relationship('Song', backref='genre', lazy=True)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hashed = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), default=1, nullable=False)
    playlists = db.relationship('Playlist', backref='user', lazy=True)
    blacklist = db.Column(db.Boolean, default=0)

    def generate_password(self, password):
        self.password_hashed = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hashed, password)


class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    users = db.relationship('User', backref='role', lazy=True)


class SongRating(db.Model):
    __tablename__ = 'rating'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)

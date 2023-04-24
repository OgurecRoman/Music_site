from PIL import Image
import requests
import os
from flask import Flask, render_template, redirect, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session
from data.users import User
from data.songs import Songs
from data.bands import Bands
from forms.register import RegisterForm
from forms.login import LoginForm
from forms.song import SongForm
from forms.band import BandForm
from forms.user import UserForm

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


def get_size(fname, a):  # приводит изображение к заданному размеру
    im = Image.open(fname)
    width, height = im.size
    k = width / height
    new_im = im.resize((a, int(a / k)))
    new_im.save(fname)


def get_map(adress, id):  # получает адрес и сохраняет картинку с расположением магазина
    link = 'https://geocode-maps.yandex.ru/1.x'
    data = {'geocode': adress.replace(' ', '+'),
            'apikey': '40d1649f-0493-4b70-98ba-98533de7710b',
            'format': 'json'}
    coords = ','.join(
        requests.get(link, params=data).json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject'][
            'Point']['pos'].split())

    search_api_server = "https://search-maps.yandex.ru/v1/"
    search_params = {
        "apikey": 'dda3ddba-c9ea-4ead-9010-f43fbc15c6e3',
        "text": "музыкальный магазин",
        "lang": "ru_RU",
        "ll": coords,
        "type": "biz"}

    response = requests.get(search_api_server, params=search_params).json()

    organization = response["features"][0]
    org_name = organization["properties"]["CompanyMetaData"]["name"]
    org_address = organization["properties"]["CompanyMetaData"]["address"]

    point = organization["geometry"]["coordinates"]
    org_point = "{0},{1}".format(point[0], point[1])
    delta = "0.02"

    # Собираем параметры для запроса к StaticMapsAPI:
    map_params = {
        "ll": coords,
        "spn": ",".join([delta, delta]),
        "l": "map",
        "pt": "{0},org".format(org_point)
    }

    map_api_server = "http://static-maps.yandex.ru/1.x/"
    response = requests.get(map_api_server, params=map_params)

    map_file = f"static/img/maps/{id}.png"
    with open(map_file, "wb") as file:
        file.write(response.content)
    return org_name, org_address


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        songs = db_sess.query(Songs).filter(
            (Songs.user == current_user) | (Songs.is_private != True)).order_by(Songs.count_likes.desc())
        name = f'static/favorites/{current_user.id}.txt'
        if os.path.isfile(name):
            with open(name, 'r', encoding='utf-8') as f:
                nums = list(map(int, f.readlines()))
        else:
            with open(name, 'w', encoding='utf-8') as f:
                f.write('')
            nums = []
    else:
        songs = db_sess.query(Songs).filter(Songs.is_private != True).order_by(Songs.count_likes.desc())
        nums = []
    return render_template("index.html", songs=songs, nums=nums)


@app.route("/bands")
def bands():
    db_sess = db_session.create_session()
    bands = db_sess.query(Bands).order_by(Bands.name)
    return render_template("list_bands.html", bands=bands)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/profile/<int:id>', methods=['GET', 'POST'])
def profile(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    if user == current_user:
        form = UserForm()
        if request.method == "GET":
            form.name.data = user.name
            form.about.data = user.about
            form.adress.data = user.adress
        if form.validate_on_submit():
            user.name = form.name.data
            user.about = form.about.data
            if user.adress != form.adress.data:
                user.org_name, user.org_adress = get_map(form.adress.data, id)
            user.adress = form.adress.data
            db_sess.commit()
            return redirect(f'/profile/{id}')
        if request.method == 'POST':
            f = request.files['file']
            if f:
                name = f'static/img/users/{id}.png'
                f.save(name)
                get_size(name, 200)
                user.photo = '/' + name
            db_sess.commit()
            return redirect(f'/profile/{id}')
        return render_template('profile.html', form=form, user=user)
    else:
        return render_template('profile.html', user=user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/add_songs', methods=['GET', 'POST'])
@login_required
def add_song():
    form = SongForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        song = Songs()
        song.name = form.name.data
        band = form.band.data
        song.band_id = band.id
        text = form.chords.data
        with open(f'static/chords/{band.name}-{form.name.data}.txt', 'w', encoding='utf-8') as f:
            f.writelines(text.split('\n'))

        song.chords = f'static/chords/{band.name}-{form.name.data}.txt'
        song.user_id = current_user.id
        song.is_private = form.is_private.data
        current_user.songs.append(song)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('songs.html', title='Добавление композиции',
                           form=form)


@app.route('/edit_songs/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_songs(id):
    form = SongForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        song = db_sess.query(Songs).filter(Songs.id == id,
                                           (Songs.user == current_user) | (current_user.id == 1)).first()
        if song:
            form.name.data = song.name
            form.band.data = song.band
            print(form.band.data)

            if song.chords:
                with open(song.chords, 'r', encoding='utf-8') as f:
                    text = f.read()
            else:
                text = ''
            form.chords.data = text
            form.is_private.data = song.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        song = db_sess.query(Songs).filter(Songs.id == id,
                                           (Songs.user == current_user) | (current_user.id == 1)).first()
        if song:
            song.name = form.name.data
            band = form.band.data
            song.band_id = band.id
            text = form.chords.data
            with open(f'static/chords/{band.name}-{form.name.data}.txt', 'w+', encoding='utf-8') as f:
                f.writelines(text.split('\n'))

            song.chords = f'static/chords/{band.name}-{form.name.data}.txt'
            song.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('songs.html',
                           title='Редактирование композиции',
                           form=form)


@app.route('/songs_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def songs_delete(id):
    db_sess = db_session.create_session()
    song = db_sess.query(Songs).filter(Songs.id == id,
                                       (Songs.user == current_user) | (current_user.id == 1)).first()
    if song:
        os.remove(song.chords)
        db_sess.delete(song)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/song/<int:id>')
def page_song(id):
    db_sess = db_session.create_session()
    song = db_sess.query(Songs).filter(Songs.id == id).first()
    text = open(song.chords, encoding='utf-8').readlines()
    return render_template('page_song.html', title='Страница композиции',
                           song=song, text=text)


@app.route('/add_bands', methods=['GET', 'POST'])
@login_required
def add_band():
    form = BandForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        band = Bands()
        band.name = form.name.data

        with open(f'static/biographies/{form.name.data}.txt', 'w', encoding='utf-8') as f:
            f.write(form.biography.data)

        band.biography = f'static/biographies/{form.name.data}.txt'
        band.user_id = current_user.id
        band.is_private = form.is_private.data
        current_user.bands.append(band)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('bands.html', title='Добавление исполнителя',
                           form=form)


@app.route('/edit_bands/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_bands(id):
    form = BandForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        band = db_sess.query(Bands).filter(Bands.id == id,
                                           (Bands.user == current_user) | (current_user.id == 1)).first()
        if band:
            form.name.data = band.name
            with open(band.biography, 'r', encoding='utf-8') as f:
                text = f.read()
            form.biography.data = text
            form.is_private.data = band.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        band = db_sess.query(Bands).filter(Bands.id == id,
                                           (Bands.user == current_user) | (current_user.id == 1)).first()
        if band:
            band.name = form.name.data
            text = form.biography.data
            with open(f'static/biographies/{form.name.data}.txt', 'w+', encoding='utf-8') as f:
                f.writelines(text.split('\n'))

            band.biography = f'static/biographies/{form.name.data}.txt'
            band.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('bands.html',
                           title='Редактирование исполнителя',
                           form=form)


@app.route('/bands_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def bands_delete(id):
    db_sess = db_session.create_session()
    band = db_sess.query(Bands).filter(Bands.id == id,
                                       (Bands.user == current_user) | (current_user.id == 1)).first()
    if band:
        songs = db_sess.query(Songs).filter(Songs.band_id == band.id)
        for song in songs:
            os.remove(song.chords)
            db_sess.delete(song)
        os.remove(band.biography)
        db_sess.delete(band)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/band/<int:id>')
def page_band(id):
    db_sess = db_session.create_session()
    band = db_sess.query(Bands).filter(Bands.id == id).first()
    songs = db_sess.query(Songs).filter(Songs.band_id == id)
    text = open(band.biography, encoding='utf-8').readlines()
    return render_template('page_band.html', title='Страница исполнителя',
                           band=band, songs=songs, text=text)


@app.route('/add_favorites/<int:id>')
def add_favorites(id):
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        song = db_sess.query(Songs).filter(Songs.id == id).first()
        name = f'static/favorites/{current_user.id}.txt'
        nums = list(map(lambda x: x.strip(), open(name).readlines()))
        if str(id) in nums:
            nums.pop(nums.index(str(id)))
            song.count_likes -= 1
        else:
            nums.append(str(id))
            song.count_likes += 1
        with open(name, 'w', encoding='utf-8') as f:
            f.write('\n'.join(nums))
        db_sess.commit()
    return redirect('/')


@app.route('/favorites', methods=['GET', 'POST'])
@login_required
def favorites():
    db_sess = db_session.create_session()
    name = f'static/favorites/{current_user.id}.txt'
    with open(name, 'r', encoding='utf-8') as f:
        nums = list(map(int, f.readlines()))
    songs = db_sess.query(Songs).filter(Songs.id.in_(nums))
    return render_template("favorites.html", songs=songs)


def main():
    app.run()


if __name__ == '__main__':
    db_session.global_init("db/music.db")
    main()

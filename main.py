from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

tmdb_api_key = "fdcfd4b5127c6f5b41a2b72d880a11d2"
tmdb_search_endpoint = "https://api.themoviedb.org/3/search/movie"
# tmdb_movie_endpoint = f"https://api.themoviedb.org/3/movie/{movie_id}"


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYzckEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie-collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description  = db.Column(db.String(500), nullable=False)
    rating  = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

    #Optional: this will allow each book object to be identified by its title when printed.
    def __repr__(self):
        return f'<Movie {self.title}>'

# db.create_all()

# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg")
# db.session.add(new_movie)
# db.session.commit()

class RatingReviewForm(FlaskForm):
    rating_field = StringField('Your Rating Out of 10 e.g. 7.5 ', validators=[DataRequired()])
    review_field = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField(label='Submit')

class MovieForm(FlaskForm):
    title_field = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField(label='Add Movie')

@app.route("/")
def home():

    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)

@app.route("/add", methods=['GET', 'POST'])
def add():
    form = MovieForm()

    if form.validate_on_submit():
        movie_title = form.title_field.data
        search_params = {
            "api_key": tmdb_api_key,
            "query": movie_title,
        }
        response = requests.get(tmdb_search_endpoint, params=search_params)
        response.raise_for_status()
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)

@app.route("/select")
def select():
    movie_id = request.args.get("id")
    movie_params = {
        "api_key": tmdb_api_key
    }
    response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}", params=movie_params)
    response.raise_for_status()
    movie_data = response.json()
    add_movie = Movie(
        title=movie_data["original_title"],
        year=movie_data["release_date"].split("-")[0],
        description=movie_data["overview"],
        img_url=f'https://www.themoviedb.org/t/p/w600_and_h900_bestv2{movie_data["poster_path"]}'
    )
    db.session.add(add_movie)
    db.session.commit()
    return redirect(url_for('rate_movie', id=add_movie.id))

@app.route("/edit", methods=['GET', 'POST'])
def rate_movie():
    form = RatingReviewForm()
    movie_id = request.args.get('id')
    movie_selected = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie_selected.rating = form.rating_field.data
        movie_selected.review = form.review_field.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie_selected, form=form)

@app.route("/delete")
def delete_movie():
    movie_id = request.args.get('id')
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)

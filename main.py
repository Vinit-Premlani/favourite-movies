from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Integer, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ecac0342befc610c9e83c3c6b633d523'
Bootstrap5(app)


app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///Movies-collection.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy()
db.init_app(app)


class Movie(db.Model):
    id = Column(Integer,primary_key=True)
    title = Column(String(250),nullable=False, unique=True)
    year = Column(Integer,nullable=False)
    description = Column(String(500),nullable=False)
    rating = Column(Float,nullable=True)
    ranking = Column(Integer,nullable=True)
    review = Column(String(250),nullable=True)
    img_url =  Column(String(250),nullable=False)

with app.app_context():
    db.create_all()

class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")

class AddMovieForm(FlaskForm):
    movieTitle = StringField("Movie name")
    submit = SubmitField("Add Movie")


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)

@app.route("/delete", methods=["GET", "POST"])
def delete_movie():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie,movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = AddMovieForm()
    
    if form.validate_on_submit():
        movie_title = form.movieTitle.data
        response = requests.get('https://api.themoviedb.org/3/search/movie', params={"api_key": app.config['SECRET_KEY'], "query": movie_title})
        print("This is Response",response.json())
        data = response.json()["results"]
        return render_template("select.html", options=data)    
    return render_template("add.html", form=form)

@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"https://api.themoviedb.org/3/movie/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": app.config['SECRET_KEY'], "language": "en-US"})
        data = response.json()
        MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
        new_movie = Movie(
            title = data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"])

        db.session.add(new_movie)
        db.session.commit()

        return redirect(url_for("rate_movie",id=new_movie.id))
    
if __name__ == '__main__':
    app.run(debug=True)

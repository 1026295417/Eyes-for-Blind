# @Author      : 'Savvy'
# @Created_date: 2018/12/5 3:54 PM

import os
from flask import Flask, render_template
from src.database import Database
from src.models.locations.views import location_blueprint
from src.models.visions.views import vision_blueprint

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.config.from_object('src.config')
app.secret_key = "123"
app.register_blueprint(location_blueprint, url_prefix="/locations")
app.register_blueprint(vision_blueprint, url_prefix="/visions")


@app.before_first_request
def init_db():
    Database.initialize()


@app.route('/')
def home():
    return render_template("home.jinja2")


app.run(host='0.0.0.0', debug=app.config['DEBUG'], port=5050)

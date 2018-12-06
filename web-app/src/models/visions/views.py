# @Author      : 'Savvy'
# @Created_date: 2018/12/5 4:44 PM

from flask import request, Response, render_template, Blueprint
from src.models.locations.location import Location
from src.models.visions.vision import Vision
import jsonpickle
import datetime
import base64
import pytz

vision_blueprint = Blueprint('visions', __name__)


# route http posts to this method
@vision_blueprint.route('/save_img', methods=['POST'])
def save_image():
    # convert string of image data to uint8

    encoded_string = base64.b64encode(request.data)

    vision = Vision(encoded_string)
    vision.save_to_db()

    # build a response dict to send back to client
    response = {'message': 'image received...'}
    # encode response using jsonpickle
    response_pickled = jsonpickle.encode(response)

    return Response(response=response_pickled, status=200, mimetype="application/json")


@vision_blueprint.route('/view', methods=['GET', 'POST'])
def view():
    if request.method == 'POST':
        raw_time = request.form['timeThreshold']
        time = datetime.datetime.strptime(raw_time, '%m/%d/%y %H:%M:%S')
    else:
        time = datetime.datetime.now(pytz.timezone('US/Eastern'))
    vision = Vision.find_latest_before_time(time)
    location = Location.find_latest_before_time(time)
    tmp = "data:image/jpeg;base64,"+str(vision.image)
    imgStr = tmp[:23] + tmp[25:-1]
    if vision is None or location is None:
        return render_template()

    return render_template("visions/view_image.jinja2", image=imgStr, location=location)
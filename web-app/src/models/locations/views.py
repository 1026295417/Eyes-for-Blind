# @Author      : 'Savvy'
# @Created_date: 2018/12/5 4:44 PM

from flask import Flask, request, Response, Blueprint
from src.models.locations.location import Location
import json
import jsonpickle

location_blueprint = Blueprint('locations', __name__)


@location_blueprint.route('/save_loc', methods=['POST'])
def save_location():
    # convert string of image data to uint8
    coord_data = json.loads(request.data.decode('utf-8'))
    print(coord_data)

    loc = Location(coord_data)
    print(loc.time)
    loc.save_to_db()

    # build a response dict to send back to client
    response = {'message': 'location info received...'}
    # encode response using jsonpickle
    response_pickled = jsonpickle.encode(response)

    return Response(response=response_pickled, status=200, mimetype="application/json")

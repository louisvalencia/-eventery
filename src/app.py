import json
from db import db
from flask import Flask, request
from db import User
from db import Event
from db import Category
import os
import users_dao
import datetime 
# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
import sendgrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)
db_filename = "cms.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()

def success_response(data, code=200):
    """
    Helper function for outputting success data
    """
    return json.dumps(data, default=str), code

def failure_response(message, code=404):
    """
    Helper function for outputting error message
    """
    return json.dumps({"error": message}), code
  
def extract_token(request):
    """
    Helper function that extracts the token from the header of a request
    """
    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        return False, json.dumps({"error": "Missing auth header"}), 404

    bearer_token = auth_header.replace("Bearer", "").strip()
    if not bearer_token: 
        return False, json.dumps({"error": "Invalid auth header"})
    return True, bearer_token



@app.route("/")
def hello():
    """
    Endpoint for printing welcome message!
    """
    return json.dumps({"message": "Hi, welcome to Eventery!"})

# -- EVENT ROUTES ------------------------------------------------------
  
@app.route("/api/events/")
def get_events():
    """
    Endpoint for getting all events
    """
    events = [event.serialize() for event in Event.query.all()]
    return success_response({"events": events})

@app.route("/api/events/", methods=["POST"])
def create_event():
    """
    Endpoint for creating a new event
    """
    body = json.loads(request.data)

    host_email = body.get("host_email")

    if not body.get("title"):
        return failure_response("Missing title field in the body", 400)
    elif not body.get("address"):
        return failure_response("Missing address field in the body", 400)
    elif not body.get("start"):
        return failure_response("Missing start field in the body", 400)
    elif not body.get("end"):
        return failure_response("Missing end field in the body", 400)
    elif not body.get("description"):
        return failure_response("Missing description field in the body", 400)
    elif not body.get("host"):
        return failure_response("Missing host field in the body", 400)
    elif not host_email:
        return failure_response("Missing host_email field in the body", 400)
    elif body.get("free") is None:
        return failure_response("Missing free field in the body", 400)
    elif not body.get("category"):
        return failure_response("Missing category field in the body", 400)

    new_event = Event(
        title = body.get("title"),
        address = body.get("address"),
        start = body.get("start"),
        end = body.get("end"),
        description = body.get("description"),
        host = body.get("host"),
        host_email = body.get("host_email"),
        free = body.get("free"),
        category = body.get("category")
    )

    db.session.add(new_event)
    db.session.commit()

    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    data = {
    "personalizations": [
        {
        "to": [
            {
            "email": host_email
            }
        ],
        "subject": "Eventery Notification"
        }
    ],
    "from": {
        "email": "louissean12@gmail.com"
    },
    "content": [
        {
        "type": "text/plain",
        "value": "You received the following notification from eventery: https://drive.google.com/file/d/1r_g9LWH-_McHuVXuEwn9RXNUEq8Voxt6/view?usp=sharing"
        }
    ]
    }
    response = sg.client.mail.send.post(request_body=data)
    print(response.status_code)
    print(response.body)
    print(response.headers)

    return success_response(new_event.serialize(), 201)


@app.route("/api/events/<int:event_id>/")
def get_event(event_id):
    """
    Endpoint for getting an event by id
    """
    event = Event.query.filter_by(id = event_id).first()
    if event is None:
        return failure_response("Event not found!")
    return success_response(event.serialize())


@app.route("/api/events/<int:event_id>/", methods=["DELETE"])
def delete_event(event_id):
    """
    Endpoint for deleting an event by id
    """
    event = Event.query.filter_by(id = event_id).first()
    if event is None:
        return failure_response("Event not found!")
    db.session.delete(event)
    db.session.commit()
    return success_response(event.serialize())

@app.route("/api/events/category/<string:category>/")
def get_events_by_category(category):
    """
    Endpoint for getting Events by Category name
    """
    events = Event.query.filter_by(category = category)

    if events is None:
      return success_response({"message": "No events in this category found"})
    
    events_serialized = []

    for row in events:
      events_serialized.append(row.serialize())

    return success_response(events_serialized)

@app.route("/api/events/host/<string:host_query>/")
def get_events_by_host(host_query):
    """
    Endpoint for getting Events by email
    """
    new_host = host_query.replace("-", " ")
    events = Event.query.filter_by(host = new_host)

    if events is None:
      return success_response({"message": "You have no created events"})
    
    events_serialized = []

    for row in events:
      events_serialized.append(row.serialize())

    return success_response(events_serialized)

@app.route("/api/events/day/<string:day>/")
def get_events_by_day(day):
    """
    Endpoint for getting Events by day (YYYY-MM-DD) format
    """
    events = []

    for event in Event.query.all():
      if event.start.strftime('%Y-%m-%d') == day:
        events.append(event)

    if len(events) == 0:
      return success_response({"message": "No events for this day"})
    
    events_serialized = []

    for row in events:
      events_serialized.append(row.serialize())

    return success_response(events_serialized)

# -- USER ROUTES ---------------------------------------------------
@app.route("/api/users/")
def get_users():
    """
    Endpoint for getting all users
    """
    users = [user.serialize() for user in User.query.all()]
    return success_response({"users": users})

@app.route("/api/users/<int:user_id>/")
def get_user(user_id):
    """
    Endpoint for getting a user by id
    """
    user = User.query.filter_by(id = user_id).first()
    if user is None:
        return failure_response("User not found!")
    return success_response(user.serialize())

@app.route("/api/users/<int:user_id>/", methods=["DELETE"])
def delete_user(user_id):
    """
    Endpoint for deleting a user by id
    """
    user = User.query.filter_by(id = user_id).first()
    if user is None:
        return failure_response("User not found!")
    db.session.delete(user)
    db.session.commit()
    return success_response(user.serialize())



# -- Category ROUTES ---------------------------------------------------
@app.route("/api/categories/")
def get_categories():
    """
    Endpoint for getting all Categories
    """
    categories = [category.serialize() for category in Category.query.all()]
    return success_response({"categories": categories})

@app.route("/api/categories/", methods=["POST"])
def create_category():
    """
    Endpoint for creating a new Category
    """
    body = json.loads(request.data)

    if not body.get("name"):
        return failure_response("Missing name field in the body", 400)

    new_category = Category(
        name = body.get("name"),
    )

    db.session.add(new_category)
    db.session.commit()
    return success_response(new_category.serialize(), 201)


@app.route("/api/categories/<int:category_id>/")
def get_category_by_id(category_id):
    """
    Endpoint for getting a Category by id
    """
    category = Category.query.filter_by(id = category_id).first()
    if category is None:
        return failure_response("Category not found!")
    return success_response(category.serialize())


@app.route("/api/categories/<int:category_id>/", methods=["DELETE"])
def delete_category(category_id):
    """
    Endpoint for deleting a Category by id
    """
    category = Category.query.filter_by(id = category_id).first()
    if category is None:
        return failure_response("Category not found!")
    db.session.delete(category)
    db.session.commit()
    return success_response(category.serialize())
  

@app.route("/api/events/<int:event_id>/category/", methods=["POST"])
def assign_category(event_id):
    """
    Endpoint for assigning a Category to an Event by id
    """

    event = Event.query.filter_by(id=event_id).first()
    if event is None:
        return failure_response("Event not found")
    body = json.loads(request.data)
    name = body.get("name")

    if not name:
        return failure_response("Missing name field in the body", 400)
    
    # create new Category if it doesn't exist, otherwise assign existing one
    category = Category.query.filter_by(name=name).first()
    if category is None:
        category = Category(name=name)
    event.category = category
    db.session.commit()
    return success_response(category.serialize())


# -- USER AUTHENTICATION ROUTES ---------------------------------------------------
@app.route("/register/", methods=["POST"])
def register_account():
    """
    Endpoint for registering a new user
    """
    body = json.loads(request.data)
    email = body.get("email")
    password = body.get("password")
    name = body.get("name")
    netid = body.get("netid")

    if email is None or password is None:
        return json.dumps({"error": "Invalid email or password"}), 400
    elif not name:
        return failure_response("Missing name field in the body", 400)
    elif not netid:
        return failure_response("Missing netid field in the body", 400)
    
    created, user = users_dao.create_user(email, password, name, netid)

    if not created:
        return json.dumps({"error": "User already exists."}), 400
    
    return json.dumps({
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "netid": user.netid,

        "session_token": user.session_token,
        "session_expiration": str(user.session_expiration),
        "update_token": user.update_token
    }), 200


@app.route("/login/", methods=["POST"])
def login():
    """
    Endpoint for logging in a user
    """
    body = json.loads(request.data)
    email = body.get("email")
    password = body.get("password")

    if email is None or password is None: 
        return json.dumps({"error": "Invalid email or password"}), 400
    
    success, user = users_dao.verify_credentials(email, password)

    if not success:
        return json.dumps({"error": "Incorrect email or password"}), 400
    
    return json.dumps({
        "session_token": user.session_token,
        "session_expiration": str(user.session_expiration),
        "update_token": user.update_token
    }), 200
    


@app.route("/session/", methods=["POST"])
def update_session():
    """
    Endpoint for updating a user's session
    """
    success, update_token = extract_token(request)

    if not success:
        return update_token

    user = users_dao.renew_session(update_token)

    if user is None:
        return json.dumps({"error": "Invalid update token"}), 400
    
    return json.dumps({
        "session_token": user.session_token,
        "session_expiration": str(user.session_expiration),
        "update_token": user.update_token
    }), 200



@app.route("/secret/", methods=["GET"])
def secret_message():
    """
    Endpoint for verifying a session token and returning a secret message
    """

    success, session_token = extract_token(request)

    if not success:
        return session_token
    
    user = users_dao.get_user_by_session_token(session_token)

    if user is None or not user.verify_session_token(session_token):
        return json.dumps({"error": "Invalid session token"}), 400
    
    return json.dumps({"message": "Valid session token"}), 200



@app.route("/logout/", methods=["POST"])
def logout():
    """
    Endpoint for logging out a user
    """
    success, session_token = extract_token(request)
    if not success:
        return session_token
    user = users_dao.get_user_by_session_token(session_token)

    if not user or not user.verify_session_token(session_token):
        return json.dumps({"error": "Invalid session token"}), 400
    
    user.session_expiration = datetime.datetime.now()
    db.session.commit()

    return json.dumps({"message": "User has successfully logged out"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
from flask_sqlalchemy import SQLAlchemy
import datetime
import hashlib
import os
import bcrypt

db = SQLAlchemy()

class MyDateTime(db.TypeDecorator):
    impl = db.DateTime
    
    def process_bind_param(self, value, dialect):
        if type(value) is str:
            return datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
        return value


class Event(db.Model):
  """
  Event model
  """
  __tablename__ = "event"
  id = db.Column(db.Integer, primary_key = True, autoincrement = True)
  title = db.Column(db.String, nullable=False)
  address = db.Column(db.String, nullable=False)
  start = db.Column(MyDateTime, nullable=False)
  end = db.Column(MyDateTime, nullable=False)
  description = db.Column(db.String, nullable=False)
  host = db.Column(db.String, nullable=False)
  host_email = db.Column(db.String, nullable=False)
  free = db.Column(db.Boolean, nullable=False)
  category = db.Column(db.String, db.ForeignKey("category.name"), nullable=True)

  def ___init___(self, **kwargs):
    """
    Initializes an Event object
    """
    self.title = kwargs.get("title", "")
    self.address = kwargs.get("address", "")
    self.start = kwargs.get("start", "")
    self.end = kwargs.get("end", "")
    self.description = kwargs.get("description", "")
    self.host = kwargs.get("host", "")
    self.host_email = kwargs.get("host_email", "")
    self.free = kwargs.get("free", False)
    self.category = kwargs.get("category")

  def serialize(self):
    """
    Serializes an Event object
    """
    return{
      "id": self.id,
      "title": self.title,
      "address": self.address,
      "start": self.start,
      "end": self.end,
      "description": self.description,
      "host": self.host,
      "host_email": self.host_email,
      "free": self.free,
      "category": self.category
    }



class User(db.Model):
  """
  User model
  """

  __tablename__ = "user"
  id = db.Column(db.Integer, primary_key = True, autoincrement=True)
  email = db.Column(db.String, nullable=False, unique=True)
  password_digest = db.Column(db.String, nullable=False)

  name = db.Column(db.String, nullable=False)
  netid = db.Column(db.String, nullable=True, unique = True)

  session_token = db.Column(db.String, nullable=False, unique=True)
  session_expiration = db.Column(db.DateTime, nullable=False)
  update_token = db.Column(db.String, nullable=False, unique=True)


  def __init__(self, **kwargs):
    """
    Initializes a User object
    """
    self.name = kwargs.get("name", "")
    self.netid = kwargs.get("netid", "")
    self.email = kwargs.get("email", "")
    self.password_digest = bcrypt.hashpw(kwargs.get("password").encode("utf8"), bcrypt.gensalt(13))
    self.renew_session()

  def serialize(self):
    """
    Serializes a User object
    """
    return{
      "id": self.id,
      "name": self.name,
      "netid": self.netid
    }

  def _urlsafe_base_64(self):
        """
        Randomly generates hashed tokens (used for session/update tokens)
        """
        return hashlib.sha1(os.urandom(64)).hexdigest()

  def renew_session(self):
      """
      Renews the sessions, i.e.
      1. Creates a new session token
      2. Sets the expiration time of the session to be a day from now
      3. Creates a new update token
      """
      self.session_token = self._urlsafe_base_64()
      self.session_expiration = datetime.datetime.now() + datetime.timedelta(minutes=1)
      self.update_token = self._urlsafe_base_64()

  def verify_password(self, password):
      """
      Verifies the password of a user
      """
      return bcrypt.checkpw(password.encode("utf8"), self.password_digest)

  def verify_session_token(self, session_token):
      """
      Verifies the session token of a user
      """
      return session_token == self.session_token and datetime.datetime.now() < self.session_expiration

  def verify_update_token(self, update_token):
      """
      Verifies the update token of a user
      """
      return update_token == self.update_token
  

class Category(db.Model):
  """
  Category model
  """
  __tablename__ = "category"
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  name = db.Column(db.String, nullable=False, unique=True)
  events = db.relationship("Event")

  def __init__(self, **kwargs):
    """
    Initializes a Category object
    """
    self.name = kwargs.get("name")

  def serialize(self):
    """
    Serializes a Category object
    """
    return {
    "id": self.id, 
    "name": self.name,
    "events": [e.serialize() for e in self.events]
    }

  def simple_serialize(self):
    """
    Serializes a Category object without the Events and Users fields
    """
    return{
      "id": self.id, 
      "name": self.name,
    }
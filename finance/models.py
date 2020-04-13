from app import db
from datetime import datetime

class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.Text)
    date_created = db.Column(db.DateTime(19),default=datetime.now())
    protfolio = db.relationship("Protfolio", backref=db.backref("user", lazy=True))

    '''def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password'''

class Protfolio(db.Model):
    symbol = db.Column(db.String(10), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    stock_name = db.Column(db.Text)
    shares = db.Column(db.Integer)
    avg_price = db.Column(db.Float(10,3))
    mkt_price = db.Column(db.Float(10,3), default = 0)
    mkt_value = db.Column(db.Float(10,3), default = 0)
    mkt_value_ex = db.Column(db.Float(10,3), default=0)
    last_update_date = db.Column(db.DateTime(2), default = datetime.now())

class Trans_history(db.Model):
    trans_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    symbol = db.Column(db.String(10))
    shares = db.Column(db.Integer)
    trans_price = db.Column(db.Float(10,3))
    trans_date = db.Column(db.Date)
    record_date = db.Column(db.DateTime(2), default = datetime.now())
from api import app, db

with app.app_context(): # with config settings (context) from app, 
    db.create_all() # create data schema 





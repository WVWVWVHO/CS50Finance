from flask import Flask, flash, redirect, render_template, request, session, url_for
import json

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

notes = {
    0: 'Frontend is using React',
    1: 'Backend is using Flask',
    2: 'Have fun!'
}

@app.route("/home", methods=["GET"])
def index():
    return 'server return success'

if __name__ == "__main__":
    app.run(port=7000, debug=True)
from flask import *

app = Flask(__name__)

@app.route("/")
def first():        
    return render_template("first.html")

@app.route("/",methods=['POST'])
def login():    
    if request.method == 'POST':
        return render_template("first.html")

if __name__ == "__main__":
    app.run(debug=True)


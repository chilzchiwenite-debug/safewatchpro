from flask import Flask

app = Flask(_name_)

@app.route("/")
def home():
    return "SafeWatchPro is LIVE 🚀"

if _name_ == "_main_":
    app.run(debug=True)
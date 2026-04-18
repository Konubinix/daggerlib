# [[file:readme.org::+begin_src python :tangle app.py][No heading:1]]
from flask import Flask

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def webhook():
    return "deployment triggered\n"


@app.route("/health")
def health():
    return "ok\n"
# No heading:1 ends here

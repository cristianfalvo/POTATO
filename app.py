import os
from uuid import uuid4

from flask import Flask, jsonify, redirect, render_template, session, url_for

from nordigen.types import *

from client import client

from api.defs import api_blueprint, render_blueprint
from api.balances import render_balances, api_balances
from api.transactions import render_get_transactions_by_account, api_get_transactions_by_account

app = Flask(__name__)
# set Flask secret key
app.config["SECRET_KEY"] = os.urandom(24)

app.register_blueprint(api_blueprint)
app.register_blueprint(render_blueprint)

COUNTRY = "IT"
REDIRECT_URI = "http://127.0.0.1:5000/results"

# Init Nordigen client pass secret_id and secret_key generated from OB portal
# In this example we will load secrets from .env file

@app.route("/agreements/<institution_id>", methods=["GET"])
def agreements(institution_id):

    if institution_id:

        init = client.initialize_session(
            institution_id=institution_id,
            redirect_uri=REDIRECT_URI,
            reference_id=str(uuid4()),
        )

        redirect_url = init.link
        # save requisiton id to a session
        session["req_id"] = init.requisition_id
        return redirect(redirect_url)

    return redirect(url_for("home"))


@app.route("/results", methods=["GET"])
def results():

    if "req_id" in session:

        accounts = client.requisition.get_requisition_by_id(
            requisition_id=session["req_id"]
        )["accounts"]

        accounts_data = []
        for id in accounts:
            account = client.account_api(id)
            metadata = account.get_metadata()
            transactions = account.get_transactions()
            details = account.get_details()
            balances = account.get_balances()

            accounts_data.append(
                {
                    "metadata": metadata,
                    "details": details,
                    "balances": balances,
                    "transactions": transactions,
                }
            )

        return jsonify(accounts_data)

    raise Exception(
        "Requisition ID is not found. Please complete authorization with your bank"
    )

print(app.url_map)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
print(app.url_map)
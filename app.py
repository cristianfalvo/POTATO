import os
from uuid import uuid4

from functools import reduce

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, session, url_for, request, abort

from nordigen import NordigenClient
from datetime import date

from requests import HTTPError

app = Flask(__name__)
# set Flask secret key
app.config["SECRET_KEY"] = os.urandom(24)

COUNTRY = "IT"
REDIRECT_URI = "http://127.0.0.1:5000/results"

# Load secrets from .env file
load_dotenv()

# Init Nordigen client pass secret_id and secret_key generated from OB portal
# In this example we will load secrets from .env file
client = NordigenClient(
    secret_id=os.getenv("SECRET_ID"),
    secret_key=os.getenv("SECRET_KEY")
)

# Generate access & refresh token
client.generate_token()


@app.route("/institutions", methods=["GET"])
def institutions():
    # Get list of institutions
    institution_list = client.institution.get_institutions(country=COUNTRY)
    return render_template("institutions.html", institutions=institution_list)


@app.route("/home", methods=["GET"])
def home():
    reqs = client.requisition.get_requisitions()["results"]
    print(reqs)
    account_ids = []
    account_refs = {}
    for req in reqs:
        account_ids.extend(req["accounts"])
    print("\n\n")
    print(account_ids)
    balances = {}
    for acc in account_ids:
        account = client.account_api(acc)
        balances[acc] = account.get_balances()
        details = account.get_details()["account"]
        print(details)
        account_refs[acc] = details["name"]
    return render_template("home.html", balances=balances, accounts=account_refs)


@app.route("/transactions/<account_id>", methods=["GET"])
def get_transactions_by_account(account_id: str):
    # TODO: check if account id is a valid uuid
    args = request.args
    account = client.account_api(account_id)
    date_from, date_to = args.get("from"), args.get("to")
    try:
        date_from = None if not date_from else str(date.fromisoformat(date_from))
        date_to = None if not date_to else str(date.fromisoformat(date_to))
    except ValueError as e:
        print(e)
        # TODO: provide error info
        abort(400)
    except TypeError as e:
        print(e)
        # TODO: provide error info
        abort(400)
    try:
        t = account.get_transactions(date_from, date_to)
    except HTTPError as e:
        print(e)
        abort(e.response)
        
    exclude_headers = [
        "internalTransactionId",
        "transactionId"
    ]
    
    transactions = t["transactions"]
    booked = transactions["booked"]
    for entry in booked:
        e = entry["transactionAmount"]
        entry["transactionAmount"] = "{} {}".format(e["currency"], e["amount"])
    booked_headers = reduce(
        lambda x, y: x.union(y),
        [x.keys() for x in booked],
        set()
    )
    booked_headers.difference_update(exclude_headers)
    pending = transactions["pending"]
    for entry in pending:
        e = entry["transactionAmount"]
        entry["transactionAmount"] = "{} {}".format(e["currency"], e["amount"])
    pending_headers = reduce(
        lambda x, y: x.union(y),
        [x.keys() for x in pending],
        set()
    )
    pending_headers.difference_update(exclude_headers)
    return render_template(
        "transactions.html",
        booked=booked,
        booked_headers=booked_headers,
        pending=pending,
        pending_headers=pending_headers,
        name=account.get_details()["account"]["name"]
    )


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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

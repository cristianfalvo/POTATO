from flask import request, abort, render_template, jsonify
from requests import HTTPError
from functools import reduce
from datetime import date
from .defs import api_blueprint, render_blueprint
from client import client


def get_transactions_by_account(account_id: str, date_from: str | None, date_to: str | None):
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
    booked: dict = transactions["booked"]
    for entry in booked:
        e = entry["transactionAmount"]
        entry["transactionAmount"] = "{} {}".format(e["currency"], e["amount"])
    booked_headers = reduce(
        lambda x, y: x.union(y),
        [x.keys() for x in booked],
        set()
    )
    booked_headers.difference_update(exclude_headers)
    booked = [{entry[key] for key in booked_headers} for entry in booked]

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
    booked = [{entry[key] for key in pending_headers} for entry in pending]

    return {
        "account_name": account.get_details()["account"]["name"],
        "pending": {
            "headers": pending_headers,
            "entries": pending
        },
        "booked": {
            "headers": booked_headers,
            "entries": booked
        }
    }


@api_blueprint.route("/transactions/<account_id>", methods=["GET"])
def api_get_transactions_by_account(account_id: str):
    # TODO: check if account id is a valid uuid
    args = request.args
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
        
    return jsonify(
        get_transactions_by_account(
            account_id=account_id,
            date_from=date_from,
            date_to=date_to
        )
    )
   
    
@render_blueprint.route("/transactions/<account_id>", methods=["GET"])
def render_get_transactions_by_account(account_id: str):
    
    args = request.args
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
    
    data = get_transactions_by_account(
        account_id=account_id,
        date_from=date_from,
        date_to=date_to
    )
    
    return render_template(
        "transactions.html",
        booked=data["booked"]["entries"],
        booked_headers=data["booked"]["headers"],
        pending=data["pending"]["entries"],
        pending_headers=data["pending"]["headers"],
        name=data["account_name"]
    )

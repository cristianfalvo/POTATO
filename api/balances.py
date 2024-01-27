from decimal import Decimal
from flask import render_template, jsonify, Blueprint
from .defs import api_blueprint, render_blueprint
from client import client

def get_balances():
    reqs = client.requisition.get_requisitions()["results"]
    print(reqs)
    account_ids = []
    account_refs = {}
    for req in reqs:
        account_ids.extend(req["accounts"])
    print("\n\n")
    print(account_ids)
    balances = {}
    total_balances = {}
    for acc in account_ids:
        account = client.account_api(acc)
        balances[acc] = account.get_balances()["balances"]
        
        # take the account balance that's most relevant
        # no balance available, so skip
        
        if len(balances[acc]) == 0:
            continue
        
        # only one balance, use it
        
        elif len(balances[acc]) == 1:
            cur_balance = balances[acc][0]["balanceAmount"]
        
        # multple balances exist; 
        # use ones marked with "available" and take the ***LOWEST***
        # if none match "available" still take the lowest overall
        # TODO: comparison of amounts should keep currency into account
        # however chances of one account having balances in multiple currencies is low
        
        else:
            cur_balance = None
            available = False
            for balance in balances[acc]:
                if not available:
                    if "available" in balance["balanceType"].lower():
                        available = True
                        cur_balance = balance
                    elif (
                        not cur_balance
                        or Decimal(balance["balanceAmount"]["amount"])
                        <
                        Decimal(cur_balance["balanceAmount"]["amount"])
                    ):
                        cur_balance = balance
                else:
                    if (
                        Decimal(balance["balanceAmount"]["amount"])
                        <
                        Decimal(cur_balance["balanceAmount"]["amount"])
                    ):
                        cur_balance = balance
        
        cur_balance = cur_balance["balanceAmount"]
        amount = Decimal(cur_balance["amount"])
        cur = cur_balance["currency"]
        details = account.get_details()["account"]
        print(details)
        account_refs[acc] = details.get("name")
        total_balances[cur] = (
            amount
            if cur not in total_balances
            else Decimal(total_balances[cur]) + amount
        )
        total_balances[cur] = float(total_balances[cur])
    return {
        "balances": total_balances,
        "accounts": account_refs
    }


@api_blueprint.route("/balances", methods=["GET"])
def api_balances():
    return jsonify(get_balances())


@render_blueprint.route("/home", methods=["GET"])
@render_blueprint.route("/balances", methods=["GET"])
def render_balances():
    data = get_balances()
    return render_template("home.html", balances=data["balances"], accounts=data["accounts"])

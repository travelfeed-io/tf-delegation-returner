import datetime
import json
import os

from beem import Steem
from beem.account import Account
from beem.amount import Amount
from beem.nodelist import NodeList

# Ignore internal testing accounts
ignored_accounts = ["travelfeedio", "tftest17",
                    "tfawesome", "testytest", "testcat"]

nl = NodeList()
nl.update_nodes()
node_list = nl.get_nodes()

stm = Steem(node=node_list, use_condenser=True)
walletpw = os.environ.get('UNLOCK')
stm.wallet.unlock(walletpw)

account = Account("travelfeed", steem_instance=stm)
delegations = account.get_vesting_delegations()

for d in delegations:
    # Only check delegations made more than a week ago
    if datetime.datetime.strptime(d['min_delegation_time'], '%Y-%m-%dT%H:%M:%S') < (datetime.datetime.utcnow() - datetime.timedelta(days=7)) and not d.get('delegatee') in ignored_accounts:
        vests_delegated = d.get('vesting_shares')
        delegatee = d.get('delegatee')
        acc = Account(delegatee, steem_instance=stm)
        posts = []
        goal = 0
        sp = stm.vests_to_sp(acc.get_balances().get('available')[2])
        # Get TravelFeed posts of account
        history = acc.history_reverse(only_ops=['comment'])
        for h in history:
            try:
                meta = json.loads(h.get('json_metadata', {}))
                app = meta.get('app', '').split('/')[0]
                if app == "travelfeed":
                    posts += [datetime.datetime.strptime(
                        h['timestamp'], '%Y-%m-%dT%H:%M:%S')]
            except:
                print("Error when processing post...")
        # Set goal SP based on how active the account is
        for d in posts:
            if d > (datetime.datetime.utcnow() - datetime.timedelta(days=3)):
                goal = 35
            elif d > (datetime.datetime.utcnow() - datetime.timedelta(days=7)):
                goal = 25
            elif d > (datetime.datetime.utcnow() - datetime.timedelta(days=14)):
                goal = 20
            elif d > (datetime.datetime.utcnow() - datetime.timedelta(days=28)):
                goal = 15
            elif goal is 0 and d > (datetime.datetime.utcnow() - datetime.timedelta(days=56)):
                goal = 10
            elif goal is 0 and d > (datetime.datetime.utcnow() - datetime.timedelta(days=84)):
                goal = 5
        # New delegation aim based on goal SP minus active SP
        adjusted_delegation = goal-sp
        if(adjusted_delegation < 0):
            adjusted_delegation = 0
        adjusted_vesting_shares = stm.sp_to_vests(adjusted_delegation)
        # Broadcast only if adjusted delegation is lower than current delegation
        if(Amount(vests_delegated).amount > adjusted_delegation):
            try:
                account.delegate_vesting_shares(
                    delegatee, adjusted_vesting_shares, account="travelfeed")
            except Exception as err:
                print(repr(err))

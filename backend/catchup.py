import calendar
from datetime import datetime, timedelta

from flask import current_app

from models import Transaction, db, utcnow


def run_catchup(user):
    """Materialize any missing daily income and month-end interest transactions.

    Income accrues only on days on or after allowance_start_date and while the
    allowance is above zero; interest settles every month-end regardless, so a
    paused allowance still earns (or is charged) interest on its balance.
    """
    if user.is_admin:
        return

    last_income = db.session.execute(
        db.select(Transaction)
        .filter_by(user_id=user.id, type="income")
        .order_by(Transaction.created_at.desc())
    ).scalars().first()

    if last_income:
        start_date = last_income.created_at.date() + timedelta(days=1)
    else:
        start_date = user.allowance_start_date or user.created_at.date()

        # Insert starting balance adjustment on first catchup
        if user.starting_balance != 0:
            existing_adj = db.session.execute(
                db.select(Transaction).filter_by(
                    user_id=user.id, type="adjustment"
                )
            ).scalars().first()
            if not existing_adj:
                db.session.add(
                    Transaction(
                        user_id=user.id,
                        type="adjustment",
                        amount=round(user.starting_balance, 2),
                        description="Starting balance",
                        created_at=datetime(
                            start_date.year, start_date.month, start_date.day
                        )
                        - timedelta(seconds=1),
                    )
                )

    end_date = utcnow().date()

    if start_date > end_date:
        return

    # Interest for a month-end is deferred until that day is over; if the last
    # materialized day was a month-end, it has now passed and can be settled.
    if last_income:
        prev = start_date - timedelta(days=1)
        if prev.day == calendar.monthrange(prev.year, prev.month)[1]:
            _apply_monthly_interest(user, prev)

    # Days before this (e.g. while paused, see admin.update_user) earn nothing.
    income_from = user.allowance_start_date or start_date

    current = start_date
    while current <= end_date:
        days_in_month = calendar.monthrange(current.year, current.month)[1]
        daily = round(user.monthly_allowance / days_in_month, 2)

        if daily > 0 and current >= income_from:
            db.session.add(
                Transaction(
                    user_id=user.id,
                    type="income",
                    amount=daily,
                    description="Daily allowance",
                    created_at=datetime(current.year, current.month, current.day),
                )
            )

        # Skip today's month-end: later transactions today must count toward it.
        if current.day == days_in_month and current < end_date:
            db.session.flush()
            _apply_monthly_interest(user, current)

        current += timedelta(days=1)

    db.session.commit()


def _apply_monthly_interest(user, month_end_date):
    """Apply savings interest or penalty interest for a completed month."""
    month_start = month_end_date.replace(day=1)
    existing = db.session.execute(
        db.select(Transaction)
        .filter_by(user_id=user.id)
        .filter(Transaction.type.in_(["interest", "penalty"]))
        .filter(
            Transaction.created_at
            >= datetime(month_start.year, month_start.month, month_start.day)
        )
        .filter(
            Transaction.created_at
            <= datetime(
                month_end_date.year, month_end_date.month, month_end_date.day, 23, 59, 59
            )
        )
    ).scalars().first()
    if existing:
        return

    balance = get_balance(
        user,
        as_of=datetime(
            month_end_date.year, month_end_date.month, month_end_date.day, 23, 59, 58
        ),
    )

    month_name = month_end_date.strftime("%B %Y")

    if balance > 0:
        apy = current_app.config["SAVINGS_INTEREST_RATE"]
        monthly_rate = (1 + apy) ** (1 / 12) - 1
        interest = round(balance * monthly_rate, 2)
        if interest > 0:
            db.session.add(
                Transaction(
                    user_id=user.id,
                    type="interest",
                    amount=interest,
                    description=f"Savings interest for {month_name}",
                    created_at=datetime(
                        month_end_date.year,
                        month_end_date.month,
                        month_end_date.day,
                        23,
                        59,
                        59,
                    ),
                )
            )
    elif balance < 0:
        apr = current_app.config["CREDIT_INTEREST_RATE"]
        monthly_rate = apr / 12
        penalty = round(abs(balance) * monthly_rate, 2)
        if penalty > 0:
            db.session.add(
                Transaction(
                    user_id=user.id,
                    type="penalty",
                    amount=penalty,
                    description=f"Interest charge for {month_name}",
                    created_at=datetime(
                        month_end_date.year,
                        month_end_date.month,
                        month_end_date.day,
                        23,
                        59,
                        59,
                    ),
                )
            )


def get_balance(user, as_of=None):
    """Calculate user's balance from transaction history."""
    filters = [Transaction.user_id == user.id]
    if as_of:
        filters.append(Transaction.created_at <= as_of)

    credits = db.session.execute(
        db.select(db.func.coalesce(db.func.sum(Transaction.amount), 0))
        .filter(*filters)
        .filter(Transaction.type.in_(["income", "interest", "adjustment"]))
    ).scalar()

    debits = db.session.execute(
        db.select(db.func.coalesce(db.func.sum(Transaction.amount), 0))
        .filter(*filters)
        .filter(Transaction.type.in_(["withdrawal", "penalty"]))
    ).scalar()

    return round(credits - debits, 2)


CREDIT_TYPES = ("income", "interest", "adjustment")
DEBIT_TYPES = ("withdrawal", "penalty")


def get_totals(user):
    """Lifetime totals per transaction type (amounts stored positive)."""
    rows = db.session.execute(
        db.select(
            Transaction.type,
            db.func.coalesce(db.func.sum(Transaction.amount), 0),
        )
        .filter(Transaction.user_id == user.id)
        .group_by(Transaction.type)
    ).all()
    by_type = {t: amt for t, amt in rows}
    return {
        "earned": round(by_type.get("income", 0), 2),
        "interest": round(by_type.get("interest", 0), 2),
        "penalties": round(by_type.get("penalty", 0), 2),
        "withdrawn": round(by_type.get("withdrawal", 0), 2),
    }


def build_chart_data(user):
    """Daily balance series for the last 90 days (UTC date buckets)."""
    cutoff_date = utcnow().date() - timedelta(days=90)
    all_txns = db.session.execute(
        db.select(Transaction)
        .filter_by(user_id=user.id)
        .order_by(Transaction.created_at.asc())
    ).scalars().all()

    labels = []
    balances = []
    running = 0.0

    start_date_str = cutoff_date.isoformat()
    start_point_added = False

    for txn in all_txns:
        delta = txn.amount if txn.type in CREDIT_TYPES else -txn.amount

        txn_date = txn.created_at.date()
        if txn_date < cutoff_date:
            running += delta
        else:
            if not start_point_added:
                labels.append(start_date_str)
                balances.append(round(running, 2))
                start_point_added = True

            running += delta

            day_label = txn_date.isoformat()
            # Collapse multiple transactions on the same day to the last one
            if labels and labels[-1] == day_label:
                balances[-1] = round(running, 2)
            else:
                labels.append(day_label)
                balances.append(round(running, 2))

    if not start_point_added:
        labels.append(start_date_str)
        balances.append(round(running, 2))

    today_str = utcnow().date().isoformat()
    if labels and labels[-1] != today_str:
        labels.append(today_str)
        balances.append(balances[-1])

    return {"labels": labels, "balances": balances}


def txn_with_balance(txn, balance_after):
    """Return a transaction dict with balance_after included."""
    d = txn.to_dict()
    d["balance_after"] = balance_after
    return d


def annotate_running_balance(user, transactions):
    """Add balance_after to each transaction, preserving the list's order.

    Balances come from a running total over all of the user's transactions
    (ordered by created_at, then id), so they're correct for filtered or
    non-contiguous lists too.
    """
    if not transactions:
        return []

    signed = db.case(
        (Transaction.type.in_(CREDIT_TYPES), Transaction.amount),
        else_=-Transaction.amount,
    )
    running = (
        db.select(
            Transaction.id,
            db.func.sum(signed)
            .over(order_by=(Transaction.created_at, Transaction.id))
            .label("balance"),
        )
        .filter(Transaction.user_id == user.id)
        .subquery()
    )
    balances = dict(
        db.session.execute(
            db.select(running.c.id, running.c.balance).filter(
                running.c.id.in_([t.id for t in transactions])
            )
        ).all()
    )
    return [txn_with_balance(t, round(balances[t.id], 2)) for t in transactions]

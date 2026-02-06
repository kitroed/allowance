import calendar
from datetime import date, datetime, timedelta

from flask import current_app

from models import Transaction, db


def run_catchup(user):
    """Materialize any missing daily income and month-end interest transactions."""
    if user.monthly_allowance <= 0:
        return

    last_income = (
        Transaction.query.filter_by(user_id=user.id, type="income")
        .order_by(Transaction.created_at.desc())
        .first()
    )

    if last_income:
        start_date = last_income.created_at.date() + timedelta(days=1)
    else:
        start_date = user.allowance_start_date or user.created_at.date()

        # Insert starting balance adjustment on first catchup
        if user.starting_balance != 0:
            existing_adj = Transaction.query.filter_by(
                user_id=user.id, type="adjustment"
            ).first()
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

    end_date = date.today()

    if start_date > end_date:
        return

    current = start_date
    while current <= end_date:
        days_in_month = calendar.monthrange(current.year, current.month)[1]
        daily = round(user.monthly_allowance / days_in_month, 2)

        txn = Transaction(
            user_id=user.id,
            type="income",
            amount=daily,
            description="Daily allowance",
            created_at=datetime(current.year, current.month, current.day),
        )
        db.session.add(txn)

        if current.day == days_in_month:
            db.session.flush()
            _apply_monthly_interest(user, current)

        current += timedelta(days=1)

    db.session.commit()


def _apply_monthly_interest(user, month_end_date):
    """Apply savings interest or penalty interest for a completed month."""
    month_start = month_end_date.replace(day=1)
    existing = (
        Transaction.query.filter_by(user_id=user.id)
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
        .first()
    )
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
    query = Transaction.query.filter_by(user_id=user.id)
    if as_of:
        query = query.filter(Transaction.created_at <= as_of)

    credits = (
        query.filter(Transaction.type.in_(["income", "interest", "adjustment"]))
        .with_entities(db.func.coalesce(db.func.sum(Transaction.amount), 0))
        .scalar()
    )

    debits = (
        query.filter(Transaction.type.in_(["withdrawal", "penalty"]))
        .with_entities(db.func.coalesce(db.func.sum(Transaction.amount), 0))
        .scalar()
    )

    return round(credits - debits, 2)


CREDIT_TYPES = ("income", "interest", "adjustment")
DEBIT_TYPES = ("withdrawal", "penalty")


def txn_with_balance(txn, balance_after):
    """Return a transaction dict with balance_after included."""
    d = txn.to_dict()
    d["balance_after"] = balance_after
    return d


def annotate_running_balance(user, transactions):
    """Add balance_after to a list of transactions (assumed chronological ascending).

    For a desc-ordered page, pass the list reversed, then reverse the result,
    or use annotate_page_balances instead.
    """
    # Get balance before the first transaction in the list
    if not transactions:
        return []

    first_txn = transactions[0]
    # Balance right before this transaction
    balance_before = _balance_before(user, first_txn)

    result = []
    running = balance_before
    for txn in transactions:
        if txn.type in CREDIT_TYPES:
            running += txn.amount
        else:
            running -= txn.amount
        result.append(txn_with_balance(txn, round(running, 2)))
    return result


def _balance_before(user, txn):
    """Calculate balance just before a given transaction."""
    query = Transaction.query.filter_by(user_id=user.id).filter(
        Transaction.created_at < txn.created_at
    )

    # Handle transactions at the exact same timestamp
    same_time = Transaction.query.filter_by(user_id=user.id).filter(
        Transaction.created_at == txn.created_at,
        Transaction.id < txn.id,
    )

    credits = 0.0
    debits = 0.0

    for q in (query, same_time):
        credits += (
            q.filter(Transaction.type.in_(CREDIT_TYPES))
            .with_entities(db.func.coalesce(db.func.sum(Transaction.amount), 0))
            .scalar()
        )
        debits += (
            q.filter(Transaction.type.in_(DEBIT_TYPES))
            .with_entities(db.func.coalesce(db.func.sum(Transaction.amount), 0))
            .scalar()
        )

    return round(credits - debits, 2)


export function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

export function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

// A transaction reduces the balance if it's a withdrawal/penalty, or a
// negative-amount adjustment.
export function isDebitTxn(txn) {
    return txn.type === 'withdrawal' || txn.type === 'penalty' || txn.amount < 0;
}

// Currency string prefixed with +/- according to the transaction's direction.
export function formatSignedAmount(txn) {
    const sign = isDebitTxn(txn) ? '-' : '+';
    return `${sign}${formatCurrency(Math.abs(txn.amount))}`;
}

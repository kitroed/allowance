<script>
	import { onMount } from 'svelte';
	import { get } from '$lib/api.js';
	import { formatCurrency, formatDate } from '$lib/utils.js';

	let transactions = [];
	let total = 0;
	let page = 1;
	let pages = 1;
	let typeFilter = '';
	let loading = true;

	async function loadTransactions() {
		loading = true;
		try {
			let url = `/api/transactions?page=${page}&per_page=20`;
			if (typeFilter) url += `&type=${typeFilter}`;
			const data = await get(url);
			transactions = data.transactions;
			total = data.total;
			pages = data.pages;
		} catch (err) {
			console.error('Failed to load transactions:', err);
		} finally {
			loading = false;
		}
	}

	function changeFilter() {
		page = 1;
		loadTransactions();
	}

	function prevPage() {
		if (page > 1) {
			page--;
			loadTransactions();
		}
	}

	function nextPage() {
		if (page < pages) {
			page++;
			loadTransactions();
		}
	}

	onMount(loadTransactions);
</script>

<h2>Transaction History</h2>

<div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
	<label style="margin: 0;">
		Filter:
		<select bind:value={typeFilter} onchange={changeFilter} style="display: inline; width: auto; margin-left: 0.5rem;">
			<option value="">All types</option>
			<option value="income">Income</option>
			<option value="withdrawal">Withdrawals</option>
			<option value="interest">Interest</option>
			<option value="penalty">Penalties</option>
		</select>
	</label>
	<small>{total} transaction{total !== 1 ? 's' : ''}</small>
</div>

{#if loading}
	<p aria-busy="true">Loading transactions...</p>
{:else if transactions.length === 0}
	<p>No transactions found.</p>
{:else}
	<figure>
		<table>
			<thead>
				<tr>
					<th>Date</th>
					<th>Type</th>
					<th>Amount</th>
					<th>Description</th>
					<th>Balance</th>
				</tr>
			</thead>
			<tbody>
				{#each transactions as txn}
					<tr>
						<td>{formatDate(txn.created_at)}</td>
						<td><span class="badge badge-{txn.type}">{txn.type}</span></td>
						<td class={(txn.type === 'withdrawal' || txn.type === 'penalty' || txn.amount < 0) ? 'balance-negative' : 'balance-positive'}>
							{(txn.type === 'withdrawal' || txn.type === 'penalty' || txn.amount < 0) ? '-' : '+'}{formatCurrency(Math.abs(txn.amount))}
						</td>
						<td>{txn.description}</td>
						<td class={txn.balance_after >= 0 ? 'balance-positive' : 'balance-negative'}>
							{formatCurrency(txn.balance_after)}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</figure>

	<div style="display: flex; justify-content: space-between; align-items: center;">
		<button class="outline" onclick={prevPage} disabled={page <= 1}>Previous</button>
		<small>Page {page} of {pages}</small>
		<button class="outline" onclick={nextPage} disabled={page >= pages}>Next</button>
	</div>
{/if}

<script>
	import { onMount } from 'svelte';
	import { get, post } from '$lib/api.js';
	import { formatCurrency, formatDate } from '$lib/utils.js';

	let amount = '';
	let reason = '';
	let submitting = false;
	let success = '';
	let error = '';
	let requests = [];
	let loadingRequests = true;

	async function loadRequests() {
		try {
			requests = await get('/api/withdrawals');
		} catch (err) {
			console.error('Failed to load requests:', err);
		} finally {
			loadingRequests = false;
		}
	}

	async function handleSubmit(e) {
		e.preventDefault();
		error = '';
		success = '';
		submitting = true;
		try {
			const data = await post('/api/withdrawals', {
				amount: parseFloat(amount),
				reason
			});
			success = `Request for ${formatCurrency(data.amount)} submitted!`;
			amount = '';
			reason = '';
			loadRequests();
		} catch (err) {
			error = err.message || 'Failed to submit request';
		} finally {
			submitting = false;
		}
	}

	onMount(loadRequests);
</script>

<h2>Request Withdrawal</h2>

<article>
	<form onsubmit={handleSubmit}>
		<label>
			Amount
			<input
				type="number"
				step="0.01"
				min="0.01"
				bind:value={amount}
				required
				placeholder="0.00"
			/>
		</label>
		<label>
			Reason
			<input type="text" bind:value={reason} placeholder="What is this for?" />
		</label>
		{#if error}
			<p style="color: red;">{error}</p>
		{/if}
		{#if success}
			<p style="color: green;">{success}</p>
		{/if}
		<button type="submit" aria-busy={submitting} disabled={submitting}>
			{submitting ? 'Submitting...' : 'Submit Request'}
		</button>
	</form>
</article>

<h3>Your Requests</h3>

{#if loadingRequests}
	<p aria-busy="true">Loading requests...</p>
{:else if requests.length === 0}
	<p>No withdrawal requests yet.</p>
{:else}
	<figure>
		<table>
			<thead>
				<tr>
					<th>Date</th>
					<th>Amount</th>
					<th>Reason</th>
					<th>Status</th>
				</tr>
			</thead>
			<tbody>
				{#each requests as req}
					<tr>
						<td>{formatDate(req.created_at)}</td>
						<td>{formatCurrency(req.amount)}</td>
						<td>{req.reason || '-'}</td>
						<td><span class="badge badge-{req.status}">{req.status}</span></td>
					</tr>
				{/each}
			</tbody>
		</table>
	</figure>
{/if}

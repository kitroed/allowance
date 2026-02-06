<script>
	import { onMount } from 'svelte';
	import { Chart, registerables } from 'chart.js';
	import { get } from '$lib/api.js';
	import { formatCurrency, formatDate } from '$lib/utils.js';

	Chart.register(...registerables);

	let balance = 0;
	let recentTransactions = [];
	let loading = true;
	let canvas;
	let chart;

	onMount(async () => {
		try {
			const data = await get('/api/dashboard');
			balance = data.balance;
			recentTransactions = data.recent_transactions;

			if (canvas && data.chart_data.labels.length > 0) {
				chart = new Chart(canvas, {
					type: 'line',
					data: {
						labels: data.chart_data.labels,
						datasets: [
							{
								label: 'Balance',
								data: data.chart_data.balances,
								borderColor: balance >= 0 ? '#43a047' : '#e53935',
								backgroundColor: balance >= 0 ? 'rgba(67,160,71,0.1)' : 'rgba(229,57,53,0.1)',
								fill: true,
								tension: 0.3
							}
						]
					},
					options: {
						responsive: true,
						plugins: {
							legend: { display: false }
						},
						scales: {
							y: {
								ticks: {
									callback: (v) => '$' + v.toFixed(2)
								}
							}
						}
					}
				});
			}
		} catch (err) {
			console.error('Dashboard load failed:', err);
		} finally {
			loading = false;
		}

		return () => {
			if (chart) chart.destroy();
		};
	});
</script>

<h2>Dashboard</h2>

{#if loading}
	<p aria-busy="true">Loading dashboard...</p>
{:else}
	<div class="grid">
		<article class="text-center">
			<header>Current Balance</header>
			<p class="balance-display {balance >= 0 ? 'balance-positive' : 'balance-negative'}">
				{formatCurrency(balance)}
			</p>
		</article>
	</div>

	<article>
		<header>Balance History (Last 90 Days)</header>
		{#if recentTransactions.length === 0}
			<p>No transactions yet. Your daily allowance will appear here.</p>
		{:else}
			<canvas bind:this={canvas}></canvas>
		{/if}
	</article>

	<article>
		<header>Recent Transactions</header>
		{#if recentTransactions.length === 0}
			<p>No transactions yet.</p>
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
						{#each recentTransactions as txn}
							<tr>
								<td>{formatDate(txn.created_at)}</td>
								<td><span class="badge badge-{txn.type}">{txn.type}</span></td>
								<td class={txn.type === 'withdrawal' || txn.type === 'penalty' ? 'balance-negative' : 'balance-positive'}>
									{txn.type === 'withdrawal' || txn.type === 'penalty' ? '-' : '+'}{formatCurrency(txn.amount)}
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
		{/if}
	</article>
{/if}

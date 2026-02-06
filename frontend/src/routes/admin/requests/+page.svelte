<script>
	import { onMount } from 'svelte';
	import { get, put } from '$lib/api.js';
	import { formatCurrency, formatDate } from '$lib/utils.js';

	let requests = [];
	let loading = true;
	let filter = 'pending';
	let processingId = null;

	async function loadRequests() {
		loading = true;
		try {
			requests = await get(`/api/admin/requests?status=${filter}`);
		} catch (err) {
			console.error('Failed to load requests:', err);
		} finally {
			loading = false;
		}
	}

	async function resolve(id, status) {
		processingId = id;
		try {
			await put(`/api/admin/requests/${id}`, { status });
			loadRequests();
		} catch (err) {
			console.error('Failed to resolve request:', err);
		} finally {
			processingId = null;
		}
	}

	function changeFilter() {
		loadRequests();
	}

	onMount(loadRequests);
</script>

<h2>Withdrawal Requests</h2>

<div style="margin-bottom: 1rem;">
	<label style="display: inline-flex; align-items: center; gap: 0.5rem;">
		Show:
		<select bind:value={filter} onchange={changeFilter} style="display: inline; width: auto;">
			<option value="pending">Pending</option>
			<option value="all">All</option>
			<option value="approved">Approved</option>
			<option value="denied">Denied</option>
		</select>
	</label>
</div>

{#if loading}
	<p aria-busy="true">Loading requests...</p>
{:else if requests.length === 0}
	<p>No {filter === 'all' ? '' : filter} requests.</p>
{:else}
	<figure>
		<table>
			<thead>
				<tr>
					<th>Date</th>
					<th>Child</th>
					<th>Amount</th>
					<th>Reason</th>
					<th>Status</th>
					{#if filter === 'pending'}
						<th>Actions</th>
					{/if}
				</tr>
			</thead>
			<tbody>
				{#each requests as req}
					<tr>
						<td>{formatDate(req.created_at)}</td>
						<td>{req.child_name}</td>
						<td>{formatCurrency(req.amount)}</td>
						<td>{req.reason || '-'}</td>
						<td><span class="badge badge-{req.status}">{req.status}</span></td>
						{#if filter === 'pending'}
							<td>
								{#if req.status === 'pending'}
									<div class="button-group">
										<button
											onclick={() => resolve(req.id, 'approved')}
											aria-busy={processingId === req.id}
											disabled={processingId !== null}
										>
											Approve
										</button>
										<button
											class="outline"
											onclick={() => resolve(req.id, 'denied')}
											aria-busy={processingId === req.id}
											disabled={processingId !== null}
										>
											Deny
										</button>
									</div>
								{/if}
							</td>
						{/if}
					</tr>
				{/each}
			</tbody>
		</table>
	</figure>
{/if}

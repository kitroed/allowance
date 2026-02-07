<script>
  import { onMount } from 'svelte';
  import { get, put } from '$lib/api.js';
  import { formatCurrency, formatDate } from '$lib/utils.js';

  let requests = [];
  let loading = true;
  let filter = 'pending';
  let processingId = null;
  let actionError = '';
  let adjustedAmounts = {};

  async function loadRequests() {
    loading = true;
    actionError = '';
    try {
      requests = await get(`/api/admin/requests?status=${filter}`);
      adjustedAmounts = requests.reduce((acc, req) => {
        acc[req.id] = req.amount;
        return acc;
      }, {});
    } catch (err) {
      console.error('Failed to load requests:', err);
    } finally {
      loading = false;
    }
  }

  async function resolve(id, status) {
    processingId = id;
    actionError = '';
    try {
      const payload = { status };
      if (status === 'approved') {
        const rawAmount = adjustedAmounts[id];
        const amount = parseFloat(rawAmount);
        if (Number.isNaN(amount) || amount <= 0) {
          actionError = 'Enter a valid amount greater than 0 before approving.';
          return;
        }
        payload.amount = amount;
      }

      await put(`/api/admin/requests/${id}`, payload);
      loadRequests();
    } catch (err) {
      actionError = err.message || 'Failed to resolve request.';
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
  {#if actionError}
    <p style="color: red;">{actionError}</p>
  {/if}
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
            <td>
              {#if filter === 'pending' && req.status === 'pending'}
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  bind:value={adjustedAmounts[req.id]}
                  aria-label="Adjusted amount"
                  style="max-width: 8rem;"
                />
              {:else}
                {formatCurrency(req.amount)}
              {/if}
            </td>
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

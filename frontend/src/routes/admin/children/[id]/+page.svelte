<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { Chart, registerables } from 'chart.js';
  import { get } from '$lib/api.js';
  import { formatCurrency, formatDate, formatSignedAmount, isDebitTxn } from '$lib/utils.js';

  Chart.register(...registerables);

  $: childId = $page.params.id;

  let detail = null;
  let loading = true;
  let loadError = '';
  let canvas;
  let chart;

  // Transaction history
  let transactions = [];
  let total = 0;
  let txnPage = 1;
  let pages = 1;
  let typeFilter = '';
  let txnLoading = true;

  async function loadDetail() {
    loading = true;
    loadError = '';
    try {
      detail = await get(`/api/admin/users/${childId}`);
    } catch (err) {
      loadError = err.message || 'Failed to load child';
    } finally {
      loading = false;
    }
  }

  async function loadTransactions() {
    txnLoading = true;
    try {
      let url = `/api/admin/users/${childId}/transactions?page=${txnPage}&per_page=20`;
      if (typeFilter) url += `&type=${typeFilter}`;
      const data = await get(url);
      transactions = data.transactions;
      total = data.total;
      pages = data.pages;
    } catch (err) {
      console.error('Failed to load transactions:', err);
    } finally {
      txnLoading = false;
    }
  }

  function changeFilter() {
    txnPage = 1;
    loadTransactions();
  }

  function prevPage() {
    if (txnPage > 1) {
      txnPage--;
      loadTransactions();
    }
  }

  function nextPage() {
    if (txnPage < pages) {
      txnPage++;
      loadTransactions();
    }
  }

  onMount(() => {
    loadDetail();
    loadTransactions();
    return () => {
      if (chart) chart.destroy();
    };
  });

  $: if (canvas && detail && detail.chart_data && detail.chart_data.labels.length > 0) {
    if (chart) chart.destroy();
    chart = new Chart(canvas, {
      type: 'line',
      data: {
        labels: detail.chart_data.labels,
        datasets: [
          {
            label: 'Balance',
            data: detail.chart_data.balances,
            borderColor: detail.balance >= 0 ? '#43a047' : '#e53935',
            backgroundColor: detail.balance >= 0 ? 'rgba(67,160,71,0.1)' : 'rgba(229,57,53,0.1)',
            fill: true,
            tension: 0.3
          }
        ]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { ticks: { callback: (v) => '$' + v.toFixed(2) } } }
      }
    });
  }
</script>

<p><a href="/admin">← Back to children</a></p>

{#if loading}
  <p aria-busy="true">Loading...</p>
{:else if loadError}
  <p style="color: red;">{loadError}</p>
{:else if detail}
  <hgroup>
    <h2>{detail.display_name}</h2>
    <p>@{detail.username} · {formatCurrency(detail.monthly_allowance)}/mo allowance</p>
  </hgroup>

  <div class="grid">
    <article class="text-center">
      <header>Balance</header>
      <p class="balance-display {detail.balance >= 0 ? 'balance-positive' : 'balance-negative'}">
        {formatCurrency(detail.balance)}
      </p>
    </article>
  </div>

  <div class="grid">
    <article class="text-center">
      <header>Lifetime Earned</header>
      <p class="stat balance-positive">{formatCurrency(detail.totals.earned)}</p>
    </article>
    <article class="text-center">
      <header>Interest Earned</header>
      <p class="stat balance-positive">{formatCurrency(detail.totals.interest)}</p>
    </article>
    <article class="text-center">
      <header>Penalties Paid</header>
      <p class="stat balance-negative">{formatCurrency(detail.totals.penalties)}</p>
    </article>
    <article class="text-center">
      <header>Total Withdrawn</header>
      <p class="stat balance-negative">{formatCurrency(detail.totals.withdrawn)}</p>
    </article>
  </div>

  <article>
    <header>Balance History (Last 90 Days)</header>
    {#if detail.chart_data.labels.length > 0}
      <canvas bind:this={canvas}></canvas>
    {:else}
      <p>No transactions yet.</p>
    {/if}
  </article>

  <article>
    <header>Transaction History</header>
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
      <label style="margin: 0;">
        Filter:
        <select bind:value={typeFilter} onchange={changeFilter} style="display: inline; width: auto; margin-left: 0.5rem;">
          <option value="">All types</option>
          <option value="income">Income</option>
          <option value="withdrawal">Withdrawals</option>
          <option value="interest">Interest</option>
          <option value="penalty">Penalties</option>
          <option value="adjustment">Adjustments</option>
        </select>
      </label>
      <small>{total} transaction{total !== 1 ? 's' : ''}</small>
    </div>

    {#if txnLoading}
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
                <td class={isDebitTxn(txn) ? 'balance-negative' : 'balance-positive'}>
                  {formatSignedAmount(txn)}
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
        <button class="outline" onclick={prevPage} disabled={txnPage <= 1}>Previous</button>
        <small>Page {txnPage} of {pages}</small>
        <button class="outline" onclick={nextPage} disabled={txnPage >= pages}>Next</button>
      </div>
    {/if}
  </article>
{/if}

<style>
  .stat {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0.25rem 0;
  }
</style>

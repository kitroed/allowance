<script>
	import { onMount } from 'svelte';
	import { get, post, put } from '$lib/api.js';
	import { formatCurrency } from '$lib/utils.js';

	let children = [];
	let loading = true;

	// Add child form
	let showAddForm = false;
	let newUsername = '';
	let newPassword = '';
	let newDisplayName = '';
	let newAllowance = '';
	let newStartingBalance = '';
	let newStartDate = '';
	let addError = '';
	let addSubmitting = false;

	// Edit child
	let editingId = null;
	let editDisplayName = '';
	let editAllowance = '';
	let editStartingBalance = '';
	let editStartDate = '';
	let editPassword = '';
	let editError = '';
	let editSubmitting = false;

	async function loadChildren() {
		try {
			children = await get('/api/admin/users');
		} catch (err) {
			console.error('Failed to load children:', err);
		} finally {
			loading = false;
		}
	}

	async function addChild(e) {
		e.preventDefault();
		addError = '';
		addSubmitting = true;
		try {
			await post('/api/admin/users', {
				username: newUsername,
				password: newPassword,
				display_name: newDisplayName,
				monthly_allowance: parseFloat(newAllowance) || 0,
				starting_balance: parseFloat(newStartingBalance) || 0,
				allowance_start_date: newStartDate || null
			});
			newUsername = '';
			newPassword = '';
			newDisplayName = '';
			newAllowance = '';
			newStartingBalance = '';
			newStartDate = '';
			showAddForm = false;
			loadChildren();
		} catch (err) {
			addError = err.message || 'Failed to add child';
		} finally {
			addSubmitting = false;
		}
	}

	function startEdit(child) {
		editingId = child.id;
		editDisplayName = child.display_name;
		editAllowance = child.monthly_allowance;
		editStartingBalance = child.starting_balance;
		editStartDate = child.allowance_start_date || '';
		editPassword = '';
		editError = '';
	}

	function cancelEdit() {
		editingId = null;
	}

	async function saveEdit(e) {
		e.preventDefault();
		editError = '';
		editSubmitting = true;
		try {
			const body = {
				display_name: editDisplayName,
				monthly_allowance: parseFloat(editAllowance) || 0,
				starting_balance: parseFloat(editStartingBalance) || 0,
				allowance_start_date: editStartDate || null
			};
			if (editPassword) body.password = editPassword;
			await put(`/api/admin/users/${editingId}`, body);
			editingId = null;
			loadChildren();
		} catch (err) {
			editError = err.message || 'Failed to update';
		} finally {
			editSubmitting = false;
		}
	}

	onMount(loadChildren);
</script>

<h2>Manage Children</h2>

<button onclick={() => (showAddForm = !showAddForm)}>
	{showAddForm ? 'Cancel' : 'Add Child'}
</button>

{#if showAddForm}
	<article>
		<header>Add New Child</header>
		<form onsubmit={addChild}>
			<div class="grid">
				<label>
					Display Name
					<input type="text" bind:value={newDisplayName} required />
				</label>
				<label>
					Username
					<input type="text" bind:value={newUsername} required />
				</label>
			</div>
			<div class="grid">
				<label>
					Password
					<input type="password" bind:value={newPassword} required />
				</label>
				<label>
					Monthly Allowance ($)
					<input type="number" step="0.01" min="0" bind:value={newAllowance} required />
				</label>
			</div>
			<div class="grid">
				<label>
					Starting Balance ($)
					<input type="number" step="0.01" bind:value={newStartingBalance} placeholder="0.00" />
				</label>
				<label>
					Allowance Start Date
					<input type="date" bind:value={newStartDate} />
				</label>
			</div>
			{#if addError}
				<p style="color: red;">{addError}</p>
			{/if}
			<button type="submit" aria-busy={addSubmitting} disabled={addSubmitting}>
				{addSubmitting ? 'Creating...' : 'Create Account'}
			</button>
		</form>
	</article>
{/if}

{#if loading}
	<p aria-busy="true">Loading children...</p>
{:else if children.length === 0}
	<p>No children added yet. Click "Add Child" to create an account.</p>
{:else}
	<figure>
		<table>
			<thead>
				<tr>
					<th>Name</th>
					<th>Username</th>
					<th>Monthly Allowance</th>
					<th>Balance</th>
					<th>Actions</th>
				</tr>
			</thead>
			<tbody>
				{#each children as child}
					{#if editingId === child.id}
						<tr>
							<td colspan="5">
								<form onsubmit={saveEdit} style="margin: 0;">
									<div class="grid">
										<label>
											Name
											<input type="text" bind:value={editDisplayName} required />
										</label>
										<label>
											Monthly Allowance ($)
											<input type="number" step="0.01" min="0" bind:value={editAllowance} required />
										</label>
									</div>
									<div class="grid">
										<label>
											Starting Balance ($)
											<input type="number" step="0.01" bind:value={editStartingBalance} />
										</label>
										<label>
											Start Date
											<input type="date" bind:value={editStartDate} />
										</label>
										<label>
											New Password (optional)
											<input type="password" bind:value={editPassword} placeholder="Leave blank to keep" />
										</label>
									</div>
									{#if editError}
										<p style="color: red;">{editError}</p>
									{/if}
									<div class="button-group">
										<button type="submit" aria-busy={editSubmitting} disabled={editSubmitting}>Save</button>
										<button type="button" class="outline" onclick={cancelEdit}>Cancel</button>
									</div>
								</form>
							</td>
						</tr>
					{:else}
						<tr>
							<td>{child.display_name}</td>
							<td>{child.username}</td>
							<td>{formatCurrency(child.monthly_allowance)}</td>
							<td class={child.balance >= 0 ? 'balance-positive' : 'balance-negative'}>
								{formatCurrency(child.balance)}
							</td>
							<td>
								<button class="outline" onclick={() => startEdit(child)}>Edit</button>
							</td>
						</tr>
					{/if}
				{/each}
			</tbody>
		</table>
	</figure>
{/if}

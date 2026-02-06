<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { get, post } from '$lib/api.js';
	import { user } from '$lib/stores.js';
	import '../app.css';

	let loading = true;

	onMount(async () => {
		try {
			const data = await get('/api/me');
			user.set(data.user);
		} catch {
			user.set(null);
		}
		loading = false;
	});

	async function logout() {
		await post('/api/logout');
		user.set(null);
		goto('/login');
	}

	$: currentPath = $page.url.pathname;
	$: if (!loading && !$user && currentPath !== '/login') {
		goto('/login');
	}
</script>

{#if loading}
	<main class="container">
		<p aria-busy="true">Loading...</p>
	</main>
{:else}
	{#if $user}
		<nav class="container-fluid">
			<ul>
				<li><strong>Allowance</strong></li>
			</ul>
			<ul>
				{#if !$user.is_admin}
					<li><a href="/dashboard" class:active={currentPath === '/dashboard'}>Dashboard</a></li>
					<li><a href="/transactions" class:active={currentPath === '/transactions'}>History</a></li>
					<li><a href="/withdraw" class:active={currentPath === '/withdraw'}>Withdraw</a></li>
				{/if}
				{#if $user.is_admin}
					<li><a href="/admin" class:active={currentPath === '/admin'}>Children</a></li>
					<li><a href="/admin/requests" class:active={currentPath === '/admin/requests'}>Requests</a></li>
				{/if}
				<li>
					<a href="/login" role="button" class="outline" onclick={logout}>Logout</a>
				</li>
			</ul>
		</nav>
	{/if}
	<main class="container">
		<slot />
	</main>
{/if}

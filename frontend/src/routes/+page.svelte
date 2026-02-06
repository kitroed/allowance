<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores.js';

	onMount(() => {
		const unsub = user.subscribe((u) => {
			if (u) {
				goto(u.is_admin ? '/admin' : '/dashboard');
			} else {
				goto('/login');
			}
		});
		return unsub;
	});
</script>

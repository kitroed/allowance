<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { user } from '$lib/stores.js';

  onMount(() => {
    const unsub = user.subscribe((u) => {
      if (u && !u.is_admin) {
        goto('/dashboard');
      }
    });
    return unsub;
  });
</script>

<slot />

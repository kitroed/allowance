<script>
  import { goto } from '$app/navigation';
  import { post } from '$lib/api.js';
  import { user } from '$lib/stores.js';

  let username = '';
  let password = '';
  let error = '';
  let submitting = false;

  async function handleLogin(e) {
    e.preventDefault();
    error = '';
    submitting = true;
    try {
      const data = await post('/api/login', { username, password });
      user.set(data.user);
      goto(data.user.is_admin ? '/admin' : '/dashboard');
    } catch (err) {
      error = err.message || 'Login failed';
    } finally {
      submitting = false;
    }
  }
</script>

<article class="grid" style="max-width: 400px; margin: 2rem auto;">
  <div>
    <hgroup>
      <h2>Login</h2>
      <p>Sign in to your allowance account</p>
    </hgroup>
    <form onsubmit={handleLogin}>
      <label>
        Username
        <input type="text" bind:value={username} required autocomplete="username" />
      </label>
      <label>
        Password
        <input type="password" bind:value={password} required autocomplete="current-password" />
      </label>
      {#if error}
        <p style="color: red;">{error}</p>
      {/if}
      <button type="submit" aria-busy={submitting} disabled={submitting}>
        {submitting ? 'Signing in...' : 'Login'}
      </button>
    </form>
  </div>
</article>

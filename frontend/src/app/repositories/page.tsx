'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import { GitBranch, LoaderCircle, RefreshCw, Trash2 } from 'lucide-react';
import EmptyState from '@/components/ui/EmptyState';
import PageHeader from '@/components/ui/PageHeader';
import Panel from '@/components/ui/Panel';
import { useAuth } from '@/lib/auth';
import type { Repository } from '@/lib/types';

export default function RepositoriesPage() {
  const { token, isAuthenticated, isLoading: authLoading, loginUrl } = useAuth();
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [owner, setOwner] = useState('');
  const [repository, setRepository] = useState('');
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const loadRepositories = useCallback(async () => {
    if (!token) return;
    const response = await fetch('/api/v1/repositories', {
      headers: { Authorization: `Bearer ${token}` },
      cache: 'no-store',
    });
    if (!response.ok) throw new Error('Could not load repositories');
    setRepositories(await response.json());
  }, [token]);

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      loadRepositories().catch((error: Error) => setMessage(error.message));
    }
  }, [authLoading, isAuthenticated, loadRepositories]);

  async function connect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    setBusy('connect');
    setMessage(null);
    try {
      const response = await fetch('/api/v1/repositories', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ owner: owner.trim(), repository: repository.trim() }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail ?? 'Could not connect repository');
      }
      setOwner('');
      setRepository('');
      setMessage('Repository connected. Run sync to import recent pull-request signals.');
      await loadRepositories();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not connect repository');
    } finally {
      setBusy(null);
    }
  }

  async function mutate(id: string, action: 'sync' | 'disconnect') {
    if (!token) return;
    setBusy(id);
    setMessage(null);
    try {
      const response = await fetch(
        action === 'sync' ? `/api/v1/repositories/${id}/sync` : `/api/v1/repositories/${id}`,
        {
          method: action === 'sync' ? 'POST' : 'DELETE',
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail ?? `Could not ${action} repository`);
      }
      setMessage(action === 'sync' ? 'Repository signals synchronized.' : 'Repository disconnected.');
      await loadRepositories();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : `Could not ${action} repository`);
    } finally {
      setBusy(null);
    }
  }

  if (authLoading) {
    return <div className="p-8"><PageHeader title="Repositories" subtitle="Loading…" /></div>;
  }

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col gap-7 p-8 animate-fadein">
        <PageHeader title="Repositories" subtitle="Connect GitHub to collect deployment risk signals." />
        <Panel title="GitHub connection">
          <div className="p-7">
            <p className="mb-5 text-sm text-slate-400">
              Sign in before connecting repositories or importing pull-request history.
            </p>
            <a href={loginUrl} className="inline-flex rounded-lg bg-cyan-400 px-4 py-2.5 text-sm font-bold text-slate-950">
              Sign in with GitHub
            </a>
          </div>
        </Panel>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-7 p-8 animate-fadein">
      <PageHeader
        title="Repositories"
        subtitle="Connect source repositories and synchronize pull-request risk signals."
      />

      <Panel title="Connect a repository">
        <form onSubmit={connect} className="grid gap-4 p-5 sm:grid-cols-[1fr_1fr_auto]">
          <label className="grid gap-1.5 text-xs font-semibold text-slate-400">
            GitHub owner
            <input
              required
              value={owner}
              onChange={(event) => setOwner(event.target.value)}
              placeholder="your-org"
              className="rounded-lg border border-white/10 bg-white/[0.03] px-3.5 py-2.5 text-sm text-white outline-none placeholder:text-slate-600"
            />
          </label>
          <label className="grid gap-1.5 text-xs font-semibold text-slate-400">
            Repository
            <input
              required
              value={repository}
              onChange={(event) => setRepository(event.target.value)}
              placeholder="payments-api"
              className="rounded-lg border border-white/10 bg-white/[0.03] px-3.5 py-2.5 text-sm text-white outline-none placeholder:text-slate-600"
            />
          </label>
          <button
            disabled={busy === 'connect'}
            className="self-end rounded-lg bg-gradient-to-r from-cyan-400 to-emerald-400 px-5 py-2.5 text-sm font-bold text-slate-950 disabled:opacity-50"
          >
            {busy === 'connect' ? 'Connecting…' : 'Connect'}
          </button>
        </form>
      </Panel>

      {message && (
        <p role="status" className="rounded-lg border border-cyan-500/15 bg-cyan-500/[0.05] px-4 py-3 text-sm text-cyan-200">
          {message}
        </p>
      )}

      <Panel title={`${repositories.length} connected`}>
        {repositories.length === 0 ? (
          <EmptyState
            icon={<GitBranch className="h-5 w-5 text-cyan-400" />}
            title="No repositories connected"
            description="Connect a public GitHub repository to begin collecting change-risk signals."
          />
        ) : (
          <div className="divide-y divide-white/[0.05]">
            {repositories.map((item) => (
              <div key={item.id} className="flex items-center gap-4 px-5 py-4">
                <GitBranch className="h-4 w-4 text-cyan-400" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-white">{item.owner}/{item.repository_name}</p>
                  <p className="text-xs text-slate-500">{item.default_branch} · {item.status}</p>
                </div>
                <button
                  aria-label={`Sync ${item.repository_name}`}
                  disabled={busy === item.id}
                  onClick={() => mutate(item.id, 'sync')}
                  className="rounded-lg border border-white/10 p-2 text-slate-400 hover:text-cyan-300 disabled:opacity-40"
                >
                  {busy === item.id ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                </button>
                <button
                  aria-label={`Disconnect ${item.repository_name}`}
                  disabled={busy === item.id}
                  onClick={() => mutate(item.id, 'disconnect')}
                  className="rounded-lg border border-white/10 p-2 text-slate-400 hover:text-red-400 disabled:opacity-40"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}

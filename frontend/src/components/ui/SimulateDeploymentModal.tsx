'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createDeployment } from '@/lib/api';
import { Rocket, X, Loader2 } from 'lucide-react';

export default function SimulateDeploymentModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [serviceName, setServiceName] = useState('api');
  const [environment, setEnvironment] = useState('production');
  const router = useRouter();

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Generate a random 7-character hex string for the fake git SHA
    const fakeSha = Math.random().toString(16).substring(2, 9);
    const fakeVersion = `v1.0.${Math.floor(Math.random() * 100)}`;

    try {
      const dep = await createDeployment({
        service_name: serviceName,
        environment,
        git_sha: fakeSha,
        version: fakeVersion,
        deployed_by: 'Simulated User',
      });
      
      setIsOpen(false);
      // Navigate to the new deployment
      router.push(`/deployments/${dep.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to simulate deployment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-md transition-colors"
      >
        <Rocket className="w-4 h-4" />
        Simulate Deployment
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadein">
          <div className="bg-slate-900 border border-slate-700 rounded-lg shadow-xl w-full max-w-md overflow-hidden flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/50">
              <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
                <Rocket className="w-5 h-5 text-blue-400" />
                Simulate Deployment
              </h2>
              <button 
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={handleSimulate} className="p-4 flex flex-col gap-4">
              {error && (
                <div className="p-3 bg-red-900/30 border border-red-500/50 text-red-200 text-sm rounded-md">
                  {error}
                </div>
              )}
              
              <p className="text-sm text-slate-400">
                This will create a mock deployment and instantly trigger the AI Risk Engine to evaluate it.
              </p>
              
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-slate-300">Service Name</label>
                <input 
                  type="text" 
                  value={serviceName}
                  onChange={(e) => setServiceName(e.target.value)}
                  className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. api, frontend, worker"
                  required
                />
              </div>
              
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-slate-300">Environment</label>
                <select 
                  value={environment}
                  onChange={(e) => setEnvironment(e.target.value)}
                  className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="production">production</option>
                  <option value="staging">staging</option>
                  <option value="development">development</option>
                </select>
              </div>

              <div className="mt-4 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-600/50 text-white font-medium rounded-md transition-colors"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Rocket className="w-4 h-4" />}
                  Deploy Now
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

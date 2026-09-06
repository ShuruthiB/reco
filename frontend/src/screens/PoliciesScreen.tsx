import { useState, useEffect } from 'react';
import { Card, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { ShieldCheck, Plus, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/Button';

export function PoliciesScreen() {
  const [policies, setPolicies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ name: '', description: '', rules: '' });

  const fetchPolicies = async () => {
    try {
      const res = await fetch('/api/policies');
      if (res.ok) {
        setPolicies(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const rulesArray = formData.rules.split('\n').filter(r => r.trim().length > 0);
      const res = await fetch('/api/policies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...formData, rules: rulesArray })
      });
      if (res.ok) {
        setShowModal(false);
        setFormData({ name: '', description: '', rules: '' });
        fetchPolicies();
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Policies & Guardrails</h1>
          <p className="text-sm text-slate-500">Hard rules that constrain AI decision-making.</p>
        </div>
        <Button onClick={() => setShowModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Policy
        </Button>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 z-50 flex items-center justify-center">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <h2 className="font-semibold text-slate-900">Define New Policy</h2>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">&times;</button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Policy Name</label>
                <input required type="text" className="w-full p-2 border border-slate-300 rounded-lg text-sm" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} placeholder="e.g. VIP Customer Protection" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                <input type="text" className="w-full p-2 border border-slate-300 rounded-lg text-sm" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Rules (One per line)</label>
                <textarea required rows={4} className="w-full p-2 border border-slate-300 rounded-lg text-sm" value={formData.rules} onChange={e => setFormData({...formData, rules: e.target.value})} placeholder="NEVER escalate to collections for VIPs&#10;ALWAYS waive fees for VIPs" />
              </div>
              <div className="pt-4 flex justify-end gap-3 border-t border-slate-100 mt-6">
                <Button variant="outline" type="button" onClick={() => setShowModal(false)}>Cancel</Button>
                <Button type="submit">Create Policy</Button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="grid gap-6">
        {policies.length === 0 ? (
          <div className="text-center py-12 text-slate-500">No policies defined.</div>
        ) : policies.map(policy => (
          <Card key={policy.id}>
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-6 border-b border-slate-100 bg-slate-50 rounded-t-xl gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-white border border-slate-200 flex items-center justify-center">
                  <ShieldCheck className="w-5 h-5 text-indigo-600" />
                </div>
                <div>
                  <CardTitle className="text-lg mb-1">{policy.name}</CardTitle>
                  <p className="text-xs text-slate-500">{policy.description}</p>
                </div>
              </div>
              <Badge variant={policy.status === 'active' ? 'success' : 'neutral'}>
                {policy.status.toUpperCase()}
              </Badge>
            </div>
            <CardContent className="pt-6">
              <h4 className="text-sm font-semibold text-slate-900 mb-3">Active Rules</h4>
              <ul className="space-y-2">
                {policy.rules.map((rule: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-slate-700 bg-white p-3 border border-slate-200 rounded-md shadow-sm">
                    <span className="font-mono text-xs text-indigo-500 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-100 mt-0.5">R{idx + 1}</span>
                    {rule}
                  </li>
                ))}
              </ul>
              <div className="mt-4 pt-4 border-t border-slate-100 flex justify-between items-center text-xs text-slate-500">
                <span>Last updated: {new Date(policy.last_updated).toLocaleString()}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

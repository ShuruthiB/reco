import { MOCK_POLICIES } from '../data/mock';
import { Card, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { ShieldCheck, Plus } from 'lucide-react';
import { Button } from '../components/ui/Button';

export function PoliciesScreen() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Policies & Guardrails</h1>
          <p className="text-sm text-slate-500">Hard rules that constrain AI decision-making.</p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          New Policy
        </Button>
      </div>

      <div className="grid gap-6">
        {MOCK_POLICIES.map(policy => (
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
                {policy.rules.map((rule, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-slate-700 bg-white p-3 border border-slate-200 rounded-md shadow-sm">
                    <span className="font-mono text-xs text-indigo-500 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-100 mt-0.5">R{idx + 1}</span>
                    {rule}
                  </li>
                ))}
              </ul>
              <div className="mt-4 pt-4 border-t border-slate-100 flex justify-between items-center text-xs text-slate-500">
                <span>Last updated: {new Date(policy.lastUpdated).toLocaleString()}</span>
                <Button variant="ghost" size="sm">Edit Rules</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

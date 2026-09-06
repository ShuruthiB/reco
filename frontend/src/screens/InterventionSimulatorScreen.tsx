import { useState, type FormEvent } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Sparkles, ArrowRight } from 'lucide-react';

interface SimulationCandidate {
  name: string;
  uplift: number;
  cost: number;
  net: number;
  policy_approved: boolean;
}

interface SimulationResult {
  baseline: number;
  recommended_action: string;
  candidates: SimulationCandidate[];
}

function parseSimulationResult(value: unknown): SimulationResult {
  if (!value || typeof value !== 'object') {
    throw new Error('The simulation returned an invalid response.');
  }

  const response = value as Record<string, unknown>;
  if (typeof response.recommended_action !== 'string' || !Array.isArray(response.candidates)) {
    throw new Error('The simulation returned an invalid response.');
  }

  const candidates = response.candidates.map((candidate) => {
    if (!candidate || typeof candidate !== 'object') {
      throw new Error('The simulation returned an invalid candidate.');
    }

    const item = candidate as Record<string, unknown>;
    if (typeof item.name !== 'string' || typeof item.policy_approved !== 'boolean') {
      throw new Error('The simulation returned an invalid candidate.');
    }

    return {
      name: item.name,
      uplift: Number(item.uplift),
      cost: Number(item.cost),
      net: Number(item.net),
      policy_approved: item.policy_approved,
    };
  });

  if (
    !Number.isFinite(Number(response.baseline)) ||
    candidates.some((candidate) => !Number.isFinite(candidate.uplift) || !Number.isFinite(candidate.cost) || !Number.isFinite(candidate.net))
  ) {
    throw new Error('The simulation returned invalid numeric values.');
  }

  return {
    baseline: Number(response.baseline),
    recommended_action: response.recommended_action,
    candidates,
  };
}

export function InterventionSimulatorScreen() {
  const [amount, setAmount] = useState('500');
  const [risk, setRisk] = useState('high');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSimulate = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/simulations/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: Number(amount), currency: 'USD', risk_profile: risk }),
      });

      if (!response.ok) {
        throw new Error('The simulation could not be completed.');
      }

      setResult(parseSimulationResult(await response.json()));
    } catch (requestError) {
      console.error(requestError);
      setResult(null);
      setError('Unable to connect to the simulation service.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Intervention Simulator</h1>
          <p className="text-sm text-slate-500">Test hypothetical recovery scenarios against the current ML models and policies.</p>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Scenario Parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSimulate} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Transaction Amount ($)</label>
                <input 
                  type="number" 
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full h-10 px-3 rounded-md border border-slate-200 bg-white text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Risk Profile</label>
                <select 
                  value={risk}
                  onChange={(e) => setRisk(e.target.value)}
                  className="w-full h-10 px-3 rounded-md border border-slate-200 bg-white text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="low">Low Risk (High Intent)</option>
                  <option value="medium">Medium Risk</option>
                  <option value="high">High Risk (Low Intent)</option>
                </select>
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Simulating...' : 'Run Simulation'}
                {!loading && <Sparkles className="w-4 h-4 ml-2" />}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Simulation Results</CardTitle>
          </CardHeader>
          <CardContent>
            {!result && !loading && (
              <div className="h-64 flex items-center justify-center border-2 border-dashed border-slate-200 rounded-lg bg-slate-50">
                <p className="text-slate-500 text-sm">Run a simulation to see expected net contributions.</p>
              </div>
            )}
            {loading && (
              <div className="h-64 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
              </div>
            )}
            {error && !loading && (
              <div className="h-64 flex items-center justify-center border border-rose-200 rounded-lg bg-rose-50">
                <p className="text-rose-700 text-sm">{error}</p>
              </div>
            )}
            {result && !loading && (
              <div className="space-y-6">
                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 flex justify-between items-center">
                  <div>
                    <p className="text-sm text-slate-500 mb-1">Baseline Recovery Probability</p>
                    <p className="text-2xl font-bold text-slate-900">{(result.baseline * 100).toFixed(1)}%</p>
                  </div>
                  <ArrowRight className="text-slate-300" />
                  <div className="text-right">
                    <p className="text-sm text-slate-500 mb-1">Best Recommended Action</p>
                    <p className="text-lg font-bold text-indigo-600">{result.recommended_action.replace(/_/g, ' ')}</p>
                  </div>
                </div>

                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-slate-900">Ranked Interventions</h4>
                  {result.candidates.map((c) => (
                    <div key={c.name} className={`flex items-center justify-between p-3 rounded-md border ${c.name === result.recommended_action ? 'border-indigo-200 bg-indigo-50/50' : 'border-slate-100 bg-white'}`}>
                      <div className="flex-1">
                        <span className="font-medium text-sm text-slate-900">{c.name.replace(/_/g, ' ')}</span>
                      </div>
                      <div className="flex-1 text-center">
                        <span className="text-xs text-slate-500 block">Incremental Uplift</span>
                        <span className="text-sm font-medium text-emerald-600 numeric-data">+{(c.uplift * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex-1 text-center">
                        <span className="text-xs text-slate-500 block">Cost</span>
                        <span className="text-sm font-medium text-rose-600 numeric-data">-${c.cost.toFixed(2)}</span>
                      </div>
                      <div className="flex-1 text-right">
                        <span className="text-xs text-slate-500 block">Net Expected</span>
                        <span className={`text-sm font-bold numeric-data ${c.net > 0 ? 'text-indigo-600' : 'text-slate-500'}`}>${c.net.toFixed(2)}</span>
                        {!c.policy_approved && <span className="text-xs text-rose-600 block">Policy rejected</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

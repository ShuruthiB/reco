import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { TestTube2, AlertCircle, Plus, CheckCircle2 } from 'lucide-react';

interface Experiment {
  id: string;
  name: string;
  description: string;
  status: string;
  startDate: string;
  total_transactions: number;
  control_recovery_rate: number;
  treatment_recovery_rate: number;
  estimated_lift_points: number;
  recovered_gross_value: number;
  intervention_cost: number;
  net_incremental_contribution: number;
  has_statistical_significance: boolean;
  control_count: number;
  treatment_count: number;
}

export function ExperimentsScreen() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    hypothesis: '',
    control_percentage: 10,
    treatment_action: 'RETRY',
    duration_days: 14,
    budget_minor: 100000
  });

  const fetchExperiments = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/experiments');
      if (res.ok) {
        const data = await res.json();
        setExperiments(data);
      } else {
        setExperiments([]);
      }
    } catch (err) {
      console.error(err);
      setExperiments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExperiments();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch('http://localhost:8000/api/experiments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        setShowModal(false);
        fetchExperiments();
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return <div className="p-8 text-slate-500">Loading experiments...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Experiments</h1>
          <p className="text-sm text-slate-500">Measure true incrementality with randomized holdouts and A/B tests.</p>
        </div>
        <Button onClick={() => setShowModal(true)} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Create Experiment
        </Button>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 z-50 flex items-center justify-center">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <h2 className="font-semibold text-slate-900">Define New Experiment</h2>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">&times;</button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Experiment Name</label>
                <input required type="text" className="w-full p-2 border border-slate-300 rounded-lg text-sm" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} placeholder="e.g. Incentive Escalation Test" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Hypothesis</label>
                <textarea required className="w-full p-2 border border-slate-300 rounded-lg text-sm" value={formData.hypothesis} onChange={e => setFormData({...formData, hypothesis: e.target.value})} placeholder="Offering a 10% discount will yield higher net contribution." />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Control Group %</label>
                  <input required type="number" min="0" max="100" className="w-full p-2 border border-slate-300 rounded-lg text-sm" value={formData.control_percentage} onChange={e => setFormData({...formData, control_percentage: parseInt(e.target.value)})} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Treatment Action</label>
                  <select className="w-full p-2 border border-slate-300 rounded-lg text-sm" value={formData.treatment_action} onChange={e => setFormData({...formData, treatment_action: e.target.value})}>
                    <option value="RETRY">Retry</option>
                    <option value="REMINDER">Reminder</option>
                    <option value="INCENTIVE">Incentive</option>
                    <option value="ALTERNATIVE_METHOD">Alternative Method</option>
                  </select>
                </div>
              </div>
              <div className="pt-4 flex justify-end gap-3 border-t border-slate-100 mt-6">
                <Button variant="outline" type="button" onClick={() => setShowModal(false)}>Cancel</Button>
                <Button type="submit">Start Experiment</Button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="grid gap-6">
        {experiments.length === 0 ? (
          <div className="text-center py-12 bg-slate-50 border border-slate-200 rounded-lg border-dashed">
            <TestTube2 className="mx-auto h-12 w-12 text-slate-400 mb-4" />
            <h3 className="text-sm font-semibold text-slate-900">No experiments running</h3>
            <p className="text-sm text-slate-500 mt-1">Get started by creating your first A/B test.</p>
          </div>
        ) : (
          experiments.map(exp => (
            <Card key={exp.id}>
              <CardHeader className="flex flex-row items-center justify-between bg-slate-50 border-b border-slate-100 pb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-indigo-100 text-indigo-700 rounded-lg">
                    <TestTube2 className="w-5 h-5" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{exp.name}</CardTitle>
                    <p className="text-xs text-slate-500 mt-1">Started {new Date(exp.startDate || '').toLocaleDateString()}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {!exp.has_statistical_significance && (
                    <Badge variant="warning" className="flex items-center gap-1 bg-yellow-100 text-yellow-800">
                      <AlertCircle className="w-3 h-3" />
                      Observational (N&lt;100)
                    </Badge>
                  )}
                  {exp.has_statistical_significance && (
                    <Badge variant="success" className="flex items-center gap-1 bg-emerald-100 text-emerald-800">
                      <CheckCircle2 className="w-3 h-3" />
                      Statistically Significant
                    </Badge>
                  )}
                  <Badge variant={exp.status === 'active' ? 'success' : 'neutral'}>
                    {exp.status.toUpperCase()}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="grid md:grid-cols-2 gap-8">
                  {/* Left Column: Recovery Rates */}
                  <div className="space-y-6">
                    <div>
                      <h4 className="text-sm font-semibold text-slate-900 mb-4 uppercase tracking-wider text-slate-500">Recovery Metrics</h4>
                      
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-sm font-medium text-slate-700">CONTROL Recovery:</span>
                        <span className="text-lg font-semibold text-slate-900">{(exp.control_recovery_rate * 100).toFixed(1)}%</span>
                      </div>
                      
                      <div className="flex justify-between items-center mb-6">
                        <span className="text-sm font-medium text-slate-700">TREATMENT Recovery:</span>
                        <span className="text-lg font-semibold text-slate-900">{(exp.treatment_recovery_rate * 100).toFixed(1)}%</span>
                      </div>
                      
                      <div className="p-4 bg-indigo-50 border border-indigo-100 rounded-lg flex justify-between items-center">
                        <span className="text-sm font-semibold text-indigo-900">Estimated incremental lift:</span>
                        <span className={`text-lg font-bold ${exp.estimated_lift_points > 0 ? 'text-emerald-600' : 'text-slate-700'}`}>
                          {exp.estimated_lift_points > 0 ? '+' : ''}{exp.estimated_lift_points.toFixed(1)} percentage points
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Right Column: Financials */}
                  <div className="space-y-6">
                    <div>
                      <h4 className="text-sm font-semibold text-slate-900 mb-4 uppercase tracking-wider text-slate-500">Financial Impact</h4>
                      
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-sm text-slate-600">Gross recovered:</span>
                        <span className="text-base font-medium text-blue-600 numeric-data">₹{exp.recovered_gross_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                      </div>
                      
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-sm text-slate-600">Intervention cost:</span>
                        <span className="text-base font-medium text-rose-600 numeric-data">-₹{exp.intervention_cost.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                      </div>
                      
                      <div className="h-px bg-slate-200 my-4 w-full" />
                      
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-bold text-slate-900">Net incremental contribution:</span>
                        <span className={`text-xl font-bold numeric-data ${exp.net_incremental_contribution >= 0 ? 'text-indigo-600' : 'text-rose-600'}`}>
                          {exp.net_incremental_contribution >= 0 ? '' : '-'}₹{Math.abs(exp.net_incremental_contribution).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                        </span>
                      </div>
                    </div>
                  </div>

                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}

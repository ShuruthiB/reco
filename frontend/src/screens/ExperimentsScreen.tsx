import { MOCK_EXPERIMENTS } from '../data/mock';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { TestTube2, ArrowUpRight } from 'lucide-react';

export function ExperimentsScreen() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Experiments</h1>
          <p className="text-sm text-slate-500">Measure true incrementality with randomized holdouts and A/B tests.</p>
        </div>
      </div>

      <div className="grid gap-6">
        {MOCK_EXPERIMENTS.map(exp => (
          <Card key={exp.id}>
            <CardHeader className="flex flex-row items-center justify-between bg-slate-50 border-b border-slate-100 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-100 text-indigo-700 rounded-lg">
                  <TestTube2 className="w-5 h-5" />
                </div>
                <div>
                  <CardTitle className="text-lg">{exp.name}</CardTitle>
                  <p className="text-xs text-slate-500 mt-1">Started {new Date(exp.startDate).toLocaleDateString()}</p>
                </div>
              </div>
              <Badge variant={exp.status === 'active' ? 'success' : 'neutral'}>
                {exp.status.toUpperCase()}
              </Badge>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid md:grid-cols-4 gap-8">
                <div className="col-span-1 space-y-6">
                  <div>
                    <p className="text-sm text-slate-500 mb-1">Total Transactions in Test</p>
                    <p className="text-2xl font-bold text-slate-900">{exp.totalTransactions.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500 mb-1">Measured Incremental Revenue</p>
                    <div className="flex items-center gap-2">
                      <p className="text-2xl font-bold text-emerald-600">${exp.incrementalRevenue.toLocaleString()}</p>
                      <ArrowUpRight className="w-5 h-5 text-emerald-500" />
                    </div>
                  </div>
                </div>
                
                <div className="col-span-3">
                  <h4 className="text-sm font-semibold text-slate-900 mb-4">Treatment Arms</h4>
                  <div className="space-y-3">
                    {exp.arms.map(arm => (
                      <div key={arm.name} className="flex items-center justify-between p-3 rounded border border-slate-200 bg-white shadow-sm">
                        <div className="flex items-center gap-4 w-1/3">
                          <div className={`w-3 h-3 rounded-full ${arm.incrementalUplift > 0 ? 'bg-indigo-500' : 'bg-slate-300'}`} />
                          <span className="font-medium text-sm text-slate-800">{arm.name}</span>
                        </div>
                        <div className="w-1/3">
                          <div className="w-full bg-slate-100 rounded-full h-2 mb-1">
                            <div className="bg-slate-400 h-2 rounded-full" style={{ width: `${arm.trafficShare * 100}%` }} />
                          </div>
                          <span className="text-xs text-slate-500">{(arm.trafficShare * 100)}% Traffic Allocation</span>
                        </div>
                        <div className="w-1/4 text-right">
                          <span className="block text-xs text-slate-500">Incremental Uplift</span>
                          <span className={`font-bold ${arm.incrementalUplift > 0 ? 'text-emerald-600' : 'text-slate-600'}`}>
                            {arm.incrementalUplift > 0 ? '+' : ''}{(arm.incrementalUplift * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

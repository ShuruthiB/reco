import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Wallet, TrendingDown } from 'lucide-react';
import { MetricCard } from '../components/ui/MetricCard';

export function RecoveryBudgetScreen() {
  const totalBudget = 25000;
  const consumed = 4200;
  const remaining = totalBudget - consumed;
  const percentage = (consumed / totalBudget) * 100;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Recovery Budget</h1>
          <p className="text-sm text-slate-500">Manage incentive spend limits for the current billing cycle.</p>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <MetricCard
          title="Total Monthly Budget"
          value={`$${totalBudget.toLocaleString()}`}
          icon={<Wallet className="h-4 w-4" />}
        />
        <MetricCard
          title="Consumed (MTD)"
          value={`$${consumed.toLocaleString()}`}
          icon={<TrendingDown className="h-4 w-4 text-red-500" />}
          highlight="brand"
        />
        <MetricCard
          title="Remaining Runway"
          value={`$${remaining.toLocaleString()}`}
          subtitle={`${(100 - percentage).toFixed(1)}% remaining`}
          highlight={percentage > 90 ? 'positive' : 'neutral'}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Budget Utilization</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 pt-4">
            <div className="flex justify-between text-sm font-medium mb-1">
              <span>{percentage.toFixed(1)}% Consumed</span>
              <span className="text-slate-500">Reset in 14 days</span>
            </div>
            <div className="h-4 w-full bg-slate-100 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all ${percentage > 90 ? 'bg-red-500' : percentage > 75 ? 'bg-yellow-500' : 'bg-indigo-500'}`}
                style={{ width: `${percentage}%` }}
              />
            </div>
            <p className="text-xs text-slate-500 pt-2">
              The AI Decision engine is constrained by this budget. If the budget is exhausted, it will only recommend zero-cost interventions (like emails or retries) until the cycle resets.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

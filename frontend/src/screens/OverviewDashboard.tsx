import { MetricCard } from '../components/ui/MetricCard';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { MOCK_DASHBOARD_METRICS } from '../data/mock';
import { DollarSign, ShieldAlert, Sparkles, RefreshCcw } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const formatCurrency = (val: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);

const chartData = [
  { name: 'Mon', gross: 4000, incremental: 2400 },
  { name: 'Tue', gross: 3000, incremental: 1398 },
  { name: 'Wed', gross: 2000, incremental: 9800 },
  { name: 'Thu', gross: 2780, incremental: 3908 },
  { name: 'Fri', gross: 1890, incremental: 4800 },
  { name: 'Sat', gross: 2390, incremental: 3800 },
  { name: 'Sun', gross: 3490, incremental: 4300 },
];

export function OverviewDashboard() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Overview</h1>
          <p className="text-sm text-slate-500">Real-time revenue experimentation and recovery performance.</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Revenue at Risk"
          value={formatCurrency(MOCK_DASHBOARD_METRICS.revenueAtRisk)}
          icon={<ShieldAlert className="h-4 w-4" />}
          trend={{ value: -2.4, label: "from last week" }}
        />
        <MetricCard
          title="Natural Recovery (Gross)"
          value={formatCurrency(MOCK_DASHBOARD_METRICS.naturalRecovery)}
          icon={<RefreshCcw className="h-4 w-4" />}
          trend={{ value: 1.2, label: "baseline trend" }}
        />
        <MetricCard
          title="AI Incremental Revenue"
          value={formatCurrency(MOCK_DASHBOARD_METRICS.aiIncrementalRevenue)}
          icon={<Sparkles className="h-4 w-4" />}
          highlight="brand"
          trend={{ value: 14.5, label: "uplift vs baseline" }}
        />
        <MetricCard
          title="Net Incremental Revenue"
          value={formatCurrency(MOCK_DASHBOARD_METRICS.netIncrementalRevenue)}
          subtitle={`After ${formatCurrency(MOCK_DASHBOARD_METRICS.interventionCost)} intervention cost`}
          icon={<DollarSign className="h-4 w-4 text-emerald-600" />}
          highlight="positive"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Recovery Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorGross" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#94a3b8" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorInc" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} tickFormatter={(value) => `$${value}`} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)' }}
                  />
                  <Area type="monotone" dataKey="gross" stroke="#94a3b8" fillOpacity={1} fill="url(#colorGross)" name="Gross Recovery" />
                  <Area type="monotone" dataKey="incremental" stroke="#4f46e5" fillOpacity={1} fill="url(#colorInc)" name="Incremental Recovery" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Intervention Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
             <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={[
                  { name: 'Retry', net: 4000, cost: 200 },
                  { name: 'Email', net: 3000, cost: 100 },
                  { name: 'SMS', net: 2000, cost: 500 },
                  { name: 'Discount', net: 2780, cost: 1200 },
                ]} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} tickFormatter={(value) => `$${value}`} />
                  <Tooltip cursor={{ fill: '#f8fafc' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                  <Bar dataKey="net" fill="#10b981" name="Net Revenue" radius={[4, 4, 0, 0]} barSize={32} />
                  <Bar dataKey="cost" fill="#ef4444" name="Cost" radius={[4, 4, 0, 0]} barSize={32} />
                </BarChart>
              </ResponsiveContainer>
             </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

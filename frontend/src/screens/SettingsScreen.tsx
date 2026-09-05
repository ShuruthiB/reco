import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

export function SettingsScreen() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Settings</h1>
          <p className="text-sm text-slate-500">Manage merchant account, users, and API integrations.</p>
        </div>
      </div>

      <div className="grid gap-6 max-w-3xl">
        <Card>
          <CardHeader>
            <CardTitle>Merchant Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-700">Company Name</label>
                <input type="text" defaultValue="Acme Corp" className="w-full h-9 px-3 rounded-md border border-slate-200 bg-slate-50 text-sm outline-none" disabled />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-700">Merchant ID</label>
                <input type="text" defaultValue="m_837294827" className="w-full h-9 px-3 rounded-md border border-slate-200 bg-slate-50 text-sm outline-none font-mono" disabled />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Razorpay Integration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 border border-slate-200 rounded-md bg-slate-50">
              <div>
                <p className="text-sm font-medium text-slate-900">Live Mode</p>
                <p className="text-xs text-slate-500">Connected on Aug 15, 2026</p>
              </div>
              <Button variant="outline" size="sm">Rotate Keys</Button>
            </div>
            <div className="flex items-center justify-between p-3 border border-slate-200 rounded-md bg-white">
              <div>
                <p className="text-sm font-medium text-slate-900">Test Mode</p>
                <p className="text-xs text-slate-500">Used for simulator and staging</p>
              </div>
              <Button variant="outline" size="sm">Manage</Button>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end">
          <Button>Save Changes</Button>
        </div>
      </div>
    </div>
  );
}

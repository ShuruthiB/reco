import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Loader2, CheckCircle2 } from 'lucide-react';

export function SettingsScreen() {
  const [isRotating, setIsRotating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [companyName, setCompanyName] = useState('Acme Corp');
  const [lastRotated, setLastRotated] = useState('Aug 15, 2026');
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleRotate = () => {
    setIsRotating(true);
    setTimeout(() => {
      setLastRotated('Just now');
      setIsRotating(false);
    }, 1500);
  };

  const handleSave = () => {
    setIsSaving(true);
    setSaveSuccess(false);
    setTimeout(() => {
      setIsSaving(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    }, 1000);
  };

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
                <input 
                  type="text" 
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="w-full h-9 px-3 rounded-md border border-slate-300 bg-white text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500" 
                />
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
                <p className="text-xs text-slate-500">Connected on {lastRotated}</p>
              </div>
              <Button variant="outline" size="sm" onClick={handleRotate} disabled={isRotating}>
                {isRotating ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Rotate Keys'}
              </Button>
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

        <div className="flex justify-end items-center gap-4">
          {saveSuccess && (
            <span className="text-sm text-emerald-600 flex items-center gap-1">
              <CheckCircle2 className="w-4 h-4" />
              Settings saved
            </span>
          )}
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
            {isSaving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>
    </div>
  );
}

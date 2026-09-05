import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  CreditCard, 
  BrainCircuit, 
  TestTube2, 
  Wallet, 
  ShieldCheck, 
  ScrollText, 
  Activity, 
  Settings,
  Zap
} from 'lucide-react';
import { cn } from '../../utils';

const navItems = [
  { name: 'Overview', path: '/', icon: LayoutDashboard },
  { name: 'Transactions', path: '/transactions', icon: CreditCard },
  { name: 'AI Decision Center', path: '/decisions', icon: BrainCircuit },
  { name: 'Simulator', path: '/simulator', icon: Zap },
  { name: 'Experiments', path: '/experiments', icon: TestTube2 },
  { name: 'Budget', path: '/budget', icon: Wallet },
  { name: 'Policies', path: '/policies', icon: ShieldCheck },
  { name: 'Audit Trail', path: '/audit', icon: ScrollText },
  { name: 'System Health', path: '/health', icon: Activity },
  { name: 'Settings', path: '/settings', icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="w-64 border-r border-slate-200 bg-white hidden md:flex flex-col h-screen sticky top-0">
      <div className="h-16 flex items-center px-6 border-b border-slate-200">
        <div className="flex items-center gap-2 font-bold text-xl text-slate-900 tracking-tight">
          <div className="w-8 h-8 rounded bg-slate-900 text-white flex items-center justify-center">
            R
          </div>
          RECO
        </div>
      </div>
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 px-3">
          Menu
        </div>
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => cn(
              "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
              isActive 
                ? "bg-slate-100 text-slate-900" 
                : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
            )}
          >
            <item.icon className="w-4 h-4" />
            {item.name}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-sm font-medium">
            M
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-900 truncate">Merchant Admin</p>
            <p className="text-xs text-slate-500 truncate">admin@merchant.com</p>
          </div>
        </div>
      </div>
    </aside>
  );
}

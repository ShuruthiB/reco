import { useNavigate } from 'react-router-dom';
import { MOCK_TRANSACTIONS, type Transaction } from '../data/mock';
import { DataTable } from '../components/ui/DataTable';
import { Badge } from '../components/ui/Badge';

export function TransactionsScreen() {
  const navigate = useNavigate();

  const columns = [
    {
      header: 'Transaction ID',
      accessorKey: 'id' as keyof Transaction,
      className: 'font-medium',
    },
    {
      header: 'Customer',
      cell: (item: Transaction) => (
        <div>
          <div className="font-medium text-slate-900">{item.customerName}</div>
          <div className="text-xs text-slate-500">{item.customerEmail}</div>
        </div>
      ),
    },
    {
      header: 'Amount',
      cell: (item: Transaction) => (
        <span className="font-medium">
          ${item.amount.toFixed(2)}
        </span>
      ),
    },
    {
      header: 'Status',
      cell: (item: Transaction) => {
        const variants: Record<string, "success" | "warning" | "danger" | "default" | "neutral"> = {
          pending: 'warning',
          recovered: 'success',
          failed: 'danger',
          quarantined: 'neutral'
        };
        return (
          <Badge variant={variants[item.status]}>
            {item.status.toUpperCase()}
          </Badge>
        );
      },
    },
    {
      header: 'Risk',
      cell: (item: Transaction) => {
        const variants: Record<string, "danger" | "warning" | "default"> = {
          high: 'danger',
          medium: 'warning',
          low: 'default'
        };
        return (
          <Badge variant={variants[item.riskLevel]}>
            {item.riskLevel.toUpperCase()}
          </Badge>
        );
      },
    },
    {
      header: 'Date',
      cell: (item: Transaction) => (
        <span className="text-slate-500">
          {new Date(item.createdAt).toLocaleDateString()}
        </span>
      ),
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Transactions</h1>
          <p className="text-sm text-slate-500">Manage and monitor payment attempts and recoveries.</p>
        </div>
      </div>
      
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <h3 className="font-semibold text-sm text-slate-700">Recent Transactions</h3>
        </div>
        <DataTable 
          data={MOCK_TRANSACTIONS} 
          columns={columns} 
          onRowClick={(item) => navigate(`/transactions/${item.id}`)}
        />
      </div>
    </div>
  );
}

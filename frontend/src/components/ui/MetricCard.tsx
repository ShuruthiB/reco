import { type ReactNode } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './Card';
import { cn } from '../../utils';

interface MetricCardProps {
  title: string;
  value: string | ReactNode;
  subtitle?: string;
  icon?: ReactNode;
  trend?: {
    value: number;
    label: string;
  };
  highlight?: 'positive' | 'neutral' | 'brand' | 'gross' | 'natural' | 'incremental' | 'cost' | 'net';
  className?: string;
}

export function MetricCard({ title, value, subtitle, icon, trend, highlight = 'neutral', className }: MetricCardProps) {
  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-slate-500">{title}</CardTitle>
        {icon && <div className="text-slate-400">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className={cn("text-2xl font-bold numeric-data tracking-tight", {
          'text-emerald-600': highlight === 'positive' || highlight === 'incremental',
          'text-indigo-600': highlight === 'brand' || highlight === 'net',
          'text-slate-900': highlight === 'neutral',
          'text-blue-600': highlight === 'gross',
          'text-slate-500': highlight === 'natural',
          'text-rose-600': highlight === 'cost',
        })}>
          {value}
        </div>
        {(subtitle || trend) && (
          <p className="text-xs text-slate-500 mt-1 flex items-center gap-2">
            {trend && (
              <span className={cn("font-medium", trend.value > 0 ? "text-green-600" : trend.value < 0 ? "text-red-600" : "text-slate-500")}>
                {trend.value > 0 ? '+' : ''}{trend.value}%
              </span>
            )}
            <span>{trend?.label || subtitle}</span>
          </p>
        )}
      </CardContent>
    </Card>
  );
}

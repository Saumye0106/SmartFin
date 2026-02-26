import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const SpendingChart = ({ patterns }) => {
  if (!patterns || !patterns.breakdown) return null;

  const { breakdown } = patterns;

  const data = [
    { name: 'Rent', value: breakdown.rent, color: '#ef4444', icon: 'solar:home-2-linear' },
    { name: 'Food', value: breakdown.food, color: '#f97316', icon: 'solar:cart-large-2-linear' },
    { name: 'Travel', value: breakdown.travel, color: '#eab308', icon: 'solar:bus-linear' },
    { name: 'Shopping', value: breakdown.shopping, color: '#8b5cf6', icon: 'solar:bag-smile-linear' },
    { name: 'EMI', value: breakdown.emi, color: '#ec4899', icon: 'solar:card-linear' },
    { name: 'Savings', value: breakdown.savings, color: '#10b981', icon: 'solar:safe-square-linear' }
  ].filter(item => item.value > 0);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-black/90 backdrop-blur-md border border-white/10 rounded-lg px-4 py-2">
          <p className="text-white/60 text-xs">{payload[0].name}</p>
          <p className="text-white font-bold text-sm">{payload[0].value.toFixed(1)}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
          <iconify-icon icon="solar:pie-chart-2-linear" className="text-purple-400 text-xl"></iconify-icon>
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Spending Breakdown</h2>
          <p className="text-xs text-white/50">Where your money goes each month</p>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
            strokeWidth={2}
            stroke="rgba(0,0,0,0.5)"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>

      <div className="grid grid-cols-2 gap-3 mt-6">
        {data.map((item, index) => (
          <div key={index} className="flex items-center gap-2 p-2 rounded-lg bg-white/5 border border-white/5">
            <iconify-icon icon={item.icon} style={{ color: item.color }} width="18"></iconify-icon>
            <div className="flex-1 min-w-0">
              <div className="text-xs text-white/60">{item.name}</div>
              <div className="text-sm font-semibold text-white">{item.value.toFixed(1)}%</div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-6 border-t border-white/10 space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-white/60">Total Expenses</span>
          <span className="font-semibold text-white">{(patterns.expense_ratio * 100).toFixed(1)}% of income</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-white/60">Savings Rate</span>
          <span className="font-semibold text-green-400">{(patterns.savings_ratio * 100).toFixed(1)}% of income</span>
        </div>
      </div>
    </div>
  );
};

export default SpendingChart;

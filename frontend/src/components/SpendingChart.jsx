import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import './SpendingChart.css';

const SpendingChart = ({ patterns }) => {
  if (!patterns || !patterns.breakdown) return null;

  const { breakdown } = patterns;

  const data = [
    { name: 'Rent', value: breakdown.rent, color: '#ef4444' },
    { name: 'Food', value: breakdown.food, color: '#f97316' },
    { name: 'Travel', value: breakdown.travel, color: '#eab308' },
    { name: 'Shopping', value: breakdown.shopping, color: '#8b5cf6' },
    { name: 'EMI', value: breakdown.emi, color: '#ec4899' },
    { name: 'Savings', value: breakdown.savings, color: '#10b981' }
  ].filter(item => item.value > 0);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">{payload[0].name}</p>
          <p className="tooltip-value">{payload[0].value.toFixed(1)}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="spending-chart-container">
      <h2 className="section-title">💳 Spending Breakdown</h2>
      
      <ResponsiveContainer width="100%" height={350}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            outerRadius={120}
            fill="#8884d8"
            dataKey="value"
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>

      <div className="spending-summary">
        <div className="summary-row">
          <span>Total Expenses:</span>
          <strong>{(patterns.expense_ratio * 100).toFixed(1)}% of income</strong>
        </div>
        <div className="summary-row">
          <span>Savings:</span>
          <strong className="savings-text">{(patterns.savings_ratio * 100).toFixed(1)}% of income</strong>
        </div>
      </div>
    </div>
  );
};

export default SpendingChart;

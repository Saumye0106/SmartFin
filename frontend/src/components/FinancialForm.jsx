import { useState } from 'react';

const FinancialForm = ({ onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    income: '',
    rent: '',
    food: '',
    travel: '',
    shopping: '',
    emi: '',
    savings: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Convert to numbers
    const data = {
      income: Number(formData.income),
      rent: Number(formData.rent),
      food: Number(formData.food),
      travel: Number(formData.travel),
      shopping: Number(formData.shopping),
      emi: Number(formData.emi),
      savings: Number(formData.savings)
    };
    
    onSubmit(data);
  };

  const loadSampleData = () => {
    setFormData({
      income: '50000',
      rent: '15000',
      food: '8000',
      travel: '3000',
      shopping: '5000',
      emi: '10000',
      savings: '9000'
    });
  };

  const fields = [
    { name: 'income', label: 'Monthly Income', icon: 'solar:wallet-money-linear', placeholder: '50000', color: 'cyan' },
    { name: 'rent', label: 'Rent/Housing', icon: 'solar:home-2-linear', placeholder: '15000', color: 'purple' },
    { name: 'food', label: 'Food & Groceries', icon: 'solar:cart-large-2-linear', placeholder: '8000', color: 'green' },
    { name: 'travel', label: 'Travel & Transport', icon: 'solar:bus-linear', placeholder: '3000', color: 'blue' },
    { name: 'shopping', label: 'Shopping & Entertainment', icon: 'solar:bag-smile-linear', placeholder: '5000', color: 'pink' },
    { name: 'emi', label: 'EMI & Loans', icon: 'solar:card-linear', placeholder: '10000', color: 'orange' },
    { name: 'savings', label: 'Monthly Savings', icon: 'solar:safe-square-linear', placeholder: '9000', color: 'emerald' },
  ];

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Form Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {fields.map((field) => (
          <div key={field.name} className="space-y-2 group">
            <label 
              htmlFor={field.name} 
              className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-cyan-400 flex items-center gap-2"
            >
              <iconify-icon icon={field.icon} width="14" className={`text-${field.color}-400`}></iconify-icon>
              {field.label}
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30 text-sm font-mono">₹</span>
              <input
                type="number"
                id={field.name}
                name={field.name}
                value={formData[field.name]}
                onChange={handleChange}
                placeholder={field.placeholder}
                required
                min="0"
                className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-3 pl-8 text-sm text-white placeholder-white/20 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200 font-mono"
              />
            </div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-3 pt-4">
        <button
          type="submit"
          disabled={loading}
          className="relative flex-1 group overflow-hidden rounded-lg bg-white py-3 transition-all hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 focus:ring-offset-black disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {!loading && (
            <>
              <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-cyan-400/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
              <span className="relative text-sm font-semibold text-black flex items-center justify-center gap-2">
                <iconify-icon icon="solar:chart-2-linear" width="18"></iconify-icon>
                Analyze My Finances
              </span>
            </>
          )}
          {loading && (
            <div className="flex items-center justify-center text-black gap-2">
              <iconify-icon icon="solar:spinner-solid" className="animate-spin text-lg"></iconify-icon>
              <span className="text-sm font-semibold">Analyzing...</span>
            </div>
          )}
        </button>
        
        <button
          type="button"
          onClick={loadSampleData}
          disabled={loading}
          className="flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 py-3 px-6 text-sm font-medium text-white hover:bg-white/10 hover:border-white/20 transition-all focus:outline-none focus:ring-2 focus:ring-white/20 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <iconify-icon icon="solar:document-add-linear" width="18"></iconify-icon>
          Load Sample
        </button>
      </div>
    </form>
  );
};

export default FinancialForm;

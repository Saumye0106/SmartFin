import { useState } from 'react';
import './FinancialForm.css';

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

  return (
    <div className="financial-form-container">
      <div className="form-header">
        <h2>💰 Enter Your Financial Details</h2>
        <p>Fill in your monthly financial information</p>
      </div>
      
      <form onSubmit={handleSubmit} className="financial-form">
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="income">Monthly Income (₹)</label>
            <input
              type="number"
              id="income"
              name="income"
              value={formData.income}
              onChange={handleChange}
              placeholder="50000"
              required
              min="0"
            />
          </div>

          <div className="form-group">
            <label htmlFor="rent">Rent/Housing (₹)</label>
            <input
              type="number"
              id="rent"
              name="rent"
              value={formData.rent}
              onChange={handleChange}
              placeholder="15000"
              required
              min="0"
            />
          </div>

          <div className="form-group">
            <label htmlFor="food">Food & Groceries (₹)</label>
            <input
              type="number"
              id="food"
              name="food"
              value={formData.food}
              onChange={handleChange}
              placeholder="8000"
              required
              min="0"
            />
          </div>

          <div className="form-group">
            <label htmlFor="travel">Travel & Transport (₹)</label>
            <input
              type="number"
              id="travel"
              name="travel"
              value={formData.travel}
              onChange={handleChange}
              placeholder="3000"
              required
              min="0"
            />
          </div>

          <div className="form-group">
            <label htmlFor="shopping">Shopping & Entertainment (₹)</label>
            <input
              type="number"
              id="shopping"
              name="shopping"
              value={formData.shopping}
              onChange={handleChange}
              placeholder="5000"
              required
              min="0"
            />
          </div>

          <div className="form-group">
            <label htmlFor="emi">EMI & Loans (₹)</label>
            <input
              type="number"
              id="emi"
              name="emi"
              value={formData.emi}
              onChange={handleChange}
              placeholder="10000"
              required
              min="0"
            />
          </div>

          <div className="form-group">
            <label htmlFor="savings">Monthly Savings (₹)</label>
            <input
              type="number"
              id="savings"
              name="savings"
              value={formData.savings}
              onChange={handleChange}
              placeholder="9000"
              required
              min="0"
            />
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Analyzing...' : '🔍 Analyze My Finances'}
          </button>
          <button type="button" className="btn btn-secondary" onClick={loadSampleData} disabled={loading}>
            Load Sample Data
          </button>
        </div>
      </form>
    </div>
  );
};

export default FinancialForm;

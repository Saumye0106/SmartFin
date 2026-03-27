import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Sidebar.css';

const Sidebar = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const navigate = useNavigate();

  const menuItems = [
    {
      icon: 'solar:home-2-linear',
      label: 'Dashboard',
      path: '/dashboard',
      color: 'blue'
    },
    {
      icon: 'solar:wallet-money-linear',
      label: 'Loans',
      path: '/loans',
      color: 'cyan'
    },
    {
      icon: 'solar:target-linear',
      label: 'Goals',
      path: '/goals',
      color: 'purple'
    },
    {
      icon: 'solar:calculator-linear',
      label: 'SIP Calculator',
      path: '/sip-calculator',
      color: 'orange'
    },
    {
      icon: 'solar:chart-2-linear',
      label: 'Retirement',
      path: '/retirement',
      color: 'green'
    },
    {
      icon: 'solar:wallet-money-linear',
      label: 'Budget Tracker',
      path: '/budget',
      color: 'green'
    },
    {
      icon: 'solar:chat-round-dots-linear',
      label: 'AI Assistant',
      path: '/chat',
      color: 'pink'
    }
  ];

  return (
    <div className={`sidebar ${isExpanded ? 'expanded' : 'collapsed'}`}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="sidebar-toggle"
        title={isExpanded ? 'Collapse' : 'Expand'}
      >
        <iconify-icon 
          icon={isExpanded ? 'solar:alt-arrow-left-linear' : 'solar:alt-arrow-right-linear'} 
          width="20"
        ></iconify-icon>
      </button>

      {/* Menu Items */}
      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <button
            key={item.path}
            onClick={() => {
              navigate(item.path);
              setIsExpanded(false);
            }}
            className={`sidebar-item sidebar-item-${item.color}`}
            title={item.label}
          >
            <iconify-icon icon={item.icon} width="24"></iconify-icon>
            {isExpanded && <span className="sidebar-label">{item.label}</span>}
          </button>
        ))}
      </nav>
    </div>
  );
};

export default Sidebar;

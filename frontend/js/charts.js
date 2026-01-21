// Charts Module using Chart.js
window.spendingChart = null;

const Charts = {
    // Create spending breakdown pie chart
    createSpendingChart(patterns) {
        const canvas = document.getElementById('spendingChart');

        // Reset reference (destruction happens in app.js before canvas replacement)
        window.spendingChart = null;

        const breakdown = patterns.breakdown;

        window.spendingChart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Rent', 'Food', 'Travel', 'Shopping', 'EMI', 'Savings'],
                datasets: [{
                    data: [
                        breakdown.rent,
                        breakdown.food,
                        breakdown.travel,
                        breakdown.shopping,
                        breakdown.emi,
                        breakdown.savings
                    ],
                    backgroundColor: [
                        '#3b82f6',
                        '#10b981',
                        '#f59e0b',
                        '#8b5cf6',
                        '#ef4444',
                        '#06b6d4'
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return `${label}: ${value.toFixed(1)}%`;
                            }
                        }
                    }
                }
            }
        });
    },

    // Animate ratio bars
    animateRatios(patterns) {
        const expenseRatio = (patterns.expense_ratio * 100).toFixed(1);
        const savingsRatio = (patterns.savings_ratio * 100).toFixed(1);
        const emiRatio = (patterns.emi_ratio * 100).toFixed(1);

        // Reset bars first
        document.getElementById('expenseBar').style.width = '0%';
        document.getElementById('savingsBar').style.width = '0%';
        document.getElementById('emiBar').style.width = '0%';

        // Expense bar
        setTimeout(() => {
            document.getElementById('expenseBar').style.width = `${Math.min(expenseRatio, 100)}%`;
            document.getElementById('expenseValue').textContent = `${expenseRatio}%`;

            // Color based on value
            const expenseBar = document.getElementById('expenseBar');
            if (expenseRatio > 80) {
                expenseBar.style.background = '#ef4444';
            } else if (expenseRatio > 60) {
                expenseBar.style.background = '#f59e0b';
            } else {
                expenseBar.style.background = '#10b981';
            }
        }, 300);

        // Savings bar
        setTimeout(() => {
            document.getElementById('savingsBar').style.width = `${Math.min(savingsRatio, 100)}%`;
            document.getElementById('savingsValue').textContent = `${savingsRatio}%`;
        }, 600);

        // EMI bar
        setTimeout(() => {
            document.getElementById('emiBar').style.width = `${Math.min(emiRatio, 100)}%`;
            document.getElementById('emiValue').textContent = `${emiRatio}%`;
        }, 900);
    }
};

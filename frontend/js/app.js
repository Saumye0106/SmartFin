// Main Application Logic
let currentFinancialData = null;
let currentResult = null;

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    // Form submission
    document.getElementById('financialForm').addEventListener('submit', handleFormSubmit);

    // Load sample data button
    document.getElementById('loadSampleBtn').addEventListener('click', loadSampleData);

    // What-if simulation
    document.getElementById('runSimulationBtn').addEventListener('click', runWhatIfSimulation);
}

// Handle form submission
async function handleFormSubmit(e) {
    e.preventDefault();

    // Get form data
    const financialData = {
        income: parseInt(document.getElementById('income').value),
        rent: parseInt(document.getElementById('rent').value),
        food: parseInt(document.getElementById('food').value),
        travel: parseInt(document.getElementById('travel').value),
        shopping: parseInt(document.getElementById('shopping').value),
        emi: parseInt(document.getElementById('emi').value),
        savings: parseInt(document.getElementById('savings').value)
    };

    // Validate
    const total = financialData.rent + financialData.food + financialData.travel +
                  financialData.shopping + financialData.emi + financialData.savings;

    if (total > financialData.income) {
        alert('Warning: Your total expenses and savings exceed your income!');
    }

    // Store current data
    currentFinancialData = financialData;

    // Show loading
    showLoading();

    try {
        // Call API
        const result = await API.predict(financialData);
        currentResult = result;

        // Hide loading
        hideLoading();

        // Display results
        displayResults(result);

    } catch (error) {
        hideLoading();
        alert('Error connecting to backend. Make sure Flask server is running on port 5000.');
        console.error(error);
    }
}

// Load sample data
function loadSampleData() {
    document.getElementById('income').value = '50000';
    document.getElementById('rent').value = '15000';
    document.getElementById('food').value = '8000';
    document.getElementById('travel').value = '3000';
    document.getElementById('shopping').value = '5000';
    document.getElementById('emi').value = '10000';
    document.getElementById('savings').value = '9000';
}

// Show loading indicator
function showLoading() {
    document.getElementById('loadingIndicator').classList.remove('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
}

// Hide loading indicator
function hideLoading() {
    document.getElementById('loadingIndicator').classList.add('hidden');
}

// Display results
function displayResults(result) {
    const resultsSection = document.getElementById('resultsSection');

    // Hide results section first to reset layout
    resultsSection.classList.add('hidden');

    // Destroy existing chart first
    if (window.spendingChart) {
        window.spendingChart.destroy();
        window.spendingChart = null;
    }

    // Completely replace the canvas element to remove all Chart.js artifacts
    const oldCanvas = document.getElementById('spendingChart');
    const canvasParent = oldCanvas.parentElement;

    // Remove all child nodes from parent (including Chart.js wrapper divs)
    while (canvasParent.firstChild) {
        canvasParent.removeChild(canvasParent.firstChild);
    }

    // Create fresh canvas with explicit dimensions
    const newCanvas = document.createElement('canvas');
    newCanvas.id = 'spendingChart';
    newCanvas.width = 400;
    newCanvas.height = 250;
    newCanvas.style.width = '100%';
    newCanvas.style.height = '250px';
    canvasParent.appendChild(newCanvas);

    // Force a reflow to ensure the reset happens
    void resultsSection.offsetHeight;

    // Show results section
    resultsSection.classList.remove('hidden');

    // Display score
    displayScore(result.score, result.classification);

    // Display patterns - add small delay to ensure DOM is ready
    setTimeout(() => {
        Charts.createSpendingChart(result.patterns);
        Charts.animateRatios(result.patterns);
    }, 50);

    // Display anomalies
    displayAnomalies(result.anomalies);

    // Display guidance
    displayGuidance(result.guidance);

    // Display investment advice
    displayInvestmentAdvice(result.investments);

    // Setup what-if simulator with current values
    setupWhatIfSimulator();
}

// Display score with animation
function displayScore(score, classification) {
    const scoreElement = document.getElementById('scoreValue');
    const circleElement = document.getElementById('scoreCircle');
    const badgeElement = document.getElementById('categoryBadge');
    const descElement = document.getElementById('categoryDescription');

    // Animate number
    let currentScore = 0;
    const increment = score / 50;
    const timer = setInterval(() => {
        currentScore += increment;
        if (currentScore >= score) {
            currentScore = score;
            clearInterval(timer);
        }
        scoreElement.textContent = Math.round(currentScore);
    }, 20);

    // Animate circle
    const circumference = 2 * Math.PI * 90;
    const offset = circumference - (score / 100) * circumference;

    setTimeout(() => {
        circleElement.style.strokeDashoffset = offset;
        circleElement.style.stroke = classification.color;
    }, 100);

    // Update badge
    badgeElement.textContent = `${classification.emoji} ${classification.category}`;
    badgeElement.style.background = classification.color;

    // Update description
    descElement.textContent = classification.description;
}

// Display anomalies
function displayAnomalies(anomalies) {
    const section = document.getElementById('anomaliesSection');
    const list = document.getElementById('anomaliesList');

    if (anomalies.length === 0) {
        section.classList.add('hidden');
        return;
    }

    section.classList.remove('hidden');
    list.innerHTML = '';

    anomalies.forEach(anomaly => {
        const item = document.createElement('div');
        item.className = `anomaly-item ${anomaly.severity}`;
        item.innerHTML = `
            <div class="anomaly-icon">${getSeverityIcon(anomaly.severity)}</div>
            <div class="anomaly-content">
                <div class="anomaly-type">${anomaly.severity} - ${anomaly.type}</div>
                <div class="anomaly-message">${anomaly.message}</div>
            </div>
        `;
        list.appendChild(item);
    });
}

function getSeverityIcon(severity) {
    const icons = {
        'critical': '🚨',
        'high': '⚠️',
        'medium': 'ℹ️',
        'low': '💡'
    };
    return icons[severity] || 'ℹ️';
}

// Display guidance
function displayGuidance(guidance) {
    // Strengths
    displayGuidanceList('strengths', guidance.strengths, 'strengthsSection', 'strengthsList');

    // Warnings
    displayGuidanceList('warnings', guidance.warnings, 'warningsSection', 'warningsList');

    // Recommendations
    displayGuidanceList('recommendations', guidance.recommendations, 'recommendationsSection', 'recommendationsList');
}

function displayGuidanceList(type, items, sectionId, listId) {
    const section = document.getElementById(sectionId);
    const list = document.getElementById(listId);

    if (items.length === 0) {
        section.classList.add('hidden');
        return;
    }

    section.classList.remove('hidden');
    list.innerHTML = '';

    items.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        list.appendChild(li);
    });
}

// Display investment advice
function displayInvestmentAdvice(investments) {
    const eligibilityDiv = document.getElementById('investmentEligibility');
    const adviceDiv = document.getElementById('investmentAdvice');
    const listDiv = document.getElementById('investmentList');

    // Eligibility
    eligibilityDiv.className = `investment-eligibility ${investments.eligible_for_investment ? 'eligible' : 'not-eligible'}`;
    eligibilityDiv.textContent = investments.eligible_for_investment
        ? '✓ You are eligible for investments'
        : '✗ Focus on improving financial health before investing';

    // Overall advice
    adviceDiv.textContent = investments.overall_advice;

    // Investment suggestions
    listDiv.innerHTML = '';
    investments.suggestions.forEach(suggestion => {
        const item = document.createElement('div');
        item.className = `investment-item ${suggestion.suitable ? 'suitable' : 'not-suitable'}`;
        item.innerHTML = `
            <div class="investment-header">
                <div class="investment-type">${suggestion.type}</div>
                <div class="investment-risk">Risk: ${suggestion.risk}</div>
            </div>
            <div class="investment-amount">${suggestion.recommended_amount}</div>
            <div class="investment-reason">${suggestion.reason}</div>
        `;
        listDiv.appendChild(item);
    });
}

// Setup what-if simulator
function setupWhatIfSimulator() {
    document.getElementById('whatifShopping').value = currentFinancialData.shopping;
    document.getElementById('whatifSavings').value = currentFinancialData.savings;
    document.getElementById('simulationResults').classList.add('hidden');
}

// Run what-if simulation
async function runWhatIfSimulation() {
    const modifiedShopping = parseInt(document.getElementById('whatifShopping').value);
    const modifiedSavings = parseInt(document.getElementById('whatifSavings').value);

    // Create modified data
    const modifiedData = {
        ...currentFinancialData,
        shopping: modifiedShopping,
        savings: modifiedSavings
    };

    try {
        // Call API
        const result = await API.whatIf(currentFinancialData, modifiedData);

        // Display simulation results
        displaySimulationResults(result);

    } catch (error) {
        alert('Error running simulation. Make sure Flask server is running.');
        console.error(error);
    }
}

// Display simulation results
function displaySimulationResults(result) {
    const resultsDiv = document.getElementById('simulationResults');
    resultsDiv.classList.remove('hidden');

    // Scores
    document.getElementById('currentSimScore').textContent = result.current_score.toFixed(1);
    document.getElementById('newSimScore').textContent = result.modified_score.toFixed(1);

    // Change
    const changeElement = document.getElementById('scoreChange');
    const change = result.score_change;
    changeElement.textContent = change >= 0 ? `+${change.toFixed(1)}` : change.toFixed(1);
    changeElement.className = `simulation-change ${change > 0 ? 'positive' : change < 0 ? 'negative' : 'neutral'}`;

    // Impact message
    const impactDiv = document.getElementById('simulationImpact');
    let impactMessage = '';

    if (result.impact === 'positive') {
        impactMessage = `Great! This change would improve your score by ${Math.abs(change).toFixed(1)} points.`;
        impactDiv.className = 'simulation-impact positive';
    } else if (result.impact === 'negative') {
        impactMessage = `Warning: This change would decrease your score by ${Math.abs(change).toFixed(1)} points.`;
        impactDiv.className = 'simulation-impact negative';
    } else {
        impactMessage = 'No significant impact on your score.';
        impactDiv.className = 'simulation-impact neutral';
    }

    impactDiv.textContent = impactMessage;
}

document.addEventListener('DOMContentLoaded', () => {
    try {
        // Use the global window.insightsData variable
        if (!window.insightsData || window.insightsData.length === 0) {
            console.error("Dashboard cannot be displayed: No insights data found.");
            const container = document.querySelector('.container');
            if (container) {
                container.innerHTML = '<h1>Dashboard Data Not Found</h1><p>Could not load insights from the CSV file. Please check the server logs for errors.</p>';
            }
            return;
        }

        const insights = window.insightsData;

        // 1. Process data for KPIs, charts, and cards
        const reasonCounts = {};
        const returnInterestCounts = {};
        const mentionedIssuesCounts = {};
        let positiveReturnInterest = 0;

        insights.forEach(insight => {
            const reason = insight.reason_for_inactivity || 'Unknown';
            reasonCounts[reason] = (reasonCounts[reason] || 0) + 1;

            const interest = insight.is_interested_in_returning || 'Unknown';
            returnInterestCounts[interest] = (returnInterestCounts[interest] || 0) + 1;
            if (interest === 'Yes') positiveReturnInterest++;
            
            if (insight.mentioned_issues) {
                Object.keys(insight.mentioned_issues).forEach(issue => {
                    mentionedIssuesCounts[issue] = (mentionedIssuesCounts[issue] || 0) + 1;
                });
            }
        });

        // 2. Populate KPIs
        document.getElementById('total-contacts').textContent = insights.length;
        const returnInterestPercentage = ((positiveReturnInterest / insights.length) * 100).toFixed(0);
        document.getElementById('return-interest-yes').textContent = `${returnInterestPercentage}%`;
        const topReason = Object.keys(reasonCounts).reduce((a, b) => reasonCounts[a] > reasonCounts[b] ? a : b, 'N/A');
        document.getElementById('top-reason').textContent = topReason;

        // 3. Render Charts
        renderBarChart('reasonsChart', 'Reason for Inactivity', reasonCounts);
        renderPieChart('returnInterestChart', 'Interest in Returning', returnInterestCounts);
        renderBarChart('issuesChart', 'Top Mentioned Issues', mentionedIssuesCounts, 'y'); // Horizontal bar chart

        // 4. Populate Insight Cards
        const insightsGrid = document.getElementById('insights-grid');
        insightsGrid.innerHTML = ''; // Clear placeholders
        insights.forEach(insight => {
            const card = document.createElement('div');
            card.className = 'insight-card';

            const sentiment = insight.de_sentiment || 'Unknown';
            const issues = Object.keys(insight.mentioned_issues || {}).map(k => k.replace(/_/g, ' ')).join(', ') || 'None';

            card.innerHTML = `
                <p><strong>Summary:</strong> ${insight.conversation_summary || 'N/A'}</p>
                <p><strong>Key Takeaway:</strong> ${(insight.key_takeaways || []).join('; ')}</p>
                <p><strong>Mentioned Issues:</strong> ${issues}</p>
                <div>
                    <span class="tag sentiment-${sentiment}">${sentiment}</span>
                </div>
            `;
            insightsGrid.appendChild(card);
        });

    } catch (error) {
        console.error("An error occurred while rendering the dashboard:", error);
        const container = document.querySelector('.container');
        if (container) {
            container.innerHTML = `<h1>Error Rendering Dashboard</h1><p>An unexpected error occurred. Please check the browser's developer console for more details.</p><pre style="text-align: left; background-color: #eee; padding: 1rem;">${error.stack}</pre>`;
        }
    }
});

function renderBarChart(canvasId, label, data, axis = 'x') {
    const ctx = document.getElementById(canvasId).getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(data),
            datasets: [{ label: '# of Mentions', data: Object.values(data), backgroundColor: 'rgba(54, 162, 235, 0.6)' }]
        },
        options: { indexAxis: axis, scales: { [axis]: { beginAtZero: true } } }
    });
}

function renderPieChart(canvasId, label, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: ['rgba(75, 192, 192, 0.6)', 'rgba(255, 99, 132, 0.6)', 'rgba(255, 206, 86, 0.6)']
            }]
        }
    });
} 
document.addEventListener('DOMContentLoaded', () => {
    try {
        if (!window.insightsData || window.insightsData.length === 0) {
            console.error("Dashboard cannot be displayed: No insights data found.");
            const container = document.querySelector('.container');
            if (container) {
                container.innerHTML = '<h1>Dashboard Data Not Found</h1><p>Could not load insights from the CSV file. Please check the server logs for errors.</p>';
            }
            return;
        }

        const insights = window.insightsData;

        // --- 1. Prepare Aggregated Data ---
        const reasonCounts = {};
        const returnInterestCounts = {};
        const mentionedIssuesCounts = {};
        const toneCounts = {};

        let yesMaybeReturnCount = 0;
        let noReturnCount = 0;

        insights.forEach(insight => {
            // Reason for Inactivity
            const reason = insight.reason_for_inactivity || 'Unknown';
            reasonCounts[reason] = (reasonCounts[reason] || 0) + 1;

            // Interest in Returning
            const interest = insight.is_interested_in_returning || 'Unknown';
            returnInterestCounts[interest] = (returnInterestCounts[interest] || 0) + 1;

            if (interest === 'Yes' || interest === 'Maybe') {
                yesMaybeReturnCount++;
            }
            if (interest === 'No') {
                noReturnCount++;
            }

            // Mentioned Issues
            if (insight.mentioned_issues && typeof insight.mentioned_issues === 'object') {
                Object.keys(insight.mentioned_issues).forEach(issue => {
                    if(issue !== "None") { // Exclude "None" from issues
                        mentionedIssuesCounts[issue] = (mentionedIssuesCounts[issue] || 0) + 1;
                    }
                });
            }


            // Tone / Sentiment
            const tone = insight.de_sentiment || 'Unknown';
            toneCounts[tone] = (toneCounts[tone] || 0) + 1;
        });

        // --- 2. Populate KPI Cards ---
        const totalInsights = insights.length;
        document.getElementById('total-des').textContent = totalInsights;

        const willingToReturnPerc = totalInsights > 0 ? ((yesMaybeReturnCount / totalInsights) * 100).toFixed(0) : 0;
        document.getElementById('willing-return-perc').textContent = `${willingToReturnPerc}%`;

        const notWillingToReturnPerc = totalInsights > 0 ? ((noReturnCount / totalInsights) * 100).toFixed(0) : 0;
        document.getElementById('not-willing-return-perc').textContent = `${notWillingToReturnPerc}%`;

        const topReason = Object.keys(reasonCounts).length > 0 ? Object.keys(reasonCounts).reduce((a, b) => reasonCounts[a] > reasonCounts[b] ? a : b) : 'N/A';
        document.getElementById('top-reason').textContent = topReason;

        const mostCommonIssue = Object.keys(mentionedIssuesCounts).length > 0 ? Object.keys(mentionedIssuesCounts).reduce((a, b) => mentionedIssuesCounts[a] > mentionedIssuesCounts[b] ? a : b) : 'N/A';
        document.getElementById('top-issue').textContent = mostCommonIssue;


        // --- 3. Render Charts ---

        // Sort reasons by count descending
        const sortedReasons = Object.entries(reasonCounts).sort(([,a],[,b]) => b-a);
        const sortedReasonLabels = sortedReasons.map(el => el[0]);
        const sortedReasonData = sortedReasons.map(el => el[1]);

        renderBarChart('reasonsChart', 'Reasons for Inactivity', { labels: sortedReasonLabels, data: sortedReasonData });
        renderBarChart('returnInterestChart', 'Interest in Returning', { labels: Object.keys(returnInterestCounts), data: Object.values(returnInterestCounts) });
        renderBarChart('issuesChart', 'Mentioned Issues', { labels: Object.keys(mentionedIssuesCounts), data: Object.values(mentionedIssuesCounts) }, 'y');
        renderPieChart('toneChart', 'Feedback Tone', { labels: Object.keys(toneCounts), data: Object.values(toneCounts) });

        // --- 4. Render Full Drill-Down Table ---
        const tableBody = document.getElementById('details-table-body');
        tableBody.innerHTML = ''; // Clear previous content
        insights.forEach((insight, index) => {
            const row = document.createElement('tr');
            
            const issues = insight.mentioned_issues && typeof insight.mentioned_issues === 'object' 
                ? Object.keys(insight.mentioned_issues).map(k => k.replace(/_/g, ' ')).join(', ') || 'None'
                : 'None';

            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${insight.reason_for_inactivity || 'N/A'}</td>
                <td>${insight.is_interested_in_returning || 'N/A'}</td>
                <td>${(insight.key_takeaways || ['N/A']).join('; ')}</td>
                <td>${issues}</td>
                <td>${insight.de_sentiment || 'N/A'}</td>
            `;
            tableBody.appendChild(row);
        });

    } catch (error) {
        console.error("An error occurred while rendering the dashboard:", error);
        const container = document.querySelector('.container');
        if (container) {
            container.innerHTML = `<h1>Error Rendering Dashboard</h1><p>An unexpected error occurred. Please check the browser's developer console for more details.</p><pre style="text-align: left; background-color: #eee; padding: 1rem;">${error.stack}</pre>`;
        }
    }
});

function renderBarChart(canvasId, label, chartData, axis = 'x') {
    const ctx = document.getElementById(canvasId).getContext('2d');
    if (!ctx) return;
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: '# of DEs',
                data: chartData.data,
                backgroundColor: 'rgba(54, 162, 235, 0.6)'
            }]
        },
        options: {
            indexAxis: axis,
            scales: {
                [axis]: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

function renderPieChart(canvasId, label, chartData) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    if (!ctx) return;
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: chartData.labels,
            datasets: [{
                data: chartData.data,
                backgroundColor: [
                    'rgba(75, 192, 192, 0.6)', // Positive
                    'rgba(255, 206, 86, 0.6)', // Neutral
                    'rgba(255, 99, 132, 0.6)', // Negative
                    'rgba(153, 102, 255, 0.6)',
                    'rgba(255, 159, 64, 0.6)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: label
                }
            }
        }
    });
} 
const ctx = document.getElementById('expenseChart');

new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: ['Yiyecek', 'Faturalar', 'Diğer'],
        datasets: [{
            data: [45, 30, 25],
            backgroundColor: ['#3b82f6', '#22c55e', '#f97316']
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'bottom'
            }
        }
    }
});

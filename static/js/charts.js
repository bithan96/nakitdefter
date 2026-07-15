<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<script>
document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById("financeChart").getContext("2d");

    new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: ["Gelir", "Gider"],
            datasets: [{
                data: [{{ income }}, {{ expense }}],
                backgroundColor: ["#4a6cff", "#ff5a5a"]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "bottom"
                }
            }
        }
    });
});
</script>

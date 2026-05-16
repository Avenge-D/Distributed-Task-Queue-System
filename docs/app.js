const API_URL = 'http://localhost:8000'; // Replace with actual API URL if different

async function fetchStats() {
      try {
                const response = await fetch(`${API_URL}/stats`);
                const stats = await response.json();

          document.getElementById('total-tasks').textContent = stats.total;
                document.getElementById('pending-tasks').textContent = stats.pending;
                document.getElementById('processing-tasks').textContent = stats.processing;
                document.getElementById('completed-tasks').textContent = stats.completed;
                document.getElementById('failed-tasks').textContent = stats.failed;

          document.getElementById('status-badge').textContent = 'Online';
                document.getElementById('status-badge').className = 'badge status-completed';

          updateChart(stats);
      } catch (error) {
                console.error('Error fetching stats:', error);
                document.getElementById('status-badge').textContent = 'Offline';
                document.getElementById('status-badge').className = 'badge status-failed';
      }
}

async function fetchTasks() {
      try {
                const response = await fetch(`${API_URL}/tasks`);
                const tasks = await response.json();

          const tableBody = document.getElementById('task-body');
                tableBody.innerHTML = '';

          tasks.slice(0, 10).forEach(task => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                                        <td>${task.id}</td>
                                                        <td>${task.task_type}</td>
                                                                        <td class="status-${task.status.toLowerCase()}">${task.status}</td>
                                                                                        <td>${task.worker_id || '-'}</td>
                                                                                                        <td>${new Date(task.created_at).toLocaleString()}</td>
                                                                                                                    `;
                        tableBody.appendChild(row);
          });
      } catch (error) {
                console.error('Error fetching tasks:', error);
      }
}

let taskChart;
function updateChart(stats) {
      const ctx = document.getElementById('taskChart').getContext('2d');

    if (taskChart) {
              taskChart.destroy();
    }

    taskChart = new Chart(ctx, {
              type: 'doughnut',
              data: {
                            labels: ['Pending', 'Processing', 'Completed', 'Failed'],
                            datasets: [{
                                              data: [stats.pending, stats.processing, stats.completed, stats.failed],
                                              backgroundColor: ['#ca8a04', '#2563eb', '#16a34a', '#dc2626']
                            }]
              },
              options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                              legend: {
                                                                    position: 'bottom'
                                              }
                            }
              }
    });
}

// Initial fetch
fetchStats();
fetchTasks();

// Poll for updates every 5 seconds
setInterval(() => {
      fetchStats();
      fetchTasks();
}, 5000);

async function fetchData() {
    try {
        const response = await fetch('data.json');
        const data = await response.json();
        document.getElementById('date').textContent = data.date;
        document.getElementById('solution').textContent = data.solution;
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}
fetchData();

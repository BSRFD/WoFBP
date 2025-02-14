async function fetchData() {
    try {
        const timestamp = new Date().getTime();
        const response = await fetch(`data.json?t=${timestamp}`);
        const data = await response.json();
        
        document.getElementById('date').textContent = data.date;
        document.getElementById('solution').textContent = data.solution;

        // Force refresh if solution exists and page is stale
        if(data.solution !== 'Check back later' && 
           !window.location.search.includes('refreshed')) {
            window.location.search = `?refreshed=${timestamp}`;
        }
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}
fetchData();

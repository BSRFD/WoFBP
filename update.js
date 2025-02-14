async function fetchData() {
    try {
        const timestamp = new Date().getTime();
        const response = await fetch(`data.json?t=${timestamp}`);
        const data = await response.json();
        
        // Update date and solution
        document.getElementById('date').textContent = data.date;
        document.getElementById('solution').textContent = data.solution;

        // Create puzzle display
        const puzzleDisplay = document.getElementById('puzzle-display');
        puzzleDisplay.innerHTML = '';
        
        // Split solution into characters (ignore spaces)
        const letters = data.solution.replace(/ /g, '').split('');
        
        letters.forEach(letter => {
            const tile = document.createElement('div');
            tile.className = 'letter-tile';
            tile.textContent = letter;
            puzzleDisplay.appendChild(tile);
        });

        // Force refresh if solution exists
        if(data.solution !== 'Check back later' && 
           !window.location.search.includes('refreshed')) {
            window.location.search = `?refreshed=${timestamp}`;
        }
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

fetchData();

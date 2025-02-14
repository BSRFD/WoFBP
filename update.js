async function fetchData() {
    try {
        const timestamp = new Date().getTime();
        const response = await fetch(`data.json?t=${timestamp}`);
        const data = await response.json();
        
        // Update text fields
        document.getElementById('date').textContent = data.date;
        document.getElementById('solution').textContent = data.solution;

        // Build puzzle display
        const puzzleDisplay = document.getElementById('puzzle-display');
        puzzleDisplay.innerHTML = '';
        
        // Split into words using any whitespace
        const words = data.solution.split(/\s+/);
        
        words.forEach((word, index) => {
            // Create word container
            const wordContainer = document.createElement('div');
            wordContainer.className = 'word-container';
            
            // Add letter tiles
            word.split('').forEach(letter => {
                const tile = document.createElement('div');
                tile.className = 'letter-tile';
                tile.textContent = letter;
                wordContainer.appendChild(tile);
            });
            
            puzzleDisplay.appendChild(wordContainer);
            
            // Add word space separator
            if(index < words.length - 1) {
                const space = document.createElement('div');
                space.className = 'word-space';
                puzzleDisplay.appendChild(space);
            }
        });

        // Force refresh if new solution detected
        if(data.solution !== 'Check back later' && 
           !window.location.search.includes('refreshed')) {
            window.location.search = `?refreshed=${timestamp}`;
        }
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// Initial load
fetchData();

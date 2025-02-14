async function fetchData() {
    try {
        // Cache-busting using fetch headers
        const response = await fetch('data.json', {
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        });
        const data = await response.json();
        
        // Update displayed data
        document.getElementById('date').textContent = data.date;
        document.getElementById('solution').textContent = data.solution;

        // Update puzzle display
        const puzzleDisplay = document.getElementById('puzzle-display');
        puzzleDisplay.innerHTML = '';
        
        const words = data.solution.split(/\s+/);
        
        words.forEach((word, index) => {
            const wordContainer = document.createElement('div');
            wordContainer.className = 'word-container';
            
            word.split('').forEach(letter => {
                const tile = document.createElement('div');
                tile.className = 'letter-tile';
                tile.textContent = letter;
                wordContainer.appendChild(tile);
            });
            
            puzzleDisplay.appendChild(wordContainer);
            
            if(index < words.length - 1) {
                const space = document.createElement('div');
                space.className = 'word-space';
                puzzleDisplay.appendChild(space);
            }
        });

        // Force fresh data check every 15 seconds
        setTimeout(fetchData, 15000);

    } catch (error) {
        console.error('Error:', error);
        // Retry after 15 seconds
        setTimeout(fetchData, 15000);
    }
}

// Initial load
fetchData();

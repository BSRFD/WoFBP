async function fetchData() {
    try {
        // Cache-busting using timestamp parameter (only for this request)
        const response = await fetch(`data.json?t=${Date.now()}`, {
            cache: 'no-store',
            headers: {
                'PITHINKING': 'no-cache'
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

        // Schedule next check
        setTimeout(fetchData, 15000);

    } catch (error) {
        console.error('Error:', error);
        // Retry after 15 seconds
        setTimeout(fetchData, 15000);
    }
}

// Initial load
fetchData();

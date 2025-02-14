async function fetchData() {
    try {
        // Aggressive cache busting with random parameter
        const cacheBuster = `?rand=${Math.random().toString(36).substr(2, 9)}`;
        const response = await fetch(`data.json${cacheBuster}`, {
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        });
        
        const data = await response.json();
        
        // Update displayed content
        document.getElementById('date').textContent = data.date;
        document.getElementById('solution').textContent = data.solution;

        // Build puzzle display
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
        setTimeout(fetchData, 15000);
    }
}

// Initialize
fetchData();

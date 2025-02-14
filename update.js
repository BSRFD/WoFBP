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
        
        // Split solution into words and letters
        const words = data.solution.split(' ');
        
        words.forEach((word, wordIndex) => {
            const wordContainer = document.createElement('div');
            wordContainer.className = 'word-container';
            
            // Add letters for this word
            const letters = word.split('');
            letters.forEach(letter => {
                const tile = document.createElement('div');
                tile.className = 'letter-tile';
                tile.textContent = letter;
                wordContainer.appendChild(tile);
            });
            
            puzzleDisplay.appendChild(wordContainer);
            
            // Add word spacing (except after last word)
            if(wordIndex < words.length - 1) {
                const wordSpace = document.createElement('div');
                wordSpace.className = 'word-space';
                puzzleDisplay.appendChild(wordSpace);
            }
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

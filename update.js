async function fetchData() {
    try {
        const cacheBuster = `?rand=${Math.random().toString(36).substr(2, 9)}`;
        const response = await fetch(`data.json${cacheBuster}`);
        const data = await response.json();
        
        document.getElementById('date').textContent = data.date;
        document.getElementById('solution').textContent = data.solution;

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

    } catch (error) {
        console.error('Error:', error);
    }
}

async function loadHistory() {
    try {
        const response = await fetch('past-solutions.json');
        const pastSolutions = await response.json();
        const list = document.getElementById('solution-list');
        list.innerHTML = pastSolutions
            .map(item => `<li><strong>${item.date}:</strong> ${item.solution}</li>`)
            .join('');
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

function toggleHistory() {
    const content = document.getElementById('history-content');
    const button = document.getElementById('toggle-history');
    
    content.classList.toggle('hidden');
    button.textContent = content.classList.contains('hidden') 
        ? 'Show Previous Solutions' 
        : 'Hide Previous Solutions';
    
    if (!content.classList.contains('hidden') && document.getElementById('solution-list').children.length === 0) {
        loadHistory();
    }
}

// Initial load
fetchData();

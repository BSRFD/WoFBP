let historyLoaded = false;

async function revealPuzzle(solution) {
    const puzzleDisplay = document.getElementById('puzzle-display');
    puzzleDisplay.innerHTML = '';
    
    const words = solution.split(/\s+/);
    let delay = 500; // Initial delay before first letter
    
    // Create all tiles hidden
    words.forEach((word, wordIndex) => {
        const wordContainer = document.createElement('div');
        wordContainer.className = 'word-container';
        
        word.split('').forEach(letter => {
            const tile = document.createElement('div');
            tile.className = 'letter-tile';
            tile.textContent = letter.toUpperCase();
            wordContainer.appendChild(tile);
        });
        
        puzzleDisplay.appendChild(wordContainer);
        
        if(wordIndex < words.length - 1) {
            const space = document.createElement('div');
            space.className = 'word-space';
            puzzleDisplay.appendChild(space);
        }
    });

    // Reveal letters one by one
    const tiles = document.querySelectorAll('.letter-tile');
    for(const tile of tiles) {
        await new Promise(resolve => setTimeout(resolve, 200)); // 200ms between letters
        tile.classList.add('revealed');
    }
}

async function fetchData() {
    try {
        const response = await fetch(`data.json?rand=${Date.now()}`);
        const data = await response.json();
        
        document.getElementById('date').textContent = data.date;
        document.getElementById('solution').textContent = data.solution;

        await revealPuzzle(data.solution);

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
            .reverse()
            .map(item => `
                <div class="history-solution-item">
                    <div class="history-date">${item.date}</div>
                    <div class="history-solution">${item.solution}</div>
                </div>
            `).join('');

        historyLoaded = true;
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

function toggleHistory() {
    const content = document.getElementById('history-content');
    const arrow = document.querySelector('.dropdown-arrow');
    
    content.classList.toggle('visible');
    arrow.style.transform = content.classList.contains('visible') 
        ? 'rotate(225deg)' 
        : 'rotate(45deg)';
    
    if (!historyLoaded && content.classList.contains('visible')) {
        loadHistory();
    }
}

// Initial load
document.addEventListener('DOMContentLoaded', fetchData);

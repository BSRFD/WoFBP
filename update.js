const vowels = new Set(['A', 'E', 'I', 'O', 'U']);
const wildcards = new Set(['R', 'S', 'T', 'L', 'N', 'E']);
let historyLoaded = false;

async function buildPuzzleDisplay(solution) {
    const puzzleDisplay = document.getElementById('puzzle-display');
    puzzleDisplay.innerHTML = '';
    
    const words = solution.toUpperCase().split(/\s+/);
    
    for (const word of words) {
        const wordContainer = document.createElement('div');
        wordContainer.className = 'word-container';
        
        for (const letter of word) {
            await new Promise(resolve => setTimeout(resolve, 100));
            const tile = document.createElement('div');
            tile.className = 'letter-tile';
            
            if (vowels.has(letter)) {
                tile.classList.add('vowel-tile');
            } else if (wildcards.has(letter)) {
                tile.classList.add('wildcard-tile');
            }
            
            tile.textContent = letter;
            wordContainer.appendChild(tile);
        }
        
        puzzleDisplay.appendChild(wordContainer);
        
        if (words.indexOf(word) < words.length - 1) {
            const space = document.createElement('div');
            space.className = 'word-space';
            puzzleDisplay.appendChild(space);
        }
    }
}

async function fetchData() {
    try {
        const cacheBuster = `?rand=${Date.now()}`;
        const response = await fetch(`data.json${cacheBuster}`);
        const data = await response.json();
        
        document.getElementById('date').textContent = data.date;
        document.getElementById('solution').textContent = data.solution;
        
        await buildPuzzleDisplay(data.solution);

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

// Initialize on page load
document.addEventListener('DOMContentLoaded', fetchData);

let historyLoaded = false;
let lastUpdateCheck = Date.now();

// Fisher-Yates shuffle algorithm
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

// --- NEW FUNCTION to display any puzzle on the board ---
function displayPuzzleOnBoard(dateStr, solutionStr, addedUtcStr) {
    const dateElement = document.getElementById('date');
    const solutionElement = document.getElementById('solution');
    
    dateElement.textContent = dateStr;
    solutionElement.textContent = solutionStr;

    // Update click-to-copy for the new solution
    solutionElement.style.cursor = 'pointer';
    solutionElement.setAttribute('title', 'Click to copy');
    // Remove old event listener to prevent multiple listeners if any
    const newSolutionElement = solutionElement.cloneNode(true);
    solutionElement.parentNode.replaceChild(newSolutionElement, solutionElement);
    
    newSolutionElement.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(solutionStr);
            showCopyFeedback('Copied to clipboard!');
        } catch (err) {
            console.error('Failed to copy:', err);
            showCopyFeedback('Failed to copy!');
        }
    });


    const puzzleDisplay = document.getElementById('puzzle-display');
    puzzleDisplay.innerHTML = ''; // Clear previous puzzle
    
    const addedDate = addedUtcStr ? new Date(addedUtcStr) : null;
    let timeContainer = null;
    if (addedDate) {
        timeContainer = document.createElement('div');
        timeContainer.className = 'puzzle-timestamp';
        timeContainer.textContent = `Added: ${addedDate.toLocaleTimeString([], { 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: true 
        })}`;
    }

    const wordContainer = document.createElement('div');
    wordContainer.className = 'word-container';
    puzzleDisplay.appendChild(wordContainer);

    const allTiles = [];
    const words = solutionStr.split(/\s+/);
    
    const MAX_CHARS_PER_LINE = 14; 
    let currentLineElement = null;
    let currentLineCharCount = 0;

    words.forEach((word) => {
        const wordLength = word.length;
        const spaceNeededForThisWord = currentLineCharCount > 0 ? 1 + wordLength : wordLength;

        if (currentLineElement === null || (currentLineCharCount + spaceNeededForThisWord > MAX_CHARS_PER_LINE && currentLineCharCount > 0)) {
            currentLineElement = document.createElement('div');
            currentLineElement.className = 'word-row';
            wordContainer.appendChild(currentLineElement);
            currentLineCharCount = 0;
        }

        if (currentLineCharCount > 0) {
            const spaceTile = document.createElement('div');
            spaceTile.className = 'letter-tile space-tile';
            spaceTile.innerHTML = ' ';
            currentLineElement.appendChild(spaceTile);
            currentLineCharCount += 1;
        }

        [...word.toUpperCase()].forEach(letter => {
            const tile = document.createElement('div');
            tile.className = 'letter-tile';
            tile.textContent = letter;
            currentLineElement.appendChild(tile);
            allTiles.push(tile);
        });
        currentLineCharCount += wordLength;
    });

    if (timeContainer) {
         puzzleDisplay.appendChild(timeContainer);
    }

    shuffleArray(allTiles); 
    allTiles.forEach((tile, index) => {
        setTimeout(() => {
            tile.classList.add('revealed');
        }, index * 50); 
    });

    // Scroll to the top to see the newly displayed puzzle
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
// --- END NEW FUNCTION ---


async function fetchData() {
    try {
        const response = await fetch(`data.json?rand=${Date.now()}`);
        const data = await response.json();
        
        // Use the new function to display the fetched current puzzle
        displayPuzzleOnBoard(data.date, data.solution, data.added_utc);

        // Auto-refresh check every 5 minutes
        if (Date.now() - lastUpdateCheck > 300000) { 
            const freshCheck = await fetch(`data.json?rand=${Date.now()}`);
            const freshData = await freshCheck.json();
            // If current puzzle data changed, reload the page to fetch and display it
            if (freshData.date !== data.date || freshData.solution !== data.solution) { 
                window.location.reload(true);
            }
            lastUpdateCheck = Date.now();
        }
        // Note: Click-to-copy is now handled within displayPuzzleOnBoard

    } catch (error) {
        console.error('Error fetching or displaying current data:', error);
        const puzzleDisplay = document.getElementById('puzzle-display');
        if(puzzleDisplay) puzzleDisplay.textContent = "Could not load current puzzle. Please try again later.";
        // Also update info panel for consistency
        const dateElement = document.getElementById('date');
        const solutionElement = document.getElementById('solution');
        if(dateElement) dateElement.textContent = "Error";
        if(solutionElement) solutionElement.textContent = "Error";

    }
}

function showCopyFeedback(message) {
    const feedback = document.createElement('div');
    feedback.className = 'copy-feedback';
    feedback.setAttribute('role', 'alert');
    feedback.setAttribute('aria-live', 'polite');
    feedback.textContent = message;
    
    const existing = document.querySelector('.copy-feedback');
    if (existing) existing.remove();
    
    document.body.appendChild(feedback);
    void feedback.offsetWidth; 
    feedback.style.opacity = '1';
    
    setTimeout(() => {
        feedback.style.opacity = '0';
        setTimeout(() => feedback.remove(), 500);
    }, 1500);
}

async function loadHistory() {
    try {
        const response = await fetch(`past-solutions.json?rand=${Date.now()}`);
        const pastSolutions = await response.json();
        const list = document.getElementById('solution-list');
        
        list.innerHTML = pastSolutions
            .map(item => {
                const addedDate = item.added_utc ? new Date(item.added_utc) : null;
                const timeString = addedDate ? 
                    addedDate.toLocaleTimeString([], { 
                        hour: 'numeric', 
                        minute: '2-digit',
                        hour12: true 
                    }) : '';
                
                // Escape quotes in item data for use in inline JS
                const safeDate = item.date.replace(/'/g, "\\'");
                const safeSolution = item.solution.replace(/'/g, "\\'");
                const safeAddedUtc = item.added_utc ? item.added_utc.replace(/'/g, "\\'") : '';

                return `
                    <div class="history-solution-item" 
                         onclick="displayPuzzleOnBoard('${safeDate}', '${safeSolution}', '${safeAddedUtc}')"
                         title="Click to view this puzzle on the board"
                         role="button" 
                         tabindex="0" 
                         onkeypress="if(event.key==='Enter' || event.key===' ') { displayPuzzleOnBoard('${safeDate}', '${safeSolution}', '${safeAddedUtc}'); event.preventDefault(); }">
                        <div class="history-date" ${timeString ? `title="Added at ${timeString}"` : ''}>
                            ${item.date}
                        </div>
                        <div class="history-solution">
                            ${item.solution}
                        </div>
                    </div>
                `;
            }).join('');

        historyLoaded = true;
    } catch (error) {
        console.error('Error loading history:', error);
        const list = document.getElementById('solution-list');
        if(list) list.innerHTML = "<p style='text-align:center; color: var(--gold);'>Could not load history.</p>";
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

document.addEventListener('DOMContentLoaded', fetchData);

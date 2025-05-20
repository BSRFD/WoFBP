let historyLoaded = false;
let lastUpdateCheck = Date.now();

// Fisher-Yates shuffle algorithm
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

async function fetchData() {
    try {
        const response = await fetch(`data.json?rand=${Date.now()}`);
        const data = await response.json();
        
        const dateElement = document.getElementById('date');
        const solutionElement = document.getElementById('solution');
        
        dateElement.textContent = data.date;
        solutionElement.textContent = data.solution;

        // Auto-refresh check every 5 minutes
        if (Date.now() - lastUpdateCheck > 300000) { 
            const freshCheck = await fetch(`data.json?rand=${Date.now()}`);
            const freshData = await freshCheck.json();
            if (freshData.date !== data.date || freshData.solution !== data.solution) { // Check solution too for rare cases
                window.location.reload(true);
            }
            lastUpdateCheck = Date.now();
        }

        // Click-to-copy functionality
        solutionElement.style.cursor = 'pointer';
        solutionElement.setAttribute('title', 'Click to copy');
        solutionElement.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(data.solution);
                showCopyFeedback('Copied to clipboard!');
            } catch (err) {
                console.error('Failed to copy:', err);
                showCopyFeedback('Failed to copy!');
            }
        });

        const puzzleDisplay = document.getElementById('puzzle-display');
        puzzleDisplay.innerHTML = ''; // Clear previous puzzle
        
        const addedDate = data.added_utc ? new Date(data.added_utc) : null;
        let timeContainer = null; // Declare here to append later
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
        puzzleDisplay.appendChild(wordContainer); // Add wordContainer to the display

        const allTiles = []; // To store actual letter tiles for animation
        const words = data.solution.split(/\s+/);
        
        // --- NEW LINE BREAKING LOGIC ---
        const MAX_CHARS_PER_LINE = 14; // Adjust this (e.g., 12-14) for best visual fit
        let currentLineElement = null;
        let currentLineCharCount = 0;

        words.forEach((word) => { // Removed wordIndex as it's not used here
            const wordLength = word.length;
            const spaceNeededForThisWord = currentLineCharCount > 0 ? 1 + wordLength : wordLength;

            // If currentLineElement is null (first line) OR if the current word doesn't fit on the current line
            if (currentLineElement === null || (currentLineCharCount + spaceNeededForThisWord > MAX_CHARS_PER_LINE && currentLineCharCount > 0)) {
                // Start a new line
                currentLineElement = document.createElement('div');
                currentLineElement.className = 'word-row';
                wordContainer.appendChild(currentLineElement);
                currentLineCharCount = 0; // Reset char count for the new line
            }

            // Add space tile if it's not the first word on this (current or new) line
            if (currentLineCharCount > 0) {
                const spaceTile = document.createElement('div');
                spaceTile.className = 'letter-tile space-tile';
                spaceTile.innerHTML = ' '; // Visually empty, but takes up space
                currentLineElement.appendChild(spaceTile);
                currentLineCharCount += 1; // Account for the space character
            }

            // Add letter tiles for the current word
            [...word.toUpperCase()].forEach(letter => {
                const tile = document.createElement('div');
                tile.className = 'letter-tile';
                tile.textContent = letter;
                currentLineElement.appendChild(tile);
                allTiles.push(tile); // Add to allTiles for reveal animation
            });
            currentLineCharCount += wordLength; // Add length of the word
        });
        // --- END NEW LINE BREAKING LOGIC ---

        if (timeContainer) { // Append timestamp after puzzle, relying on absolute CSS positioning
             puzzleDisplay.appendChild(timeContainer);
        }

        // Shuffle and reveal only actual letter tiles
        shuffleArray(allTiles); 
        allTiles.forEach((tile, index) => {
            setTimeout(() => {
                tile.classList.add('revealed');
            }, index * 50); // Stagger reveal animation
        });

    } catch (error) {
        console.error('Error fetching or displaying data:', error);
        // Optionally, display a user-friendly error message on the page
        const puzzleDisplay = document.getElementById('puzzle-display');
        if(puzzleDisplay) puzzleDisplay.textContent = "Could not load puzzle. Please try again later.";
    }
}

function showCopyFeedback(message) {
    const feedback = document.createElement('div');
    feedback.className = 'copy-feedback';
    feedback.setAttribute('role', 'alert');
    feedback.setAttribute('aria-live', 'polite');
    feedback.textContent = message;
    
    // Clear existing feedback
    const existing = document.querySelector('.copy-feedback');
    if (existing) existing.remove();
    
    document.body.appendChild(feedback);
    
    // Force reflow to enable animation
    void feedback.offsetWidth;
    
    feedback.style.opacity = '1';
    
    setTimeout(() => {
        feedback.style.opacity = '0';
        setTimeout(() => feedback.remove(), 500); // Remove after fade out
    }, 1500);
}

async function loadHistory() {
    try {
        const response = await fetch(`past-solutions.json?rand=${Date.now()}`);
        const pastSolutions = await response.json(); // Already sorted most recent first from Python
        const list = document.getElementById('solution-list');
        
        list.innerHTML = pastSolutions
            // .reverse() // Removed as past-solutions.json is already sorted recent first
            .map(item => {
                const addedDate = item.added_utc ? new Date(item.added_utc) : null;
                const timeString = addedDate ? 
                    addedDate.toLocaleTimeString([], { 
                        hour: 'numeric', 
                        minute: '2-digit',
                        hour12: true 
                    }) : '';
                return `
                    <div class="history-solution-item">
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

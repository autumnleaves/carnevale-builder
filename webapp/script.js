// Global variables
let cardsData = null;

// Load the card data when the page loads
document.addEventListener('DOMContentLoaded', function() {
    loadCardData();
    setupEventListeners();
});

// Load card data from JSON file
async function loadCardData() {
    try {
        const response = await fetch('guild_cards.json');
        cardsData = await response.json();
        populateCardDropdown();
    } catch (error) {
        console.error('Error loading card data:', error);
        document.getElementById('cardDisplay').innerHTML = 
            '<p style="color: red;">Error loading card data. Make sure you are running this from a web server (not file://). Try running: python -m http.server 8000</p>';
    }
}

// Populate the dropdown with card names
function populateCardDropdown() {
    const select = document.getElementById('cardSelect');
    
    // Clear existing options except the first one
    while (select.children.length > 1) {
        select.removeChild(select.lastChild);
    }
    
    // Add cards grouped by rank
    const cardsByRank = groupCardsByRank(cardsData.cards);
    
    Object.keys(cardsByRank).forEach(rank => {
        if (cardsByRank[rank].length > 0) {
            const optgroup = document.createElement('optgroup');
            optgroup.label = rank || 'No Rank';
            
            cardsByRank[rank].forEach(card => {
                const option = document.createElement('option');
                option.value = card.name;
                option.textContent = `${card.name} (${card.ducats} ducats)`;
                optgroup.appendChild(option);
            });
            
            select.appendChild(optgroup);
        }
    });
}

// Group cards by rank for better organization
function groupCardsByRank(cards) {
    const groups = {
        'Leader': [],
        'Hero': [],
        'Henchman': []
    };
    
    cards.forEach(card => {
        const rank = card.rank || 'No Rank';
        if (!groups[rank]) {
            groups[rank] = [];
        }
        groups[rank].push(card);
    });
    
    // Sort each group by name
    Object.keys(groups).forEach(rank => {
        groups[rank].sort((a, b) => a.name.localeCompare(b.name));
    });
    
    return groups;
}

// Setup event listeners
function setupEventListeners() {
    const select = document.getElementById('cardSelect');
    select.addEventListener('change', function() {
        if (this.value) {
            displayCard(this.value);
        } else {
            clearCardDisplay();
        }
    });
}

// Display the selected card
function displayCard(cardName) {
    const card = cardsData.cards.find(c => c.name === cardName);
    if (!card) {
        console.error('Card not found:', cardName);
        return;
    }
    
    const cardDisplay = document.getElementById('cardDisplay');
    cardDisplay.innerHTML = generateCardHTML(card);
}

// Generate HTML for a card
function generateCardHTML(card) {
    return `
        <div class="card-header">
            <div class="card-name">${card.name}</div>
            <div class="card-meta">
                <span>Page: ${card.page}</span>
                <span>Version: ${card.version}</span>
                <span>Rank: ${card.rank || 'N/A'}</span>
            </div>
        </div>
        
        ${generateKeywords(card.keywords)}
        
        <div class="card-stats">
            ${generateBasicStats(card)}
            ${generateStatBlock(card.stat_block)}
        </div>
        
        ${generateWeapons(card.weapons)}
        ${generateAbilities(card.abilities)}
    `;
}

// Generate keywords display
function generateKeywords(keywords) {
    if (!keywords || keywords.length === 0) {
        return '';
    }
    
    const keywordTags = keywords.map(keyword => 
        `<span class="keyword">${keyword}</span>`
    ).join('');
    
    return `<div class="keywords">${keywordTags}</div>`;
}

// Generate basic stats section
function generateBasicStats(card) {
    const stats = [
        { label: 'Actions', value: card.actions },
        { label: 'Command', value: card.command },
        { label: 'Will', value: card.will },
        { label: 'Life', value: card.life },
        { label: 'Base Size', value: card.base_size ? `${card.base_size}mm` : 'N/A' },
        { label: 'Ducats', value: card.ducats }
    ];
    
    const statsHTML = stats.map(stat => 
        `<div class="stat-item">
            <span class="stat-label">${stat.label}:</span>
            <span>${stat.value || 'N/A'}</span>
        </div>`
    ).join('');
    
    return `
        <div class="stats-section">
            <h3>Basic Stats</h3>
            <div class="stat-grid">${statsHTML}</div>
        </div>
    `;
}

// Generate stat block section
function generateStatBlock(statBlock) {
    if (!statBlock) {
        return '<div class="stats-section"><h3>Combat Stats</h3><p>No combat stats available</p></div>';
    }
    
    const stats = [
        { label: 'Movement', value: statBlock.movement },
        { label: 'Dexterity', value: statBlock.dexterity },
        { label: 'Attack', value: statBlock.attack },
        { label: 'Protection', value: statBlock.protection },
        { label: 'Mind', value: statBlock.mind }
    ];
    
    const statsHTML = stats.map(stat => 
        `<div class="stat-item">
            <span class="stat-label">${stat.label}:</span>
            <span>${stat.value || 'N/A'}</span>
        </div>`
    ).join('');
    
    return `
        <div class="stats-section">
            <h3>Combat Stats</h3>
            <div class="stat-grid">${statsHTML}</div>
        </div>
    `;
}

// Generate weapons section
function generateWeapons(weapons) {
    if (!weapons || weapons.length === 0) {
        return '<div class="weapons-section"><h3>Weapons</h3><p>No weapons</p></div>';
    }
    
    const weaponsHTML = weapons.map(weapon => `
        <div class="weapon">
            <div class="weapon-name">${weapon.name}</div>
            <div class="weapon-stats">
                <div class="weapon-stat">
                    <span>Range:</span>
                    <span>${weapon.range || 'N/A'}</span>
                </div>
                <div class="weapon-stat">
                    <span>Evasion:</span>
                    <span>${weapon.evasion || 'N/A'}</span>
                </div>
                <div class="weapon-stat">
                    <span>Damage:</span>
                    <span>${weapon.damage || 'N/A'}</span>
                </div>
                <div class="weapon-stat">
                    <span>Penetration:</span>
                    <span>${weapon.penetration || 'N/A'}</span>
                </div>
                <div class="weapon-stat">
                    <span>Abilities:</span>
                    <span>${weapon.abilities || 'N/A'}</span>
                </div>
            </div>
        </div>
    `).join('');
    
    return `
        <div class="weapons-section">
            <h3>Weapons</h3>
            ${weaponsHTML}
        </div>
    `;
}

// Generate abilities section
function generateAbilities(abilities) {
    if (!abilities) {
        return '<div class="abilities-section"><h3>Abilities</h3><p>No abilities</p></div>';
    }
    
    let abilitiesHTML = '';
    
    // Common abilities
    if (abilities.common && abilities.common.length > 0) {
        const commonHTML = abilities.common.map(ability => {
            if (typeof ability === 'string') {
                return `<div class="ability"><div class="ability-name">${ability}</div></div>`;
            } else {
                return `
                    <div class="ability">
                        <div class="ability-name">${ability.name}</div>
                        <div class="ability-description">${ability.description}</div>
                    </div>
                `;
            }
        }).join('');
        
        abilitiesHTML += `
            <div class="abilities-group">
                <h4>Common Abilities</h4>
                ${commonHTML}
            </div>
        `;
    }
    
    // Unique abilities
    if (abilities.unique && abilities.unique.length > 0) {
        const uniqueHTML = abilities.unique.map(ability => `
            <div class="ability">
                <div class="ability-name">${ability.name}</div>
                <div class="ability-description">${ability.description}</div>
            </div>
        `).join('');
        
        abilitiesHTML += `
            <div class="abilities-group">
                <h4>Unique Abilities</h4>
                ${uniqueHTML}
            </div>
        `;
    }
    
    // Command abilities
    if (abilities.command && abilities.command.length > 0) {
        const commandHTML = abilities.command.map(ability => `
            <div class="ability">
                <div class="ability-name">${ability.name}</div>
                ${ability.type ? `<div class="ability-type">${ability.type}</div>` : ''}
                <div class="ability-description">${ability.description}</div>
            </div>
        `).join('');
        
        abilitiesHTML += `
            <div class="abilities-group">
                <h4>Command Abilities</h4>
                ${commandHTML}
            </div>
        `;
    }
    
    return `
        <div class="abilities-section">
            <h3>Abilities</h3>
            ${abilitiesHTML || '<p>No abilities</p>'}
        </div>
    `;
}

// Clear the card display
function clearCardDisplay() {
    document.getElementById('cardDisplay').innerHTML = '<p>Select a card to view its details.</p>';
}

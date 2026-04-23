// Dashboard Rendering Script
// This script dynamically generates the dashboard HTML from the data in dashboard-data.js

// Render Summary Cards
function renderSummaryCards() {
    const container = document.getElementById('summary-cards');
    const { summary } = dashboardData;
    
    container.innerHTML = `
        <div class="card">
            <h3>${summary.totalLanguages}</h3>
            <p>Total Languages</p>
        </div>
        <div class="card">
            <h3>${summary.totalRepos}</h3>
            <p>Repos (${summary.repoNames})</p>
        </div>
        <div class="card">
            <h3>${summary.totalFiles}</h3>
            <p>Total Files (English)</p>
        </div>
        <div class="card">
            <h3>${summary.languagesStarted}</h3>
            <p>Languages Started</p>
        </div>
        <div class="card">
            <h3>${summary.totalRows.toLocaleString()}</h3>
            <p>Total Rows (Source)</p>
        </div>
        <div class="card">
            <h3>${summary.overallCompletion}</h3>
            <p>Overall Completion</p>
        </div>
    `;
}

// Render Main 5 Processes
function renderMainProcesses() {
    const container = document.getElementById('main-processes');
    const { mainProcesses } = dashboardData;
    
    container.innerHTML = mainProcesses.map(process => {
        const borderStyle = process.status === 'in-progress' ? 'border: 3px solid #FFBA07;' : '';
        const titleColor = process.status === 'in-progress' ? '#FFBA07' : 
                          process.status === 'complete' ? '#00C3BF' : '#1B7FBD';
        const descColor = process.status === 'in-progress' ? '#FFBA07' : '#666';
        const descWeight = process.status === 'in-progress' ? 'font-weight: bold;' : '';
        
        return `
            <div style="background: rgba(255,255,255,0.95); padding: 20px; border-radius: 8px; text-align: center; ${borderStyle}">
                <div style="font-size: 2.5em; margin-bottom: 10px;">${process.icon}</div>
                <h3 style="color: ${titleColor}; margin-bottom: 10px; font-size: 1.1em;">${process.id}. ${process.name}</h3>
                <p style="color: ${descColor}; font-size: 0.9em; margin: 0; ${descWeight}">${process.description}</p>
            </div>
        `;
    }).join('');
}

// Render Process Flows
function renderProcessFlows() {
    const container = document.getElementById('process-flows');
    const { processFlows } = dashboardData;
    
    container.innerHTML = processFlows.map(flow => 
        `<p style="margin: 5px 0;"><strong>${flow.languages}:</strong> ${flow.flow}</p>`
    ).join('');
}

// Render Language Sections
function renderLanguages() {
    const container = document.getElementById('languages-grid');
    const { languages } = dashboardData;
    
    container.innerHTML = Object.values(languages).map(lang => {
        if (lang.message) {
            // Simple language card (not started)
            return `
                <div class="language-section">
                    <div class="language-header">
                        <span class="language-title">${lang.flag} ${lang.name} Language</span>
                        <span class="status-badge ${lang.statusClass}">${lang.status}</span>
                    </div>
                    <p style="color: #666; margin: 10px 0;">${lang.message}</p>
                </div>
            `;
        }
        
        // Full language card with processes
        let html = `
            <div class="language-section" ${lang.type === 'source' ? 'style="border-left-color: #0066cc;"' : ''}>
                <div class="language-header">
                    <span class="language-title">${lang.flag} ${lang.name} Language ${lang.type === 'source' ? '(SOURCE)' : ''}</span>
                    <span class="status-badge ${lang.statusClass}">${lang.status}</span>
                </div>
        `;
        
        // Alert if present
        if (lang.alert) {
            const alertStyle = lang.alert.type === 'info' ? 
                'background: #d1ecf1; border-left-color: #0066cc;' : 
                'background: #fff3cd; border-left-color: #ffc107;';
            const alertIcon = lang.alert.type === 'info' ? 'ℹ️' : '⚠️';
            const alertTitle = lang.alert.type === 'info' ? 'Info' : 'Data Quality Issue';
            
            html += `
                <div class="alert" style="${alertStyle} margin-bottom: 15px;">
                    <strong>${alertIcon} ${alertTitle}:</strong> ${lang.alert.message}
                </div>
            `;
        }
        
        // Progress bars for each process
        if (lang.processes) {
            const processNames = {
                extraction: 'Extraction',
                formatting: 'Formatting',
                qcStatus: 'QC Status',
                idGeneration: 'ID Generation',
                aiTranslation: 'AI Translation',
                bufridgenration: 'BUFR4 ID Generation',
                grib2idgenration: 'GRIB2 ID Generation',
                cctidgenration: 'CCT ID Generation'
            };
            
            for (const [key, process] of Object.entries(lang.processes)) {
                const bgColor = process.status === 'complete' ? '#00C3BF' : 
                               process.status === 'started' ? '#FFBA07' : '#dc3545';
                const text = process.status === 'complete' ? '✓ Complete' : 
                            process.status === 'started' ? 'Started' : 'Not Started';
                
                html += `
                    <div class="progress-bar-container">
                        <div class="progress-label">
                            <span>${processNames[key]}</span>
                            <span>${process.progress}%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${process.progress}%; background: ${bgColor};">${text}</div>
                        </div>
                    </div>
                `;
            }
        }
        
        // Stats row
        html += `
            <div class="stats-row">
                <div class="stat-item">
                    <div class="stat-value">${lang.totalFiles}</div>
                    <div class="stat-label">Total Files</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${lang.totalRows ? lang.totalRows.toLocaleString() : lang.repos}</div>
                    <div class="stat-label">${lang.totalRows ? 'Total Rows' : lang.reposDetail}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${lang.missingRows ? lang.missingRows.toLocaleString() : lang.repos}</div>
                    <div class="stat-label">${lang.missingRows ? 'Missing Rows' : lang.reposDetail}</div>
                </div>
            </div>
        `;
        
        // Warning alert for Spanish
        if (lang.code === 'es' && lang.alert && lang.alert.type === 'warning') {
            html += `
                <div class="alert">
                    <strong>⚠️ Data Quality Issue:</strong> ${lang.alert.message}
                </div>
            `;
        }
        
        html += `</div>`;
        return html;
    }).join('');
}

// Render Process Matrix
function renderMatrix() {
    const table = document.getElementById('matrix-table');
    const { processMatrix } = dashboardData;
    
    let html = `
        <thead>
            <tr>
                <th>Process</th>
                ${processMatrix.languages.map(lang => 
                    `<th>${lang.name}${lang.subtitle ? '<br/><small>' + lang.subtitle + '</small>' : ''}</th>`
                ).join('')}
            </tr>
        </thead>
        <tbody>
    `;
    
    processMatrix.processes.forEach((process, i) => {
        html += `<tr><td><strong>${process}</strong></td>`;
        processMatrix.data[i].forEach((value, j) => {
            const cellClass = processMatrix.cellClasses[i][j];
            html += `<td class="${cellClass}">${value}</td>`;
        });
        html += `</tr>`;
    });
    
    html += `</tbody>`;
    table.innerHTML = html;
}

// Render Blockers
function renderBlockers() {
    const container = document.getElementById('blockers-container');
    const { blockers } = dashboardData;
    
    container.innerHTML = blockers.map(blocker => {
        const alertClass = blocker.priority === 'danger' ? 'alert alert-danger' : 'alert';
        return `
            <div class="${alertClass}">
                <strong>${blocker.title}</strong><br>
                ${blocker.description}
            </div>
        `;
    }).join('');
}

// Update Footer
function updateFooter() {
    const { metadata } = dashboardData;
    document.getElementById('footer-text').textContent = metadata.generatedFrom;
    document.getElementById('last-updated').textContent = `Last updated: ${metadata.lastUpdated}`;
}

// Initialize Dashboard
function initDashboard() {
    renderSummaryCards();
    renderMainProcesses();
    renderProcessFlows();
    renderLanguages();
    renderMatrix();
    renderBlockers();
    updateFooter();
}

// Run when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
} else {
    initDashboard();
}

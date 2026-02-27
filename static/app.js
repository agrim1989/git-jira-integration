document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const searchInput = document.getElementById('ticket-search');
    const searchBtn = document.getElementById('btn-search');
    const ticketView = document.getElementById('ticket-view');
    const btnBackHome = document.getElementById('btn-back-home');

    // Ticket Elements
    const elKey = document.getElementById('ticket-key');
    const elTitle = document.getElementById('ticket-title');
    const elDesc = document.getElementById('ticket-description');
    const elStatus = document.getElementById('ticket-status');
    const elAssignee = document.getElementById('ticket-assignee');
    const elType = document.getElementById('ticket-type');

    // Buttons & Terminal
    const btnGenerate = document.getElementById('btn-generate-solution');
    const btnGithub = document.getElementById('btn-github-flow');
    const btnCancelSolution = document.getElementById('btn-cancel-solution');
    const btnPublishSolution = document.getElementById('btn-publish-solution');
    const solutionEditorPanel = document.getElementById('solution-editor-panel');
    const solutionEditor = document.getElementById('solution-editor');
    const ticketActionsPanel = document.getElementById('ticket-actions-panel');
    const terminalPanel = document.getElementById('terminal-panel');
    const terminalOutput = document.getElementById('terminal-output');
    const terminalLoader = document.getElementById('terminal-loader');
    const terminalLoaderText = document.getElementById('terminal-loader-text');
    const btnCloseTerminal = document.getElementById('btn-close-terminal');

    const btnPostComment = document.getElementById('btn-post-comment');
    const inputComment = document.getElementById('new-comment-input');

    // Modal Elements
    const settingsModal = document.getElementById('settings-modal');
    const btnOpenSettings = document.getElementById('btn-open-settings');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const btnSaveSettings = document.getElementById('btn-save-settings');
    const formSettings = document.getElementById('settings-form');

    // GitHub Modal Elements
    const githubModal = document.getElementById('github-modal');
    const btnCloseGithubModal = document.getElementById('btn-close-github-modal');
    const btnStartGithubFlow = document.getElementById('btn-start-github-flow');
    let githubFlowTargetTicket = null;

    // Draft Modal Elements
    const draftModal = document.getElementById('draft-modal');
    const btnCreateTicket = document.getElementById('btn-create-ticket');
    const btnUpdateTicket = document.getElementById('btn-update-ticket');
    const btnCloseDraftModal = document.getElementById('btn-close-draft-modal');
    const btnGenerateDraft = document.getElementById('btn-generate-draft');
    const btnSubmitDraft = document.getElementById('btn-submit-draft');
    const draftPrompt = document.getElementById('draft-prompt');
    const draftSummary = document.getElementById('draft-summary');
    const draftProjectKey = document.getElementById('draft-project-key');
    const draftDescription = document.getElementById('draft-description');
    const draftEditorSection = document.getElementById('draft-editor-section');
    const draftProjectGroup = document.getElementById('draft-project-group');
    const draftModalFooter = document.getElementById('draft-modal-footer');
    const draftModalTitle = document.getElementById('draft-modal-title');
    let draftMode = 'CREATE';

    // Theme Elements
    const btnToggleTheme = document.getElementById('btn-toggle-theme');
    const iconMoon = document.getElementById('icon-moon');
    const iconSun = document.getElementById('icon-sun');

    // Ticket List Elements
    const ticketListView = document.getElementById('ticket-list-view');
    const ticketsContainer = document.getElementById('tickets-container');
    const ticketsLoading = document.getElementById('tickets-loading');

    // Ticket Filter Elements
    const filterBtns = document.querySelectorAll('.filter-btn:not(.type-filter-btn)');
    const typeFilterBtns = document.querySelectorAll('.type-filter-btn');
    let currentFilter = 'recent';
    let currentTypeFilter = 'all';

    // Tickets cache
    let ticketsCache = {};
    let lastFetchedTickets = [];

    // State
    let currentTicket = null;
    let easyMDE = null;

    // Boot App
    initTheme();
    bootApp();

    // Event Listeners
    if (btnBackHome) {
        btnBackHome.addEventListener('click', resetView);
    }
    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    filterBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            filterBtns.forEach(b => b.classList.remove('active'));
            e.currentTarget.classList.add('active');
            currentFilter = e.currentTarget.getAttribute('data-filter');
            fetchTicketsList();
        });
    });

    typeFilterBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            typeFilterBtns.forEach(b => b.classList.remove('active'));
            e.currentTarget.classList.add('active');
            currentTypeFilter = e.currentTarget.getAttribute('data-type');
            applyTypeFilter();
        });
    });

    btnGenerate.addEventListener('click', () => generateSolution(currentTicket));
    btnGithub.addEventListener('click', () => triggerGithubFlow(currentTicket));
    btnCloseTerminal.addEventListener('click', hideTerminal);

    btnCancelSolution.addEventListener('click', cancelSolutionReview);
    btnPublishSolution.addEventListener('click', () => publishSolution(currentTicket));

    if (btnPostComment && inputComment) {
        btnPostComment.addEventListener('click', async () => {
            const body = inputComment.value.trim();
            if (!body || !currentTicket) return;
            const originalText = btnPostComment.textContent;
            btnPostComment.textContent = 'Posting...';
            btnPostComment.disabled = true;

            try {
                const res = await fetch(`${API_BASE}/tickets/${currentTicket.key}/comments`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ body })
                });
                if (!res.ok) throw new Error("Failed to post comment");
                inputComment.value = '';
                showToast("Comment posted!", "success");

                // Refresh comments
                fetchComments(currentTicket.key);
            } catch (error) {
                showToast(error.message, "error");
            } finally {
                btnPostComment.textContent = originalText;
                btnPostComment.disabled = false;
            }
        });

        inputComment.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') btnPostComment.click();
        });
    }

    btnOpenSettings.addEventListener('click', openSettings);
    btnCloseModal.addEventListener('click', closeSettings);
    btnSaveSettings.addEventListener('click', saveSettings);
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) closeSettings();
    });

    btnCreateTicket.addEventListener('click', () => openDraftModal('CREATE'));
    if (btnUpdateTicket) {
        btnUpdateTicket.addEventListener('click', () => openDraftModal('UPDATE'));
    }
    btnCloseDraftModal.addEventListener('click', closeDraftModal);
    btnGenerateDraft.addEventListener('click', generateDraftDetails);
    btnSubmitDraft.addEventListener('click', submitDraftDetails);

    btnCloseGithubModal.addEventListener('click', () => githubModal.classList.add('hidden'));
    btnStartGithubFlow.addEventListener('click', () => {
        githubModal.classList.add('hidden');
        executeGithubFlow(githubFlowTargetTicket);
    });

    btnToggleTheme.addEventListener('click', toggleTheme);

    // API Base URL
    const API_BASE = window.location.origin;

    // Functions
    function initTheme() {
        const savedTheme = localStorage.getItem('jira_theme') || 'dark';
        if (savedTheme === 'light') {
            document.body.setAttribute('data-theme', 'light');
            iconSun.style.display = 'none';
            iconMoon.style.display = 'block';
        }
    }

    function toggleTheme() {
        const currentTheme = document.body.getAttribute('data-theme');
        if (currentTheme === 'light') {
            document.body.removeAttribute('data-theme');
            localStorage.setItem('jira_theme', 'dark');
            iconMoon.style.display = 'none';
            iconSun.style.display = 'block';
        } else {
            document.body.setAttribute('data-theme', 'light');
            localStorage.setItem('jira_theme', 'light');
            iconSun.style.display = 'none';
            iconMoon.style.display = 'block';
        }
    }

    function initEditor() {
        if (!easyMDE) {
            easyMDE = new EasyMDE({
                element: solutionEditor,
                spellChecker: false,
                status: false,
                initialValue: "",
                placeholder: "Solution will appear here...",
                toolbar: ["bold", "italic", "heading", "|", "quote", "code", "unordered-list", "ordered-list", "|", "link", "preview", "side-by-side", "fullscreen"]
            });
        }
    }

    async function bootApp() {
        initEditor();
        const creds = localStorage.getItem('jira_mcp_creds');
        if (creds) {
            try {
                const parsed = JSON.parse(creds);
                document.getElementById('jira-url').value = parsed.jira_url || '';
                document.getElementById('jira-email').value = parsed.jira_username || '';
                document.getElementById('jira-token').value = parsed.jira_api_token || '';
            } catch (e) { }
        }

        try {
            const res = await fetch(`${API_BASE}/health`);
            const data = await res.json();
            if (!data.jira_configured && (!creds || !JSON.parse(creds).jira_url)) {
                openSettings();
            } else {
                fetchTicketsList();
            }
        } catch (e) {
            showToast("Backend connection failed", "error");
        }
    }

    /* ==== Draft logic ==== */
    function openDraftModal(mode) {
        draftMode = mode;
        draftPrompt.value = '';
        draftSummary.value = '';
        draftDescription.value = '';
        draftProjectKey.value = '';

        if (mode === 'CREATE') {
            draftModalTitle.textContent = 'Create New Ticket';
            draftProjectGroup.style.display = 'block';
            btnSubmitDraft.textContent = 'Create Ticket';

            // Always show the editor straight away for new tickets so they can input project key 
            draftEditorSection.classList.remove('hidden');
            draftModalFooter.classList.remove('hidden');

            let guessedProject = '';
            if (currentTicket) {
                guessedProject = currentTicket.key.split('-')[0];
            } else if (Object.keys(ticketsCache).length > 0) {
                guessedProject = Object.keys(ticketsCache)[0].split('-')[0];
            }
            draftProjectKey.value = guessedProject;
        } else {
            draftModalTitle.textContent = 'AI Detail Update';
            draftProjectGroup.style.display = 'none';
            btnSubmitDraft.textContent = 'Update Ticket';

            // Hide for updates until generated
            draftEditorSection.classList.add('hidden');
            draftModalFooter.classList.add('hidden');
        }
        draftModal.classList.remove('hidden');
    }

    function closeDraftModal() {
        draftModal.classList.add('hidden');
    }

    async function generateDraftDetails() {
        const promptText = draftPrompt.value.trim();
        if (!promptText) return;

        const originalText = btnGenerateDraft.textContent;
        btnGenerateDraft.textContent = 'Generating...';
        btnGenerateDraft.disabled = true;

        try {
            const payload = { prompt: promptText };
            if (draftMode === 'UPDATE' && currentTicket) {
                payload.existing_ticket_id = currentTicket.key;
            }

            const res = await fetch(`${API_BASE}/tickets/draft`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error("Failed to generate draft");
            const data = await res.json();

            draftSummary.value = data.summary || '';
            draftDescription.value = data.description || '';

            // Try to auto-guess project key for create
            if (draftMode === 'CREATE' && !draftProjectKey.value && Object.keys(ticketsCache).length > 0) {
                draftProjectKey.value = Object.keys(ticketsCache)[0].split('-')[0];
            }

            draftEditorSection.classList.remove('hidden');
            draftModalFooter.classList.remove('hidden');
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            btnGenerateDraft.textContent = originalText;
            btnGenerateDraft.disabled = false;
        }
    }

    async function submitDraftDetails() {
        const summary = draftSummary.value.trim();
        const description = draftDescription.value.trim();
        let projectKey = '';

        if (draftMode === 'CREATE') {
            projectKey = draftProjectKey.value.trim();
            if (!projectKey) {
                showToast("Project Key is required", "error");
                return;
            }
        }

        if (!summary) {
            showToast("Summary is required", "error");
            return;
        }

        const originalText = btnSubmitDraft.textContent;
        btnSubmitDraft.textContent = 'Submitting...';
        btnSubmitDraft.disabled = true;

        try {
            if (draftMode === 'CREATE') {
                const res = await fetch(`${API_BASE}/tickets`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        project_key: projectKey,
                        summary,
                        description
                    })
                });
                if (!res.ok) throw new Error("Failed to create ticket");
                const data = await res.json();
                showToast(`Ticket ${data.key} created!`, "success");
                closeDraftModal();
                fetchTicketsList();
            } else if (draftMode === 'UPDATE' && currentTicket) {
                const res = await fetch(`${API_BASE}/tickets/${currentTicket.key}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ summary, description })
                });
                if (!res.ok) throw new Error("Failed to update ticket");
                showToast(`Ticket ${currentTicket.key} updated!`, "success");
                closeDraftModal();
                // Refresh current ticket
                const tRes = await fetch(`${API_BASE}/tickets/${currentTicket.key}`);
                if (tRes.ok) {
                    const updatedData = await tRes.json();
                    currentTicket = updatedData;
                    displayTicket(updatedData);
                }
            }
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            btnSubmitDraft.textContent = originalText;
            btnSubmitDraft.disabled = false;
        }
    }

    async function openSettings() {
        try {
            const res = await fetch(`${API_BASE}/settings`);
            if (res.ok) {
                const bSettings = await res.json();
                if (!document.getElementById('jira-url').value) document.getElementById('jira-url').value = bSettings.jira_url || '';
                if (!document.getElementById('jira-email').value) document.getElementById('jira-email').value = bSettings.jira_username || '';
                if (!document.getElementById('jira-token').value) document.getElementById('jira-token').value = bSettings.jira_api_token || '';
                if (!document.getElementById('github-token').value) document.getElementById('github-token').value = bSettings.github_token || '';
            }
        } catch (e) {
            console.error("Could not fetch settings from backend", e);
        }

        const saved = JSON.parse(localStorage.getItem('jira_mcp_creds'));
        if (saved) {
            if (!document.getElementById('jira-url').value) document.getElementById('jira-url').value = saved.jira_url || '';
            if (!document.getElementById('jira-email').value) document.getElementById('jira-email').value = saved.jira_username || '';
            if (!document.getElementById('jira-token').value) document.getElementById('jira-token').value = saved.jira_api_token || '';
            if (!document.getElementById('github-token').value) document.getElementById('github-token').value = saved.github_token || '';
        }
        settingsModal.classList.remove('hidden');
    }

    function closeSettings() {
        settingsModal.classList.add('hidden');
    }

    async function saveSettings() {
        const url = document.getElementById('jira-url').value;
        const email = document.getElementById('jira-email').value;
        const token = document.getElementById('jira-token').value;
        const ghToken = document.getElementById('github-token').value;

        if (!url || !email || !token) {
            showToast("Please fill all required Jira fields", "error");
            return;
        }

        const payload = {
            jira_url: url,
            jira_username: email,
            jira_api_token: token,
            github_token: ghToken || null
        };

        const originalText = btnSaveSettings.textContent;
        btnSaveSettings.textContent = "Saving...";
        btnSaveSettings.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error("Failed to save settings");

            localStorage.setItem('jira_mcp_creds', JSON.stringify({
                jira_url: url,
                jira_username: email,
                jira_api_token: token,
                github_token: ghToken
            }));

            showToast("Credentials saved successfully!", "success");
            closeSettings();

            // Auto fetch immediately after setup
            fetchTicketsList();
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            btnSaveSettings.textContent = originalText;
            btnSaveSettings.disabled = false;
        }
    }

    async function fetchTicketsList() {
        ticketListView.classList.remove('hidden');
        if (currentTicket) {
            ticketView.classList.add('hidden'); // Hide detailed view if open
        }

        // Ensure extraneous modals/panels are hidden
        githubModal.classList.add('hidden');
        hideTerminal();

        ticketsContainer.innerHTML = '';
        ticketsLoading.classList.remove('hidden');

        let jql = '';
        if (currentFilter === 'assigned') {
            jql = 'assignee = currentUser() ORDER BY updated DESC';
        } else if (currentFilter === 'todo') {
            jql = 'statusCategory = "To Do" ORDER BY created DESC';
        } else if (currentFilter === 'progress') {
            jql = 'statusCategory = "In Progress" ORDER BY updated DESC';
        } else {
            jql = 'project is not empty ORDER BY created DESC';
        }

        try {
            const res = await fetch(`${API_BASE}/tickets?max_results=20&jql=${encodeURIComponent(jql)}`);
            if (!res.ok) throw new Error("Failed to fetch recent tickets");

            const tickets = await res.json();
            ticketsLoading.classList.add('hidden');
            lastFetchedTickets = tickets;
            applyTypeFilter();

        } catch (e) {
            ticketsLoading.classList.add('hidden');
            ticketsContainer.innerHTML = `<p style="color:var(--error);text-align:center;">${e.message}</p>`;
        }
    }

    function applyTypeFilter() {
        if (!lastFetchedTickets) return;
        let filtered = lastFetchedTickets;
        if (currentTypeFilter !== 'all') {
            filtered = lastFetchedTickets.filter(t => {
                const type = (t.issue_type || '').toLowerCase();
                const filter = currentTypeFilter.toLowerCase();
                if (filter === 'task') {
                    return type === 'task' || type === 'sub-task' || type === 'subtask';
                }
                return type === filter;
            });
        }
        renderTicketsList(filtered);
    }

    function renderTicketsList(tickets) {
        if (!tickets || tickets.length === 0) {
            ticketsContainer.innerHTML = `<p style="text-align:center;color:var(--text-secondary)">No tickets found. You're all caught up!</p>`;
            return;
        }

        let html = '';
        tickets.forEach(ticket => {
            ticketsCache[ticket.key] = ticket;

            html += `
                <div class="ticket-card glass-panel" data-id="${ticket.key}">
                    <div class="ticket-card-header">
                        <div class="ticket-card-title">
                            <a href="#" class="ticket-link browse-jira" data-id="${ticket.key}">
                                ${ticket.key}
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                            </a>
                            <p>${ticket.summary}</p>
                        </div>
                    </div>
                    <div class="ticket-card-meta">
                        <span class="badge outline">${ticket.issue_type || 'Task'}</span>
                        <span class="badge outline status">${ticket.status || 'Open'}</span>
                        <span style="font-size:0.8rem;color:var(--text-secondary)">Assignee: ${ticket.assignee || 'Unassigned'}</span>
                    </div>
                </div>
            `;
        });

        ticketsContainer.innerHTML = html;

        // Add listeners to new DOM elements
        document.querySelectorAll('.browse-jira').forEach(el => {
            el.addEventListener('click', async (e) => {
                e.preventDefault();
                const id = e.currentTarget.getAttribute('data-id');
                // Auto-fetch health/settings for domain
                const res = await fetch(`${API_BASE}/health`);
                // Wait for search result if we need URL
                searchInput.value = id;
                handleSearch();
            });
        });
    }

    async function handleSearch() {
        const query = searchInput.value.trim().toUpperCase();
        if (!query) return;

        showLoadingTicket();

        try {
            // Note: The FastAPI server exposes /tickets/{ticket_id}
            const res = await fetch(`${API_BASE}/tickets/${query}`);
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Ticket not found or backend error');
            }

            const ticket = await res.json();
            currentTicket = ticket;

            // Format for display
            displayTicket(ticket);
            searchInput.value = '';

        } catch (error) {
            showToast(error.message, 'error');
            resetView();
        }
    }

    function displayTicket(ticket) {
        if (ticketListView) ticketListView.classList.add('hidden');
        ticketView.classList.remove('hidden');

        // Ensure Action Panel is visible and buttons are enabled
        const ticketActionsPanel = document.getElementById('ticket-actions-panel');
        if (ticketActionsPanel) ticketActionsPanel.classList.remove('hidden');
        btnGenerate.disabled = false;
        btnGithub.disabled = false;
        btnGenerate.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg> Generate Draft Solution`;
        btnGithub.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg> GitHub Flow`;

        hideTerminal();
        cancelSolutionReview(); // Reset solution panel

        elKey.textContent = ticket.key;
        elTitle.textContent = ticket.summary;

        if (ticket.description) {
            // Jira returns Markdown or ADF based on API endpoint config
            // Simple markdown parser rendering
            if (typeof marked !== 'undefined') {
                elDesc.innerHTML = marked.parse(ticket.description);
            } else {
                elDesc.innerHTML = `<pre style="font-family: inherit; white-space: pre-wrap;">${ticket.description}</pre>`;
            }
        } else {
            elDesc.innerHTML = '<em>No description provided.</em>';
        }

        elStatus.textContent = ticket.status;

        const assigneeName = ticket.assignee ? ticket.assignee.displayName : 'Unassigned';
        elAssignee.textContent = `Assignee: ${assigneeName}`;
        elType.textContent = ticket.issue_type || 'Task';

        // Render Sub-tasks
        const subtasksSection = document.getElementById('subtasks-section');
        const subtasksContainer = document.getElementById('ticket-subtasks');
        if (ticket.subtasks && ticket.subtasks.length > 0) {
            let subHTML = '';
            // Make sure these show up if we ask to filter by task/subtask on list
            ticket.subtasks.forEach(st => {
                const stKey = st.key || 'UNKNOWN';
                const stSummary = st.fields ? st.fields.summary : 'No Summary';
                const stStatus = st.fields && st.fields.status ? st.fields.status.name : 'Open';

                subHTML += `
                    <div class="ticket-card glass-panel" style="padding: 12px; margin-bottom: 8px;">
                        <div class="ticket-card-header" style="margin-bottom: 4px;">
                            <div class="ticket-card-title">
                                <a href="#" class="ticket-link browse-jira" data-id="${stKey}">
                                    ${stKey}
                                </a>
                                <p style="font-size: 0.9rem;">${stSummary}</p>
                            </div>
                        </div>
                        <div class="ticket-card-meta">
                            <span class="badge outline">Sub-task</span>
                            <span class="badge outline status">${stStatus}</span>
                        </div>
                    </div>
                `;

                // Also add to tickets cache and lastFetchedTickets so it can be filtered/browser later
                const stMapped = {
                    key: stKey,
                    summary: stSummary,
                    status: stStatus,
                    issue_type: 'Sub-task'
                };
                ticketsCache[stKey] = stMapped;

                if (lastFetchedTickets) {
                    const existing = lastFetchedTickets.find(t => t.key === stKey);
                    if (!existing) {
                        lastFetchedTickets.push(stMapped);
                    }
                }
            });
            subtasksContainer.innerHTML = subHTML;
            subtasksSection.style.display = 'block';

            // Re-bind browse events for sub-tasks
            subtasksContainer.querySelectorAll('.browse-jira').forEach(el => {
                el.addEventListener('click', async (e) => {
                    e.preventDefault();
                    const id = e.currentTarget.getAttribute('data-id');
                    searchInput.value = id;
                    handleSearch();
                });
            });
        } else {
            subtasksSection.style.display = 'none';
        }

        // Jira external link
        const linkElem = document.getElementById('ticket-external-link');
        const urlInput = document.getElementById('jira-url').value;
        if (urlInput) {
            linkElem.href = `${urlInput}/browse/${ticket.key}`;
            linkElem.style.display = 'flex';
        } else {
            linkElem.style.display = 'none';
        }

        // Fetch comments and PR status
        fetchComments(ticket.key);
        checkPRStatus(ticket.key);
    }

    async function checkPRStatus(key) {
        try {
            const res = await fetch(`${API_BASE}/tickets/${key}/pr`);
            if (res.ok) {
                const data = await res.json();
                if (data.pr_url) {
                    btnGenerate.disabled = true;
                    btnGithub.disabled = true;
                    btnGenerate.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg> PR Active (Solution Disabled)`;
                    btnGithub.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg> PR Exists (Flow Disabled)`;
                }
            }
        } catch (e) {
            console.error("Failed to check PR status", e);
        }
    }

    async function fetchComments(key) {
        const commentsContainer = document.getElementById('ticket-comments');
        commentsContainer.innerHTML = '<em>Loading comments...</em>';
        try {
            const res = await fetch(`${API_BASE}/tickets/${key}/comments`);
            if (!res.ok) throw new Error("Failed");
            const data = await res.json();

            if (!data.comments || data.comments.length === 0) {
                commentsContainer.innerHTML = '<em>No comments found.</em>';
                return;
            }

            let html = '';
            // Show last 5 comments
            const recent = data.comments.slice(-5);
            recent.forEach(c => {
                const author = c.author ? c.author.displayName : 'Unknown';
                const created = new Date(c.created).toLocaleString();
                let text = c.body;
                // very basic adf rendering to text for comments
                if (typeof text === 'object' && text.content) {
                    text = text.content.map(p => {
                        if (p.content) return p.content.map(tc => tc.text).join(' ');
                        return '';
                    }).join('<br>');
                } else if (typeof text !== 'string') {
                    text = JSON.stringify(text);
                }

                html += `<div style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--border-color);">
                    <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 4px;"><strong>${author}</strong> at ${created}</div>
                    <div style="font-size: 0.9rem;">${text}</div>
                </div>`;
            });
            commentsContainer.innerHTML = html;
        } catch (e) {
            commentsContainer.innerHTML = '<em style="color:var(--error);">Failed to load comments</em>';
        }
    }

    function showLoadingTicket() {
        if (ticketListView) ticketListView.classList.add('hidden');
        ticketView.classList.remove('hidden');
        // Reset contents while loading
        elKey.textContent = searchInput.value.trim().toUpperCase();
        elTitle.textContent = 'Loading...';
        elDesc.textContent = '';
        btnGenerate.disabled = true;
        btnGithub.disabled = true;
    }

    function resetView() {
        fetchTicketsList();
        btnGenerate.disabled = false;
        btnGithub.disabled = false;
        currentTicket = null;
    }

    async function generateSolution(targetTicket) {
        if (!targetTicket) targetTicket = currentTicket;
        if (!targetTicket) return;

        showTerminal(`Generating solution draft for ${targetTicket.key}...`);
        setLoading(true, "AI is analyzing ticket and generating solution...");

        try {
            const res = await fetch(`${API_BASE}/tickets/${targetTicket.key}/solution`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: "Provide an approach plan (numbered steps), the detailed solution, and if this is a Story/Epic a 'Suggested sub-tasks:' list." })
            });

            const data = await res.json();

            if (!res.ok) throw new Error(data.detail || 'Failed to generate solution');

            appendTerminal(`\n✅ Draft Generated!\n`);
            appendTerminal(`Please review the solution in the editor before publishing.`);

            // Show the editor
            ticketActionsPanel.classList.add('hidden');
            solutionEditorPanel.classList.remove('hidden');
            if (easyMDE) {
                easyMDE.value(data.solution);
            } else {
                solutionEditor.value = data.solution;
            }
            solutionEditor.focus();

        } catch (error) {
            appendTerminal(`\n❌ Error: ${error.message}`);
            showToast('Failed to generate solution', 'error');
        } finally {
            setLoading(false);
        }
    }

    function cancelSolutionReview() {
        solutionEditorPanel.classList.add('hidden');
        ticketActionsPanel.classList.remove('hidden');
        if (easyMDE) {
            easyMDE.value('');
        } else {
            solutionEditor.value = '';
        }
    }

    async function publishSolution(targetTicket) {
        if (!targetTicket) targetTicket = currentTicket;
        if (!targetTicket) return;

        const editedSolution = easyMDE ? easyMDE.value().trim() : solutionEditor.value.trim();
        if (!editedSolution) {
            showToast("Solution cannot be empty", "error");
            return;
        }

        showTerminal(`Publishing reviewed solution for ${targetTicket.key}...`);
        setLoading(true, "Posting comment, creating sub-tasks, and updating description...");

        try {
            const res = await fetch(`${API_BASE}/tickets/${targetTicket.key}/solution/publish`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ solution: editedSolution })
            });

            const data = await res.json();

            if (!res.ok) throw new Error(data.detail || 'Failed to publish solution');

            appendTerminal(`\n✅ Successfully published to Jira!\n`);
            if (data.comment_id) appendTerminal(`Comment ID: ${data.comment_id}`);
            if (data.created_subtask_keys?.length) appendTerminal(`Created Sub-tasks: ${data.created_subtask_keys.join(', ')}`);

            showToast('Solution published to Jira!', 'success');
            cancelSolutionReview();

        } catch (error) {
            appendTerminal(`\n❌ Error: ${error.message}`);
            showToast('Failed to publish solution', 'error');
        } finally {
            setLoading(false);
        }
    }

    function triggerGithubFlow(targetTicket) {
        if (!targetTicket) targetTicket = currentTicket;
        if (!targetTicket) return;

        githubFlowTargetTicket = targetTicket;
        githubModal.classList.remove('hidden');
    }

    async function executeGithubFlow(targetTicket) {
        if (!targetTicket) return;

        showTerminal(`Triggering GitHub workflow for ${targetTicket.key}...`);

        // Show Stepper
        const stepper = document.getElementById('progress-stepper');
        const s1 = document.getElementById('step-1');
        const s2 = document.getElementById('step-2');
        const s3 = document.getElementById('step-3');
        stepper.classList.remove('hidden');
        [s1, s2, s3].forEach(s => { s.classList.remove('active', 'done'); });

        s1.classList.add('active'); // Start step 1

        setLoading(true, "AI is executing workflow...");

        // Simulate progress visually
        let timer1 = setTimeout(() => {
            s1.classList.remove('active');
            s1.classList.add('done');
            s2.classList.add('active');
        }, 12000); // 12s - roughly code time

        let timer2 = setTimeout(() => {
            s2.classList.remove('active');
            s2.classList.add('done');
            s3.classList.add('active');
        }, 22000); // 22s - roughly push time

        const language = document.getElementById('github-lang').value;
        const repoUrl = document.getElementById('github-repo-url').value.trim();
        const baseBranch = document.getElementById('github-base-branch').value.trim();
        const question = document.getElementById('github-question').value.trim();

        const payload = { language };
        if (repoUrl) payload.repo_url = repoUrl;
        if (baseBranch) payload.base_branch = baseBranch;
        if (question) payload.question = question;

        try {
            const res = await fetch(`${API_BASE}/tickets/${targetTicket.key}/github-flow`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (!res.ok) throw new Error(data.detail || 'Failed to execute GitHub flow');

            appendTerminal(`\n✅ Success!\n`);
            appendTerminal(`Status: ${data.status}`);
            appendTerminal(`Branch: ${data.branch}`);
            appendTerminal(`PR Output: ${data.pr_output}`);
            appendTerminal(`Jira Comment ID: ${data.jira_comment_id}`);

            clearTimeout(timer1);
            clearTimeout(timer2);
            [s1, s2, s3].forEach(s => { s.classList.remove('active'); s.classList.add('done'); });

            showToast('GitHub flow completed successfully!', 'success');

        } catch (error) {
            clearTimeout(timer1);
            clearTimeout(timer2);
            appendTerminal(`\n❌ Error: ${error.message}`);
            showToast('GitHub flow failed', 'error');
        } finally {
            setLoading(false);
            setTimeout(() => { stepper.classList.add('hidden'); }, 3000);
        }
    }

    // Terminal & UI Utils
    function showTerminal(initialMsg = "") {
        terminalPanel.classList.remove('hidden');
        terminalOutput.textContent = initialMsg ? `> ${initialMsg}\n` : '';
    }

    function hideTerminal() {
        terminalPanel.classList.add('hidden');
    }

    function appendTerminal(msg) {
        terminalOutput.textContent += `${msg}\n`;
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    }

    function setLoading(isLoading, text = "Processing...") {
        btnGenerate.disabled = isLoading;
        btnGithub.disabled = isLoading;
        btnPublishSolution.disabled = isLoading;
        btnCancelSolution.disabled = isLoading;
        // also disable inline buttons
        document.querySelectorAll('.inline-generate, .inline-github').forEach(btn => btn.disabled = isLoading);

        if (isLoading) {
            terminalLoader.classList.remove('hidden');
            terminalLoaderText.textContent = text;
        } else {
            terminalLoader.classList.add('hidden');
        }
    }

    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icon = type === 'success'
            ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>'
            : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';

        toast.innerHTML = `${icon}<span>${message}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }


});

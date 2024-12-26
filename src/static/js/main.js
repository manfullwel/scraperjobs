// Copiar código
function copyCode(btn) {
    const pre = btn.parentElement;
    const code = pre.textContent.replace('Copiar', '').trim();
    navigator.clipboard.writeText(code);
    btn.textContent = 'Copiado!';
    setTimeout(() => btn.textContent = 'Copiar', 2000);
}

// Buscar vagas
document.getElementById('searchForm').onsubmit = async (e) => {
    e.preventDefault();
    const keywords = document.getElementById('keywords').value;
    const location = document.getElementById('location').value;
    
    const searchResult = document.getElementById('searchResult');
    searchResult.style.display = 'block';
    searchResult.querySelector('.result').textContent = 'Buscando...';
    
    try {
        const response = await fetch(
            '/api/jobs/search?user_id=test_user',
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    keywords,
                    location,
                    sources: ["adzuna", "linkedin"],
                    remote_only: false
                })
            }
        );
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        searchResult.querySelector('.result').textContent = 
            JSON.stringify(data, null, 2);
    } catch (error) {
        searchResult.querySelector('.result').textContent = 
            `Erro: ${error.message}`;
    }
};

// Verificar uso da API
async function checkUsage() {
    const usageResult = document.getElementById('usageResult');
    usageResult.style.display = 'block';
    usageResult.querySelector('.result').textContent = 'Carregando...';
    
    try {
        const response = await fetch('/api/jobs/usage/test_user');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        usageResult.querySelector('.result').textContent = 
            JSON.stringify(data, null, 2);
    } catch (error) {
        usageResult.querySelector('.result').textContent = 
            `Erro: ${error.message}`;
    }
}

// Adicionar animações
document.addEventListener('DOMContentLoaded', () => {
    const endpoints = document.querySelectorAll('.endpoint');
    endpoints.forEach((endpoint, index) => {
        endpoint.style.animationDelay = `${index * 0.1}s`;
    });
});

// Global State
let jobs = [];
let filters = {
    remoteOnly: false,
    sortBy: 'date' // 'date' or 'salary'
};

// DOM Elements
const searchForm = document.getElementById('searchForm');
const loadingIndicator = document.getElementById('loadingIndicator');
const resultsContainer = document.getElementById('resultsContainer');
const jobsList = document.getElementById('jobsList');
const noResults = document.getElementById('noResults');
const toggleRemoteBtn = document.getElementById('toggleRemote');
const sortDateBtn = document.getElementById('sortDate');
const sortSalaryBtn = document.getElementById('sortSalary');
const showUsageBtn = document.getElementById('showUsage');
const apiUsageModal = new bootstrap.Modal(document.getElementById('apiUsageModal'));

// Event Listeners
searchForm.addEventListener('submit', handleSearch);
toggleRemoteBtn.addEventListener('click', toggleRemoteFilter);
sortDateBtn.addEventListener('click', () => sortJobs('date'));
sortSalaryBtn.addEventListener('click', () => sortJobs('salary'));
showUsageBtn.addEventListener('click', showApiUsage);

// Search Handler
async function handleSearch(e) {
    e.preventDefault();
    
    const keywords = document.getElementById('keywords').value;
    const location = document.getElementById('location').value;
    
    if (!keywords || !location) {
        showError('Por favor, preencha todos os campos');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(
            '/api/jobs/search?user_id=test_user',
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    keywords,
                    location,
                    sources: ["adzuna", "linkedin"],
                    remote_only: filters.remoteOnly
                })
            }
        );
        
        if (!response.ok) {
            throw new Error('Erro ao buscar vagas');
        }
        
        const data = await response.json();
        jobs = data.jobs || [];
        
        if (jobs.length > 0) {
            renderJobs();
            showResults(true);
        } else {
            showNoResults(true);
        }
        
    } catch (error) {
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

// Render Jobs
function renderJobs() {
    jobsList.innerHTML = '';
    const template = document.getElementById('jobCardTemplate');
    
    const filteredJobs = jobs.filter(job => 
        !filters.remoteOnly || job.remote
    );
    
    const sortedJobs = sortJobsList(filteredJobs);
    
    sortedJobs.forEach(job => {
        const clone = template.content.cloneNode(true);
        
        // Set badge
        const sourceBadge = clone.querySelector('.source-badge');
        sourceBadge.textContent = job.source;
        sourceBadge.classList.add(
            job.source.toLowerCase() === 'linkedin' ? 'bg-info' : 'bg-primary'
        );
        
        // Show remote badge if applicable
        const remoteBadge = clone.querySelector('.remote-badge');
        if (job.remote) {
            remoteBadge.style.display = 'inline-block';
        }
        
        // Set job details
        clone.querySelector('.job-title').textContent = job.title;
        clone.querySelector('.company-name span').textContent = job.company;
        clone.querySelector('.location span').textContent = job.location;
        clone.querySelector('.description').textContent = 
            truncateText(job.description, 150);
        
        // Set salary if available
        const salaryInfo = clone.querySelector('.salary-info');
        if (job.salary) {
            salaryInfo.style.display = 'block';
            salaryInfo.querySelector('span').textContent = 
                formatSalary(job.salary);
        }
        
        // Set posted date
        const postedDate = clone.querySelector('.posted-date span');
        postedDate.textContent = formatDate(job.posted_date);
        
        // Set apply button
        const applyBtn = clone.querySelector('.apply-btn');
        applyBtn.href = job.url;
        
        jobsList.appendChild(clone);
    });
    
    // Update results count
    const resultsTitle = document.querySelector('.results-title');
    resultsTitle.textContent = `${sortedJobs.length} Vagas Encontradas`;
}

// Filter and Sort Functions
function toggleRemoteFilter() {
    filters.remoteOnly = !filters.remoteOnly;
    toggleRemoteBtn.classList.toggle('active');
    renderJobs();
}

function sortJobs(by) {
    filters.sortBy = by;
    sortDateBtn.classList.toggle('active', by === 'date');
    sortSalaryBtn.classList.toggle('active', by === 'salary');
    renderJobs();
}

function sortJobsList(jobsList) {
    return [...jobsList].sort((a, b) => {
        if (filters.sortBy === 'date') {
            return new Date(b.posted_date) - new Date(a.posted_date);
        } else {
            return (b.salary || 0) - (a.salary || 0);
        }
    });
}

// API Usage
async function showApiUsage() {
    const content = document.getElementById('apiUsageContent');
    content.innerHTML = '<div class="text-center"><div class="spinner-border text-primary"></div></div>';
    
    apiUsageModal.show();
    
    try {
        const response = await fetch('/api/jobs/usage/test_user');
        const data = await response.json();
        
        content.innerHTML = `
            <div class="usage-stats">
                <h6 class="mb-3">Adzuna API</h6>
                <div class="progress mb-2">
                    <div class="progress-bar" role="progressbar" 
                        style="width: ${(data.adzuna.remaining_calls / data.adzuna.daily_limit) * 100}%">
                    </div>
                </div>
                <p class="text-muted">
                    ${data.adzuna.remaining_calls} de ${data.adzuna.daily_limit} chamadas restantes
                </p>
            </div>
        `;
    } catch (error) {
        content.innerHTML = `
            <div class="alert alert-danger">
                Erro ao carregar estatísticas: ${error.message}
            </div>
        `;
    }
}

// Utility Functions
function formatDate(dateStr) {
    if (!dateStr) return 'Data não informada';
    return moment(dateStr).fromNow();
}

function formatSalary(salary) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(salary);
}

function truncateText(text, length) {
    if (!text) return '';
    return text.length > length 
        ? text.substring(0, length) + '...'
        : text;
}

function showLoading(show) {
    loadingIndicator.style.display = show ? 'block' : 'none';
    resultsContainer.style.display = show ? 'none' : 'block';
    noResults.style.display = 'none';
}

function showResults(show) {
    resultsContainer.style.display = show ? 'block' : 'none';
    noResults.style.display = 'none';
}

function showNoResults(show) {
    noResults.style.display = show ? 'block' : 'none';
    resultsContainer.style.display = 'none';
}

function showError(message) {
    // TODO: Implement error toast/alert
    console.error(message);
}

document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('searchForm');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const noResultsDiv = document.getElementById('noResults');
    const filtersDiv = document.getElementById('filters');
    const totalJobsSpan = document.getElementById('totalJobs');
    const remoteFilterBtn = document.getElementById('remoteFilter');
    
    let currentJobs = [];
    let showOnlyRemote = false;

    // Função para formatar a data
    function formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) return 'Hoje';
        if (diffDays === 1) return 'Ontem';
        if (diffDays < 7) return `${diffDays} dias atrás`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)} semanas atrás`;
        return `${Math.floor(diffDays / 30)} meses atrás`;
    }

    // Função para formatar salário
    function formatSalary(min, max) {
        if (!min && !max) return '';
        if (!max) return `A partir de $${min.toLocaleString()}`;
        if (!min) return `Até $${max.toLocaleString()}`;
        return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
    }

    // Função para criar card de vaga
    function createJobCard(job) {
        const card = document.createElement('div');
        card.className = 'col-md-6 col-lg-4 mb-4';
        
        const salary = formatSalary(job.salary_min, job.salary_max);
        const date = formatDate(job.created);
        
        card.innerHTML = `
            <div class="card h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between mb-2">
                        <span class="badge bg-primary">${job.source}</span>
                        ${job.remote ? '<span class="badge bg-success">Remoto</span>' : ''}
                    </div>
                    <h5 class="card-title">${job.title}</h5>
                    <h6 class="card-subtitle mb-2 text-muted">${job.company}</h6>
                    <p class="card-text text-muted">
                        <i class="bi bi-geo-alt"></i> ${job.location}
                    </p>
                    <p class="card-text description">${job.description}</p>
                    ${salary ? `<p class="card-text"><small class="text-muted"><i class="bi bi-currency-dollar"></i> ${salary}</small></p>` : ''}
                    <p class="card-text"><small class="text-muted"><i class="bi bi-clock"></i> ${date}</small></p>
                </div>
                <div class="card-footer bg-transparent">
                    <a href="${job.url}" class="btn btn-outline-primary w-100" target="_blank">Ver Vaga</a>
                </div>
            </div>
        `;
        
        return card;
    }

    // Função para atualizar a lista de vagas
    function updateJobsList(jobs) {
        resultsDiv.innerHTML = '';
        const filteredJobs = showOnlyRemote ? jobs.filter(job => job.remote) : jobs;
        
        if (filteredJobs.length === 0) {
            noResultsDiv.style.display = 'block';
            filtersDiv.style.display = 'none';
        } else {
            noResultsDiv.style.display = 'none';
            filtersDiv.style.display = 'flex';
            totalJobsSpan.textContent = `${filteredJobs.length} Vagas Encontradas`;
            
            filteredJobs.forEach(job => {
                resultsDiv.appendChild(createJobCard(job));
            });
        }
    }

    // Função para buscar vagas
    async function searchJobs(keywords, location) {
        try {
            loadingDiv.style.display = 'block';
            resultsDiv.style.display = 'none';
            noResultsDiv.style.display = 'none';
            filtersDiv.style.display = 'none';

            const response = await fetch(`/api/jobs/search?keywords=${encodeURIComponent(keywords)}&location=${encodeURIComponent(location)}`);
            const data = await response.json();

            if (response.ok) {
                currentJobs = data.jobs;
                updateJobsList(currentJobs);
            } else {
                throw new Error(data.detail || 'Erro ao buscar vagas');
            }
        } catch (error) {
            console.error('Erro:', error);
            noResultsDiv.querySelector('p').textContent = 'Erro ao buscar vagas. Por favor, tente novamente.';
            noResultsDiv.style.display = 'block';
        } finally {
            loadingDiv.style.display = 'none';
            resultsDiv.style.display = 'block';
        }
    }

    // Event Listeners
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const keywords = document.getElementById('keywords').value;
        const location = document.getElementById('location').value;
        searchJobs(keywords, location);
    });

    remoteFilterBtn.addEventListener('click', () => {
        showOnlyRemote = !showOnlyRemote;
        remoteFilterBtn.classList.toggle('active');
        updateJobsList(currentJobs);
    });

    document.querySelectorAll('[data-sort]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const sortBy = e.target.dataset.sort;
            if (sortBy === 'date') {
                currentJobs.sort((a, b) => new Date(b.created) - new Date(a.created));
            } else if (sortBy === 'salary') {
                currentJobs.sort((a, b) => (b.salary_max || b.salary_min || 0) - (a.salary_max || a.salary_min || 0));
            }
            updateJobsList(currentJobs);
        });
    });

    // API Usage Modal
    const apiUsageModal = document.getElementById('apiUsageModal');
    apiUsageModal.addEventListener('show.bs.modal', async () => {
        try {
            const response = await fetch('/api/usage');
            const data = await response.json();
            
            if (response.ok) {
                const statsDiv = document.getElementById('apiUsageStats');
                statsDiv.innerHTML = `
                    <div class="api-stats">
                        <h6>Hoje</h6>
                        <p>${data.today_requests} requisições</p>
                    </div>
                    <div class="api-stats">
                        <h6>Este mês</h6>
                        <p>${data.month_requests} requisições</p>
                    </div>
                    <div class="api-stats">
                        <h6>Limite diário</h6>
                        <p>${data.daily_limit} requisições</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Erro ao carregar estatísticas:', error);
        }
    });
});

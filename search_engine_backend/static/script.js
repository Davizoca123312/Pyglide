
document.addEventListener('DOMContentLoaded', () => {
    const resultsContainer = document.getElementById('results-container');
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');

    const performSearch = async (query) => {
        if (!query) return;

        // Mostra um feedback de carregamento
        resultsContainer.innerHTML = '<p class="loading-message">Buscando nos confins do universo...</p>';

        try {
            // A rota /search agora retorna o JSON com os resultados
            const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            displayResults(data.results);
        } catch (error) {
            resultsContainer.innerHTML = `<p class="error-message">Erro ao contatar os sistemas de busca: ${error.message}</p>`;
        }
    };

    const displayResults = (results) => {
        resultsContainer.innerHTML = '';
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = '<p class="no-results-message">Nenhum resultado encontrado nesta galáxia.</p>';
            return;
        }

        results.forEach(result => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';

            const title = document.createElement('h3');
            const link = document.createElement('a');
            link.href = result.url;
            link.textContent = result.title;
            link.target = '_blank'; // Abre em nova aba
            title.appendChild(link);

            const snippet = document.createElement('p');
            snippet.innerHTML = result.snippet; // Usar innerHTML caso o snippet contenha tags

            const url = document.createElement('a');
            url.href = result.url;
            url.textContent = result.url;
            url.target = '_blank';
            url.className = 'url-link';

            resultItem.appendChild(title);
            resultItem.appendChild(snippet);
            resultItem.appendChild(url);
            resultsContainer.appendChild(resultItem);
        });
    };

    // Lida com o envio do formulário de busca na própria página
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = searchInput.value.trim();
        if (query) {
            // Atualiza a URL para refletir a busca (bom para histórico e compartilhamento)
            window.history.pushState({}, '', `/?q=${encodeURIComponent(query)}`);
            performSearch(query);
        }
    });

    // Verifica se há uma query na URL quando a página carrega
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('q');
    if (query) {
        searchInput.value = query; // Preenche o campo de busca
        performSearch(query);
    }
});

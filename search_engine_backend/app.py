import requests
from flask import Flask, jsonify, request, render_template
from bs4 import BeautifulSoup

app = Flask(__name__)

# Using the DuckDuckGo Search API (unofficial, via website)
DUCKDUCKGO_SEARCH_URL = "https://html.duckduckgo.com/html/"

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/profiles')
def profiles():
    """Serves the profile selector HTML page."""
    return render_template('profile_selector.html')

@app.route('/search', methods=['GET'])
def search():
    """Performs a search using the DuckDuckGo API and returns the results."""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'A search query is required.'}), 400

    try:
        # Parameters for the DuckDuckGo Search
        params = {
            'q': query
        }

        # Make the request to the API
        # We need to provide a User-Agent header to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(DUCKDUCKGO_SEARCH_URL, params=params, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        results = []
        for result in soup.find_all('div', class_='result'):
            title_element = result.find('a', class_='result__a')
            snippet_element = result.find('a', class_='result__snippet')
            url_element = result.find('a', class_='result__url')

            if title_element and snippet_element and url_element:
                results.append({
                    'title': title_element.get_text(strip=True),
                    'url': url_element['href'],
                    'snippet': snippet_element.get_text(strip=True)
                })

        return jsonify({
            'query': query,
            'results': results
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'API request failed: {e}'}), 502
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {e}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
import requests
from bs4 import BeautifulSoup, Tag
from typing import Dict, Optional
import re

class ArticleScraper:
    """Scrapes article content from URLs"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def scrape_url(self, url: str) -> Dict[str, str]:
        """
        Scrape content from a given URL

        Args:
            url: The URL to scrape

        Returns:
            Dictionary containing title, author (if available), and content
        """
        try:
            # Fetch the webpage
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title = self._extract_title(soup)

            # Extract author (if available)
            author = self._extract_author(soup)

            # Extract main content
            content = self._extract_content(soup)

            if not content:
                raise ValueError("Could not extract meaningful content from the URL")

            return {
                'title': title,
                'author': author,
                'content': content,
                'url': url
            }

        except requests.RequestException as e:
            raise Exception(f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to parse content: {str(e)}")

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the article title"""
        # Try different title selectors
        title_selectors = [
            soup.find('h1'),
            soup.find('meta', property='og:title'),
            soup.find('meta', attrs={'name': 'twitter:title'}),
            soup.find('title')
        ]

        for selector in title_selectors:
            if selector:
                if selector.name == 'meta':
                    return selector.get('content', 'Untitled Article')
                return selector.get_text(strip=True)

        return 'Untitled Article'

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the article author"""
        # Try different author selectors
        author_selectors = [
            soup.find('meta', attrs={'name': 'author'}),
            soup.find('meta', property='article:author'),
            soup.find('span', class_='author'),
            soup.find('a', rel='author')
        ]

        for selector in author_selectors:
            if selector:
                if selector.name == 'meta':
                    return selector.get('content')
                return selector.get_text(strip=True)

        return None

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract the main article content including headings, lists, quotes, and images"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'form']):
            element.decompose()

        # Try to find the main article content
        content_elements = [
            soup.find('article'),
            soup.find('div', class_='article-content'),
            soup.find('div', class_='post-content'),
            soup.find('div', class_='entry-content'),
            soup.find('main'),
            soup.find('div', id='content')
        ]

        content = None
        for element in content_elements:
            if element:
                content = element
                break

        # If no specific content container found, use the body
        if not content:
            content = soup.find('body')

        if not content:
            return ""

        # Extract content in order, preserving structure
        text_parts = []
        processed_elements = set()  # Track processed elements to avoid duplicates

        # Process direct children recursively
        def process_element(elem):
            # Skip if already processed or not a Tag element
            if id(elem) in processed_elements or not isinstance(elem, Tag):
                return

            processed_elements.add(id(elem))

            if elem.name == 'p':
                text = elem.get_text(strip=True)
                if text:
                    text_parts.append(text)

            elif elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                text = elem.get_text(strip=True)
                if text:
                    # Add heading with emphasis for context
                    text_parts.append(f"\n{text}\n")

            elif elem.name == 'blockquote':
                text = elem.get_text(strip=True)
                if text:
                    text_parts.append(f'"{text}"')

            elif elem.name in ['ul', 'ol']:
                # Extract list items
                list_items = elem.find_all('li', recursive=False)
                for li in list_items:
                    text = li.get_text(strip=True)
                    if text:
                        text_parts.append(f"- {text}")
                    processed_elements.add(id(li))

            elif elem.name == 'figure':
                # Handle figures with images and captions
                img = elem.find('img')
                if img:
                    alt_text = img.get('alt', '').strip()
                    if alt_text and len(alt_text) > 5:
                        text_parts.append(f"[Image: {alt_text}]")
                    processed_elements.add(id(img))

                caption = elem.find('figcaption')
                if caption:
                    text = caption.get_text(strip=True)
                    if text:
                        text_parts.append(f"[Caption: {text}]")
                    processed_elements.add(id(caption))

            elif elem.name == 'img' and id(elem) not in processed_elements:
                # Standalone images
                alt_text = elem.get('alt', '').strip()
                if alt_text and len(alt_text) > 5:
                    text_parts.append(f"[Image: {alt_text}]")

            else:
                # Recursively process children for other containers
                if hasattr(elem, 'children'):
                    for child in elem.children:
                        if isinstance(child, Tag):
                            process_element(child)

        # Start processing from the content root
        for child in content.children:
            if isinstance(child, Tag):
                process_element(child)

        # Join with proper spacing and remove excessive newlines
        text_content = '\n\n'.join(text_parts)

        # Clean up excessive whitespace
        text_content = re.sub(r'\n{3,}', '\n\n', text_content)

        return text_content.strip()

    def validate_url(self, url: str) -> bool:
        """Check if the URL is valid and accessible"""
        try:
            response = requests.head(url, headers=self.headers, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except:
            return False

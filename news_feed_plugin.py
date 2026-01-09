# © 2026 Colin Bond
# All rights reserved.

import os
import requests
import json
from typing import List, Dict, Optional
import argparse

class NewsFeedManager:
    """
    Uses Global News REST feeds through Home Assistant sensors to write news to a .json file, read it, update it, or list specific contents.
    Is able to run standalone in terminal.
    """

    version = "0.0.1"  # Class attribute for version
    ha_url = "http://192.168.123.199:8123"

    def __init__(self, sensors: List[str], output_file: str = "./news.json"):
        """
        Initialize the NewsFeedManager.

        Args:
            sensors (List[str]): List of sensor names to fetch news from
            output_file (str): Path to store the news JSON file (Default: ./news.json)
        """
        self.ha_token = self._load_ha_token()
        self.sensors = sensors
        self.output_file = output_file

    def _load_ha_token(self):

        ha_token = os.getenv("HA_TOKEN")

        if ha_token is None:
            raise RuntimeError("HA_TOKEN environment variable not found. A Home Assistant Token is required to run this application")
            return ""

        else:
            return ha_token

    def update_news_data(self) -> bool:
        """
        Fetch news data from sensors and save to file.

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            articles = []
            for sensor in self.sensors:
                response = requests.get(
                    f"{self.ha_url}/api/states/{sensor}",
                    headers={"Authorization": f"Bearer {self.ha_token}"}
                )
                response.raise_for_status()
                data = response.json()
                items = data["attributes"]["rss"]["channel"]["item"]
                articles.extend([
                    {
                        "Published": item["pubDate"],
                        "Title": item["title"],
                        "Description": item.get("description", "No description"),
                        "Link": item["link"]
                    } for item in items
                ])
            
            with open(self.output_file, "w") as f:
                json.dump(articles, f, indent=2)
            return True
        except Exception as e:
            print(f"Error updating news data: {e}")
            return False

    def get_all_titles(self) -> List[str]:
        """
        Get a list of all article titles from the JSON file.
        
        Returns:
            List[str]: List of article titles
        """
        articles = self.get_file_contents()
        return [article["Title"] for article in articles]

    def get_article_info(self, title: str) -> Optional[Dict]:
        """
        Get all information for a specific article title from the JSON file.
        
        Args:
            title (str): The title of the article to find
            
        Returns:
            Optional[Dict]: Article information if found, None otherwise
        """
        articles = self.get_file_contents()
        for article in articles:
            if article["Title"] == title:
                return article
        return None

    def get_file_contents(self) -> List[Dict]:
        """
        Read and return the contents of the news JSON file.
        
        Returns:
            List[Dict]: List of article dictionaries
        """
        try:
            with open(self.output_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"File {self.output_file} not found")
            return []
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {self.output_file}")
            return []

# Plugin functions
def update_news(manager: NewsFeedManager) -> Dict:
    """
    Update news data.
    """
    success = manager.update_news_data()
    return {
        "operation": "update_news",
        "success": success,
        "message": "News data updated successfully" if success else "Failed to update news data"
    }

def list_titles(manager: NewsFeedManager, output_mode: str) -> str | Dict:
    """
    Get all titles from the JSON file.
    
    Args:
        manager: NewsFeedManager instance
        output_mode: 'json' for structured output, 'text' for plain text titles
    """
    titles = manager.get_all_titles()
    if output_mode == "text":
        return "\n".join(titles)
    return {
        "operation": "list_titles",
        "titles": titles,
        "total_count": len(titles),
        "message": f"Found {len(titles)} articles"
    }

def get_article_details(manager: NewsFeedManager, title: str, output_mode: str) -> str | Dict:
    """
    Get article details for a specific title from the JSON file.
    
    Args:
        manager: NewsFeedManager instance
        title: Article title to look up
        output_mode: 'json' for structured output, 'text' for plain text key-value pairs
    """
    article_info = manager.get_article_info(title)
    if output_mode == "text":
        if not article_info:
            return ""
        return "\n".join(f"{key}: {value}" for key, value in article_info.items())
    return {
        "operation": "get_article_details",
        "title": title,
        "article": article_info,
        "message": "Article found" if article_info else "Article not found"
    }

def get_file_data(manager: NewsFeedManager, output_mode: str) -> str | Dict:
    """
    Get file contents.
    
    Args:
        manager: NewsFeedManager instance
        output_mode: 'json' for structured output, 'text' for plain text article blocks
    """
    file_contents = manager.get_file_contents()
    if output_mode == "text":
        if not file_contents:
            return ""
        return "\n\n".join(
            "\n".join(f"{key}: {value}" for key, value in article.items())
            for article in file_contents
        )
    return {
        "operation": "get_file_contents",
        "articles": file_contents,
        "total_count": len(file_contents),
        "message": f"File contains {len(file_contents)} articles"
    }

def main():
    parser = argparse.ArgumentParser(description="News Feed Manager Plugin")    
    parser.add_argument("--sensors", nargs="+", default=["sensor.global_news_toronto_rest", "sensor.global_news_main_rest"],    
                        help="List of sensor names")
    parser.add_argument("--output-file", default="./news.json", help="Output JSON file path")
    parser.add_argument("--operation", required=True,
                        choices=["update_news", "list_titles", "get_article_details", "get_file_contents"],
                        help="Operation to perform")
    parser.add_argument("--title", help="Article title for get_article_details operation")
    parser.add_argument("--output", choices=["json", "text"], default="json",
                        help="Output format: json (structured) or text (raw data)")

    args = parser.parse_args()

    manager = NewsFeedManager(args.sensors, args.output_file)

    if args.operation == "update_news":
        result = update_news(manager)
    elif args.operation == "list_titles":
        result = list_titles(manager, args.output)
    elif args.operation == "get_article_details":
        if not args.title:
            result = {"error": "Title parameter required for get_article_details"}
        else:
            result = get_article_details(manager, args.title, args.output)
    elif args.operation == "get_file_contents":
        result = get_file_data(manager, args.output)
    else:
        result = {"error": "Invalid operation"}

    if isinstance(result, str):
        print(result)
    else:
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

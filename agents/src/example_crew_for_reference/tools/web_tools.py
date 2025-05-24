import json
import logging
from typing import Optional, List, Dict, Any, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from langchain_hyperbrowser import (
    HyperbrowserBrowserUseTool,
    HyperbrowserCrawlTool,
    HyperbrowserScrapeTool,
    HyperbrowserExtractTool
)

# Configure logging
logger = logging.getLogger(__name__)
# Ensure handlers are not duplicated if this file is reloaded
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
        handlers=[logging.FileHandler('agent.log', mode='a'), logging.StreamHandler()]
    )


# --- Helper function for Pydantic model serialization ---
def _serialize_pydantic_result(data_object: Any) -> Any:
    """
    Recursively converts Pydantic models within a data structure to dictionaries
    suitable for JSON serialization.
    """
    if isinstance(data_object, list):
        return [_serialize_pydantic_result(item) for item in data_object]
    elif isinstance(data_object, dict):
        return {key: _serialize_pydantic_result(value) for key, value in data_object.items()}
    # Check if it's a Pydantic model instance (works for v1 and v2 BaseModels)
    elif hasattr(data_object, 'model_dump') and callable(getattr(data_object, 'model_dump')):
        return data_object.model_dump()
    return data_object

# --- Tool Schemas and Wrappers for Hyperbrowser ---

# Default session options for web interaction tools - removed solve_captchas for free plan compatibility
DEFAULT_WEB_SESSION_OPTIONS = {"accept_cookies": True}

# --- BrowserUseTool ---
class BrowserToolSchema(BaseModel):
    """Input schema for HyperBrowserToolWrapper."""
    task: str = Field(description="The specific task to execute using the browser agent (e.g., 'go to Hacker News and summarize the top 5 posts').")
    session_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional dictionary for browser session configuration (e.g., {'accept_cookies': True})."
    )

class HyperBrowserToolWrapper(BaseTool):
    name: str = "Web Browser Interaction"
    description: str = (
        "Executes tasks using a browser agent. Useful for navigating websites, "
        "interacting with elements (clicking, typing), and extracting information. "
        "Input must be a JSON object with a 'task' (string) and an optional 'session_options' (dictionary) key."
    )
    args_schema: Type[BaseModel] = BrowserToolSchema
    hyperbrowser_tool_instance: HyperbrowserBrowserUseTool = Field(
        default_factory=lambda: HyperbrowserBrowserUseTool(
            use_vision_for_planner=True,
            use_vision=True,
        )
    )
    default_session_options: Dict[str, Any] = DEFAULT_WEB_SESSION_OPTIONS.copy()


    def _run(self, task: str, session_options: Optional[Dict[str, Any]] = None) -> str:
        try:
            final_session_options = self.default_session_options.copy()
            if session_options:
                final_session_options.update(session_options)

            tool_args = {"task": task}
            if final_session_options:
                 tool_args["session_options"] = final_session_options

            logger.info(f"Calling hyperbrowser_tool_instance.run (BrowserUse) with dict: {tool_args}")
            result = self.hyperbrowser_tool_instance.run(tool_args)

            if not isinstance(result, str):
                if result is None:
                    return "Task completed, no textual output."
                try:
                    processed_result = _serialize_pydantic_result(result)
                    return json.dumps(processed_result)
                except Exception as e_serial:
                    logger.error(f"Error serializing result for {self.name}: {e_serial}", exc_info=True)
                    return f"Error serializing result: {str(e_serial)}"
            return result
        except Exception as e:
            logger.error(f"Error during HyperBrowserTool (BrowserUse) execution: {e}", exc_info=True)
            return f"Error performing browser task: {str(e)}"

# --- ScrapeTool ---
class ScrapeToolSchema(BaseModel):
    """Input schema for HyperScrapeToolWrapper."""
    url: str = Field(description="The URL of the page to scrape.")
    scrape_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional dictionary for scrape options (e.g., {'formats': ['markdown', 'html'], 'include_tags': ['h1', 'p']})."
    )
    session_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional dictionary for browser session configuration."
    )

class HyperScrapeToolWrapper(BaseTool):
    name: str = "Web Scraper"
    description: str = (
        "Scrapes content from a single web page. Can specify output formats (markdown, html, links, screenshot) "
        "and other scrape options like tags to include/exclude. "
        "Input must be a JSON object with 'url' (string), and optional 'scrape_options' (dictionary) "
        "and 'session_options' (dictionary) keys."
    )
    args_schema: Type[BaseModel] = ScrapeToolSchema
    hyperbrowser_scrape_tool_instance: HyperbrowserScrapeTool = Field(default_factory=HyperbrowserScrapeTool)
    default_session_options: Dict[str, Any] = DEFAULT_WEB_SESSION_OPTIONS.copy()

    def _run(self, url: str, scrape_options: Optional[Dict[str, Any]] = None, session_options: Optional[Dict[str, Any]] = None) -> str:
        try:
            final_session_options = self.default_session_options.copy()
            if session_options:
                final_session_options.update(session_options)

            tool_args = {"url": url}
            if scrape_options:
                tool_args["scrape_options"] = scrape_options
            if final_session_options:
                tool_args["session_options"] = final_session_options

            logger.info(f"Calling hyperbrowser_scrape_tool_instance.run with dict: {tool_args}")
            result = self.hyperbrowser_scrape_tool_instance.run(tool_args)

            if not isinstance(result, str):
                if result is None:
                    return "Scrape completed, no textual output."
                try:
                    processed_result = _serialize_pydantic_result(result)
                    return json.dumps(processed_result)
                except Exception as e_serial:
                    logger.error(f"Error serializing result for {self.name}: {e_serial}", exc_info=True)
                    return f"Error serializing result: {str(e_serial)}"
            return result
        except Exception as e:
            logger.error(f"Error during HyperScrapeTool execution: {e}", exc_info=True)
            return f"Error performing scrape task: {str(e)}"

# --- CrawlTool ---
class CrawlToolSchema(BaseModel):
    """Input schema for HyperCrawlToolWrapper."""
    url: str = Field(description="The starting URL for the crawl.")
    max_pages: Optional[int] = Field(default=None, description="Maximum number of pages to crawl.")
    follow_links: Optional[bool] = Field(default=None, description="Whether to follow links on pages.")
    ignore_sitemap: Optional[bool] = Field(default=None, description="Whether to ignore sitemaps for link discovery.")
    exclude_patterns: Optional[List[str]] = Field(default=None, description="List of URL patterns to exclude from crawling.")
    include_patterns: Optional[List[str]] = Field(default=None, description="List of URL patterns to include (others excluded if specified).")
    scrape_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Scrape options to apply to each crawled page (e.g., {'formats': ['markdown']})."
    )
    session_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional dictionary for browser session configuration for the crawl."
    )

class HyperCrawlToolWrapper(BaseTool):
    name: str = "Website Crawler"
    description: str = (
        "Crawls a website starting from a given URL. Can configure max pages, link following, "
        "URL patterns for inclusion/exclusion, and scrape options for each page. "
        "Input must be a JSON object with 'url' (string) and other optional crawling parameters."
    )
    args_schema: Type[BaseModel] = CrawlToolSchema
    hyperbrowser_crawl_tool_instance: HyperbrowserCrawlTool = Field(default_factory=HyperbrowserCrawlTool)
    default_session_options: Dict[str, Any] = DEFAULT_WEB_SESSION_OPTIONS.copy()

    def _run(
        self,
        url: str,
        max_pages: Optional[int] = None,
        follow_links: Optional[bool] = None,
        ignore_sitemap: Optional[bool] = None,
        exclude_patterns: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None,
        scrape_options: Optional[Dict[str, Any]] = None,
        session_options: Optional[Dict[str, Any]] = None
    ) -> str:
        try:
            final_session_options = self.default_session_options.copy()
            if session_options:
                final_session_options.update(session_options)

            tool_args = {"url": url}
            if max_pages is not None:
                tool_args["max_pages"] = max_pages
            if follow_links is not None:
                tool_args["follow_links"] = follow_links
            if ignore_sitemap is not None:
                tool_args["ignore_sitemap"] = ignore_sitemap
            if exclude_patterns:
                tool_args["exclude_patterns"] = exclude_patterns
            if include_patterns:
                tool_args["include_patterns"] = include_patterns
            if scrape_options:
                tool_args["scrape_options"] = scrape_options
            if final_session_options:
                tool_args["session_options"] = final_session_options

            logger.info(f"Calling hyperbrowser_crawl_tool_instance.run with dict: {tool_args}")
            result = self.hyperbrowser_crawl_tool_instance.run(tool_args)

            if not isinstance(result, str):
                if result is None:
                     return "Crawl completed, no textual output or an empty list of pages."
                try:
                    processed_result = _serialize_pydantic_result(result)
                    return json.dumps(processed_result)
                except Exception as e_serial:
                    logger.error(f"Error serializing result for {self.name}: {e_serial}", exc_info=True)
                    return f"Error serializing result: {str(e_serial)}"
            return result
        except Exception as e:
            logger.error(f"Error during HyperCrawlTool execution: {e}", exc_info=True)
            return f"Error performing crawl task: {str(e)}"

# --- ExtractTool ---
class ExtractToolSchema(BaseModel):
    """Input schema for HyperExtractToolWrapper."""
    url: str = Field(description="The URL of the page to extract structured data from.")
    prompt: str = Field(description="A natural language prompt describing what data to extract.")
    schema_definition: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional JSON schema definition (as a dictionary) for structured extraction."
    )
    session_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional dictionary for browser session configuration."
    )

class HyperExtractToolWrapper(BaseTool):
    name: str = "Structured Data Extractor"
    description: str = (
        "Extracts structured data from a web page using AI. Provide a URL and a prompt. "
        "Optionally, provide a JSON schema (as a dictionary under 'schema_definition' key) for more precise structured output. (EITHER schema OR prompt must be provided) "
        "Input must be a JSON object."
    )
    args_schema: Type[BaseModel] = ExtractToolSchema
    hyperbrowser_extract_tool_instance: HyperbrowserExtractTool = Field(default_factory=HyperbrowserExtractTool)
    default_session_options: Dict[str, Any] = DEFAULT_WEB_SESSION_OPTIONS.copy()

    def _run(self, url: str, prompt: str, schema_definition: Optional[Dict[str, Any]] = None, session_options: Optional[Dict[str, Any]] = None) -> str:
        try:
            final_session_options = self.default_session_options.copy()
            if session_options:
                final_session_options.update(session_options)

            tool_args = {"url": url, "prompt": prompt}

            # The underlying HyperbrowserExtractTool always expects the 'schema' key.
            # Its value can be None if no specific schema_definition is provided by the agent.
            tool_args["schema"] = schema_definition

            if final_session_options:
                tool_args["session_options"] = final_session_options

            logger.info(f"Calling hyperbrowser_extract_tool_instance.run with dict: {tool_args}")
            result = self.hyperbrowser_extract_tool_instance.run(tool_args)

            if not isinstance(result, str):
                if result is None:
                    return "Extraction completed, no textual output."
                try:
                    processed_result = _serialize_pydantic_result(result)
                    return json.dumps(processed_result)
                except Exception as e_serial:
                    logger.error(f"Error serializing result for {self.name}: {e_serial}", exc_info=True)
                    return f"Error serializing result: {str(e_serial)}"
            return result
        except Exception as e:
            logger.error(f"Error during HyperExtractTool execution: {e}", exc_info=True)
            return f"Error performing extraction task: {str(e)}"
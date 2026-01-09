from ailib import Payload
from datetime import datetime
import requests
import json
import os
import re
import logging
import sys
import news_feed_plugin


# --- AI News wrapper over Payload, ChatHistoryManager, PromptBuilder, ModelConnection, ---
class News:
    """
    Provides functions to get a news feed from a file and query it with AI for relevant information.
    """

    version = "0.0.1"

    def __init__(self, prompt_file: str, history_file: str):

        #Load Open AI Key from environment variable
        api_key = self._load_openai_key()

        #Instantiate Payload with settings values retrieved
        self.payload = Payload(prompt_file, history_file, api_key)

    def _load_openai_key(self):

        api_key = os.getenv("OPENAI_API_KEY")

        if api_key is None:
            logging.error("OPENAI_API_KEY environment variable not found. An OpenAI API Key is required to run this application")
            raise RuntimeError("OPENAI_API_KEY environment variable not found. An OpenAI API Key is required to run this application")
            return ""

        else:
            return api_key

    def _configure_logging(self, debug_mode: bool):
        """TRUE for DEBUG mode, False for INFO"""
        if debug_mode:
            logging.basicConfig(
                filename='news.log',
                level=logging.DEBUG,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
        else:
            logging.basicConfig(
                filename='news.log',
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )

    def _clean_ai_response(self, ai_response):
        # --- Clean AI response (remove ```json or ``` etc.) ---
        cleaned = re.sub(r'^```[a-zA-Z]*\n?', '', ai_response.strip())
        cleaned = re.sub(r'\n?```$', '', cleaned.strip())

        response_text = cleaned
        return response_text
  
    def process_ai_response(self, ai_response):

        clean_response = self._clean_ai_response(ai_response)

        response_text = ai_response
        return response_text

# ============================================================= M A I N ==================================================

    def main(self):

        if len(sys.argv) < 2:
            print("Usage: python news.py <MESSAGE_TO_AI>, <LOG_MODE> is Optional 'Debug' or 'Info' (default)")
            return("<MESSAGE_TO_AI> parameter is required, News exiting")
            sys.exit(1)
        
        script = sys.argv[0]
        user_msg = sys.argv[1]

        debug_mode = False
        if len(sys.argv) == 3: #Make sure not None first
            if sys.argv[2].lower() == "debug":
                debug_mode = True

        self._configure_logging(debug_mode)  

        logging.info(f"News class currently using ModelConnection v{self.payload.connection.version}, PromptBuilder v{self.payload.prompts.version}, ChatHistoryManager v{self.payload.history.version}, Payload v{self.payload.version}")

        self.payload.connection.set_model("gpt-5-nano")
        self.payload.connection.set_verbosity("low")
               
        self.payload.prompts.load_prompt("news")
        self.payload.history.load_history("news")

        #Get Current Date formatted as 'Wednesday, Oct 01, 2025
        current_date = datetime.now().strftime('%A, %b %d, %Y')
        #Get Current Time formatted as '2:10 PM'
        current_time = datetime.now().strftime('%-I:%M %p')
        curr_date_time = f"Current Date: {current_date}  Current Time: {current_time}"
        self.payload.prompts.add_to_prompt(curr_date_time)

        #Load News
        news_manager = news_feed_plugin.NewsFeedManager(["sensor.global_news_toronto_rest", "sensor.global_news_main_rest"])
        news_data = news_feed_plugin.get_file_data(news_manager,"text")
        self.payload.prompts.add_to_prompt(news_data)
        
        logging.debug(f"PROMPT: {self.payload.prompts.get_prompt()}")
        logging.debug(f"Model: {self.payload.connection.model}, Verbosity: {self.payload.connection.verbosity}, Reasoning: {self.payload.connection.reasoning_effort}, Max Tokens: {self.payload.connection.maximum_tokens}")

        logging.info(f"User Message: [{user_msg}]")
 
        reply = self.payload.send_message(user_msg, None, None)
        logging.debug(f"\nAssistant Raw Reply: {reply}")
 
        ret = self.process_ai_response(reply)
        if ret:
            response_val = ret or ""
            logging.debug(f"process_ai_response Return Value: {ret}")
        else:
            response_val = "AI response error, could not clean "
            
        logging.info(f"main() Returning (response_val): [{response_val}]\n")        

        return response_val


if __name__ == "__main__":

    # Change the current working directory to this script for imports and relative pathing
    program_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(program_path)

    wrapper = News("prompts.json", "chat_history.json")

    ai_response = wrapper.main()
  
    print(f"{ai_response}")
    
    

from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
import json
from rich.table import Table
from rich.console import Console
from rich import box
from collections import defaultdict


class Dictionary:
    def __init__(self, word):
        self.word = quote(word)
        self.data = None

    def fetch_data(self):
        try:
            url = f"https://www.dictionary.com/browse/{self.word}"
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error during requests to {url}: {str(e)}")
            return None

    def parse_data(self, response_text):
        soup = BeautifulSoup(response_text, "html.parser")
        script = soup.find("script", {"id": "preloaded-state"})
        if script is not None:
            script_text = script.string
            start = script_text.find("{")
            end = script_text.rfind("}") + 1
            json_text = script_text[start:end]
            self.data = json.loads(json_text)

    def extract_info(self):
        if self.data:
            results_data = self.data["luna"]["resultsData"]
            data = results_data["data"]
            content = data["content"]
            definitions_list = []

            for entry in content:
                entries = entry.get("entries", [])
                for entry in entries:
                    posBlocks = entry.get("posBlocks", [])
                    for posBlock in posBlocks:
                        pos = BeautifulSoup(posBlock.get("pos", ""), "html.parser").get_text()
                        pos_info = BeautifulSoup(posBlock.get("posSupplementaryInfo", ""), "html.parser").get_text()
                        definitions = posBlock.get("definitions", [])

                        if definitions:
                            for definition in definitions:
                                def_text = BeautifulSoup(definition.get("definition", ""), "html.parser").get_text()
                                subdefinitions = definition.get("subdefinitions", [])
                                if not def_text and subdefinitions:
                                    # handle the case where main definition is empty but there are sub-definitions
                                    for subdef in subdefinitions:
                                        sub_def_text = BeautifulSoup(subdef.get("definition", ""), "html.parser").get_text()
                                        definitions_list.append((pos, pos_info, sub_def_text, ""))
                                else:
                                    definitions_list.append((pos, pos_info, def_text, ""))
                                    for subdef in subdefinitions:
                                        sub_def_text = BeautifulSoup(subdef.get("definition", ""), "html.parser").get_text()
                                        definitions_list.append((pos, pos_info, sub_def_text, ""))

            return definitions_list
        return []








    def plain(self):
        response_text = self.fetch_data()
        if response_text:
            self.parse_data(response_text)
            definitions = self.extract_info()
            self.display_plain_definitions(definitions)

    def display_plain_definitions(self, definitions):
        for definition in definitions:
            pos, pos_info, def_text, example = definition
            print(f"❯ {pos} {pos_info}")
            print(def_text)
            print(example)

    def rich(self):
        response_text = self.fetch_data()
        if response_text:
            self.parse_data(response_text)
            definitions = self.extract_info()
            self.display_definitions(definitions)

    def display_definitions(self, definitions):
        console = Console()

        # Initialize a count for each part of speech
        pos_count = defaultdict(int)

        # Initialize the table and current part of speech
        table = Table(box=box.SQUARE)
        current_pos = None

        for pos, pos_info, definition, example in definitions:
            # Split definition to extract example
            definition_parts = definition.split(': ', 1)
            definition_text = definition_parts[0]
            if len(definition_parts) > 1:
                example = definition_parts[1]

            # If we've already seen two examples for this part of speech, skip it
            if pos_count[pos] >= 2:
                continue

            # If the part of speech changes, print the current table and create a new one
            if pos != current_pos:
                if current_pos is not None:
                    console.print(table)
                table = Table(box=box.SQUARE)
                table.add_column("[blue]❯ " + pos)
                current_pos = pos

            # Add rows to the current table
            table.add_row("·" + definition_text)
            if example:
                table.add_row("[gray50]" + example)

            # Increment the count for this part of speech
            pos_count[pos] += 1

        # Print the last table
        if current_pos is not None:
            console.print(table)

        console.print(
            f"[grey42][link=https://www.dictionary.com/browse/{self.word}]dictionary.com↗[/link]",
            justify="right",
        )

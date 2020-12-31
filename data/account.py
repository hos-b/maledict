import yaml
from parser.base import ParserBase

class Account:
    """
    Account class, handles reading & writing to transaction database
    """
    def __init__(self, name: str, initial_balance: float):
        self.db_name = name
        self.initial_balance = initial_balance
        self.current_balance = initial_balance

    def write_parser_to_db(self, parser: ParserBase):
        """
        """
        
    @staticmethod
    def load_from_file(yaml_path):
        """
        loads the account data from a yaml file
        """
        pass

    def save_to_file(self, yaml_path):
        """
        save the account data to a yaml file
        """
        pass
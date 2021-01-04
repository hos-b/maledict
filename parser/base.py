

class ParserBase:
    def __init__(self):
        self.categories = {}
        self.subcategories = {}
        self.businesses = {}
        self.records = []
        self.max_cat_length = 0
        self.max_subcat_length = 0
        self.max_bus_length = 0
        self.max_note_length = 0

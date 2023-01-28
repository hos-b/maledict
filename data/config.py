# config module for global access to the settings
# values populated from settings.yaml
import yaml

__config_path = None

class table:
    index_length: int = None
    amount_length: int = None
    category_length: int = None
    subcategory_length: int = None
    payee_length: int = None
    note_length: int = None
    # special case: always static
    datetime_length: int = len('1970.01.01, 00:00')
    scrollbar_enable: bool = None

class recurring:
    months: int = None
    significance_ratio: float = None
    discard_limit: int = None
    min_occurance: int = None

class main:
    x: int = None # w.r.t. screen
    y: int = None # w.r.t. screen
    list_x_offset: int = None # w.r.t. main window
    list_y_offset: int = None # w.r.t. main window
    width_percentage: float = None
    height_percentage: float = None

class action:
    x_offset: int = None # w.r.t. main window
    y: int = None # w.r.t. screen
    width_percentage: float = None
    height_percentage: float = None

class terminal:
    x: int = None # w.r.t. screen
    y_offset: int = None # w.r.t. main window
    width_offset: int = None
    height_percentage: float = None
    command_history_buffer_length: int = None

class application:
    warm_up: bool = None
    use_jdate: bool = None # not the website
    enable_utf8_support: bool = None
    command_history_file_length: int = None
    stack_trace_on_warmup_error: bool = None

def update_config(config_path: str):
    global __config_path
    __config_path = config_path
    conf_file = open(config_path)
    conf = yaml.load(conf_file, Loader=yaml.FullLoader)
    table.scrollbar_enable = conf['table']['scrollbar-enable']
    recurring.months = conf['recurring']['months']
    recurring.significance_ratio = conf['recurring']['significance-ratio']
    recurring.discard_limit = conf['recurring']['discard-limit']
    recurring.min_occurance = conf['recurring']['min-occurance']
    main.x = conf['main']['x']
    main.y = conf['main']['y']
    main.list_x_offset = conf['main']['list-x-offset']
    main.list_y_offset = conf['main']['list-y-offset']
    main.width_percentage = conf['main']['width-percentage']
    main.height_percentage = conf['main']['height-percentage']
    action.x_offset = conf['action']['x-offset']
    action.y = conf['action']['y']
    action.width_percentage = conf['action']['width-percentage']
    action.height_percentage = conf['action']['height-percentage']
    terminal.x = conf['terminal']['x']
    terminal.y_offset = conf['terminal']['y-offset']
    terminal.width_offset = conf['terminal']['width-offset']
    terminal.height_percentage = conf['terminal']['height-percentage']
    terminal.command_history_buffer_length = conf['terminal']['command-history-buffer-length']
    application.warm_up = conf['application']['warm-up']
    application.use_jdate = conf['application']['use-jdate']
    application.enable_utf8_support = conf['application']['enable-utf8-support']
    application.command_history_file_length = conf['application']['command-history-file-length']
    application.stack_trace_on_warmup_error = conf['application']['stack-trace-on-warmup-error']

def update_table_sizes(list_width: int):
    conf_file = open(__config_path)
    conf = yaml.load(conf_file, Loader=yaml.FullLoader)
    weight_sum = conf['table']['index-length-percentage'] + \
                 conf['table']['amount-length-percentage'] + \
                 conf['table']['category-length-percentage'] + \
                 conf['table']['subcategory-length-percentage'] + \
                 conf['table']['payee-length-percentage'] + \
                 conf['table']['note-length-percentage']

    assert weight_sum <= 100, 'total sum of column percentages exceeds 100'

    total_weight = 100
    table.index_length = int(list_width * conf['table']['index-length-percentage'] / total_weight)
    table.amount_length = int(list_width * conf['table']['amount-length-percentage'] / total_weight)
    table.category_length = int(list_width * conf['table']['category-length-percentage'] / total_weight)
    table.subcategory_length = int(list_width * conf['table']['subcategory-length-percentage'] / total_weight)
    table.payee_length = int(list_width * conf['table']['payee-length-percentage'] / total_weight)
    table.note_length = int(list_width * conf['table']['note-length-percentage'] / total_weight)
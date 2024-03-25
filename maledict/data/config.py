# config module for global access to the settings
# values populated from config/settings.yaml
#                       data-dir/custom-settings.yaml
import yaml


class table:
    index_length: int = None
    amount_length: int = None
    category_length: int = None
    subcategory_length: int = None
    payee_length: int = None
    note_length: int = None
    datetime_length: int = None
    scrollbar_enable: bool = None


class recurring:
    months: int = None
    significance_ratio: float = None
    min_occurance: int = None


class main:
    x: int = None  # w.r.t. screen
    y: int = None  # w.r.t. screen
    list_x_offset: int = None  # w.r.t. main window
    list_y_offset: int = None  # w.r.t. main window
    width_percentage: float = None
    height_percentage: float = None


class action:
    x_offset: int = None  # w.r.t. main window
    y: int = None  # w.r.t. screen
    width_percentage: float = None
    height_percentage: float = None


class terminal:
    x: int = None  # w.r.t. screen
    y_offset: int = None  # w.r.t. main window
    width_offset: int = None
    height_percentage: float = None
    command_history_buffer_length: int = None


class application:
    warm_up: bool = None
    use_jdate: bool = None  # not the website
    enable_utf8_support: bool = None
    command_history_file_length: int = None
    stack_trace_on_warmup_error: bool = None


def try_read_class_config(
    cls,
    config: dict,
    throw: bool,
    *filters,
):
    if cls.__name__ not in config:
        if throw:
            raise KeyError(cls.__name__)
        return
    config = config[cls.__name__]
    for cfg_key, value in config.items():
        class_key = cfg_key
        for f in filters:
            class_key = class_key.replace(f, '')
        class_key = class_key.strip('-').replace('-', '_')
        if class_key not in cls.__annotations__:
            if throw:
                raise KeyError(class_key)
            continue
        setattr(cls, class_key, value)

    if throw:
        for attr in cls.__annotations__.keys():
            if getattr(cls, attr) is None:
                raise KeyError(f'{attr} missing in config')


def update_config(config_path: str, throw: bool):
    conf_file = open(config_path)
    conf = yaml.load(conf_file, Loader=yaml.FullLoader)
    # special case: always use static length for datetime
    if 'table' in conf:
        conf['table']['datetime-length'] = len('1970.01.01, 00:00')
    try_read_class_config(table, conf, throw, 'percentage')
    try_read_class_config(recurring, conf, throw)
    try_read_class_config(main, conf, throw)
    try_read_class_config(action, conf, throw)
    try_read_class_config(terminal, conf, throw)
    try_read_class_config(application, conf, throw)


def update_table_sizes(list_width: int):
    """
    this function calculates the size of each section based on the given
    list width and the percentages defined in the configs.
    """
    for attr in table.__annotations__.keys():
        assert getattr(table, attr) is not None, f'{attr} is still not set'

    weight_sum = table.index_length + \
                 table.amount_length + \
                 table.category_length + \
                 table.subcategory_length + \
                 table.payee_length + \
                 table.note_length
    assert weight_sum <= 100, 'total sum of column percentages exceeds 100'

    table.index_length = int(list_width * table.index_length / 100)
    table.amount_length = int(list_width * table.amount_length / 100)
    table.category_length = int(list_width * table.category_length / 100)
    table.subcategory_length = int(list_width * table.subcategory_length / 100)
    table.payee_length = int(list_width * table.payee_length / 100)
    table.note_length = int(list_width * table.note_length / 100)

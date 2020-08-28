import pandas as pd
import seaborn as sns


"""
style_config = [{
          "style_option": "name",
          "style_additional_param": {"param": "value}
          "sub_set": ["col1", "col2"]
        }]
"""
# matplotlib cmap to populate the cmap param of Styler.background_gradient
cmap_preset = {
    "green_light": sns.light_palette("green", as_cmap=True),
    "viridis": "viridis",
}

def highlight_null(df_styler, color='red', subset=None):
    return df_styler.highlight_null(color=color, subset=subset)

def highlight_max(df_styler, color='green', subset=None):
    return df_styler.highlight_max(color=color, subset=subset)

def highlight_min(df_styler, color='red', subset=None):
    return df_styler.highlight_min(color=color, subset=subset)

def bar(df_styler, align='mid', color=['#d65f5f', '#5fba7d'], subset=None):
    return df_styler.bar(subset=subset, align=align, color=color)

def background_gradient(df_styler, cmap_preset_name='green_light', low=.5, high=0):
    return df_styler.background_gradient(cmap=cmap_preset.get(cmap_preset_name, sns.light_palette("green", as_cmap=True)), low=low, high=high)

# TODO: this wont run?
def color_negative(val, color_name_negative='red', color_name_positive='black'):
    """
    Takes a scalar and returns a string with
    the css property `'color: red'` for negative
    strings, black otherwise.
    """
    color = color_name_negative if val < 0 else color_name_positive
    return 'color: %s' % color

def set_precision(df_styler, precision=2):
    return df_styler.set_precision(precision)

# TODO: implement please
def highlight_condition(df_styler, col):
    return 

def highlight_alternative(df_styler, color1, color2):
    highlight_alternative = lambda x, color1, color2: ['background-color: {}'.format(color1) if v % 2 == 0 else 'background-color: {}'.format(color2) for v in x.index]
    return df_styler.apply(highlight_alternative, color1='white', color2='#f0eded')

# style options
style_options = {
    'highlight_null': highlight_null,
    'highlight_max': highlight_max,
    'highlight_min': highlight_min,
    'bar': bar,
    'background_gradient': background_gradient,
    'color_negative': color_negative,
}

# TODO: too lazy
# table styles populate method set_table_styles with list of table_styles contain selector and props param
# Each individual table_style should be a dictionary with selector and props keys. selector should be a CSS selector that the style will be applied to (automatically prefixed by the table’s UUID) and props should be a list of tuples with (attribute, value).
# table_style_preset = {
#     ""
# }


def df_decorate_tohtml(df, styles_config=[]):

    # TODO: HARD CODE PART, CHANGE TO CONFIG PLEASE, change to table_style_preset config 
    # table styles populate method set_table_styles with list of table_styles contain selector and props param
    table_styles = [

        dict(selector="",
                props=[("border-collapse", "collapse"), ("border", "0.5px solid #808080")]),

        dict(selector="tr:nth-child(even)", props=[
            ("background-color", "#f2f2f2")
        ]),
        dict(selector="tr:nth-child(odd)", props=[
            ("background-color", "white")
        ]),
        
        dict(selector="tr:hover", props=[
            ("background-color", "#ddd")
        ]),
        dict(selector="tr", props=[ 
            ("text-align", "left"), 
            ("border-style", "solid"),
            ("border-width", "0.1px"),
            ("border-color", "grey"),            
                                  ]),
        dict(selector="th", props=[
            ("padding", "2px 10px 2px 5px"),
            ("text-align", "left"),
            ("background-color", "#6699ff"),
            ("color", "white"),
            ("border", "0.5px solid #808080"),
            ("padding", "5px 5px 5px 5px"),

                                  ]),
        dict(selector="td", props=[
            ("mso-table-lspace", "0pt !important"),
            ("mso-table-rspace", "0pt !important"),
            ('border', '0.5px solid #808080'),
            ("padding", "2px 5px 2px 5px"),
        ]),
        dict(selector="caption", props=[("caption-side", "bottom")])
    ]

    df_style = df.style

    for style_config in styles_config:
        cols_to_apply = style_config.get('sub_set')
        style_option_name = style_config.get('style_option')
        style_additional_param = style_config.get('style_additional_param', {})
        df_style = style_options.get(style_option_name)(df_style, subset=cols_to_apply, **style_additional_param)
    
    # TODO: HARD CODE PART, CHANGE TO CONFIG PLEASE
    df_style = df_style.set_table_styles(table_styles).hide_index()
    df_style = highlight_alternative(df_style, color1='white', color2='#f0eded')
    return df_style.render()
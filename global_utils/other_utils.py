from xlsxwriter.utility import xl_rowcol_to_cell, xl_cell_to_rowcol, xl_range_formula


def range_to_rows(x, m = None):
    temp = x.split(":")
    res = list(
        range(
            xl_cell_to_rowcol(temp[0])[0],
            xl_cell_to_rowcol(temp[1])[0] + 1
        )
    )
    if m is not None:
        res = list(filter(lambda x: x < m, res))
    return res


def range_to_cols(x, m = None):
    temp = x.split(":")
    res = list(
        range(
            xl_cell_to_rowcol(temp[0])[1],
            xl_cell_to_rowcol(temp[1])[1] + 1
        )
    )
    if m is not None:
        res = list(filter(lambda x: x < m, res))
    return res


def metrics_handler(df, c):
    metrics = dict()
    for i in c.keys():
        address = xl_cell_to_rowcol(c[i])
        value = df.iloc[address[0], address[1]]
        _locals = locals()
        if "%>%" in c[i]:
            transform_steps = c[i].split("%>%")[1:]
            for ts in transform_steps:
                exec('value = list(map(lambda x: {}, ["{}"]))[0]'.format(ts, value), globals(), _locals)
        metrics[i] = _locals['value']
    return metrics
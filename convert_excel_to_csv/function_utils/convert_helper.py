from io import BytesIO
import pandas as pd
from xlsxwriter.utility import xl_rowcol_to_cell, xl_cell_to_rowcol, xl_range_formula

# from global_utils.blob_helper import BlobHelper
# from global_utils.log_helper import LogHelper
# from global_utils.other_utils import range_to_rows, range_to_cols, metrics_handler

from __app__.global_utils.blob_helper import BlobHelper
from __app__.global_utils.log_helper import LogHelper
from __app__.global_utils.other_utils import range_to_rows, range_to_cols, metrics_handler


class ConvertHelper:
    def __init__(self):
        self.blob_helper = None

    def connect_to_blob(self, blob_account, blob_key):
        self.blob_helper = BlobHelper(blob_account, blob_key)

    def convert_excel_to_csv(self, parameters):
        TAG = "convert_excel_to_csv.function_utils.convert_helper.convert_excel_to_csv"
        if self.blob_helper is None:
            raise ConnectionError("Connection to Blob was not established")

        container_name = parameters['blob_input']['container']
        blob_name = parameters['blob_input']['blobname']
        parse_all_sheet_flag = parameters['blob_input']['parse_all_sheet']
        sheet_names = parameters['blob_input'].get('sheetnames')

        include_blobname_in_result_flag = parameters['blob_input'].get('include_blobname_in_result')
        include_sheetname_in_result_flag = parameters['blob_input'].get('include_sheetname_in_result')

        pre_parsing_config = None
        if parameters.get('preparsing') and len(parameters.get('preparsing')) > 0:
            pre_parsing_config = parameters.get('preparsing')[0]
        parse_config = parameters.get('parseconfig')

        xls = pd.ExcelFile(self.blob_helper.download_data(container_name, blob_name))

        if parse_all_sheet_flag:
            sheet_to_process = xls.sheet_names
        elif type(sheet_names) == list and sheet_names is not None:
            sheet_to_process = sheet_names
        else:
            raise ValueError("sheetnames param must be specified when parse_all_sheet flag = false")

        res = pd.DataFrame()
        for sheet in sheet_to_process:
            if not sheet in xls.sheet_names:
                continue
            # read sheet and parse
            data = pd.read_excel(xls, sheet, header=None)
            
            if pre_parsing_config:
                data = self.preparsing(data, pre_parsing_config)

            temp_res = self.parse(data, parse_config)

            # populate file metrics
            if include_blobname_in_result_flag:
                temp_res['blob_name'] = blob_name

            if include_sheetname_in_result_flag:
                temp_res['sheet_name'] = sheet

            if ('market_share_type' in parse_config.keys()) and (parse_config['market_share_type'] == 1):
                metadatas = {
                    "WSP_Sheet1" : {"RETAIL_TYPE" : "", "AREA_TYPE" : "", "TRADING_CODE" : "", "LOCATION" : "Viet Nam"},
                    "WSP_Sheet3" : {"RETAIL_TYPE" : "On", "AREA_TYPE" : "", "TRADING_CODE" : "",  "LOCATION" : ""},
                    "WSP_Sheet4" : {"RETAIL_TYPE" : "Off", "AREA_TYPE" : "", "TRADING_CODE" : "", "LOCATION" : ""},
                    "WSP_Sheet5" : {"RETAIL_TYPE" : "", "AREA_TYPE" : "Urban", "TRADING_CODE" : "", "LOCATION" : ""},
                    "WSP_Sheet6" : {"RETAIL_TYPE" : "", "AREA_TYPE" : "Rural", "TRADING_CODE" : "", "LOCATION" : ""},
                    "WSP_Sheet7" : {"RETAIL_TYPE" : "", "AREA_TYPE" : "", "TRADING_CODE" : "Z24", "LOCATION" : ""},
                    "WSP_Sheet8" : {"RETAIL_TYPE" : "", "AREA_TYPE" : "", "TRADING_CODE" : "Z12", "LOCATION" : ""},
                    "WSP_Sheet9" : {"RETAIL_TYPE" : "", "AREA_TYPE" : "", "TRADING_CODE" : "Z13", "LOCATION" : ""},
                    "WSP_Sheet10" : {"RETAIL_TYPE" : "", "AREA_TYPE" : "", "TRADING_CODE" : "Z15", "LOCATION" : ""},
                    "WSP_Sheet11" : {"RETAIL_TYPE" : "", "AREA_TYPE" : "", "TRADING_CODE" : "Z16", "LOCATION" : ""},
                    "WSP_Sheet12" : {"RETAIL_TYPE" : "", "AREA_TYPE" : "", "TRADING_CODE" : "Z17", "LOCATION" : ""},
                    "WSP_Sheet13" : {"RETAIL_TYPE" : "", "AREA_TYPE" : "", "TRADING_CODE" : "Z18", "LOCATION" : ""},
                    "WSP_Sheet14" : {"RETAIL_TYPE" : "", "AREA_TYPE" : "", "TRADING_CODE" : "Z14", "LOCATION" : ""},
                    "WSP_Sheet15" : {"RETAIL_TYPE" : "", "AREA_TYPE" : "", "TRADING_CODE" : "Z19", "LOCATION" : ""},
                    "WSP_Sheet16" : {"RETAIL_TYPE" : "", "AREA_TYPE" : "", "TRADING_CODE" : "Z20", "LOCATION" : ""},
                }
                if sheet in metadatas.keys():
                    metadata = metadatas[sheet]
                    for k,v in metadata.items():
                        temp_res[k] = v


            # concat
            res = pd.concat([res, temp_res])
        
        if "rename_headers" in parse_config.keys():
            rename_headers = parse_config["rename_headers"]
            cols = res.columns
            for k, v in rename_headers.items():
                cols = [v if x==k else x for x in cols]
            res.columns = cols
        
        output_data = res.to_csv(index=False)
        
        self.blob_helper.upload_data(output_data, parameters['blob_output']['container'], parameters['blob_output']['blobname'])

    def preparsing(self, source, config):
        ignore = config['from_ignore_cols']

        copy_from = source.iloc[
            range_to_rows(config['from'], len(source)), range_to_cols(config['from'], len(source.columns))]

        keep_col_indexes = [i for i in range(len(copy_from.columns)) if
                            i not in [(j if j >= 0 else len(copy_from.columns) + j) for j in ignore]]

        copy_from = copy_from.iloc[:, keep_col_indexes]

        copy_to_cell = xl_cell_to_rowcol(config['to'])

        for r in range(copy_to_cell[0], copy_to_cell[0] + len(copy_from)):
            for c in range(copy_to_cell[1], copy_to_cell[1] + len(copy_from.columns)):
                source.iloc[r, c] = copy_from.iloc[r - copy_to_cell[0], c - copy_to_cell[1]]
        return source

    def parse(self, source, config):
       # header process

        headers = source.iloc[range_to_rows(config['header'], len(source)), range_to_cols(config['header'], len(source.columns))]

        if config.get('ignore', {}).get('cols') is not None:
            cols_ignore = list(map(lambda x: x if x >= 0 else x + len(headers.columns), config['ignore']['cols']))
            headers = headers.iloc[:, list(filter(lambda x: x not in cols_ignore, range(len(headers.columns))))]

        
        headers = headers.fillna('')

        values = source.iloc[range_to_rows(config['values'], len(source)), range_to_cols(config['values'], len(source.columns))]

        if config.get('values_filter_blank_col_index') is not None:
            values = values[~values[config['values_filter_blank_col_index']].isnull()]

        if config.get('ignore', {}).get('cols') is not None:
            cols_ignore = list(map(lambda x: x if x >= 0 else x + len(values.columns), config['ignore']['cols']))
            values = values.iloc[:, list(filter(lambda x: x not in cols_ignore, range(len(values.columns))))]

        if config.get('ignore', {}).get('rows') is not None:
            rows_ignore = list(map(lambda x: x if x >= 0 else x + len(values), config['ignore']['rows']))
            values = values.iloc[list(filter(lambda x: x not in rows_ignore, range(len(values)))), :]

        # exclude blank cells in header
        values.columns = ['%!%'.join(list(map(str, filter(lambda x: str(x) !='', j)))) for j in list(zip(*[headers.loc[i].reset_index(drop=True) for i in headers.index]))]
        if 'market_share_type' in config.keys():
            if config['market_share_type'] == 1:
                sub_table_col_metadata = config['table_transform'][0]['cols'][1:-1].split(':')
                sub_table_start_col = int(sub_table_col_metadata[0]) - 1 if sub_table_col_metadata[0] != '' else 0
                sub_table_end_col = int(sub_table_col_metadata[1]) - 1 if sub_table_col_metadata[1] != '' else len(values.columns)
                total_market_keys = values.columns[sub_table_start_col:sub_table_end_col]
                total_market_values = values.iloc[0, sub_table_start_col:sub_table_end_col].values.tolist()
                total_market_dict = {total_market_keys[i]: total_market_values[i] for i in range(len(total_market_keys))} 

                values = values.iloc[1:]
                cols = list(values.columns)
                cols[0] = 'COMPANY_NAME'
                cols[1] = 'PRODUCT_NAME'
                cols[2] = 'SKU_NAME'
                values.columns = cols
                values = values[values.apply(filter_unwanted_row, axis = 1) == False]
                values['LEVEL'] = None
                values.loc[values['COMPANY_NAME'].notnull(), ['PRODUCT_NAME','SKU_NAME']] = ''
                values.loc[values['COMPANY_NAME'].notnull(), ['LEVEL']] = 'Company'
                values.loc[values['PRODUCT_NAME'].notnull(), ['SKU_NAME']] = ''
                values.loc[values['PRODUCT_NAME'] !='' , ['LEVEL']] = 'Product'

                cols = ['COMPANY_NAME', 'PRODUCT_NAME']
                values.loc[:,cols] = values.loc[:,cols].ffill()

                values.loc[values['SKU_NAME']!='', ['SKU_NAME']] = values['PRODUCT_NAME'] + ' ' + values['SKU_NAME']
                values.loc[values['SKU_NAME'] !='', ['LEVEL']] = 'SKU'

                cols = list(values.columns)
                cols = cols[:3] + cols[-1:] + cols[3:-1]
                values = values[cols]
            elif config['market_share_type'] == 2:
                cols = list(values.columns)
                cols[0] = 'TRADING_REGION'
                cols[1] = 'LOCATION'
                values.columns = cols
                values.loc[:,cols] = values.loc[:,cols].ffill()
            elif config['market_share_type'] == 3:
                cols = list(values.columns)
                cols[0] = 'LOCATION'
                cols[1] = 'COMPANY_NAME'
                cols[2] = 'PRODUCT_NAME'
                cols[3] = 'SKU_NAME'
                values.columns = cols
                
                values['LEVEL'] = None
                values.loc[values['COMPANY_NAME'].str.contains('Total', na = False), ['PRODUCT_NAME','SKU_NAME']] = ''
                values.loc[values['COMPANY_NAME'].str.contains('Total', na = False), ['LEVEL']] = 'Company'
                values['COMPANY_NAME'] = values['COMPANY_NAME'].str.replace(' Total', '')

                values.loc[values['PRODUCT_NAME'].str.contains("Total", na = False), ['SKU_NAME']] = ''
                values.loc[values['PRODUCT_NAME'] !='' , ['LEVEL']] = 'Product'
                values['PRODUCT_NAME'] = values['PRODUCT_NAME'].str.replace(' Total', '')
                
                cols = ['LOCATION', 'COMPANY_NAME', 'PRODUCT_NAME']
                values.loc[:,cols] = values.loc[:,cols].ffill()

                values.loc[values['SKU_NAME'] !='', ['LEVEL']] = 'SKU'

                cols = list(values.columns)
                cols = cols[:4] + cols[-1:] + cols[4:-1]
                values = values[cols]
            

        if '' in values.columns:
            values = values.drop([''], axis=1)

        # transform
        if (config.get('table_transform') is not None) and len(config['table_transform']) > 0:
            sub_table_col_metadata = config['table_transform'][0]['cols'][1:-1].split(':')
            sub_table_start_col = int(sub_table_col_metadata[0]) if sub_table_col_metadata[0] != '' else 0
            sub_table_end_col = int(sub_table_col_metadata[1]) if sub_table_col_metadata[1] != '' else len(values.columns)
            total_market_keys = values.columns[sub_table_start_col:sub_table_end_col]

            t_sub_table_cols = values.columns[sub_table_start_col:sub_table_end_col]
            values = values.melt(id_vars=list(filter(lambda x: x not in t_sub_table_cols, values.columns)), value_vars=t_sub_table_cols)

            sub_table_variable = "key"
            sub_table_value = config['table_transform'][0]['sub_value_name']

            values.columns = list(values.columns[0:-2]) + [sub_table_variable, sub_table_value]
            resolve_split_name = config['table_transform'][0]['sub_col_name']


            temp = values[sub_table_variable].apply(lambda x: pd.Series(str(x).split("%!%")))
            values = values.drop(sub_table_variable, axis=1)
            values[resolve_split_name] = temp

        # post processing
        values.columns = list(map(lambda x: x.replace('%!%', ' - ').replace('\n', ' - '), list(values.columns)))

        # add metrics
        if config.get('metrics') is not None:
            metrics = metrics_handler(source, config['metrics'])

            for i in metrics.keys():
                values[i] = metrics[i]

        if 'market_share_type' in config.keys():
            if config['market_share_type'] == 1:
                values = values.apply(filter_label, axis = 1, args = (total_market_dict,))
                cur_date = values.tail(1).iloc[0]['DATE']
                values.loc[values['DATE'] == 'TY', 'DATE'] = cur_date
                month, year = cur_date.split(' ')
                last_date = month + ' ' + str(int(year) - 1)
                values.loc[values['DATE'] == 'LY', 'DATE'] = last_date
            elif config['market_share_type'] == 3:
                values = values.apply(filter_label_new_format, axis = 1)
        return values

def filter_unwanted_row(row):
    company_name = str(row['COMPANY_NAME'])
    if company_name.startswith(' '):
        return True
    return False


def filter_label(row, total_market):
    label = str(row['LABEL'])
    if 'MAT' in label:
        metric, date = label.split(' ')
    elif 'YTD' in label:
        metric, date = label.split(' ')
    elif '\'' in label:
        metric = 'Quarterly'
        quarter = int(label[1:2])
        year = label[-2:]
        if quarter == 1:
            month = 'MAR'
        elif quarter == 2:
            month = 'JUN'
        elif quarter == 3:
            month = 'SEP'
        else:
            month = 'DEC'
        date = month + ' 20' + year
    else:
        metric = 'Monthly'
        month = label[:-2]
        year = label[-2:]
        date = month + ' 20' + year
    row['METRIC'] = metric
    row['DATE'] = date
    row["TOTAL_MARKET"] = total_market[label]
    return row

def filter_label_new_format(row):
    label = str(row['LABEL'])

    month = label[:3]
    year = label[-2:]
    date = month.upper() + ' 20' + year

    row['DATE'] = date
    return row

if __name__ == "__main__":
    convert_helper = ConvertHelper()
    convert_helper.connect_to_blob("sbcstorageacount", "O8u92YnD90jsl/46QMSXj0iR+2wac6TKzuXJ76roZM8bHq5z+P3+dbFUDTjbGiJMks01yk31dFKsgQFyeMFLbQ==")




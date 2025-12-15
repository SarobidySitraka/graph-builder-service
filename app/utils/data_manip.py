from typing import Tuple, List, Dict
# import polars as pl
import pandas as pd
import csv
from charset_normalizer import from_bytes

def check_cols_exist_in_db(data:pd.DataFrame, cols:list[str]) -> Tuple[List[str], Dict[str, str]]:
    columns = data.columns
    exists: list[str] = []
    info: dict[str, str] = {}
    for col in cols:
        if col in columns:
            exists.append(col)
            info[col] = "exist in data columns"
        else:
            info[col] = "not in data columns"
    if exists:
        return exists, info
    else:
        raise ValueError("Your columns does not exist in the data columns")

def detect_separator(text: str) -> str:
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(text, delimiters=",;\t|:")
        return dialect.delimiter
    except csv.Error:
        return ";"
    except Exception as e:
        raise ValueError(f"Error : {e}")

def detect_encoding(content: bytes) -> str:
    result = from_bytes(content).best()
    return result.encoding if result else "utf-8"
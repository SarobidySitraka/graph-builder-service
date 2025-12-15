import os
import tempfile
import logging
from typing import Optional
# import polars as pl
import pandas as pd
from joblib import Memory 
from app.utils.data_manip import detect_encoding, detect_separator
from app.models.file_config import FileConfig

memory = Memory(os.path.join("cache_dir"), verbose=0)

logger = logging.getLogger("ingestion")
logger.setLevel(logging.INFO)

if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

@memory.cache # type: ignore
async def load_file(file_config: FileConfig) -> pd.DataFrame:
    upload = file_config.file
    # determine filename from FileConfig or uploaded file; fall back to a default name
    filename = getattr(file_config, "filename", None) or getattr(upload, "filename", None) or "uploaded_file"
    logger.info(f"Loading file : {filename}")

    temp_path: Optional[str] = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            temp_path = tmp.name
            while chunk := await upload.read(8 * 1024 * 1024):  # lecture 8 MB
                tmp.write(chunk)

        with open(temp_path, "rb") as f:
            sample = f.read(20000)
            encoding = detect_encoding(sample)
            sample_decoded = sample.decode(encoding, errors="ignore")
            sep = file_config.delimiter or detect_separator(sample_decoded)

        # map detected encoding to polars CsvEncoding literal values and cast for typing
        def _map_to_csv_encoding(enc: str) -> str:
            e = (enc or "").lower().replace("_", "-")
            if "utf" in e:
                return "utf8"
            return "utf8-lossy"

        csv_encoding = _map_to_csv_encoding(encoding)

        if filename.endswith((".csv", ".tsv", ".dsv", ".txt")):
            df = pd.read_csv(temp_path, separator=sep, encoding=csv_encoding) # type: ignore

        elif filename.endswith(".json"):
            df = pd.read_json(temp_path)

        elif filename.endswith(".parquet"):
            df = pd.read_parquet(temp_path)

        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(temp_path)

        else:
            raise ValueError(f"Unsupported file format : {filename}")

        result = df.collect() # type: ignore
        logger.info(f"File {filename} is uploaded successfully ({result.shape[0]} rows, {result.shape[1]} columns)") # type: ignore

        return result # type: ignore

    except UnicodeDecodeError:
        logger.error(f"Encoding error : impossible to decode {filename}")
        raise ValueError("Encoding file is unknown or invalid.")

    except Exception as e:
        logger.error(f"File loading error for {filename} : {e}")
        raise RuntimeError(f"Impossible to load the file : {e}")

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.debug(f"Temporary file removed : {temp_path}")
            except OSError as err:
                logger.debug(f"Failed to remove temporary file {temp_path}: {err}")
            logger.debug(f"Temporary file removed : {temp_path}")
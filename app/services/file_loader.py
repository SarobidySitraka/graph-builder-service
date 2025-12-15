# import pandas as pd
# from io import StringIO
# from app.utils.data_manip import detect_encoding, detect_separator
#
# async def load_file(content, filename) -> pd.DataFrame:
#     encoding = detect_encoding(content)  # Detect encoding automatically: utf-8, latin1, ...
#     content = content.decode(encoding)
#
#     # Detect the separator value automatically (`,` or `;` or `\t` or `|`, ...)
#     sep = detect_separator(content)
#
#     if filename.endswith(".csv") or filename.endswith(".tsv") or filename.endswith(".dsv"):
#         result = pd.read_csv(StringIO(content), sep=sep)
#
#     elif filename.endswith(".json"):
#         result = pd.read_json(StringIO(content))
#
#     elif filename.endswith(".xlsx") or filename.endswith(".xls"):
#         result = pd.read_excel(content)
#
#     elif filename.endswith(".parquet"):
#         result = pd.read_parquet(content)
#
#     elif filename.endswith(".txt"):
#         result = pd.read_csv(StringIO(content), delimiter=sep)
#
#     else:
#         raise ValueError("File format not supported")
#
#     return pd.DataFrame(result)

# import os
# import tempfile
# import pandas as pd
# from io import BytesIO, StringIO
# from time import time
# from app.utils.data_manip import detect_encoding, detect_separator
#
# try:
#     from tqdm import tqdm
#     USE_TQDM = True
# except ImportError:
#     USE_TQDM = False
#
# CACHE_THRESHOLD = 1 * 1024 * 1024 * 1024  # 1 GB
# CHUNK_SIZE = 500_000  # Rows per chunk when streaming CSV
#
# async def load_file(content: bytes, filename: str) -> pd.DataFrame:
#     """
#     Load large files efficiently using:
#       - Lazy loading (chunked reading)
#       - Temporary on-disk caching (Parquet)
#       - Progress logs and timing
#     """
#     start_time = time()
#     file_size = len(content)
#     encoding = detect_encoding(content)
#     use_disk_cache = file_size >= CACHE_THRESHOLD
#
#     print(f"Loading file: {filename}")
#     print(f"   Approx. size: {file_size / (1024 ** 2):.2f} MB")
#     print(f"   Detected encoding: {encoding}")
#     print(f"   Mode: {'disk cache (size > 1GB)' if use_disk_cache else 'in-memory'}")
#
#     temp_parquet_path = None
#     df = None
#
#     # ----- CSV/TSV/DSV/TXT -----
#     if filename.endswith((".csv", ".tsv", ".dsv", ".txt")):
#         decoded = content.decode(encoding, errors="ignore")
#         sep = detect_separator(decoded)
#         reader = pd.read_csv(
#             StringIO(decoded),
#             sep=sep,
#             chunksize=CHUNK_SIZE,
#             low_memory=True,
#         )
#
#         total_rows = 0
#         chunks = []
#         iterator = tqdm(reader, desc="Reading CSV", unit="chunk") if USE_TQDM else reader
#
#         if use_disk_cache:
#             base_name = os.path.splitext(os.path.basename(filename))[0]
#             temp_parquet_path = os.path.join(tempfile.gettempdir(), f"{base_name}_cache.parquet")
#
#             for i, chunk in enumerate(iterator):
#                 total_rows += len(chunk)
#                 mode = "overwrite" if i == 0 else "append"
#                 chunk.to_parquet(temp_parquet_path, index=False, engine="pyarrow", compression="snappy")
#             df = pd.read_parquet(temp_parquet_path)
#         else:
#             for chunk in iterator:
#                 chunks.append(chunk)
#                 total_rows += len(chunk)
#             df = pd.concat(chunks, ignore_index=True)
#
#         print(f"   → {total_rows:,} rows loaded")
#
#     # ----- JSON -----
#     elif filename.endswith(".json"):
#         try:
#             df = pd.read_json(BytesIO(content), encoding=encoding, lines=True)
#         except ValueError:
#             df = pd.read_json(BytesIO(content), encoding=encoding)
#         if use_disk_cache:
#             base_name = os.path.splitext(os.path.basename(filename))[0]
#             temp_parquet_path = os.path.join(tempfile.gettempdir(), f"{base_name}_cache.parquet")
#             df.to_parquet(temp_parquet_path, index=False, engine="pyarrow", compression="snappy")
#             df = pd.read_parquet(temp_parquet_path)
#
#     # ----- Excel -----
#     elif filename.endswith((".xlsx", ".xls")):
#         print("📘 Reading Excel file (non-lazy)...")
#         df = pd.read_excel(BytesIO(content), engine="openpyxl")
#         if use_disk_cache:
#             base_name = os.path.splitext(os.path.basename(filename))[0]
#             temp_parquet_path = os.path.join(tempfile.gettempdir(), f"{base_name}_cache.parquet")
#             df.to_parquet(temp_parquet_path, index=False, engine="pyarrow", compression="snappy")
#             df = pd.read_parquet(temp_parquet_path)
#
#     # ----- Parquet -----
#     elif filename.endswith(".parquet"):
#         df = pd.read_parquet(BytesIO(content))
#
#     else:
#         raise ValueError(f"Unsupported file format: {filename}")
#
#     duration = time() - start_time
#     print(f"✅ Load completed in {duration:.2f}s ({len(df):,} rows, {len(df.columns)} columns)")
#     if temp_parquet_path:
#         print(f"   Cached at: {temp_parquet_path}")
#
#     return df
#
#
# async def stream_csv(content: bytes, filename: str, chunksize: int = CHUNK_SIZE):
#     """
#     Streaming version: yields DataFrame chunks asynchronously.
#     Uses tqdm for progress visualization if available.
#     """
#     encoding = detect_encoding(content)
#     decoded = content.decode(encoding, errors="ignore")
#     sep = detect_separator(decoded)
#
#     reader = pd.read_csv(StringIO(decoded), sep=sep, chunksize=chunksize, low_memory=True)
#     iterator = tqdm(reader, desc="Streaming CSV", unit="chunk") if USE_TQDM else reader
#
#     for chunk in iterator:
#         yield chunk

import os
import tempfile
import pandas as pd
from io import BytesIO, StringIO
from time import time
from app.utils.data_manip import detect_encoding, detect_separator

try:
    from tqdm import tqdm
    USE_TQDM = True
except ImportError:
    USE_TQDM = False

CACHE_THRESHOLD = 1 * 1024 * 1024 * 1024  # 1 GB
CHUNK_SIZE = 500_000  # Rows per chunk for CSV


async def load_file(content: bytes, filename: str) -> pd.DataFrame:
    """
    Efficiently load large files using:
      - Lazy loading (chunked reads)
      - Temporary on-disk caching (Parquet)
      - Progress logs and timing
    """
    start_time = time()
    file_size = len(content)
    encoding = detect_encoding(content)
    use_disk_cache = file_size >= CACHE_THRESHOLD

    print(f"Loading file: {filename}")
    print(f"   Approx. size: {file_size / (1024 ** 2):.2f} MB")
    print(f"   Detected encoding: {encoding}")
    print(f"   Mode: {'disk cache (size > 1GB)' if use_disk_cache else 'in-memory'}")

    temp_parquet_path = None

    # ----- CSV / TSV / DSV / TXT -----
    if filename.endswith((".csv", ".tsv", ".dsv", ".txt")):
        decoded = content.decode(encoding, errors="ignore")
        sep = detect_separator(decoded)
        reader = pd.read_csv(
            StringIO(decoded),
            sep=sep,
            chunksize=CHUNK_SIZE,
            low_memory=True,
        )

        total_rows = 0
        chunks = []
        iterator = tqdm(reader, desc="Reading CSV", unit="chunk") if USE_TQDM else reader

        if use_disk_cache:
            base_name = os.path.splitext(os.path.basename(filename))[0]
            temp_parquet_path = os.path.join(tempfile.gettempdir(), f"{base_name}_cache.parquet")

            for i, chunk in enumerate(iterator):
                total_rows += len(chunk)
                # mode = "overwrite" if i == 0 else "append"
                chunk.to_parquet(temp_parquet_path, index=False, engine="pyarrow", compression="snappy")
            df = pd.read_parquet(temp_parquet_path)
        else:
            for chunk in iterator:
                chunks.append(chunk)
                total_rows += len(chunk)
            df = pd.concat(chunks, ignore_index=True)

        print(f"   → {total_rows:,} rows loaded")

    # ----- JSON -----
    elif filename.endswith(".json"):
        try:
            # JSON Lines (streaming style)
            df = pd.read_json(BytesIO(content), encoding=encoding, lines=True)
        except ValueError:
            # Standard JSON
            df = pd.read_json(BytesIO(content), encoding=encoding)

        if use_disk_cache:
            base_name = os.path.splitext(os.path.basename(filename))[0]
            temp_parquet_path = os.path.join(tempfile.gettempdir(), f"{base_name}_cache.parquet")
            df.to_parquet(temp_parquet_path, index=False, engine="pyarrow", compression="snappy")
            df = pd.read_parquet(temp_parquet_path)

    # ----- Excel -----
    elif filename.endswith((".xlsx", ".xls")):
        print("Reading Excel file (non-lazy)...")
        df = pd.read_excel(BytesIO(content), engine="openpyxl")
        if use_disk_cache:
            base_name = os.path.splitext(os.path.basename(filename))[0]
            temp_parquet_path = os.path.join(tempfile.gettempdir(), f"{base_name}_cache.parquet")
            df.to_parquet(temp_parquet_path, index=False, engine="pyarrow", compression="snappy")
            df = pd.read_parquet(temp_parquet_path)

    # ----- Parquet -----
    elif filename.endswith(".parquet"):
        # Parquet readers expect a buffer-like object
        df = pd.read_parquet(BytesIO(content))

    else:
        raise ValueError(f"Unsupported file format: {filename}")

    duration = time() - start_time
    print(f"Load completed in {duration:.2f}s ({len(df):,} rows, {len(df.columns)} columns)")
    if temp_parquet_path:
        print(f"   Cached at: {temp_parquet_path}")

    return df


async def stream_csv(content: bytes, chunk_size: int = CHUNK_SIZE):
    """
    Asynchronous streaming reader: yields DataFrame chunks.
    Uses tqdm if available for progress display.
    """
    encoding = detect_encoding(content)
    decoded = content.decode(encoding, errors="ignore")
    sep = detect_separator(decoded)

    reader = pd.read_csv(StringIO(decoded), sep=sep, chunksize=chunk_size, low_memory=True)
    iterator = tqdm(reader, desc="Streaming CSV", unit="chunk") if USE_TQDM else reader

    for chunk in iterator:
        yield chunk

import pandas as pd
import openpyxl
from io import BytesIO


def _best_header_row(temp_df, max_rows=10):
    best_row = 0
    best_score = -1

    rows_to_check = min(max_rows, len(temp_df))
    for i in range(rows_to_check):
        row = temp_df.iloc[i]
        non_empty = row.notna().sum()

        text_cells = sum(
            isinstance(x, str) and x.strip() != ""
            for x in row
        )

        score = (text_cells * 2) + non_empty

        if score > best_score:
            best_score = score
            best_row = i

    return best_row


def detect_header(uplaoded_file, max_rows=10):
    temp_df = pd.read_excel(uplaoded_file, header=None)
    return _best_header_row(temp_df, max_rows)


def _normalize_col(col):
    return str(col).strip().lower()


def _load_row_images(uploaded_file):
    uploaded_file.seek(0)
    try:
        wb = openpyxl.load_workbook(uploaded_file, data_only=True)
    except Exception:
        return {}

    result = {}
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        images = getattr(ws, "_images", [])
        if not images:
            continue

        row_map = {}
        for img in images:
            try:
                anchor_row = img.anchor._from.row
            except Exception:
                continue
            try:
                data = img._data()
            except Exception:
                try:
                    data = img.ref.getvalue()
                except Exception:
                    continue
            row_map[anchor_row] = data

        if row_map:
            result[sheet_name] = row_map

    return result


def load_student_sheets(uploaded_file, max_rows=10):
    """
    Reads every sheet in the workbook, auto-detects the header row in each
    sheet independently, skips sheets with no usable rows (e.g. a blank
    cover sheet), and combines the rest into a single dataframe.

    Column names that only differ by case or spacing across sheets
    (e.g. 'Mobile number' vs 'Mobile Number') are merged into one column
    instead of showing up as separate, partially-empty columns.

    If a sheet has photos embedded directly on top of the cells (instead
    of a text column with file paths), those are extracted and attached
    per row as a 'Photo' column, matched by row position.

    Returns (combined_df, used_sheets, skipped_sheets).
    """
    xls = pd.ExcelFile(uploaded_file)
    row_images_by_sheet = _load_row_images(uploaded_file)

    canonical = {}
    frames = []
    used_sheets = []
    skipped_sheets = []

    for sheet in xls.sheet_names:
        raw = xls.parse(sheet_name=sheet, header=None)
        if raw.dropna(how="all").empty:
            skipped_sheets.append(sheet)
            continue

        header_row = _best_header_row(raw, max_rows)
        df = xls.parse(sheet_name=sheet, header=header_row)
        data_cols = [c for c in df.columns if not str(c).startswith("Unnamed")]
        df = df.loc[:, data_cols]

        sheet_images = row_images_by_sheet.get(sheet)
        if sheet_images:
            df["Photo"] = [
                BytesIO(sheet_images[header_row + 1 + i])
                if (header_row + 1 + i) in sheet_images else None
                for i in range(len(df))
            ]

        df = df.dropna(how="all", subset=data_cols)

        if df.empty or df.shape[1] == 0:
            skipped_sheets.append(sheet)
            continue

        rename_map = {}
        for col in df.columns:
            norm = _normalize_col(col)
            if norm not in canonical:
                canonical[norm] = col
            rename_map[col] = canonical[norm]
        df = df.rename(columns=rename_map)

        df["Sheet"] = sheet
        frames.append(df)
        used_sheets.append(sheet)

    if not frames:
        return pd.DataFrame(), used_sheets, skipped_sheets

    combined = pd.concat(frames, ignore_index=True, sort=False)
    return combined, used_sheets, skipped_sheets










import pandas as pd
from pathlib import Path


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
CLEANED_DIR = BASE_DIR / "data" / "cleaned"

CURRENT_RAW_DIR = RAW_DIR / "current"
HISTORICAL_SEM1_RAW_DIR = RAW_DIR / "historical_sem1"
HISTORICAL_SEM2_RAW_DIR = RAW_DIR / "historical_sem2"

HISTORICAL_SEM1_CLEANED_DIR = CLEANED_DIR / "historical_sem1"
HISTORICAL_SEM2_CLEANED_DIR = CLEANED_DIR / "historical_sem2"

CLEANED_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# ACADEMIC DATA RULES
# ============================================================

ASSIGNMENT_MAX_MARKS = 20
TEST_MAX_MARKS = 20


# ============================================================
# FUNCTION 1: LOAD CSV
# ============================================================

def load_csv(file_path):

    if not file_path.exists():
        print(f"[WARNING] File not found: {file_path}")
        return None

    print(f"\nLoading: {file_path}")

    df = pd.read_csv(file_path)

    print("Rows:", len(df))
    print("Columns:", len(df.columns))

    return df


# ============================================================
# FUNCTION 2: BASIC DATA INSPECTION
# ============================================================

def inspect_data(df, filename):

    print("\n" + "=" * 60)
    print("DATA INSPECTION:", filename)
    print("=" * 60)

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nData Types:")
    print(df.dtypes)

    print("\nMissing Values:")
    print(df.isnull().sum())

    print("\nDuplicate Rows:")
    print(df.duplicated().sum())


# ============================================================
# FUNCTION 3: SAVE CLEANED DATA
# ============================================================

def save_cleaned(df, output_path):

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        output_path,
        index=False
    )

    print("\nCleaned file saved:")
    print(output_path)

    print("Final rows:", len(df))


# ============================================================
# FUNCTION 4: CLEAN TEXT COLUMN
# ============================================================

def clean_text_column(df, column):

    if column in df.columns:

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    return df


# ============================================================
# FUNCTION 5: CLEAN STUDENT DATA
# ============================================================

def clean_students(input_path, output_path):

    df = load_csv(input_path)

    if df is None:
        return None

    inspect_data(
        df,
        input_path.name
    )

    # --------------------------------------------------------
    # Remove completely empty rows
    # --------------------------------------------------------

    df = df.dropna(how="all")

    # --------------------------------------------------------
    # Clean text columns
    # --------------------------------------------------------

    for column in [
        "Name",
        "Roll_No",
        "Gender"
    ]:

        df = clean_text_column(
            df,
            column
        )

    # --------------------------------------------------------
    # Standardize Gender
    # --------------------------------------------------------

    if "Gender" in df.columns:

        df["Gender"] = (
            df["Gender"]
            .str.title()
        )

        df["Gender"] = df["Gender"].replace({
            "M": "Male",
            "F": "Female"
        })

        df["Gender"] = (
            df["Gender"]
            .fillna("Not Specified")
        )

    # --------------------------------------------------------
    # Remove duplicate students
    # --------------------------------------------------------

    if "Student_ID" in df.columns:

        df = df.drop_duplicates(
            subset=["Student_ID"],
            keep="first"
        )

    save_cleaned(
        df,
        output_path
    )

    return df


# ============================================================
# FUNCTION 6: CLEAN SUBJECT DATA
# ============================================================

def clean_subjects(input_path, output_path):

    df = load_csv(input_path)

    if df is None:
        return None

    inspect_data(
        df,
        input_path.name
    )

    # --------------------------------------------------------
    # Remove empty rows
    # --------------------------------------------------------

    df = df.dropna(how="all")

    # --------------------------------------------------------
    # Clean Subject Name
    # --------------------------------------------------------

    df = clean_text_column(
        df,
        "Subject_Name"
    )

    # --------------------------------------------------------
    # Clean Subject Type
    # --------------------------------------------------------

    df = clean_text_column(
        df,
        "Subject_Type"
    )

    if "Subject_Type" in df.columns:

        df["Subject_Type"] = (
            df["Subject_Type"]
            .str.title()
        )

        df["Subject_Type"] = (
            df["Subject_Type"]
            .fillna("Theory")
        )

    # --------------------------------------------------------
    # Remove duplicate subjects
    # --------------------------------------------------------

    if "Subject_ID" in df.columns:

        df = df.drop_duplicates(
            subset=["Subject_ID"],
            keep="first"
        )

    save_cleaned(
        df,
        output_path
    )

    return df


# ============================================================
# FUNCTION 7: CLEAN STUDENT-SUBJECT DATA
# ============================================================

def clean_student_subject(
    input_path,
    output_path
):

    df = load_csv(input_path)

    if df is None:
        return None

    inspect_data(
        df,
        input_path.name
    )

    # --------------------------------------------------------
    # Remove completely empty rows
    # --------------------------------------------------------

    df = df.dropna(how="all")

    # --------------------------------------------------------
    # Required relationship columns
    # --------------------------------------------------------

    key_columns = [
        "Student_ID",
        "Subject_ID",
        "Semester_ID"
    ]

    existing_keys = [
        column
        for column in key_columns
        if column in df.columns
    ]

    # --------------------------------------------------------
    # Remove rows with missing relationship IDs
    # --------------------------------------------------------

    if existing_keys:

        df = df.dropna(
            subset=existing_keys
        )

        # Remove duplicate mapping
        df = df.drop_duplicates(
            subset=existing_keys,
            keep="first"
        )

    else:

        df = df.drop_duplicates()

    save_cleaned(
        df,
        output_path
    )

    return df


# ============================================================
# FUNCTION 8: CLEAN ATTENDANCE DATA
# ============================================================

def clean_attendance(
    input_path,
    output_path
):

    df = load_csv(input_path)

    if df is None:
        return None

    inspect_data(
        df,
        input_path.name
    )

    # --------------------------------------------------------
    # Convert Attendance Date
    # --------------------------------------------------------

    if "Attendance_Date" in df.columns:

        original_dates = df["Attendance_Date"]
        parsed_dates = pd.to_datetime(
            original_dates,
            errors="coerce"
        )

        # Keep missing dates because Attendance_Date is not required for
        # student-level attendance percentage analysis. Remove only dates
        # that were actually supplied but could not be parsed.
        invalid_supplied_dates = (
            original_dates.notna()
            & parsed_dates.isna()
        )

        df = df[~invalid_supplied_dates].copy()
        df["Attendance_Date"] = parsed_dates.loc[df.index]

        # Remove Sunday attendance when a valid date is available.
        df = df[
            df["Attendance_Date"].isna()
            | (df["Attendance_Date"].dt.dayofweek != 6)
        ]

    # --------------------------------------------------------
    # Standardize Attendance Status
    # --------------------------------------------------------

    if "Status" in df.columns:
        # Final generated raw data stores attendance as numeric Status:
        # 1 = Present, 0 = Absent. Keep Status unchanged and create the
        # analysis-friendly Attendance_Status column.
        status = pd.to_numeric(df["Status"], errors="coerce")
        df["Status"] = status.fillna(0).astype(int).clip(0, 1)
        df["Attendance_Status"] = df["Status"].map({1: "Present", 0: "Absent"})

    elif "Attendance_Status" in df.columns:
        df["Attendance_Status"] = (
            df["Attendance_Status"].astype("string").str.strip().str.title().fillna("Absent")
        )
        df["Status"] = df["Attendance_Status"].map({"Present": 1, "Absent": 0}).fillna(0).astype(int)

    # --------------------------------------------------------
    # Remove exact duplicate records
    # --------------------------------------------------------

    df = df.drop_duplicates()

    save_cleaned(
        df,
        output_path
    )

    return df


# ============================================================
# FUNCTION 9: CLEAN PRACTICAL ATTENDANCE
# ============================================================

def clean_practical_attendance(
    input_path,
    output_path
):

    df = load_csv(input_path)

    if df is None:
        return None

    inspect_data(
        df,
        input_path.name
    )

    # --------------------------------------------------------
    # Convert Attendance Date
    # --------------------------------------------------------

    if "Attendance_Date" in df.columns:

        original_dates = df["Attendance_Date"]
        parsed_dates = pd.to_datetime(
            original_dates,
            errors="coerce"
        )

        # Keep missing dates because Attendance_Date is not required for
        # student-level attendance percentage analysis. Remove only dates
        # that were actually supplied but could not be parsed.
        invalid_supplied_dates = (
            original_dates.notna()
            & parsed_dates.isna()
        )

        df = df[~invalid_supplied_dates].copy()
        df["Attendance_Date"] = parsed_dates.loc[df.index]

        # Remove Sunday attendance when a valid date is available.
        df = df[
            df["Attendance_Date"].isna()
            | (df["Attendance_Date"].dt.dayofweek != 6)
        ]

    # --------------------------------------------------------
    # Practical Attendance uses Status
    # --------------------------------------------------------

    if "Status" in df.columns:
        status = pd.to_numeric(df["Status"], errors="coerce")
        df["Status"] = status.fillna(0).astype(int).clip(0, 1)
        df["Attendance_Status"] = df["Status"].map({1: "Present", 0: "Absent"})

    elif "Attendance_Status" in df.columns:
        df["Attendance_Status"] = (
            df["Attendance_Status"].astype("string").str.strip().str.title().fillna("Absent")
        )
        df["Status"] = df["Attendance_Status"].map({"Present": 1, "Absent": 0}).fillna(0).astype(int)

    # --------------------------------------------------------
    # Remove duplicate records
    # --------------------------------------------------------

    df = df.drop_duplicates()

    save_cleaned(
        df,
        output_path
    )

    return df


# ============================================================
# FUNCTION 10: COMMON MARKS CLEANING
# ============================================================

def clean_marks(
    df,
    max_marks=None
):

    if "Marks" not in df.columns:
        return df

    # --------------------------------------------------------
    # Convert marks to numeric
    # --------------------------------------------------------

    df["Marks"] = pd.to_numeric(
        df["Marks"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Negative marks are invalid
    # --------------------------------------------------------

    df["Marks"] = df["Marks"].clip(
        lower=0
    )

    # --------------------------------------------------------
    # Apply maximum marks
    # --------------------------------------------------------

    if max_marks is not None:

        df["Marks"] = df["Marks"].clip(
            upper=max_marks
        )

    # --------------------------------------------------------
    # Fill missing marks using subject-wise median
    # --------------------------------------------------------

    if "Subject_ID" in df.columns:

        df["Marks"] = (
            df.groupby("Subject_ID")["Marks"]
            .transform(
                lambda x: x.fillna(
                    x.median()
                )
            )
        )

    # --------------------------------------------------------
    # If entire subject has missing marks
    # --------------------------------------------------------

    df["Marks"] = (
        df["Marks"]
        .fillna(0)
    )

    return df


# ============================================================
# FUNCTION 11: CLEAN ASSIGNMENT DATA
# ============================================================

def clean_assignments(
    input_path,
    output_path
):

    df = load_csv(input_path)

    if df is None:
        return None

    inspect_data(
        df,
        input_path.name
    )

    df = df.dropna(how="all")

    # Assignment marks are out of 20
    df = clean_marks(
        df,
        max_marks=ASSIGNMENT_MAX_MARKS
    )

    # Remove duplicate records
    df = df.drop_duplicates()

    save_cleaned(
        df,
        output_path
    )

    return df


# ============================================================
# FUNCTION 12: CLEAN TEST DATA
# ============================================================

def clean_tests(
    input_path,
    output_path
):

    df = load_csv(input_path)

    if df is None:
        return None

    inspect_data(
        df,
        input_path.name
    )

    df = df.dropna(how="all")

    # Test marks are out of 20
    df = clean_marks(
        df,
        max_marks=TEST_MAX_MARKS
    )

    # Remove duplicate records
    df = df.drop_duplicates()

    save_cleaned(
        df,
        output_path
    )

    return df


# ============================================================
# FUNCTION 13: CLEAN SEMESTER RESULTS
# ============================================================

def clean_results(
    input_path,
    output_path
):

    df = load_csv(input_path)

    if df is None:
        return None

    inspect_data(
        df,
        input_path.name
    )

    df = df.dropna(how="all")

    # Semester result marks
    # No artificial maximum is applied here.
    df = clean_marks(
        df,
        max_marks=None
    )

    # Remove duplicate records
    df = df.drop_duplicates()

    save_cleaned(
        df,
        output_path
    )

    return df


# ============================================================
# FUNCTION 14: CLEAN ONE COMPLETE DATASET
# ============================================================

def clean_dataset(
    raw_dir,
    cleaned_dir,
    dataset_name
):

    print("\n")
    print("=" * 70)
    print("CLEANING DATASET:", dataset_name)
    print("=" * 70)

    cleaned_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # STUDENTS
    # --------------------------------------------------------

    clean_students(
        raw_dir / "students.csv",
        cleaned_dir / "students_cleaned.csv"
    )

    # --------------------------------------------------------
    # SUBJECTS
    # --------------------------------------------------------

    clean_subjects(
        raw_dir / "subjects.csv",
        cleaned_dir / "subjects_cleaned.csv"
    )

    # --------------------------------------------------------
    # STUDENT-SUBJECT
    # --------------------------------------------------------

    clean_student_subject(
        raw_dir / "student_subject.csv",
        cleaned_dir / "student_subject_cleaned.csv"
    )

    # --------------------------------------------------------
    # ATTENDANCE
    # --------------------------------------------------------

    clean_attendance(
        raw_dir / "attendance.csv",
        cleaned_dir / "attendance_cleaned.csv"
    )

    # --------------------------------------------------------
    # PRACTICAL ATTENDANCE
    # --------------------------------------------------------

    clean_practical_attendance(
        raw_dir / "practical_attendance.csv",
        cleaned_dir / "practical_attendance_cleaned.csv"
    )

    # --------------------------------------------------------
    # ASSIGNMENTS
    # --------------------------------------------------------

    clean_assignments(
        raw_dir / "assignments.csv",
        cleaned_dir / "assignments_cleaned.csv"
    )

    # --------------------------------------------------------
    # TESTS
    # --------------------------------------------------------

    clean_tests(
        raw_dir / "tests.csv",
        cleaned_dir / "tests_cleaned.csv"
    )

    # --------------------------------------------------------
    # SEMESTER RESULTS
    # --------------------------------------------------------

    clean_results(
        raw_dir / "semester_results.csv",
        cleaned_dir / "semester_results_cleaned.csv"
    )

    print("\n")
    print("=" * 70)
    print(dataset_name, "CLEANING COMPLETED")
    print("=" * 70)


# ============================================================
# FUNCTION 15: RUN COMPLETE CLEANING PIPELINE
# ============================================================

def run_cleaning():

    print("\n")
    print("=" * 70)
    print("STUDENT PERFORMANCE SYSTEM")
    print("DATA CLEANING PIPELINE")
    print("=" * 70)

    # ========================================================
    # CURRENT DATA
    # ========================================================

    if not CURRENT_RAW_DIR.exists():
        raise FileNotFoundError(
            f"Current raw data folder not found: {CURRENT_RAW_DIR}"
        )

    clean_dataset(
        CURRENT_RAW_DIR,
        CLEANED_DIR,
        "CURRENT DATA"
    )

    # ========================================================
    # HISTORICAL SEMESTER 1
    # ========================================================

    if HISTORICAL_SEM1_RAW_DIR.exists():

        clean_dataset(
            HISTORICAL_SEM1_RAW_DIR,
            HISTORICAL_SEM1_CLEANED_DIR,
            "HISTORICAL SEMESTER 1"
        )

    else:

        print(
            "\n[INFO] Historical Semester 1 folder not found:"
        )

        print(
            HISTORICAL_SEM1_RAW_DIR
        )

    # ========================================================
    # HISTORICAL SEMESTER 2
    # ========================================================

    if HISTORICAL_SEM2_RAW_DIR.exists():

        clean_dataset(
            HISTORICAL_SEM2_RAW_DIR,
            HISTORICAL_SEM2_CLEANED_DIR,
            "HISTORICAL SEMESTER 2"
        )

    else:

        print(
            "\n[INFO] Historical Semester 2 folder not found:"
        )

        print(
            HISTORICAL_SEM2_RAW_DIR
        )

    # ========================================================
    # COMPLETED
    # ========================================================

    print("\n")
    print("=" * 70)
    print("ALL DATA CLEANING COMPLETED SUCCESSFULLY")
    print("=" * 70)


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":

    run_cleaning()
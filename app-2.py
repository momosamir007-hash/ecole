import io
import json
import re
import html
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import requests


# ============================================================
# إعدادات التطبيق
# ============================================================
st.set_page_config(
    page_title="النظام الذكي لحساب معدلات التلاميذ",
    page_icon="🏫",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: Cairo, sans-serif; }
.main .block-container { direction: rtl; text-align: right; }
h1,h2,h3,h4,p,li,span,label,td,th { direction: rtl; text-align: right; }
.ai-box {
    background: linear-gradient(135deg,#11998e 0%,#38ef7d 100%);
    border-radius: 16px; padding: 22px; margin-bottom: 18px; color: white;
}
.analysis-box {
    background:#f8f9fa; border-right:5px solid #6c5ce7;
    border-radius:10px; padding:20px; line-height:2;
}
.small-note { color:#666; font-size:13px; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# مستويات ومواد الدراسة
# ============================================================
def subject(name, kind="secondary", teacher="معلم القسم", quizzes=None, tests=None):
    return {
        "name": name,
        "type": kind,
        "teacher": teacher,
        "keywords": {
            "quizzes": quizzes or [],
            "tests": tests or ["اختبار", "امتحان", "تقويم", "مستمر"],
        },
    }


MAIN_AR = ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج"]
MAIN_FR = MAIN_AR + ["فهم"]
MAIN_EN = MAIN_AR + ["فهم"]
TEST_MAIN = ["اختبار", "امتحان"]

LEVELS = {
    "السنة الأولى": [
        subject("اللغة العربية", "main", quizzes=MAIN_AR, tests=TEST_MAIN),
        subject("الرياضيات", "main",
                quizzes=["أعداد", "حساب", "مقادير", "قياس", "معطيات", "فضاء", "هندسة"],
                tests=TEST_MAIN),
        subject("التربية الإسلامية"),
        subject("التربية الموسيقية"),
        subject("التربية التشكيلية"),
        subject("التربية البدنية", teacher="أستاذ التربية البدنية"),
    ],
    "السنة الثانية": [
        subject("اللغة العربية", "main", quizzes=MAIN_AR, tests=TEST_MAIN),
        subject("الرياضيات", "main",
                quizzes=["أعداد", "حساب", "مقادير", "قياس", "معطيات", "فضاء", "هندسة"],
                tests=TEST_MAIN),
        subject("التربية الإسلامية"),
        subject("التربية الموسيقية"),
        subject("التربية التشكيلية"),
        subject("التربية البدنية", teacher="أستاذ التربية البدنية"),
    ],
    "السنة الثالثة": [
        subject("اللغة العربية", "main", quizzes=MAIN_AR, tests=TEST_MAIN),
        subject("الرياضيات", "main",
                quizzes=["أعداد", "حساب", "مقادير", "قياس", "معطيات", "فضاء", "هندسة"],
                tests=TEST_MAIN),
        subject("اللغة الفرنسية", "main", teacher="أستاذ اللغة الفرنسية",
                quizzes=MAIN_FR, tests=TEST_MAIN),
        subject("اللغة الإنجليزية", "main", teacher="أستاذ اللغة الإنجليزية",
                quizzes=MAIN_EN, tests=TEST_MAIN),
        subject("التربية الإسلامية"),
        subject("التربية العلمية والتكنولوجية"),
        subject("التاريخ"),
        subject("التربية التشكيلية"),
        subject("التربية الموسيقية"),
        subject("التربية البدنية", teacher="أستاذ التربية البدنية"),
    ],
    "السنة الرابعة": [
        subject("اللغة العربية", "main", quizzes=MAIN_AR, tests=TEST_MAIN),
        subject("الرياضيات", "main",
                quizzes=["أعداد", "حساب", "مقادير", "قياس", "معطيات", "فضاء", "هندسة"],
                tests=TEST_MAIN),
        subject("اللغة الفرنسية", "main", teacher="أستاذ اللغة الفرنسية",
                quizzes=MAIN_FR, tests=TEST_MAIN),
        subject("اللغة الإنجليزية", "main", teacher="أستاذ اللغة الإنجليزية",
                quizzes=MAIN_EN, tests=TEST_MAIN),
        subject("التربية الإسلامية"),
        subject("التربية العلمية والتكنولوجية"),
        subject("التربية المدنية"),
        subject("التاريخ والجغرافيا"),
        subject("التربية التشكيلية"),
        subject("التربية الموسيقية"),
        subject("التربية البدنية", teacher="أستاذ التربية البدنية"),
    ],
    "السنة الخامسة": [
        subject("اللغة العربية", "main", quizzes=MAIN_AR, tests=TEST_MAIN),
        subject("الرياضيات", "main",
                quizzes=["أعداد", "حساب", "مقادير", "قياس", "معطيات", "فضاء", "هندسة"],
                tests=TEST_MAIN),
        subject("اللغة الفرنسية", "main", teacher="أستاذ اللغة الفرنسية",
                quizzes=MAIN_FR, tests=TEST_MAIN),
        subject("اللغة الإنجليزية", "main", teacher="أستاذ اللغة الإنجليزية",
                quizzes=MAIN_EN, tests=TEST_MAIN),
        subject("التربية الإسلامية"),
        subject("التربية العلمية والتكنولوجية"),
        subject("التربية المدنية"),
        subject("التاريخ والجغرافيا"),
        subject("التربية التشكيلية"),
        subject("التربية الموسيقية"),
        subject("التربية البدنية", teacher="أستاذ التربية البدنية"),
    ],
}

SHEET_ALIASES = {
    ("السنة الأولى", "التربية البدنية"): ["ت البدنية والرياضية"],
    ("السنة الثانية", "التربية البدنية"): ["ت البدنية والرياضية 1"],
    ("السنة الثالثة", "التربية البدنية"): ["ت البدنية والرياضية 2"],
    ("السنة الرابعة", "التربية البدنية"): ["ت البدنية والرياضية 3"],
    ("السنة الخامسة", "التربية البدنية"): ["ت البدنية والرياضية 4"],
    ("السنة الثالثة", "اللغة الفرنسية"): ["اللغة الفرنسية"],
    ("السنة الرابعة", "اللغة الفرنسية"): ["اللغة الفرنسية 1"],
    ("السنة الخامسة", "اللغة الفرنسية"): ["اللغة الفرنسية 2"],
    ("السنة الثالثة", "اللغة الإنجليزية"): ["اللغة الإنجليزية"],
    ("السنة الرابعة", "اللغة الإنجليزية"): ["اللغة الإنجليزية 1"],
    ("السنة الخامسة", "اللغة الإنجليزية"): ["اللغة الإنجليزية 2"],
    ("السنة الثالثة", "التربية العلمية والتكنولوجية"): ["ت العلمية و التكنولوجية"],
    ("السنة الرابعة", "التربية العلمية والتكنولوجية"): ["ت العلمية و التكنولوجية"],
    ("السنة الخامسة", "التربية العلمية والتكنولوجية"): ["ت العلمية و التكنولوجية"],
    ("السنة الرابعة", "التاريخ والجغرافيا"): ["التاريخ و الجغرافيا"],
    ("السنة الخامسة", "التاريخ والجغرافيا"): ["التاريخ و الجغرافيا"],
}


# ============================================================
# أدوات النص والأسماء
# ============================================================
ARABIC_TRANSLATIONS = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه",
    "ى": "ي", "ئ": "ي", "ؤ": "و",
    "ـ": "",
})


def normalize_arabic(value):
    if pd.isna(value):
        return ""
    s = str(value).strip().lower()
    s = s.translate(ARABIC_TRANSLATIONS)
    s = re.sub(r"[\u064B-\u065F\u0670]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_identifier(value):
    if pd.isna(value):
        return ""
    s = str(value).strip().lower()
    s = re.sub(r"\.0$", "", s)
    s = re.sub(r"\s+", "", s)
    return s


def clean_grade_value(value, scale=10):
    if pd.isna(value):
        return np.nan

    s = str(value).strip()
    if not s:
        return np.nan

    s_norm = normalize_arabic(s)
    absent = ["غائب", "غياب", "معفى", "معفي", "مريض", "absent", "absence"]
    if any(x in s_norm for x in absent):
        return np.nan

    if s in {"/", "-", ".", "*", "x", "X", "—", "–"}:
        return np.nan

    # دعم 15/20 و15 / 20 و 15 من 20
    m = re.search(r"(-?\d+(?:[.,]\d+)?)\s*(?:/|من)\s*(20|10)", s, flags=re.I)
    if m:
        value_num = float(m.group(1).replace(",", "."))
        source_scale = int(m.group(2))
        if source_scale == 20:
            value_num /= 2
        return value_num if 0 <= value_num <= 10 else np.nan

    s = s.replace(",", ".")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return np.nan

    try:
        value_num = float(m.group())
    except ValueError:
        return np.nan

    # العلامات في المشروع موحدة على 10.
    # إذا كان الرقم أكبر من 10 وأقصاه 20، نعتبره /20 ونحوّله.
    if 10 < value_num <= 20:
        value_num /= 2

    return value_num if 0 <= value_num <= 10 else np.nan


def find_name_columns(df):
    nom = prenom = combined = None
    id_col = None

    for col in df.columns:
        raw = str(col).strip()
        norm = normalize_arabic(raw)
        low = raw.lower()

        if any(k in norm for k in [
            "رقم التعريف", "رقم التسجيل", "الرقم التعريفي",
            "المعرف", "matricule", "identifiant", "id"
        ]):
            if id_col is None:
                id_col = col

        if any(k in norm for k in [
            "لقب والاسم", "اسم واللقب", "اسم ولقب", "لقب واسم",
            "التلميذ", "الطالب", "الاسم الكامل", "الاسم واللقب"
        ]):
            combined = col
        elif norm in {"اللقب", "لقب"} or low == "nom":
            nom = col
        elif norm in {"الاسم", "اسم"} or low in {"prenom", "prénom"}:
            prenom = col

    return id_col, nom, prenom, combined


def process_names(df):
    """اكتشاف هوية التلميذ بشكل أكثر مرونة."""
    id_col, nom_col, prenom_col, combined_col = find_name_columns(df)

    if combined_col:
        return combined_col, id_col

    if nom_col and prenom_col:
        new_col = "__الاسم_الكامل__"
        df[new_col] = (
            df[nom_col].fillna("").astype(str).str.strip()
            + " "
            + df[prenom_col].fillna("").astype(str).str.strip()
        ).str.replace(r"\\s+", " ", regex=True).str.strip()
        return new_col, id_col

    if nom_col:
        return nom_col, id_col

    if prenom_col:
        return prenom_col, id_col

    # اكتشاف مرن لأسماء الأعمدة الفرنسية/العربية حتى مع اختلاف الكتابة.
    candidates = []
    for col in df.columns:
        n = normalize_arabic(str(col))
        low = str(col).strip().lower()

        if any(k in n for k in [
            "اسم", "لقب", "تلميذ", "طالب", "الطفل"
        ]) or low in {
            "nom", "prenom", "prénom", "fullname", "full name",
            "student", "student name", "name"
        }:
            candidates.append(col)

    if candidates:
        # إذا وجد أكثر من عمود اسم/لقب، ندمج أول اثنين النصيين.
        if len(candidates) >= 2:
            c1, c2 = candidates[0], candidates[1]
            new_col = "__الاسم_الكامل__"
            df[new_col] = (
                df[c1].fillna("").astype(str).str.strip()
                + " "
                + df[c2].fillna("").astype(str).str.strip()
            ).str.replace(r"\\s+", " ", regex=True).str.strip()
            if df[new_col].str.len().gt(1).sum() > 0:
                return new_col, id_col
        c = candidates[0]
        if df[c].fillna("").astype(str).str.strip().ne("").sum() > 0:
            return c, id_col

    # آخر حل آمن: اختيار العمود النصي الذي يحتوي أكبر عدد من القيم
    # وليس الأعمدة الرقمية مثل السن/المعدل/الترتيب.
    ignored = [
        "رقم", "ملاحظ", "تاريخ", "قرار", "ترتيب", "معدل",
        "مجموع", "matricule", "identifiant", "id", "date",
        "obs", "rang", "coefficient", "معامل", "قسم", "فوج"
    ]
    scored = []
    for col in df.columns:
        if col in {id_col} or str(col).startswith("__"):
            continue
        n = normalize_arabic(str(col))
        nonempty = df[col].fillna("").astype(str).str.strip()
        count = int(nonempty.ne("").sum())
        if count == 0 or any(k in n for k in ignored):
            continue

        # نسبة النصوص غير الرقمية
        numeric = pd.to_numeric(nonempty.str.replace(",", ".", regex=False), errors="coerce")
        text_ratio = float(numeric.isna().mean())
        score = count * (0.5 + text_ratio)
        scored.append((score, col))

    if scored:
        scored.sort(reverse=True)
        return scored[0][1], id_col

    return None, id_col


def build_master_from_dataframe(df, name_col, id_col):
    """يبني مفتاحاً ثابتاً للتلميذ من رقم التعريف أو الاسم."""
    if df is None or df.empty or not name_col or name_col not in df.columns:
        return pd.DataFrame(columns=["_key", "الاسم"]), "لا توجد بيانات تلاميذ."

    work = df.copy()

    if id_col and id_col in work.columns:
        ids = work[id_col].apply(normalize_identifier)
    else:
        ids = pd.Series("", index=work.index)

    names = work[name_col].fillna("").astype(str).str.strip()
    name_keys = names.apply(normalize_arabic)

    keys = ids.copy()
    keys.loc[keys == ""] = name_keys.loc[keys == ""]

    valid = keys.ne("") & names.ne("")
    work = work.loc[valid].copy()
    keys = keys.loc[valid]
    names = names.loc[valid]

    if work.empty:
        return pd.DataFrame(columns=["_key", "الاسم"]), (
            f"تم العثور على الشيت لكن لم توجد أسماء صالحة في العمود «{name_col}»."
        )

    master = pd.DataFrame({
        "_key": keys.values,
        "الاسم": names.values,
    })

    # الاحتفاظ بأول اسم ظاهر مع منع التكرار.
    master = master.drop_duplicates("_key", keep="first").reset_index(drop=True)
    return master, None


def is_gradeable_column(col):
    norm = normalize_arabic(str(col))
    ignored = [
        "رقم", "matricule", "identifiant", "تاريخ", "date",
        "لقب", "اسم", "nom", "prenom", "obs", "ملاحظ",
        "قرار", "ترتيب", "معدل", "مجموع", "عدد", "rang"
    ]
    return not any(x in norm for x in ignored)


def get_gradeable_columns(df, name_col=None, id_col=None):
    result = []
    for col in df.columns:
        if col in {name_col, id_col} or str(col).startswith("__"):
            continue
        if not is_gradeable_column(col):
            continue

        cleaned = df[col].apply(clean_grade_value)
        if cleaned.notna().sum() >= max(1, int(len(df) * 0.05)):
            result.append(col)
    return result


def detect_columns(df, keywords, gradeable):
    quizzes, tests = [], []
    for col in gradeable:
        norm = normalize_arabic(str(col))

        if any(normalize_arabic(k) in norm for k in keywords.get("quizzes", [])):
            quizzes.append(col)

        if any(normalize_arabic(k) in norm for k in keywords.get("tests", [])):
            tests.append(col)

    return quizzes, tests


# ============================================================
# Excel
# ============================================================
def read_excel_sheets(file):
    file.seek(0)
    return pd.ExcelFile(file).sheet_names


def read_sheet_safe(file, sheet_name):
    try:
        file.seek(0)
        raw = pd.read_excel(file, sheet_name=sheet_name, header=None, dtype=str)
    except Exception as e:
        return pd.DataFrame(), f"تعذر قراءة الورقة: {e}"

    if raw.empty:
        return pd.DataFrame(), "الورقة فارغة."

    header_idx = 0
    best_score = -1

    for i in range(min(20, len(raw))):
        values = " ".join(raw.iloc[i].dropna().astype(str).tolist())
        norm = normalize_arabic(values)
        score = 0
        if "لقب" in norm:
            score += 2
        if "اسم" in norm or "prenom" in values.lower():
            score += 2
        if "nom" in values.lower():
            score += 2
        if "matricule" in values.lower() or "رقم التعريف" in norm:
            score += 2

        if score > best_score:
            best_score = score
            header_idx = i

    try:
        file.seek(0)
        df = pd.read_excel(file, sheet_name=sheet_name, header=header_idx, dtype=str)
    except Exception as e:
        return pd.DataFrame(), f"تعذر إنشاء الجدول: {e}"

    df.columns = [
        re.sub(r"\s+", " ", str(c).replace("\n", " ").strip())
        for c in df.columns
    ]
    df = df.dropna(how="all").reset_index(drop=True)

    # إزالة الصفوف العلوية المكررة
    while not df.empty:
        first = " ".join(df.iloc[0].fillna("").astype(str).tolist())
        n = normalize_arabic(first)
        if any(k in n for k in ["اللقب", "الاسم", "matricule", "prenom", "nom"]):
            df = df.iloc[1:].reset_index(drop=True)
        else:
            break

    return df, None


def choose_sheet(sheet_names, level, subject_name):
    aliases = SHEET_ALIASES.get((level, subject_name), [subject_name])
    normalized_aliases = [normalize_arabic(x) for x in aliases]

    for i, sh in enumerate(sheet_names):
        n = normalize_arabic(sh)
        if n in normalized_aliases:
            return i

    for i, sh in enumerate(sheet_names):
        n = normalize_arabic(sh)
        if any(a in n or n in a for a in normalized_aliases):
            return i

    target = normalize_arabic(subject_name)
    for i, sh in enumerate(sheet_names):
        if target in normalize_arabic(sh):
            return i

    return 0


# ============================================================
# الحساب
# ============================================================
def calculate_subject(df, name_col, id_col, mapping, subject_cfg):
    work = df.copy()

    if id_col and id_col in work.columns:
        work["_key"] = work[id_col].apply(normalize_identifier)
        # إذا كان رقم التعريف فارغاً نرجع للاسم
        name_keys = work[name_col].apply(normalize_arabic)
        work.loc[work["_key"] == "", "_key"] = name_keys[work["_key"] == ""]
    else:
        work["_key"] = work[name_col].apply(normalize_arabic)

    work = work[work["_key"] != ""].copy()

    test_col = mapping.get("test_col")
    quiz_cols = mapping.get("quiz_cols", [])

    if test_col and test_col in work.columns:
        test_score = work[test_col].apply(clean_grade_value)
    else:
        test_score = pd.Series(np.nan, index=work.index)

    quiz_scores = []
    for col in quiz_cols:
        if col in work.columns:
            quiz_scores.append(work[col].apply(clean_grade_value))

    if subject_cfg["type"] == "main" and quiz_scores:
        qdf = pd.concat(quiz_scores, axis=1)
        quiz_avg = qdf.mean(axis=1, skipna=True)

        # إذا توفر الاختبار والفروض: متوسطهما.
        # إذا توفر أحدهما فقط: استعمال المتوفر، وعدم تحويل الغياب إلى صفر.
        final = pd.Series(np.nan, index=work.index)
        both = quiz_avg.notna() & test_score.notna()
        final.loc[both] = (quiz_avg.loc[both] + test_score.loc[both]) / 2
        final = final.fillna(quiz_avg).fillna(test_score)
    else:
        final = test_score

    result = pd.DataFrame({
        "_key": work["_key"],
        subject_cfg["name"]: final,
    })

    # منع تكرار التلميذ: نحتفظ بأول سجل له، مع أفضل قيمة متوفرة.
    result = (
        result.groupby("_key", as_index=False)[subject_cfg["name"]]
        .max()
    )

    return result


def classify_student(avg):
    if pd.isna(avg):
        return "—"
    if avg >= 9:
        return "ممتاز 🌟"
    if avg >= 8:
        return "جيد جداً ✅"
    if avg >= 7:
        return "جيد 👍"
    if avg >= 5:
        return "مقبول 📗"
    if avg >= 3.5:
        return "ضعيف ⚠️"
    return "ضعيف جداً ❌"


def rank_with_ties(series):
    return series.rank(method="min", ascending=False).astype("Int64")


def build_results(master, subject_results):
    merged = master.copy()

    for sg in subject_results:
        merged = merged.merge(sg, on="_key", how="outer")

    subject_cols = [c for c in merged.columns if c not in {"_key", "الاسم"}]

    if "الاسم" not in merged.columns:
        merged["الاسم"] = merged["_key"]

    for col in subject_cols:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")

    merged["عدد المواد"] = merged[subject_cols].notna().sum(axis=1)
    merged["المجموع"] = merged[subject_cols].sum(axis=1, skipna=True)
    merged["المعدل الفصلي"] = np.where(
        merged["عدد المواد"] > 0,
        merged["المجموع"] / merged["عدد المواد"],
        np.nan
    )
    merged["المعدل الفصلي"] = merged["المعدل الفصلي"].round(2)
    merged["التقدير"] = merged["المعدل الفصلي"].apply(classify_student)

    # التلاميذ الذين لا توجد لهم أي علامة يبقون في الكشف، لكن في الأسفل.
    merged["الترتيب"] = rank_with_ties(merged["المعدل الفصلي"])

    merged = merged.sort_values(
        ["المعدل الفصلي", "الاسم"],
        ascending=[False, True],
        na_position="last"
    ).reset_index(drop=True)

    # ترتيب الأعمدة
    cols = ["الترتيب", "الاسم"] + subject_cols + [
        "عدد المواد", "المجموع", "المعدل الفصلي", "التقدير"
    ]
    return merged[["_key"] + [c for c in cols if c in merged.columns]], subject_cols


# ============================================================
# التحقق
# ============================================================
def validation_report(df, name_col, id_col, gradeable_cols):
    issues = []

    if name_col is None:
        issues.append("لم يتم العثور على عمود أسماء.")
    else:
        empty_names = df[name_col].fillna("").astype(str).str.strip().eq("").sum()
        if empty_names:
            issues.append(f"يوجد {empty_names} سجل بدون اسم.")

    if id_col and id_col in df.columns:
        ids = df[id_col].apply(normalize_identifier)
        duplicated = ids[ids != ""].duplicated().sum()
        if duplicated:
            issues.append(f"يوجد {duplicated} رقم تعريف مكرر.")

    invalid = 0
    for col in gradeable_cols:
        raw_nonempty = df[col].fillna("").astype(str).str.strip().ne("")
        cleaned = df[col].apply(clean_grade_value)
        invalid += int((raw_nonempty & cleaned.isna()).sum())

    if invalid:
        issues.append(f"يوجد {invalid} إدخال علامة غير قابل للتحويل أو قيمة غائبة.")

    return issues


# ============================================================
# Mistral AI
# ============================================================
def get_api_key():
    try:
        return st.secrets.get("MISTRAL_API_KEY")
    except Exception:
        return None


def call_mistral(api_key, prompt):
    if not api_key:
        return "لم يتم إعداد MISTRAL_API_KEY."

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "mistral-large-latest",
        "messages": [
            {
                "role": "system",
                "content": (
                    "أنت مفتش تربوي جزائري خبير في التعليم الابتدائي. "
                    "حلل الإحصائيات بموضوعية ولا تخترع بيانات غير موجودة."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        return f"تعذر الاتصال بخدمة Mistral: {e}"
    except (KeyError, IndexError, ValueError) as e:
        return f"استجابة Mistral غير متوقعة: {e}"


# ============================================================
# PDF عربي
# ============================================================
def generate_pdf(text):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase import pdfmetrics
        import arabic_reshaper
        from bidi.algorithm import get_display
    except ImportError:
        st.error(
            "مكتبات PDF غير مثبتة. ثبّت: "
            "reportlab arabic-reshaper python-bidi"
        )
        return None

    # البحث عن خط موجود محلياً
    import os
    candidates = [
        "arial.ttf",
        "Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
    ]
    font = next((p for p in candidates if os.path.exists(p)), None)

    if not font:
        st.warning(
            "لم يتم العثور على خط عربي محلي. "
            "سيتم عرض النص في الواجهة، لكن PDF يحتاج خطاً عربياً."
        )
        return None

    try:
        pdfmetrics.registerFont(TTFont("ArabicFont", font))
    except Exception:
        pass

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=35,
        leftMargin=35,
        topMargin=35,
        bottomMargin=35,
    )

    styles = getSampleStyleSheet()
    style = ParagraphStyle(
        "Arabic",
        parent=styles["Normal"],
        fontName="ArabicFont",
        fontSize=11,
        leading=18,
        alignment=2,
    )

    story = []
    for line in str(text).splitlines():
        if not line.strip():
            story.append(Spacer(1, 8))
            continue
        safe = html.escape(line)
        shaped = get_display(arabic_reshaper.reshape(safe))
        story.append(Paragraph(shaped, style))
        story.append(Spacer(1, 4))

    try:
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"فشل إنشاء PDF: {e}")
        return None


# ============================================================
# Excel export
# ============================================================
def export_excel(df, sheet_name="النتائج"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        clean = df.drop(columns=["_key"], errors="ignore")
        clean.to_excel(writer, index=False, sheet_name=sheet_name)

        ws = writer.sheets[sheet_name]
        ws.freeze_panes(1, 0)
        ws.autofilter(0, 0, len(clean), max(0, len(clean.columns) - 1))

        for i, col in enumerate(clean.columns):
            values = clean[col].astype(str)
            max_len = max([len(str(col))] + values.map(len).tolist()) + 2
            ws.set_column(i, i, min(max_len, 35))

    return output.getvalue()


# ============================================================
# الحالة
# ============================================================
defaults = {
    "final_result": None,
    "subject_cols": [],
    "mappings": {},
    "analysis": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ============================================================
# اكتشاف ملفات الرقمنة الحقيقية
# ============================================================
def detect_level_from_sheet(df):
    """يقرأ سطر وصف الوثيقة في نماذج الرقمنة."""
    for i in range(min(10, len(df))):
        line = " ".join(df.iloc[i].fillna("").astype(str).tolist())
        n = normalize_arabic(line)

        if "خامسه" in n or "خامسة" in n:
            return "السنة الخامسة"
        if "رابعه" in n or "رابعة" in n:
            return "السنة الرابعة"
        if "ثالثه" in n or "ثالثة" in n:
            return "السنة الثالثة"
        if "ثانيه" in n or "ثانية" in n:
            return "السنة الثانية"
        if "اولي" in n or "اولى" in n or "اول" in n:
            return "السنة الأولى"
    return None


def subject_match_score(sheet_name, subject_name, level):
    a = normalize_arabic(sheet_name)
    b = normalize_arabic(subject_name)

    aliases = SHEET_ALIASES.get((level, subject_name), [])
    score = 0

    if a == b:
        score = 100
    elif any(a == normalize_arabic(x) for x in aliases):
        score = 100
    elif b in a or a in b:
        score = 80

    # اختلافات النماذج الرسمية
    special = {
        "التربية العلمية والتكنولوجية": [
            "ت العلمية و التكنولوجية", "ت العلمية والتكنولوجية",
            "التربية العلمية والتكنولوجية"
        ],
        "التاريخ والجغرافيا": [
            "التاريخ و الجغرافيا", "التاريخ والجغرافيا"
        ],
        "التربية البدنية": [
            "ت البدنية والرياضية", "التربية البدنية والرياضية",
            "التربية البدنية"
        ],
    }
    for alias in special.get(subject_name, []):
        if a == normalize_arabic(alias):
            score = max(score, 100)
        elif normalize_arabic(alias) in a:
            score = max(score, 85)

    return score


def scan_uploaded_files(files):
    """
    يفحص جميع ملفات الرقمنة مرة واحدة.
    كل شيت في النماذج الحقيقية يمثل مادة، والوصف في الصفوف
    الأولى يحدد المستوى الدراسي.
    """
    catalog = []

    for file in files:
        try:
            sheets = read_excel_sheets(file)
        except Exception as e:
            catalog.append({
                "file": file.name,
                "sheet": None,
                "level": None,
                "subject": None,
                "error": str(e),
            })
            continue

        for sheet in sheets:
            if normalize_arabic(sheet) == "worksheet":
                continue

            df, err = read_sheet_safe(file, sheet)
            if err or df.empty:
                continue

            level = detect_level_from_sheet(df)
            name_col, id_col = process_names(df)
            gradeable = get_gradeable_columns(df, name_col, id_col)

            catalog.append({
                "file": file.name,
                "file_obj": file,
                "sheet": sheet,
                "level": level,
                "name_col": name_col,
                "id_col": id_col,
                "gradeable": gradeable,
                "rows": len(df),
                "error": err,
            })

    return catalog


def build_mapping_from_catalog(catalog, level, level_subjects):
    mappings = {}
    used = set()

    for cfg in level_subjects:
        subject_name = cfg["name"]

        candidates = []
        for item in catalog:
            if item["level"] != level:
                continue
            score = subject_match_score(item["sheet"], subject_name, level)
            if score:
                candidates.append((score, item))

        candidates.sort(key=lambda x: x[0], reverse=True)

        # منع استعمال نفس الشيت لمادتين.
        chosen = None
        for score, item in candidates:
            key = (item["file"], item["sheet"])
            if key not in used:
                chosen = item
                break

        if not chosen:
            mappings[subject_name] = None
            continue

        item = chosen
        used.add((item["file"], item["sheet"]))

        df, err = read_sheet_safe(item["file_obj"], item["sheet"])
        if err or df.empty:
            mappings[subject_name] = None
            continue

        name_col = item["name_col"]
        id_col = item["id_col"]

        gradeable = get_gradeable_columns(df, name_col, id_col)
        detected_q, detected_t = detect_columns(
            df, cfg["keywords"], gradeable
        )

        # في نماذج الرقمنة الرسمية:
        # العربية/الرياضيات/اللغات: الأعمدة 01/02/04 هي مكونات مستمرة
        # والعمود 09 هو الاختبار.
        # إذا لم يكتشف البحث الكلمات، نستخدم عناوين الصف العربي الذي
        # يحتوي /10، مع استثناء "ملاحظات".
        if not detected_t:
            for col in gradeable:
                n = normalize_arabic(str(col))
                if "اختبار" in n or "امتحان" in n:
                    detected_t.append(col)

        if cfg["type"] == "main" and not detected_q:
            for col in gradeable:
                n = normalize_arabic(str(col))
                if any(x in n for x in [
                    "تعبير", "تواصل", "قراءة", "محفوظات",
                    "انتاج", "كتابة", "املاء", "اعداد",
                    "حساب", "مقادير", "قياس", "معطيات",
                    "فضاء", "هندسة"
                ]):
                    detected_q.append(col)

        # لا نختار عموداً عشوائياً. فقط إذا كان هناك عمود وحيد.
        if not detected_t and len(gradeable) == 1:
            detected_t = [gradeable[0]]

        mappings[subject_name] = {
            "file": item["file"],
            "file_obj": item["file_obj"],
            "sheet": item["sheet"],
            "name_col": name_col,
            "id_col": id_col,
            "quiz_cols": detected_q,
            "test_col": detected_t[0] if detected_t else None,
            "score": candidates[0][0] if candidates else 0,
        }

    return mappings


def calculate_from_real_forms(catalog, level, level_subjects, mappings):
    subject_results = []
    master_parts = []
    logs = []

    for cfg in level_subjects:
        subject_name = cfg["name"]
        mapping = mappings.get(subject_name)

        if not mapping:
            logs.append(
                f"⚠️ {subject_name}: لم يتم العثور على شيت مطابق للمستوى "
                f"{level} ضمن الملفات المرفوعة."
            )
            continue

        df, err = read_sheet_safe(
            mapping["file_obj"], mapping["sheet"]
        )
        if err or df.empty:
            logs.append(f"❌ {subject_name}: {err or 'الشيت فارغ'}")
            continue

        name_col = mapping["name_col"]
        id_col = mapping["id_col"]

        if not name_col or name_col not in df.columns:
            auto_name, auto_id = process_names(df)
            name_col = auto_name
            id_col = id_col if id_col in df.columns else auto_id

        if not name_col:
            logs.append(
                f"❌ {subject_name}: لم يتم اكتشاف الاسم. "
                f"الأعمدة={list(df.columns)}"
            )
            continue

        # إضافة جميع التلاميذ إلى القائمة الرئيسية.
        part, master_err = build_master_from_dataframe(
            df, name_col, id_col
        )
        if not part.empty:
            master_parts.append(part)
        if master_err:
            logs.append(f"⚠️ {subject_name}: {master_err}")

        try:
            sg = calculate_subject(
                df,
                name_col,
                id_col,
                mapping,
                cfg,
            )
            subject_results.append(sg)
            logs.append(
                f"✅ {subject_name}: {len(sg)} تلميذ | "
                f"الشيت: {mapping['sheet']} | "
                f"الملف: {mapping['file']} | "
                f"المستمر: {len(mapping['quiz_cols'])} | "
                f"الاختبار: {mapping['test_col'] or 'غير محدد'}"
            )
        except Exception as e:
            logs.append(f"❌ {subject_name}: {e}")

    if not master_parts:
        return None, [], logs

    master = (
        pd.concat(master_parts, ignore_index=True)
        .drop_duplicates("_key", keep="first")
        .reset_index(drop=True)
    )

    result, subject_cols = build_results(master, subject_results)
    return result, subject_cols, logs


# ============================================================
# الواجهة
# ============================================================
st.markdown("""
<div class="ai-box">
<h1 style="color:white;text-align:center">🏫🤖 النظام الذكي لحساب معدلات التلاميذ</h1>
<p style="text-align:center;font-size:16px">
متوافق مع نماذج الرقمنة Excel الرسمية — الفصل الثاني 2025-2026
</p>
</div>
""", unsafe_allow_html=True)

st.subheader("📚 الخطوة 1: المستوى الدراسي")
selected_level = st.selectbox(
    "🎓 اختر المستوى المراد حساب نتائجه:",
    list(LEVELS.keys()),
)

level_subjects = LEVELS[selected_level]
st.info(
    f"📌 المستوى المحدد: {selected_level} — "
    f"عدد المواد المتوقع: {len(level_subjects)}"
)

st.markdown("---")
st.subheader("📁 الخطوة 2: رفع نماذج الرقمنة Excel")

uploaded_files = st.file_uploader(
    "ارفع جميع ملفات Excel الصادرة من الرقمنة، ويمكن رفع أكثر من ملف:",
    type=["xlsx", "xls"],
    accept_multiple_files=True,
    key="real_digitization_files",
)

if not uploaded_files:
    st.info(
        "مثال: ارفع ملف الأستاذ الذي يحتوي على اللغة العربية والرياضيات، "
        "وملف أستاذ اللغة الإنجليزية، وهكذا. لا يشترط أن يكون ملف واحد لكل مادة."
    )
    st.stop()

st.success(f"✅ تم رفع {len(uploaded_files)} ملف/ملفات.")

with st.spinner("🔎 فحص نماذج الرقمنة واكتشاف المستوى والمواد..."):
    catalog = scan_uploaded_files(uploaded_files)

detected_rows = [
    x for x in catalog
    if x.get("sheet") and not x.get("error")
]

with st.expander("🔍 نتيجة فحص ملفات الرقمنة", expanded=True):
    table = pd.DataFrame([
        {
            "الملف": x["file"],
            "الشيت": x["sheet"],
            "المستوى المكتشف": x["level"] or "غير مكتشف",
            "عمود الاسم": x["name_col"] or "غير مكتشف",
            "رقم التعريف": x["id_col"] or "غير مكتشف",
            "عدد السجلات": x["rows"],
        }
        for x in detected_rows
    ])
    if table.empty:
        st.error("❌ لم يتم التعرف على أي شيت صالح.")
    else:
        st.dataframe(table, use_container_width=True, hide_index=True)

mappings = build_mapping_from_catalog(
    catalog,
    selected_level,
    level_subjects,
)

st.markdown("---")
st.subheader("🔗 الخطوة 3: المواد التي تم اكتشافها")

map_table = []
for cfg in level_subjects:
    m = mappings.get(cfg["name"])
    map_table.append({
        "المادة": cfg["name"],
        "الحالة": "✅ مكتشفة" if m else "❌ غير مكتشفة",
        "الملف": m["file"] if m else "—",
        "الشيت": m["sheet"] if m else "—",
        "الاسم": m["name_col"] if m else "—",
        "Matricule": m["id_col"] if m else "—",
        "فروض/مستمر": ", ".join(map(str, m["quiz_cols"])) if m else "—",
        "الاختبار": str(m["test_col"]) if m and m["test_col"] else "—",
    })

st.dataframe(
    pd.DataFrame(map_table),
    use_container_width=True,
    hide_index=True,
)

missing_subjects = [
    x["المادة"] for x in map_table if x["الحالة"] == "❌ غير مكتشفة"
]
if missing_subjects:
    st.warning(
        "⚠️ مواد لم يتم العثور عليها في الملفات المرفوعة: "
        + "، ".join(missing_subjects)
    )

st.markdown("---")
st.subheader("⚙️ الخطوة 4: بدء الحساب")

if st.button(
    "🚀 بدء الحساب",
    type="primary",
    use_container_width=True,
):
    with st.spinner("⏳ جاري استخراج التلاميذ وحساب النتائج..."):
        result, subject_cols, logs = calculate_from_real_forms(
            catalog,
            selected_level,
            level_subjects,
            mappings,
        )

    with st.expander("📋 سجل المعالجة التفصيلي", expanded=True):
        for log in logs:
            st.write(log)

    if result is None or result.empty:
        st.error(
            "❌ لم يتم العثور على قائمة تلاميذ صالحة. "
            "راجع جدول «نتيجة فحص ملفات الرقمنة» وسجل المعالجة."
        )
        st.stop()

    st.session_state.final_result = result
    st.session_state.subject_cols = subject_cols
    st.session_state.mappings = mappings
    st.session_state.analysis = None
    st.success(
        f"✅ تم الحساب بنجاح — تم العثور على {len(result)} تلميذ."
    )


# ============================================================
# النتائج
# ============================================================
if st.session_state.final_result is not None:
    final_df = st.session_state.final_result
    subject_cols = st.session_state.subject_cols

    st.markdown("---")
    st.subheader("📊 كشف النقاط الإجمالي")

    display_cols = ["الترتيب", "الاسم"] + subject_cols + [
        "عدد المواد", "المجموع", "المعدل الفصلي", "التقدير"
    ]
    display_cols = [
        c for c in display_cols if c in final_df.columns
    ]

    st.dataframe(
        final_df[display_cols],
        use_container_width=True,
        height=600,
    )

    valid_avgs = final_df["المعدل الفصلي"].dropna()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("👥 عدد التلاميذ", len(final_df))
    with c2:
        st.metric(
            "📈 المعدل العام",
            f"{valid_avgs.mean():.2f}" if not valid_avgs.empty else "—",
        )
    with c3:
        st.metric(
            "🏆 أعلى معدل",
            f"{valid_avgs.max():.2f}" if not valid_avgs.empty else "—",
        )
    with c4:
        rate = (valid_avgs >= 5).mean() * 100 if not valid_avgs.empty else 0
        st.metric("✅ نسبة النجاح", f"{rate:.1f}%")

    excel_bytes = export_excel(final_df)
    st.download_button(
        "📥 تحميل النتائج Excel",
        data=excel_bytes,
        file_name=(
            f"نتائج_{selected_level}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

    st.markdown("---")
    st.subheader("📚 متوسطات المواد")

    if subject_cols:
        subject_avg_df = pd.DataFrame({
            "المادة": subject_cols,
            "المعدل": [
                pd.to_numeric(final_df[c], errors="coerce").mean()
                for c in subject_cols
            ],
        })
        subject_avg_df["المعدل"] = subject_avg_df["المعدل"].round(2)
        st.dataframe(
            subject_avg_df.sort_values("المعدل", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    # ========================================================
    # الذكاء الاصطناعي
    # ========================================================
    st.markdown("---")
    st.subheader("🧠 التحليل البيداغوجي بالذكاء الاصطناعي")

    api_key = get_api_key()
    if not api_key:
        st.info(
            "لتفعيل التحليل: أضف MISTRAL_API_KEY إلى "
            ".streamlit/secrets.toml"
        )
    else:
        if st.button("✨ توليد التقرير التحليلي"):
            with st.spinner("🤖 جاري التحليل..."):
                subject_avgs = {
                    c: round(float(final_df[c].mean()), 2)
                    for c in subject_cols
                    if pd.notna(final_df[c].mean())
                }
                valid = final_df["المعدل الفصلي"].dropna()
                class_avg = (
                    round(float(valid.mean()), 2)
                    if not valid.empty else None
                )
                pass_rate = (
                    round(float((valid >= 5).mean() * 100), 1)
                    if not valid.empty else 0
                )

                prompt = f"""
المستوى: {selected_level}
عدد التلاميذ: {len(final_df)}
المعدل العام: {class_avg} / 10
نسبة النجاح: {pass_rate}%

معدلات المواد:
{json.dumps(subject_avgs, ensure_ascii=False, indent=2)}

حلل النتائج تربوياً باللغة العربية:
1. الوضع العام.
2. نقاط القوة.
3. نقاط الضعف.
4. المواد التي تحتاج تدخلاً.
5. توصيات عملية للمعلم.
6. توصيات لمتابعة التلاميذ الضعفاء.
7. خاتمة.

لا تخترع بيانات.
"""
                st.session_state.analysis = call_mistral(
                    api_key, prompt
                )

        if st.session_state.analysis:
            safe = html.escape(st.session_state.analysis)
            st.markdown(
                f'<div class="analysis-box">{safe}</div>',
                unsafe_allow_html=True,
            )

            pdf = generate_pdf(st.session_state.analysis)
            if pdf:
                st.download_button(
                    "📥 تحميل التقرير PDF",
                    data=pdf,
                    file_name=(
                        f"تقرير_{selected_level}_"
                        f"{datetime.now().strftime('%Y%m%d')}.pdf"
                    ),
                    mime="application/pdf",
                    use_container_width=True,
                )

st.caption(
    "النظام مصمم لقراءة نماذج الرقمنة التي تحتوي على بيانات المدرسة "
    "في الصفوف الأولى، ثم صف matricule/nom/prenom ثم صف عناوين العلامات."
)

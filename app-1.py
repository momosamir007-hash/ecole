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
    id_col, nom_col, prenom_col, combined_col = find_name_columns(df)

    if combined_col:
        return combined_col, id_col

    if nom_col and prenom_col:
        new_col = "__الاسم_الكامل__"
        df[new_col] = (
            df[nom_col].fillna("").astype(str).str.strip()
            + " "
            + df[prenom_col].fillna("").astype(str).str.strip()
        ).str.strip()
        return new_col, id_col

    if nom_col:
        return nom_col, id_col

    if prenom_col:
        return prenom_col, id_col

    # بحث احتياطي في الأعمدة النصية
    ignored = [
        "رقم", "ملاحظ", "تاريخ", "قرار", "ترتيب", "معدل",
        "مجموع", "matricule", "id", "date", "obs", "rang"
    ]
    for col in df.columns:
        if df[col].dtype == object and df[col].notna().sum() > 0:
            norm = normalize_arabic(str(col))
            if not any(k in norm for k in ignored):
                return col, id_col

    return None, id_col


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
# الواجهة
# ============================================================
st.markdown("""
<div class="ai-box">
<h1 style="color:white;text-align:center">🏫🤖 النظام الذكي لحساب معدلات التلاميذ</h1>
<p style="text-align:center;font-size:16px">
نسخة موحدة ومصححة — قراءة Excel + مطابقة التلاميذ + حساب المعدلات + تحليل بيداغوجي
</p>
</div>
""", unsafe_allow_html=True)

st.subheader("📚 الخطوة 1: المستوى الدراسي")
levels = list(LEVELS.keys())
selected_level = st.selectbox("🎓 اختر المستوى:", levels)
level_subjects = LEVELS[selected_level]

st.info(f"عدد المواد المبرمجة لهذا المستوى: {len(level_subjects)}")

teacher_groups = {}
for s in level_subjects:
    teacher_groups.setdefault(s["teacher"], []).append(s["name"])

for teacher, subjects in teacher_groups.items():
    st.markdown(f"**👨‍🏫 {teacher}:** " + " — ".join(subjects))

st.markdown("---")
st.subheader("📁 الخطوة 2: رفع ملفات الأساتذة")

teachers = list(teacher_groups.keys())
uploaded_files = {}

upload_cols = st.columns(min(4, max(1, len(teachers))))
for i, teacher in enumerate(teachers):
    with upload_cols[i % len(upload_cols)]:
        f = st.file_uploader(
            f"📄 {teacher}",
            type=["xlsx", "xls"],
            key=f"upload_{selected_level}_{teacher}",
        )
        if f is not None:
            uploaded_files[teacher] = f

missing = [t for t in teachers if t not in uploaded_files]
if missing:
    st.warning("⏳ الملفات المطلوبة: " + " ، ".join(missing))
    st.stop()

st.success("✅ تم رفع جميع الملفات.")

# ============================================================
# إعداد المادت
# ============================================================
st.markdown("---")
st.subheader("🔗 الخطوة 3: ربط الشيتات والأعمدة")

mappings = {}
all_preview_issues = []

for teacher, subject_names in teacher_groups.items():
    st.markdown(f"### 👨‍🏫 {teacher}")
    file = uploaded_files[teacher]

    try:
        sheets = read_excel_sheets(file)
    except Exception as e:
        st.error(f"تعذر قراءة ملف {teacher}: {e}")
        continue

    if not sheets:
        st.error("الملف لا يحتوي على أوراق.")
        continue

    for subject_name in subject_names:
        cfg = next(x for x in level_subjects if x["name"] == subject_name)

        st.markdown(f"#### 📘 {subject_name}")

        suggested = choose_sheet(sheets, selected_level, subject_name)
        sheet = st.selectbox(
            "الشيت:",
            sheets,
            index=suggested,
            key=f"sheet_{selected_level}_{teacher}_{subject_name}",
        )

        df, err = read_sheet_safe(file, sheet)
        if err:
            st.error(err)
            mappings[(teacher, subject_name)] = {
                "sheet": sheet, "quiz_cols": [], "test_col": None
            }
            continue

        name_col, id_col = process_names(df)
        gradeable = get_gradeable_columns(df, name_col, id_col)
        detected_q, detected_t = detect_columns(
            df, cfg["keywords"], gradeable
        )

        if name_col is None:
            st.error("❌ لم يتم اكتشاف عمود الأسماء في هذا الشيت.")

        name_options = ["— غير مكتشف —"] + list(df.columns)
        name_default = (
            name_options.index(name_col) if name_col in name_options else 0
        )
        selected_name = st.selectbox(
            "👤 عمود الاسم:",
            name_options,
            index=name_default,
            key=f"name_{selected_level}_{teacher}_{subject_name}",
        )
        selected_name = None if selected_name == "— غير مكتشف —" else selected_name

        id_options = ["— بدون رقم تعريف —"] + list(df.columns)
        id_default = (
            id_options.index(id_col) if id_col in id_options else 0
        )
        selected_id = st.selectbox(
            "🆔 عمود رقم التعريف/Matricule (اختياري):",
            id_options,
            index=id_default,
            key=f"id_{selected_level}_{teacher}_{subject_name}",
        )
        selected_id = None if selected_id == "— بدون رقم تعريف —" else selected_id

        valid_gradeable = get_gradeable_columns(
            df, selected_name, selected_id
        )

        c1, c2 = st.columns(2)

        with c1:
            if cfg["type"] == "main" and cfg["keywords"]["quizzes"]:
                defaults_q = [x for x in detected_q if x in valid_gradeable]
                selected_q = st.multiselect(
                    "🧪 أعمدة الفروض المستمرة:",
                    valid_gradeable,
                    default=defaults_q,
                    key=f"q_{selected_level}_{teacher}_{subject_name}",
                )
            else:
                selected_q = []

        with c2:
            test_options = ["— بدون —"] + valid_gradeable
            detected_test = next(
                (x for x in detected_t if x in valid_gradeable), None
            )
            test_default = (
                test_options.index(detected_test)
                if detected_test in test_options else 0
            )
            selected_test = st.selectbox(
                "📝 عمود الاختبار/النقطة النهائية:",
                test_options,
                index=test_default,
                key=f"test_{selected_level}_{teacher}_{subject_name}",
            )
            selected_test = (
                None if selected_test == "— بدون —" else selected_test
            )

        issues = validation_report(
            df, selected_name, selected_id, valid_gradeable
        )
        if issues:
            with st.expander("⚠️ ملاحظات التحقق", expanded=False):
                for issue in issues:
                    st.write("• " + issue)
                    all_preview_issues.append(
                        f"{teacher} / {subject_name}: {issue}"
                    )

        mappings[(teacher, subject_name)] = {
            "sheet": sheet,
            "name_col": selected_name,
            "id_col": selected_id,
            "quiz_cols": selected_q,
            "test_col": selected_test,
        }

        with st.expander("👁️ معاينة البيانات"):
            st.dataframe(df.head(8), use_container_width=True)

# ============================================================
# الحساب
# ============================================================
st.markdown("---")
st.subheader("⚙️ الخطوة 4: الدمج والحساب")

if st.button("🚀 بدء الحساب", type="primary", use_container_width=True):

    with st.spinner("جاري قراءة الملفات وحساب النتائج..."):
        subject_results = []
        master = None
        logs = []

        for cfg in level_subjects:
            subject_name = cfg["name"]
            teacher = cfg["teacher"]
            mapping = mappings.get((teacher, subject_name))

            if not mapping:
                logs.append(f"❌ {subject_name}: لا توجد إعدادات.")
                continue

            df, err = read_sheet_safe(
                uploaded_files[teacher], mapping["sheet"]
            )

            if err or df.empty:
                logs.append(f"❌ {subject_name}: {err or 'فارغة'}")
                continue

            name_col = mapping["name_col"]
            id_col = mapping["id_col"]

            if not name_col or name_col not in df.columns:
                logs.append(f"❌ {subject_name}: عمود الاسم غير صالح.")
                continue

            # إنشاء قائمة التلاميذ الرئيسية من أول ملف صالح.
            if master is None:
                temp = df.copy()
                if id_col and id_col in temp.columns:
                    temp["_key"] = temp[id_col].apply(normalize_identifier)
                    fallback = temp[name_col].apply(normalize_arabic)
                    temp.loc[temp["_key"] == "", "_key"] = fallback[
                        temp["_key"] == ""
                    ]
                else:
                    temp["_key"] = temp[name_col].apply(normalize_arabic)

                temp["الاسم"] = temp[name_col].astype(str).str.strip()
                temp = temp[temp["_key"] != ""]
                master = (
                    temp[["_key", "الاسم"]]
                    .drop_duplicates("_key")
                    .reset_index(drop=True)
                )

            try:
                sg = calculate_subject(df, name_col, id_col, mapping, cfg)
                subject_results.append(sg)
                logs.append(
                    f"✅ {subject_name}: تم الحساب "
                    f"(فروض: {len(mapping['quiz_cols'])}, "
                    f"اختبار: {'نعم' if mapping['test_col'] else 'لا'})."
                )
            except Exception as e:
                logs.append(f"❌ {subject_name}: {e}")

        if master is None or master.empty:
            st.error("❌ لم يتم العثور على قائمة تلاميذ صالحة.")
            st.stop()

        result, subject_cols = build_results(master, subject_results)

        st.session_state.final_result = result
        st.session_state.subject_cols = subject_cols
        st.session_state.mappings = mappings
        st.session_state.analysis = None

    with st.expander("📋 سجل المعالجة", expanded=True):
        for log in logs:
            st.write(log)

    st.success("✅ اكتمل الحساب بنجاح.")


# ============================================================
# النتائج
# ============================================================
if st.session_state.final_result is not None:
    final_df = st.session_state.final_result
    subject_cols = st.session_state.subject_cols

    st.markdown("---")
    st.subheader("📊 كشف النقاط الإجمالي")

    display_cols = [
        "الترتيب", "الاسم"
    ] + subject_cols + [
        "عدد المواد", "المجموع", "المعدل الفصلي", "التقدير"
    ]
    display_cols = [c for c in display_cols if c in final_df.columns]

    st.dataframe(
        final_df[display_cols],
        use_container_width=True,
        height=520,
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
        pass_rate = (
            (valid_avgs >= 5).mean() * 100
            if not valid_avgs.empty else 0
        )
        st.metric("✅ نسبة النجاح", f"{pass_rate:.1f}%")

    excel_bytes = export_excel(final_df)
    st.download_button(
        "📥 تحميل النتائج Excel",
        data=excel_bytes,
        file_name=(
            f"النتائج_{selected_level}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

    # ========================================================
    # تحليل المادة
    # ========================================================
    st.markdown("---")
    st.subheader("📚 تحليل المواد")

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
    st.subheader("🧠 الخطوة 5: التحليل البيداغوجي بالذكاء الاصطناعي")

    api_key = get_api_key()

    if not api_key:
        st.info(
            "للتفعيل أضف MISTRAL_API_KEY إلى "
            ".streamlit/secrets.toml"
        )
    else:
        if st.button("✨ توليد التقرير التحليلي", type="secondary"):
            with st.spinner("🤖 Mistral يقوم بتحليل النتائج..."):
                subject_avgs = {
                    c: round(float(final_df[c].mean()), 2)
                    for c in subject_cols
                    if pd.notna(final_df[c].mean())
                }
                valid = final_df["المعدل الفصلي"].dropna()
                class_avg = round(float(valid.mean()), 2) if not valid.empty else None
                pass_rate = (
                    round(float((valid >= 5).mean() * 100), 1)
                    if not valid.empty else 0
                )
                distribution = final_df["التقدير"].value_counts().to_dict()

                prompt = f"""
المستوى الدراسي: {selected_level}
عدد التلاميذ: {len(final_df)}
المعدل العام للقسم: {class_avg} / 10
نسبة النجاح: {pass_rate}%

معدلات المواد:
{json.dumps(subject_avgs, ensure_ascii=False, indent=2)}

توزيع التقديرات:
{json.dumps(distribution, ensure_ascii=False, indent=2)}

أكتب تقريراً بيداغوجياً باللغة العربية يتضمن:
1. قراءة عامة للنتائج.
2. نقاط القوة.
3. نقاط الضعف.
4. المواد التي تستحق تدخلاً.
5. ثلاث توصيات عملية قابلة للتطبيق.
6. خاتمة قصيرة.

لا تخترع أسماء تلاميذ أو بيانات غير موجودة.
لا تستخدم Markdown أو جداول.
"""
                analysis = call_mistral(api_key, prompt)
                st.session_state.analysis = analysis

        if st.session_state.analysis:
            # escape لمنع HTML غير موثوق من AI
            safe_analysis = html.escape(st.session_state.analysis)
            st.markdown(
                f'<div class="analysis-box">{safe_analysis}</div>',
                unsafe_allow_html=True,
            )

            pdf = generate_pdf(st.session_state.analysis)
            if pdf:
                st.download_button(
                    "📥 تحميل التقرير PDF",
                    data=pdf,
                    file_name=(
                        f"تقرير_تحليلي_{selected_level}_"
                        f"{datetime.now().strftime('%Y%m%d')}.pdf"
                    ),
                    mime="application/pdf",
                    use_container_width=True,
                )

st.caption(
    "ملاحظة: النظام يحافظ على التلاميذ حتى عند نقص بعض العلامات، "
    "ولا يحسب الغياب كصفر."
)

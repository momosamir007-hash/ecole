
import streamlit as st
import pandas as pd
import numpy as np
import io
import re
import requests
import json
from datetime import datetime
import textwrap
import zipfile
import os
from collections import Counter

# ══════════════════════════════════════════════════════════════
# إعدادات الصفحة
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="نظام حساب المعدلات v2.0 — الابتدائي الجزائري",
    layout="wide",
    page_icon="🏫"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
.main .block-container {direction: rtl; text-align: right; font-family: 'Cairo', sans-serif;}
h1,h2,h3,h4,p,li,span,label,td,th {direction: rtl; text-align: right;}
.stMetric {direction: ltr;}
.ai-box { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); border-radius: 15px; padding: 20px; margin: 15px 0; color: white; box-shadow: 0 8px 32px rgba(17,153,142,0.3); }
.analysis-box { background: #f8f9fa; border-radius: 10px; padding: 20px; border-right: 5px solid #6c5ce7; margin-top: 15px; direction: rtl; line-height: 2;}
.fix-badge { background: #d4edda; color: #155724; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# مفاتيح مزودي الذكاء الاصطناعي
# ══════════════════════════════════════════════════════════════
def get_secret(name):
    """الحصول الآمن على مفتاح من Streamlit Secrets"""
    try:
        return st.secrets[name]
    except Exception:
        return None

MISTRAL_API_KEY = get_secret("MISTRAL_API_KEY")
OPENROUTER_API_KEY = get_secret("OPENROUTER_API_KEY")

st.markdown("""
<div class="ai-box">
    <h1 style="color:white; text-align:center;">🏫🤖 النظام الذكي لحساب معدلات التلاميذ</h1>
    <p style="text-align:center; font-size:16px;"> متوافق كلياً مع مستخرجات الأرضية الرقمية (الرقمنة) | مدعوم بالتحليل البيداغوجي الذكي متعدد المزودين </p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# تعريف المواد الدراسية لكل مستوى
# ══════════════════════════════════════════════════════════════
LEVELS = {
    "السنة الأولى": {
        "total_subjects": 6,
        "subjects": [
            {"name": "اللغة العربية", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج"]}},
            {"name": "الرياضيات", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["أعداد", "حساب", "مقادير", "قياس", "معطيات", "فضاء", "هندسة"]}},
            {"name": "التربية الإسلامية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية الموسيقية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية التشكيلية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية البدنية", "type": "secondary", "teacher": "أستاذ التربية البدنية", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}}
        ]
    },
    "السنة الثانية": {
        "total_subjects": 6,
        "subjects": [
            {"name": "اللغة العربية", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج"]}},
            {"name": "الرياضيات", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["أعداد", "حساب", "مقادير", "قياس", "معطيات", "فضاء", "هندسة"]}},
            {"name": "التربية الإسلامية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية الموسيقية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية التشكيلية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية البدنية", "type": "secondary", "teacher": "أستاذ التربية البدنية", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}}
        ]
    },
    "السنة الثالثة": {
        "total_subjects": 10,
        "subjects": [
            {"name": "اللغة العربية", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج"]}},
            {"name": "الرياضيات", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["أعداد", "حساب", "مقادير", "قياس", "معطيات", "فضاء", "هندسة"]}},
            {"name": "اللغة الفرنسية", "type": "main", "teacher": "أستاذ اللغة الفرنسية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج", "فهم"]}},
            {"name": "اللغة الإنجليزية", "type": "main", "teacher": "أستاذ اللغة الإنجليزية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج", "فهم"]}},
            {"name": "التربية الإسلامية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية العلمية والتكنولوجية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التاريخ", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية التشكيلية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية الموسيقية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية البدنية", "type": "secondary", "teacher": "أستاذ التربية البدنية", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}}
        ]
    },
    "السنة الرابعة": {
        "total_subjects": 11,
        "subjects": [
            {"name": "اللغة العربية", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج"]}},
            {"name": "الرياضيات", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["أعداد", "حساب", "مقادير", "قياس", "معطيات", "فضاء", "هندسة"]}},
            {"name": "اللغة الفرنسية", "type": "main", "teacher": "أستاذ اللغة الفرنسية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج", "فهم"]}},
            {"name": "اللغة الإنجليزية", "type": "main", "teacher": "أستاذ اللغة الإنجليزية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج", "فهم"]}},
            {"name": "التربية الإسلامية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية العلمية والتكنولوجية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية المدنية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التاريخ والجغرافيا", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية التشكيلية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية الموسيقية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية البدنية", "type": "secondary", "teacher": "أستاذ التربية البدنية", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}}
        ]
    },
    "السنة الخامسة": {
        "total_subjects": 11,
        "subjects": [
            {"name": "اللغة العربية", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج"]}},
            {"name": "الرياضيات", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["أعداد", "حساب", "مقادير", "قياس", "معطيات", "فضاء", "هندسة"]}},
            {"name": "اللغة الفرنسية", "type": "main", "teacher": "أستاذ اللغة الفرنسية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج", "فهم"]}},
            {"name": "اللغة الإنجليزية", "type": "main", "teacher": "أستاذ اللغة الإنجليزية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج", "فهم"]}},
            {"name": "التربية الإسلامية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية العلمية والتكنولوجية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية المدنية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التاريخ والجغرافيا", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية التشكيلية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية الموسيقية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "التربية البدنية", "type": "secondary", "teacher": "أستاذ التربية البدنية", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}}
        ]
    }
}

# ══════════════════════════════════════════════════════════════
# الدوال المساعدة
# ══════════════════════════════════════════════════════════════
def normalize_arabic(text):
    if pd.isna(text): return ""
    text = str(text).strip()
    text = re.sub(r'\s+', ' ', text)
    for old, new in [('أ', 'ا'), ('إ', 'ا'), ('آ', 'ا'), ('ة', 'ه'), ('ى', 'ي'), ('ئ', 'ي'), ('ؤ', 'و')]:
        text = text.replace(old, new)
    return text

def get_expected_sheet_name(level, subject_name):
    mapping = {
        "التربية البدنية": {
            "السنة الأولى": "ت البدنية والرياضية",
            "السنة الثانية": "ت البدنية والرياضية 1",
            "السنة الثالثة": "ت البدنية والرياضية 2",
            "السنة الرابعة": "ت البدنية والرياضية 3",
            "السنة الخامسة": "ت البدنية والرياضية 4"
        },
        "اللغة الفرنسية": {
            "السنة الثالثة": "اللغة الفرنسية",
            "السنة الرابعة": "اللغة الفرنسية 1",
            "السنة الخامسة": "اللغة الفرنسية 2"
        },
        "اللغة الإنجليزية": {
            "السنة الثالثة": "اللغة الإنجليزية",
            "السنة الرابعة": "اللغة الإنجليزية 1",
            "السنة الخامسة": "اللغة الإنجليزية 2"
        },
        "التربية العلمية والتكنولوجية": {
            "السنة الثالثة": "ت العلمية و التكنولوجية",
            "السنة الرابعة": "ت العلمية و التكنولوجية",
            "السنة الخامسة": "ت العلمية و التكنولوجية"
        },
        "التاريخ والجغرافيا": {
            "السنة الرابعة": "التاريخ و الجغرافيا",
            "السنة الخامسة": "التاريخ و الجغرافيا"
        }
    }
    return mapping.get(subject_name, {}).get(level, subject_name)

def find_student_id_column(df):
    candidates = ['matricule', 'رقم التعريف', 'رقم_التعريف', 'رقم التسجيل', 'id']
    for col in df.columns:
        norm = normalize_arabic(str(col)).lower()
        if any(normalize_arabic(c).lower() in norm for c in candidates):
            values = df[col].astype(str).str.strip()
            if values.replace({'nan': np.nan, '': np.nan}).notna().sum() > 0:
                return col
    return None

def process_names(df):
    nom_col, prenom_col, combined_col = None, None, None
    for col in df.columns:
        c_str = str(col).strip()
        c_norm = normalize_arabic(c_str)
        if any(kw in c_norm for kw in ['لقب والاسم', 'اسم واللقب', 'اسم ولقب', 'لقب واسم', 'التلميذ', 'الطالب']):
            combined_col = col
        elif c_norm in ['اللقب', 'لقب'] or c_str.lower() == 'nom':
            nom_col = col
        elif c_norm in ['الاسم', 'اسم'] or c_str.lower() in ['prenom', 'prénom']:
            prenom_col = col

    if combined_col:
        return combined_col
    if nom_col and prenom_col:
        df['الاسم_الكامل'] = (df[nom_col].astype(str).str.strip() + " " + df[prenom_col].astype(str).str.strip())
        return 'الاسم_الكامل'
    if nom_col:
        return nom_col
    if prenom_col:
        return prenom_col

    skip_kw = ['رقم', 'ملاحظ', 'تاريخ', 'قرار', 'ترتيب', 'معدل', 'مجموع', '#', 'num', 'id']
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].notna().sum() > 0:
            if not any(kw in normalize_arabic(str(col)) for kw in skip_kw):
                return col
    return None

def clean_grade_value(val):
    if pd.isna(val): return np.nan
    s = str(val).strip()
    if any(kw in s for kw in ['غائب', 'غياب', 'معفى', 'معفي', 'مريض']):
        return np.nan
    if s in ['/', '-', '', '.', '*', 'x', 'X']:
        return np.nan
    s = s.replace(',', '.')
    match = re.search(r'(\d+\.?\d*)', s)
    if match:
        try:
            v = float(match.group(1))
            return v if v <= 20 else np.nan
        except ValueError:
            return np.nan
    return np.nan

def is_final_assessment_column(column_name):
    c = normalize_arabic(str(column_name)).lower()
    aliases = [
        'اختبار', 'امتحان', 'تقويم مستمر', 'معدل التقويم المستمر',
        'المعدل التقويمي', 'معدل التقويم', 'النقطة النهائية',
        'التقييم النهائي', 'تقويم نهائي'
    ]
    return any(normalize_arabic(alias) in c for alias in aliases)

def get_gradeable_columns(df, name_col=None):
    ignore_patterns = ['رقم', 'matricule', 'تاريخ', 'date', 'لقب', 'اسم', 'nom', 'prenom', 'obs', 'ملاحظ', 'قرار', 'ترتيب', 'مجموع', 'عدد']
    result = []
    for col in df.columns:
        if col == name_col:
            continue
        col_norm = normalize_arabic(str(col)).lower()
        if any(ign in col_norm for ign in ignore_patterns):
            continue
        if 'معدل' in col_norm and not is_final_assessment_column(col):
            continue
        cleaned = df[col].apply(clean_grade_value)
        valid_count = cleaned.notna().sum()
        if valid_count >= max(1, len(df) * 0.1):
            result.append(col)
    return result

def detect_subject_columns(df, subject_keywords, gradeable_cols):
    quiz_cols = []
    test_candidates = []
    for col in gradeable_cols:
        col_norm = normalize_arabic(str(col))
        if is_final_assessment_column(col):
            test_candidates.append(col)
            continue
        is_test = any(normalize_arabic(kw) in col_norm for kw in subject_keywords.get('tests', []))
        is_quiz = any(normalize_arabic(kw) in col_norm for kw in subject_keywords.get('quizzes', []))
        if is_test:
            test_candidates.append(col)
        elif is_quiz:
            quiz_cols.append(col)
    def priority(col):
        c = normalize_arabic(str(col))
        if 'معدل التقويم المستمر' in c: return 0
        if 'النقطه النهائيه' in c: return 1
        if 'اختبار' in c or 'امتحان' in c: return 2
        if 'تقويم' in c: return 3
        return 9
    test_col = sorted(test_candidates, key=priority)[0] if test_candidates else None
    return quiz_cols, test_col

def mapping_confidence(subject, quiz_cols, test_col, gradeable_cols):
    score = 0
    reasons = []
    if test_col:
        score += 55
        reasons.append(f"تم العثور على النقطة النهائية: {test_col}")
    else:
        reasons.append("لم يتم التعرف على النقطة النهائية تلقائياً")
    if subject['type'] == 'main':
        if quiz_cols:
            score += min(35, 10 * len(quiz_cols))
            reasons.append(f"تم العثور على {len(quiz_cols)} أعمدة تقييم مستمر")
        elif gradeable_cols:
            score += 10
            reasons.append("تم العثور على أعمدة نقاط لكن دون تطابق قوي مع المهارات")
    else:
        score += 25 if test_col else 0
    score += 10 if gradeable_cols else 0
    return min(score, 100), reasons

def make_descriptive_headers(raw, header_idx):
    current = raw.iloc[header_idx].fillna('').astype(str).tolist()
    previous = raw.iloc[header_idx - 1].fillna('').astype(str).tolist() if header_idx > 0 else [''] * len(current)
    generic_counter = 0
    headers = []
    for idx, value in enumerate(current):
        value = re.sub(r'\s+', ' ', str(value)).strip()
        prev = re.sub(r'\s+', ' ', str(previous[idx])).strip() if idx < len(previous) else ''
        is_numeric_header = bool(re.fullmatch(r'\d+(?:\.0+)?', value)) or value.lower().startswith('unnamed') or not value
        if is_numeric_header:
            if prev and not re.fullmatch(r'\d+(?:\.0+)?', prev):
                value = prev
            else:
                generic_counter += 1
                value = f'تقييم {generic_counter}'
        headers.append(value)
    seen, result = {}, []
    for idx, value in enumerate(headers):
        seen[value] = seen.get(value, 0) + 1
        result.append(value if seen[value] == 1 else f'{value} ({seen[value]})')
    return result

def read_sheet_safe(file, sheet_name):
    try:
        file.seek(0)
        raw = pd.read_excel(file, sheet_name=sheet_name, header=None, dtype=object)
    except Exception as e:
        st.error(f"❌ خطأ في قراءة الورقة «{sheet_name}»: {e}")
        return pd.DataFrame()

    header_idx = None
    best_score = -1
    header_tokens = ['matricule', 'nom', 'prenom', 'لقب', 'الاسم', 'اسم', 'رقم التعريف']
    for i, row in raw.head(25).iterrows():
        cells = [normalize_arabic(str(v)).lower() for v in row.dropna().tolist()]
        score = sum(any(token in cell for cell in cells) for token in header_tokens)
        if score > best_score:
            best_score, header_idx = score, i

    if best_score < 2:
        st.warning(f"⚠️ لم يتم التعرف بثقة على صف العناوين في «{sheet_name}». سيتم استخدام أول صف.")
        header_idx = 0

    clean_headers = make_descriptive_headers(raw, header_idx)

    df = raw.iloc[header_idx + 1:].copy()
    df.columns = clean_headers
    df = df.dropna(how='all').reset_index(drop=True)

    name_col = process_names(df)
    if name_col is not None:
        key = df[name_col].astype(str).str.strip().str.lower()
        df = df[~key.isin(['nan', 'none', 'الاسم', 'اللقب'])].copy()

    return df.reset_index(drop=True)

@st.cache_data(show_spinner=False)
def _sheet_names_from_bytes(file_bytes):
    return pd.ExcelFile(io.BytesIO(file_bytes)).sheet_names

def get_sheet_names(file):
    file.seek(0)
    return _sheet_names_from_bytes(file.getvalue())

def classify_student(avg):
    if pd.isna(avg): return "—"
    if avg >= 9: return "ممتاز 🌟"
    if avg >= 8: return "جيد جداً ✅"
    if avg >= 7: return "جيد 👍"
    if avg >= 5: return "مقبول 📗"
    if avg >= 3.5: return "ضعيف ⚠️"
    return "ضعيف جداً ❌"

# ══════════════════════════════════════════════════════════════
# دوال الذكاء الاصطناعي (Mistral و OpenRouter والتحليل المحلي)
# ══════════════════════════════════════════════════════════════
def call_mistral_api(api_key, prompt, model="mistral-small-latest"):
    """ الاتصال بـ Mistral AI """
    if not api_key:
        return {
            "success": False,
            "provider": "Mistral",
            "error": "مفتاح Mistral غير موجود"
        }
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "أنت خبير تربوي جزائري متخصص في تحليل "
                    "نتائج تلاميذ التعليم الابتدائي. "
                    "أجب باللغة العربية الواضحة."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 2000
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {
                "success": True,
                "provider": "Mistral",
                "model": model,
                "content": content
            }
        return {
            "success": False,
            "provider": "Mistral",
            "status_code": response.status_code,
            "error": response.text
        }
    except Exception as e:
        return {
            "success": False,
            "provider": "Mistral",
            "error": str(e)
        }

def call_openrouter_api(api_key, prompt, model="openrouter/auto"):
    """ الاتصال بـ OpenRouter """
    if not api_key:
        return {
            "success": False,
            "provider": "OpenRouter",
            "error": "مفتاح OpenRouter غير موجود"
        }
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": "نظام حساب معدلات التلاميذ"
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "أنت خبير تربوي جزائري متخصص في "
                    "تحليل نتائج التعليم الابتدائي. "
                    "اكتب باللغة العربية الواضحة."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 2000
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {
                "success": True,
                "provider": "OpenRouter",
                "model": model,
                "content": content
            }
        return {
            "success": False,
            "provider": "OpenRouter",
            "status_code": response.status_code,
            "error": response.text
        }
    except Exception as e:
        return {
            "success": False,
            "provider": "OpenRouter",
            "error": str(e)
        }

def analyze_with_ai(prompt, provider, model, mistral_key=None, openrouter_key=None):
    """ بوابة موحدة لجميع مزودي الذكاء الاصطناعي """
    if provider == "Mistral":
        return call_mistral_api(api_key=mistral_key, prompt=prompt, model=model)
    elif provider == "OpenRouter":
        return call_openrouter_api(api_key=openrouter_key, prompt=prompt, model=model)
    return {
        "success": False,
        "provider": provider,
        "error": "مزود غير معروف"
    }

def auto_ai_analysis(prompt, mistral_key=None, openrouter_key=None):
    """ نظام التحليل التلقائي: ينتقل للمزود التالي عند الفشل """
    errors = []
    
    # المحاولة الأولى: OpenRouter
    if openrouter_key:
        result = call_openrouter_api(api_key=openrouter_key, prompt=prompt, model="openrouter/auto")
        if result["success"]:
            return result
        errors.append(f"OpenRouter: {result.get('error')}")
        
    # المحاولة الثانية: Mistral
    if mistral_key:
        result = call_mistral_api(api_key=mistral_key, prompt=prompt, model="mistral-small-latest")
        if result["success"]:
            return result
        errors.append(f"Mistral: {result.get('error')}")
        
    # فشل جميع الخدمات
    return {
        "success": False,
        "provider": "Local",
        "error": "\n".join(errors)
    }

def generate_local_pedagogical_report(selected_level, final_df, subject_cols):
    """تقرير بيداغوجي محلي يعمل بدون إنترنت أو API."""
    valid_avgs = final_df['المعدل الفصلي'].dropna()
    class_avg = float(valid_avgs.mean()) if not valid_avgs.empty else 0.0
    pass_rate = float((final_df['المعدل الفصلي'] >= 5).mean() * 100) if len(final_df) else 0.0
    student_count = len(final_df)
    needs_support = int((final_df['المعدل الفصلي'] < 5).sum())
    very_low = int((final_df['المعدل الفصلي'] < 3.5).sum())
    subject_avgs = final_df[subject_cols].mean().dropna().sort_values(ascending=False)
    strongest = subject_avgs.head(3)
    weakest = subject_avgs.tail(min(3, len(subject_avgs))).sort_values()

    if class_avg >= 9:
        overall = 'ممتاز، ويعكس تحكماً جيداً في أغلب التعلمات الأساسية.'
    elif class_avg >= 8:
        overall = 'جيد جداً، مع وجود فرصة لتعزيز بعض جوانب التعلم.'
    elif class_avg >= 7:
        overall = 'جيد بصفة عامة، مع الحاجة إلى متابعة الفوارق الفردية.'
    elif class_avg >= 5:
        overall = 'مقبول، لكنه يحتاج إلى تدخلات بيداغوجية مركزة لرفع الأداء.'
    else:
        overall = 'دون المستوى المأمول ويحتاج إلى خطة دعم ومتابعة منتظمة.'

    lines = [
        f'التقرير البيداغوجي المحلي — {selected_level}',
        '',
        '1. القراءة العامة للنتائج',
        f'بلغ عدد التلاميذ {student_count}، بينما بلغ المعدل العام للقسم {class_avg:.2f} من 10، ونسبة النجاح {pass_rate:.1f}%. المستوى العام {overall}',
        '',
        '2. نقاط القوة',
    ]
    if len(strongest):
        for name, value in strongest.items():
            lines.append(f'- {name}: متوسط {value:.2f}/10.')
    else:
        lines.append('- لا توجد بيانات كافية لاستخراج نقاط القوة حسب المواد.')

    lines += ['', '3. جوانب تحتاج إلى تحسين']
    if len(weakest):
        for name, value in weakest.items():
            lines.append(f'- {name}: متوسط {value:.2f}/10، ويستحسن إعطاء هذه المادة أولوية في الدعم.')
    else:
        lines.append('- لا توجد بيانات كافية لاستخراج المواد التي تحتاج إلى دعم.')

    lines += [
        '', '4. متابعة التلاميذ',
        f'- عدد التلاميذ الذين تقل معدلاتهم عن 5/10: {needs_support}.',
        f'- عدد التلاميذ الذين تقل معدلاتهم عن 3.5/10: {very_low}.',
        '', '5. توصيات بيداغوجية عملية',
        '- إعداد مجموعات دعم صغيرة حسب الصعوبات المشتركة، مع أنشطة قصيرة ومحددة الأهداف.',
        '- تخصيص تقويمات تشخيصية في المواد ذات المتوسطات الأضعف لتحديد المهارات التي تحتاج إلى معالجة.',
        '- متابعة التلاميذ الأكثر حاجة إلى الدعم فردياً وتسجيل تطور نتائجهم في التقويمات اللاحقة.',
        '', 'ملاحظة: هذا التقرير تم إنشاؤه محلياً اعتماداً على الأرقام الفعلية للنتائج، دون استخدام خدمة ذكاء اصطناعي خارجية.'
    ]
    return '\n'.join(lines)

def generate_arabic_pdf(text, font_path="arial.ttf"):
    import os
    import urllib.request

    if not os.path.exists(font_path):
        try:
            font_url = "https://github.com/matomo-org/travis-scripts/raw/master/fonts/Arial.ttf"
            urllib.request.urlretrieve(font_url, font_path)
        except Exception as e:
            st.error(f"❌ لم يتم العثور على الخط ولم نتمكن من تحميله تلقائياً: {e}")
            return None

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase import pdfmetrics
        import arabic_reshaper
        from bidi.algorithm import get_display

        pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        
        styles = getSampleStyleSheet()
        arabic_style = ParagraphStyle(
            'Arabic',
            parent=styles['Normal'],
            fontName='ArabicFont',
            fontSize=12,
            leading=18,
            alignment=2,
        )
        
        story = []
        
        paragraphs = text.split('\n')
        for para in paragraphs:
            if para.strip() == '':
                story.append(Spacer(1, 10))
                continue
            
            wrapped_lines = textwrap.wrap(para, width=75)
            for line in wrapped_lines:
                reshaped = arabic_reshaper.reshape(line)
                bidi_text = get_display(reshaped)
                p = Paragraph(bidi_text, arabic_style)
                story.append(p)
            story.append(Spacer(1, 6))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        st.error("❌ لإنشاء PDF بالعربية، يرجى تثبيت المكتبات: `pip install reportlab arabic-reshaper python-bidi`")
        return None
    except Exception as e:
        st.error(f"❌ خطأ أثناء بناء ملف PDF: {e}")
        return None

# ══════════════════════════════════════════════════════════════
# التطبيق الرئيسي (حالة الجلسة والواجهة)
# ══════════════════════════════════════════════════════════════
for key, default in [('subject_mappings', {}), ('final_result', None), ('selected_level', list(LEVELS.keys())[0]), ('subject_cols', []), ('validation_report', None), ('auto_mapping_summary', [])]:
    if key not in st.session_state:
        st.session_state[key] = default

st.subheader("📚 الخطوة 1: اختر المستوى الدراسي")
selected_level = st.selectbox(
    "🎓 المستوى:", list(LEVELS.keys()), index=list(LEVELS.keys()).index(st.session_state.selected_level)
)
st.session_state.selected_level = selected_level
level_config = LEVELS[selected_level]

st.markdown(f"#### 📋 مواد {selected_level} ({level_config['total_subjects']} مادة)")
teachers_list = {}
for subject in level_config['subjects']:
    teachers_list.setdefault(subject['teacher'], []).append(subject['name'])

cols_display = st.columns(len(teachers_list))
for i, (teacher, subs) in enumerate(teachers_list.items()):
    with cols_display[i]:
        st.markdown(f"**{teacher}**")
        for s in subs:
            st.markdown(f"- {s}")

st.markdown("---")
st.subheader("📁 الخطوة 2: رفع ملفات الأساتذة")

unique_teachers = list(dict.fromkeys(s['teacher'] for s in level_config['subjects']))
uploaded_files = {}

cols_upload = st.columns(min(len(unique_teachers), 4))
for i, teacher in enumerate(unique_teachers):
    with cols_upload[i % len(cols_upload)]:
        f = st.file_uploader(
            f"📄 {teacher}", type=['xlsx', 'xls'], key=f"up_{teacher}"
        )
        if f:
            uploaded_files[teacher] = f
        else:
            st.caption("⏳ مطلوب")

missing_teachers = [t for t in unique_teachers if t not in uploaded_files]
if missing_teachers:
    st.warning(f"⏳ في انتظار رفع ملفات: **{' ، '.join(missing_teachers)}**")
    st.stop()
st.success("✅ تم رفع جميع الملفات!")

st.markdown("---")
st.subheader("🔗 الخطوة 3: إعدادات الأعمدة والشيتات")

subjects_by_teacher = {}
for subject in level_config['subjects']:
    subjects_by_teacher.setdefault(subject['teacher'], []).append(subject)

subject_mappings = {}

for teacher, subjects in subjects_by_teacher.items():
    st.markdown(f"### 👨‍🏫 {teacher}")
    file = uploaded_files[teacher]
    sheet_names = get_sheet_names(file)
    
    for subject in subjects:
        subject_name = subject['name']
        st.markdown(f"#### 📘 {subject_name}")
        
        expected = get_expected_sheet_name(selected_level, subject_name)
        norm_expected = normalize_arabic(expected)
        
        suggested_sheet = 0
        for idx, sh in enumerate(sheet_names):
            if normalize_arabic(sh) == norm_expected:
                suggested_sheet = idx
                break
        else:
            for idx, sh in enumerate(sheet_names):
                sh_norm = normalize_arabic(sh)
                if norm_expected in sh_norm or sh_norm in norm_expected:
                    suggested_sheet = idx
                    break
                    
        selected_sheet = st.selectbox(
            f"اختر الشيت الخاص بـ {subject_name}:",
            sheet_names,
            index=suggested_sheet,
            key=f"sheet_{teacher}_{subject_name}"
        )
        
        df_sheet = read_sheet_safe(file, selected_sheet)
        if df_sheet.empty:
            st.warning(f"⚠️ الورقة «{selected_sheet}» فارغة!")
            subject_mappings[(teacher, subject_name)] = {
                'sheet': selected_sheet,
                'quiz_cols': [],
                'test_col': None,
                'type': subject['type']
            }
            continue
            
        local_name_col = process_names(df_sheet)
        gradeable_cols = get_gradeable_columns(df_sheet, local_name_col)
        
        quiz_cols_detected, test_col_detected = detect_subject_columns(
            df_sheet, subject['keywords'], gradeable_cols
        )
        confidence, detection_reasons = mapping_confidence(subject, quiz_cols_detected, test_col_detected, gradeable_cols)
        if confidence >= 80:
            st.success(f"🤖 التعرف التلقائي: ثقة {confidence}%")
        elif confidence >= 50:
            st.warning(f"🤖 التعرف التلقائي: ثقة متوسطة {confidence}% — راجع الاختيارات")
        else:
            st.error(f"🤖 التعرف التلقائي: ثقة منخفضة {confidence}% — يلزم التحقق اليدوي")
        with st.expander("🧠 تفاصيل الاكتشاف التلقائي"):
            for reason in detection_reasons:
                st.write("• " + reason)
            st.write("الأعمدة الرقمية المكتشفة:", len(gradeable_cols))

        col1, col2 = st.columns(2)
        with col1:
            if subject['type'] == 'main' and subject['keywords'].get('quizzes'):
                default_q = [q for q in quiz_cols_detected if q in gradeable_cols]
                selected_quizzes = st.multiselect(
                    "🧪 أعمدة الفروض المستمرة:",
                    options=gradeable_cols,
                    default=default_q,
                    key=f"quizzes_{teacher}_{subject_name}"
                )
            else:
                selected_quizzes = []
                st.caption("ℹ️ هذه المادة تعتمد على النقطة النهائية فقط")
                
        with col2:
            test_options = ["— بدون —"] + gradeable_cols
            test_index = 0
            if test_col_detected and test_col_detected in gradeable_cols:
                test_index = gradeable_cols.index(test_col_detected) + 1
            elif gradeable_cols:
                test_index = len(gradeable_cols)
                
            selected_test_raw = st.selectbox(
                "📝 عمود النقطة النهائية (الاختبار / التقويم):",
                options=test_options,
                index=test_index,
                key=f"test_{teacher}_{subject_name}"
            )
            selected_test = (None if selected_test_raw == "— بدون —" else selected_test_raw)
            
        subject_mappings[(teacher, subject_name)] = {
            'sheet': selected_sheet,
            'quiz_cols': selected_quizzes,
            'test_col': selected_test,
            'type': subject['type'],
            'confidence': confidence,
            'available_grade_columns': gradeable_cols
        }
        
        with st.expander(f"👁️ معاينة «{selected_sheet}»"):
            st.dataframe(df_sheet.head(4), use_container_width=True)
        st.markdown("---")

st.session_state.subject_mappings = subject_mappings

st.markdown("### 🤖 ملخص الاكتشاف التلقائي")
auto_rows = []
for (teacher, subject_name), mapping in subject_mappings.items():
    auto_rows.append({
        'المادة': subject_name,
        'الورقة': mapping['sheet'],
        'أعمدة التقييم': ' | '.join(map(str, mapping.get('quiz_cols', []))) or '—',
        'النقطة النهائية': mapping.get('test_col') or '⚠️ غير محددة',
        'الث الثقة': f"{mapping.get('confidence', 0)}%"
    })
auto_df = pd.DataFrame(auto_rows)
st.dataframe(auto_df, use_container_width=True, hide_index=True)
missing_final = auto_df[auto_df['النقطة النهائية'] == '⚠️ غير محددة'] if not auto_df.empty else pd.DataFrame()
if not missing_final.empty:
    st.warning("⚠️ توجد مواد بلا نقطة نهائية محددة. راجعها قبل بدء الحساب.")

st.markdown("---")
st.subheader("⚙️ الخطوة 4: الدمج وحساب المعدلات")

if st.button("🚀 بدء الحساب", type="primary", use_container_width=True):
    progress = st.progress(0, text="بدء المعالجة...")
    
    subject_grades = {}
    master_names = None
    computation_log = []
    
    step = 0
    total_steps = len(subject_mappings)
    
    for (teacher, subject_name), mapping in subject_mappings.items():
        step += 1
        progress.progress(
            int(step / total_steps * 50), text=f"معالجة {subject_name}..."
        )
        
        file = uploaded_files[teacher]
        df = read_sheet_safe(file, mapping['sheet'])
        
        if df.empty:
            computation_log.append(f"⚠️ {subject_name}: الورقة فارغة — تم تخطيها")
            continue
            
        name_col = process_names(df)
        if name_col is None or name_col not in df.columns:
            computation_log.append(f"⚠️ {subject_name}: لم يُعثر على عمود أسماء — تم تخطيها")
            continue
            
        df['_key'] = df[name_col].apply(normalize_arabic)
        
        if teacher == "معلم القسم" and master_names is None:
            master_names = (df[['_key', name_col]]
                            .rename(columns={name_col: 'الاسم'})
                            .drop_duplicates('_key')
                            .reset_index(drop=True))
        elif master_names is None:
            master_names = (df[['_key', name_col]]
                            .rename(columns={name_col: 'الاسم'})
                            .drop_duplicates('_key')
                            .reset_index(drop=True))
                            
        test_col = mapping['test_col']
        test_score = (df[test_col].apply(clean_grade_value) if test_col and test_col in df.columns else pd.Series(np.nan, index=df.index))
        
        if mapping['type'] == 'main' and mapping['quiz_cols']:
            quiz_scores = [df[qc].apply(clean_grade_value) for qc in mapping['quiz_cols'] if qc in df.columns]
            if quiz_scores:
                quiz_avg = pd.concat(quiz_scores, axis=1).mean(axis=1, skipna=True)
            else:
                quiz_avg = pd.Series(np.nan, index=df.index)
                
            both_ok = quiz_avg.notna() & test_score.notna()
            final_grade = pd.Series(np.nan, index=df.index)
            final_grade[both_ok] = ((quiz_avg[both_ok] + test_score[both_ok]) / 2)
            
            final_grade = final_grade.fillna(quiz_avg).fillna(test_score)
            
            computation_log.append(
                f"✅ {subject_name} (أساسية): "
                f"فروض={len(quiz_scores)} أعمدة + اختبار → معدل المادة"
            )
        else:
            final_grade = test_score
            computation_log.append(f"✅ {subject_name} (ثانوية): نقطة واحدة مباشرة")
            
        sg = pd.DataFrame({
            '_key': df['_key'],
            subject_name: final_grade
        })
        sg = sg.groupby('_key', as_index=False)[subject_name].mean()
        missing_count = int(sg[subject_name].isna().sum())
        computation_log.append(f"📊 {subject_name}: {len(sg)} تلميذاً، نقاط مفقودة={missing_count}")
        subject_grades[subject_name] = sg
        
    if not subject_grades:
        st.error("❌ لم يتم حساب أي مادة!")
        st.stop()
        
    if master_names is None or master_names.empty:
        st.error("❌ لم يتم العثور على قائمة أسماء التلاميذ!")
        st.stop()
        
    with st.expander("📋 سجل العمليات"):
        for log in computation_log:
            st.write(log)
            
    progress.progress(60, text="فحص جودة البيانات ودمجها...")
    duplicate_names = master_names['_key'].duplicated().sum()
    if duplicate_names:
        computation_log.append(f"⚠️ تم العثور على {duplicate_names} معرفات مكررة في القائمة المرجعية.")
    merged = master_names.copy()
    
    for subj_name, sg_df in subject_grades.items():
        merged = pd.merge(
            merged, sg_df[['_key', subj_name]],
            on='_key',
            how='left'
        )
        
    all_extra_keys = set()
    for subj_name, sg_df in subject_grades.items():
        all_extra_keys.update(sg_df['_key'].tolist())
        
    missing_keys = all_extra_keys - set(merged['_key'].tolist())
    
    if missing_keys:
        extra_rows = []
        for mk in missing_keys:
            row = {'_key': mk, 'الاسم': mk}
            for subj_name, sg_df in subject_grades.items():
                match = sg_df[sg_df['_key'] == mk]
                row[subj_name] = (match[subj_name].iloc[0] if not match.empty else np.nan)
            extra_rows.append(row)
            
        if extra_rows:
            extra_df = pd.DataFrame(extra_rows)
            merged = pd.concat([merged, extra_df], ignore_index=True)
            
    progress.progress(80, text="حساب المعدلات...")
    subject_col_names = list(subject_grades.keys())
    
    for col in subject_col_names:
        merged[col] = pd.to_numeric(merged[col], errors='coerce')
        
    merged['عدد المواد'] = merged[subject_col_names].notna().sum(axis=1)
    merged['المجموع'] = merged[subject_col_names].sum(axis=1, skipna=True)
    merged['المعدل الفصلي'] = (
        merged['المجموع'] / merged['عدد المواد'].replace(0, np.nan)
    ).round(2)
    merged['التقدير'] = merged['المعدل الفصلي'].apply(classify_student)
    
    merged = (merged
              .sort_values('المعدل الفصلي', ascending=False)
              .reset_index(drop=True))
    merged.insert(0, 'الترتيب', range(1, len(merged) + 1))
    merged = merged.drop(columns=['_key'], errors='ignore')
    
    progress.progress(100, text="✅ اكتمل الحساب!")
    st.session_state.final_result = merged
    st.session_state.subject_cols = subject_col_names

if st.session_state.final_result is not None:
    final_df = st.session_state.final_result
    subject_cols = st.session_state.subject_cols
    
    st.markdown("---")
    st.subheader("📊 كشف النقاط الإجمالي")
    
    display_cols = (['الترتيب', 'الاسم'] + subject_cols + ['عدد المواد', 'المجموع', 'المعدل الفصلي', 'التقدير'])
    display_cols = [c for c in display_cols if c in final_df.columns]
    
    st.dataframe(final_df[display_cols], use_container_width=True, height=450)
    
    col1, col2, col3, col4 = st.columns(4)
    avg_val = final_df['المعدل الفصلي'].mean()
    max_val = final_df['المعدل الفصلي'].max()
    min_val = final_df['المعدل الفصلي'].min()
    pass_rate = (final_df['المعدل الفصلي'] >= 5).mean() * 100
    
    with col1:
        st.metric("عدد التلاميذ", len(final_df))
    with col2:
        st.metric("المعدل العام", round(avg_val, 2) if pd.notna(avg_val) else 0)
    with col3:
        st.metric("أعلى معدل", round(max_val, 2) if pd.notna(max_val) else 0)
    with col4:
        st.metric("نسبة النجاح", f"{round(pass_rate, 1)}%" if pd.notna(pass_rate) else "0%")
        
    st.markdown("### 🔎 مركز المتابعة الذكية")
    search_name = st.text_input("🔍 ابحث عن تلميذ بالاسم")
    if search_name.strip():
        mask = final_df['الاسم'].astype(str).str.contains(search_name.strip(), case=False, na=False)
        st.dataframe(final_df.loc[mask, display_cols], use_container_width=True)

    st.markdown("### ⚠️ قائمة تحتاج إلى تدخل بيداغوجي")
    risk_df = final_df[final_df['المعدل الفصلي'] < 5].copy()
    if not risk_df.empty:
        st.warning(f"تم اكتشاف {len(risk_df)} تلميذاً بمعدل أقل من 5/10.")
        st.dataframe(risk_df[['الترتيب', 'الاسم', 'المعدل الفصلي', 'التقدير']], use_container_width=True)
    else:
        st.success("لا يوجد تلاميذ تحت عتبة 5/10 في النتائج الحالية.")

    st.markdown("### 🧪 جودة البيانات")
    quality_rows = []
    for subject in subject_cols:
        missing = int(final_df[subject].isna().sum())
        quality_rows.append({'المادة': subject, 'نقاط مفقودة': missing, 'نسبة الاكتمال %': round((1 - missing / max(len(final_df), 1)) * 100, 1)})
    st.dataframe(pd.DataFrame(quality_rows), use_container_width=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        export_df = final_df[display_cols]
        export_df.to_excel(writer, index=False, sheet_name="النتائج")
        ws = writer.sheets["النتائج"]
        for i, col in enumerate(display_cols):
            values = export_df[col].fillna('').astype(str).tolist()
            max_value_len = max((len(value) for value in values), default=0)
            max_len = max(max_value_len, len(str(col))) + 2
            ws.set_column(i, i, min(max_len, 35))
            
    st.download_button(
        "📥 تحميل النتائج (Excel)",
        data=output.getvalue(),
        file_name=(f"النتائج_{selected_level}_" f"{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"),
        use_container_width=True
    )

    # ══════════════════════════════════════════════════════════
    # الخطوة 5: التحليل البيداغوجي الهجين
    # ══════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("🤖 إعدادات الذكاء الاصطناعي و إنشاء التقرير")
    
    available_providers = ["🏠 التحليل المحلي"]
    if MISTRAL_API_KEY or OPENROUTER_API_KEY:
        available_providers.insert(0, "⚡ تلقائي (OpenRouter ثم Mistral ثم محلي)")
    if MISTRAL_API_KEY:
        available_providers.append("🤖 Mistral AI")
    if OPENROUTER_API_KEY:
        available_providers.append("🌐 OpenRouter")
        
    ai_provider = st.selectbox("اختر طريقة التحليل:", available_providers)
    
    selected_openrouter_model = "openrouter/auto"
    if ai_provider == "🌐 OpenRouter":
        openrouter_models = [
            "openrouter/auto",
            "meta-llama/llama-3.3-70b-instruct",
            "google/gemini-2.5-flash",
        ]
        selected_openrouter_model = st.selectbox("🤖 اختر النموذج:", openrouter_models)

    if st.button("✨ توليد التقرير التحليلي", type="secondary", use_container_width=True):
        with st.spinner("🧠 جاري تحليل النتائج..."):
            subject_avgs = final_df[subject_cols].mean().round(2).to_dict()
            class_avg = round(final_df['المعدل الفصلي'].mean(), 2)
            pass_r = round((final_df['المعدل الفصلي'] >= 5).mean() * 100, 1)
            grades_dist = final_df['التقدير'].value_counts().to_dict()
            local_report = generate_local_pedagogical_report(selected_level, final_df, subject_cols)
            
            report = None
            report_source = None
            
            prompt = f"""حلل نتائج قسم ابتدائي جزائري باللغة العربية. اعتمد حصراً على البيانات التالية ولا تخترع أرقاماً أو أسماء:
المستوى: {selected_level}
عدد التلاميذ: {len(final_df)}
المعدل العام: {class_avg}/10
نسبة النجاح: {pass_r}%
معدلات المواد: {json.dumps(subject_avgs, ensure_ascii=False)}
توزيع التقديرات: {json.dumps(grades_dist, ensure_ascii=False)}
المطلوب: قراءة عامة، نقاط القوة، نقاط الضعف، ثم 3 توصيات بيداغوجية عملية. اكتب نصاً عربياً واضحاً دون Markdown."""

            if ai_provider == "⚡ تلقائي (OpenRouter ثم Mistral ثم محلي)":
                result = auto_ai_analysis(prompt, MISTRAL_API_KEY, OPENROUTER_API_KEY)
                if result["success"]:
                    report = result["content"]
                    report_source = f"🤖 تم إنشاء التقرير بواسطة {result['provider']} ({result.get('model', 'auto')})"
                else:
                    st.warning(f"فشلت خدمات الذكاء الاصطناعي. جاري استخدام التحليل المحلي.\nالأخطاء:\n{result.get('error')}")
                    report = local_report
                    report_source = "🏠 تم إنشاء التقرير بالتحليل المحلي (احتياطي)."
                    
            elif ai_provider == "🤖 Mistral AI":
                result = analyze_with_ai(prompt, "Mistral", "mistral-small-latest", mistral_key=MISTRAL_API_KEY)
                if result["success"]:
                    report = result["content"]
                    report_source = "🤖 تم إنشاء التقرير بواسطة Mistral AI"
                else:
                    st.error(f"خطأ في الاتصال بـ Mistral: {result.get('error')}")
                    
            elif ai_provider == "🌐 OpenRouter":
                result = analyze_with_ai(prompt, "OpenRouter", selected_openrouter_model, openrouter_key=OPENROUTER_API_KEY)
                if result["success"]:
                    report = result["content"]
                    report_source = f"🤖 تم إنشاء التقرير بواسطة OpenRouter ({selected_openrouter_model})"
                else:
                    st.error(f"خطأ في الاتصال بـ OpenRouter: {result.get('error')}")
                    
            elif ai_provider == "🏠 التحليل المحلي":
                report = local_report
                report_source = "🏠 تم إنشاء التقرير بالتحليل المحلي دون الحاجة إلى API."

            if report:
                st.success(report_source)
                safe_response = str(report).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
                st.markdown(f'<div class="analysis-box">{safe_response}</div>', unsafe_allow_html=True)
                pdf_bytes = generate_arabic_pdf(report, font_path="arial.ttf")
                if pdf_bytes:
                    st.download_button(
                        label="📥 تحميل التقرير (PDF)", data=pdf_bytes,
                        file_name=f"تقرير_تحليلي_{selected_level}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf", use_container_width=True
                    )

import streamlit as st
import pandas as pd
import numpy as np
import io
import re
import requests
import json
from datetime import datetime

# ══════════════════════════════════════════════════════════════
# إعدادات الصفحة
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="نظام حساب المعدلات — الابتدائي الجزائري",
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
.analysis-box { background: #f8f9fa; border-radius: 10px; padding: 20px; border-right: 5px solid #6c5ce7; margin-top: 15px;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# القائمة الجانبية - إعدادات الذكاء الاصطناعي
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("🤖 إعدادات الذكاء الاصطناعي")
    st.markdown("أدخل مفتاح **Mistral AI** لتفعيل ميزة التحليل البيداغوجي المتقدم للنتائج.")
    mistral_api_key = st.text_input("MISTRAL_API_KEY:", type="password", help="احصل على المفتاح من console.mistral.ai")
    if mistral_api_key:
        st.success("✅ المفتاح متوفر")
    else:
        st.warning("⚠️ يرجى إدخال المفتاح لتفعيل التحليل")

st.markdown("""
<div class="ai-box">
    <h1 style="color:white; text-align:center;">🏫🤖 النظام الذكي لحساب معدلات التلاميذ</h1>
    <p style="text-align:center; font-size:16px;"> متوافق كلياً مع مستخرجات الأرضية الرقمية (الرقمنة) | مدعوم بالتحليل البيداغوجي لـ Mistral AI </p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# تعريف المواد الدراسية 
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
            {"name": "اللغة الفرنسية", "type": "secondary", "teacher": "أستاذ اللغة الفرنسية", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "اللغة الإنجليزية", "type": "secondary", "teacher": "أستاذ اللغة الإنجليزية", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
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
            {"name": "اللغة الفرنسية", "type": "secondary", "teacher": "أستاذ اللغة الفرنسية", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "اللغة الإنجليزية", "type": "secondary", "teacher": "أستاذ اللغة الإنجليزية", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
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
            {"name": "اللغة الفرنسية", "type": "secondary", "teacher": "أستاذ اللغة الفرنسية", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
            {"name": "اللغة الإنجليزية", "type": "secondary", "teacher": "أستاذ اللغة الإنجليزية", "keywords": {"tests": ["اختبار", "امتحان", "تقويم", "مستمر"], "quizzes": []}},
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
# دوال مساعدة 
# ══════════════════════════════════════════════════════════════
def get_expected_sheet_name(level, subject_name):
    if subject_name == "التربية البدنية":
        return {
            "السنة الأولى": "ت البدنية والرياضية",
            "السنة الثانية": "ت البدنية والرياضية 1",
            "السنة الثالثة": "ت البدنية والرياضية 2",
            "السنة الرابعة": "ت البدنية والرياضية 3",
            "السنة الخامسة": "ت البدنية والرياضية 4"
        }.get(level, "ت البدنية والرياضية")
        
    if subject_name == "اللغة الفرنسية":
        return {
            "السنة الثالثة": "اللغة الفرنسية",
            "السنة الرابعة": "اللغة الفرنسية 1",
            "السنة الخامسة": "اللغة الفرنسية 2"
        }.get(level, "اللغة الفرنسية")
        
    if subject_name == "اللغة الإنجليزية":
        return {
            "السنة الثالثة": "اللغة الإنجليزية",
            "السنة الرابعة": "اللغة الإنجليزية 1",
            "السنة الخامسة": "اللغة الإنجليزية 2"
        }.get(level, "اللغة الإنجليزية")
        
    return subject_name

def normalize_arabic(text):
    if pd.isna(text): return ""
    text = str(text).strip()
    text = re.sub(r'\s+', ' ', text)
    for old, new in [('أ','ا'),('إ','ا'),('آ','ا'), ('ة','ه'),('ى','ي'),('ئ','ي'),('ؤ','و')]:
        text = text.replace(old, new)
    return text

def process_names(df):
    nom_col, prenom_col = None, None
    for col in df.columns:
        c_norm = str(col).strip().lower()
        if c_norm in ['اللقب', 'لقب', 'nom']: nom_col = col
        if c_norm in ['الاسم', 'اسم', 'prenom', 'prénom']: prenom_col = col
    
    if nom_col and prenom_col:
        df['الاسم_الكامل'] = df[nom_col].astype(str).str.strip() + " " + df[prenom_col].astype(str).str.strip()
        return 'الاسم_الكامل'
    
    for col in df.columns:
        c_norm = str(col).strip()
        if any(kw in c_norm for kw in ['اللقب والاسم', 'الاسم واللقب', 'اسم ولقب', 'التلميذ', 'الطالب']):
            return col
    return nom_col or prenom_col

def clean_grade_value(val):
    if pd.isna(val): return np.nan
    s = str(val).strip()
    if s in ['غائب', 'غياب', 'معفى', '/', '-', '']: return np.nan
    s = s.replace(',', '.')
    match = re.search(r'(\d+\.?\d*)', s)
    if match:
        try:
            return float(match.group(1))
        except:
            return np.nan
    return np.nan

def detect_subject_columns(df, subject_keywords):
    quiz_cols = []
    test_col = None
    cols = {col: normalize_arabic(col) for col in df.columns}
    for col, col_norm in cols.items():
        if any(kw in col_norm for kw in subject_keywords.get('tests', [])):
            test_col = col
        elif any(kw in col_norm for kw in subject_keywords.get('quizzes', [])):
            quiz_cols.append(col)
    return quiz_cols, test_col

def read_sheet_safe(file, sheet_name):
    file.seek(0)
    temp_df = pd.read_excel(file, sheet_name=sheet_name, header=None)
    header_idx = 0
    for i, row in temp_df.head(15).iterrows():
        row_str = ' '.join(row.dropna().astype(str))
        if 'اللقب' in row_str and 'الاسم' in row_str:
            header_idx = i
            break
        elif 'nom' in row_str.lower() and 'prenom' in row_str.lower():
            header_idx = i
            
    file.seek(0)
    df = pd.read_excel(file, sheet_name=sheet_name, header=header_idx)
    df.columns = df.columns.astype(str).str.replace('\n', ' ').str.strip()
    if len(df) > 0 and ('اللقب' in str(df.iloc[0].values) or 'الاسم' in str(df.iloc[0].values) or 'رقم' in str(df.iloc[0].values)):
        df = df.iloc[1:].reset_index(drop=True)
    df = df.dropna(how='all')
    return df

def get_sheet_names(file):
    file.seek(0)
    return pd.ExcelFile(file).sheet_names

def classify_student(avg):
    if pd.isna(avg): return "—"
    if avg >= 9: return "ممتاز 🌟"
    if avg >= 8: return "جيد جداً ✅"
    if avg >= 7: return "جيد 👍"
    if avg >= 5: return "مقبول 📗"
    if avg >= 3.5: return "ضعيف ⚠️"
    return "ضعيف جداً ❌"

def call_mistral_api(api_key, prompt):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "system", "content": "أنت مفتش تربوي جزائري خبير في التعليم الابتدائي. مهمتك تقديم تحليلات دقيقة وتوصيات بيداغوجية لتحسين مستوى التلاميذ بناءً على إحصائيات معدلاتهم."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"❌ حدث خطأ في الاتصال بالذكاء الاصطناعي: {response.text}"

# ══════════════════════════════════════════════════════════════
# التطبيق الرئيسي
# ══════════════════════════════════════════════════════════════
if 'subject_mappings' not in st.session_state:
    st.session_state.subject_mappings = {}
if 'final_result' not in st.session_state:
    st.session_state.final_result = None
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = {}
if 'selected_level' not in st.session_state:
    st.session_state.selected_level = list(LEVELS.keys())[0]

# الخطوة 1: اختيار المستوى
st.subheader("📚 الخطوة 1: اختر المستوى الدراسي")
selected_level = st.selectbox("🎓 المستوى:", list(LEVELS.keys()), index=list(LEVELS.keys()).index(st.session_state.selected_level))
st.session_state.selected_level = selected_level
level_config = LEVELS[selected_level]

st.markdown(f"#### 📋 مواد {selected_level} ({level_config['total_subjects']} مادة)")
teachers_list = {}
for subject in level_config['subjects']:
    teachers_list.setdefault(subject['teacher'], []).append(subject['name'])

cols = st.columns(len(teachers_list))
for i, (teacher, subs) in enumerate(teachers_list.items()):
    with cols[i]:
        st.markdown(f"**{teacher}**")
        for s in subs:
            st.markdown(f"- {s}")

# الخطوة 2: رفع الملفات
st.markdown("---")
st.subheader("📁 الخطوة 2: رفع ملفات الأساتذة")
unique_teachers = set([s['teacher'] for s in level_config['subjects']])
uploaded_files = {}

cols = st.columns(min(len(unique_teachers), 4))
for i, teacher in enumerate(unique_teachers):
    with cols[i % len(cols)]:
        f = st.file_uploader(f"📄 {teacher}", type=['xlsx', 'xls'], key=f"up_{teacher}")
        if f:
            uploaded_files[teacher] = f
            st.session_state.uploaded_files[teacher] = f
        elif teacher in st.session_state.uploaded_files:
            uploaded_files[teacher] = st.session_state.uploaded_files[teacher]
        else:
            st.caption("⏳ مطلوب")

missing_teachers = [t for t in unique_teachers if t not in uploaded_files]
if missing_teachers:
    st.warning(f"⏳ في انتظار رفع ملفات: **{' ، '.join(missing_teachers)}**")
    st.stop()
st.success("✅ تم رفع جميع الملفات!")

# الخطوة 3: ربط المواد وتحديد الأعمدة
st.markdown("---")
st.subheader("🔗 الخطوة 3: إعدادات الأعمدة والشيتات (تلقائي)")

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
        
        expected_sheet_name = get_expected_sheet_name(selected_level, subject_name)
        norm_expected = normalize_arabic(expected_sheet_name)
        
        suggested_sheet = 0
        exact_match_found = False
        
        for idx, sh in enumerate(sheet_names):
            if normalize_arabic(sh) == norm_expected:
                suggested_sheet = idx
                exact_match_found = True
                break
                
        if not exact_match_found:
            for idx, sh in enumerate(sheet_names):
                if norm_expected in normalize_arabic(sh):
                    suggested_sheet = idx
                    break
        
        selected_sheet = st.selectbox(
            f"اختر الشيت الخاص بـ {subject_name}:",
            sheet_names,
            index=suggested_sheet,
            key=f"sheet_{teacher}_{subject_name}"
        )
        
        df_sheet = read_sheet_safe(file, selected_sheet)
        ignore_cols = ['رقم', 'matricule', 'تاريخ', 'date', 'اللقب', 'الاسم', 'nom', 'prenom', 'obs', 'ملاحظات']
        numeric_cols = [c for c in df_sheet.select_dtypes(include='number').columns.tolist() if not any(ign in c.lower() for ign in ignore_cols)]
                        
        quiz_cols, test_col = detect_subject_columns(df_sheet, subject['keywords'])
        
        col1, col2 = st.columns(2)
        with col1:
            if subject['type'] == 'main':
                default_quizzes = [q for q in quiz_cols if q in numeric_cols]
                selected_quizzes = st.multiselect(
                    "🧪 أعمدة الفروض المستمرة:",
                    options=numeric_cols,
                    default=default_quizzes,
                    key=f"quizzes_{teacher}_{subject_name}"
                )
            else:
                selected_quizzes = st.multiselect(
                    "🧪 أعمدة الفروض:",
                    options=numeric_cols,
                    default=[],
                    key=f"quizzes_{teacher}_{subject_name}",
                    disabled=True,
                    help="هذه المادة تعتمد على عمود النقطة النهائية فقط."
                )
                
        with col2:
            test_options = [None] + numeric_cols
            test_index = 0
            if test_col and test_col in numeric_cols:
                test_index = numeric_cols.index(test_col) + 1
                
            selected_test = st.selectbox(
                "📝 عمود النقطة النهائية (الاختبار / التقويم):",
                options=test_options,
                index=test_index,
                format_func=lambda x: "يرجى التحديد" if x is None else x,
                key=f"test_{teacher}_{subject_name}"
            )
        
        subject_mappings[(teacher, subject_name)] = {
            'sheet': selected_sheet,
            'quiz_cols': selected_quizzes,
            'test_col': selected_test,
            'type': subject['type']
        }
        st.markdown("---")

st.session_state.subject_mappings = subject_mappings

# الخطوة 4: الحساب والدمج
st.markdown("---")
st.subheader("⚙️ الخطوة 4: الدمج وحساب المعدلات")

if st.button("🚀 بدء الحساب", type="primary", use_container_width=True):
    progress = st.progress(0, text="بدء المعالجة...")
    all_data = [] 
    step = 0
    total_steps = len(subject_mappings)
    
    for (teacher, subject_name), mapping in subject_mappings.items():
        step += 1
        progress.progress(int(step / total_steps * 50), text=f"معالجة {subject_name}...")
        
        file = uploaded_files[teacher]
        df = read_sheet_safe(file, mapping['sheet'])
        name_col = process_names(df)
        
        if name_col is None or name_col not in df.columns:
            continue
        
        df['_key'] = df[name_col].apply(normalize_arabic)
        df['الاسم_الأصلي'] = df[name_col].astype(str)
        
        test_col = mapping['test_col']
        test_score = df[test_col].apply(clean_grade_value) if test_col and test_col in df.columns else pd.Series(np.nan, index=df.index)
        
        if mapping['type'] == 'main':
            quiz_cols = mapping['quiz_cols']
            quiz_scores = [df[qcol].apply(clean_grade_value) for qcol in quiz_cols if qcol in df.columns]
            quiz_avg = pd.concat(quiz_scores, axis=1).mean(axis=1, skipna=True) if quiz_scores else pd.Series(np.nan, index=df.index)
            
            final_grade = (quiz_avg + test_score) / 2
            final_grade = final_grade.fillna(quiz_avg).fillna(test_score)
        else:
            final_grade = test_score
        
        df_subject = df[['_key', 'الاسم_الأصلي']].copy()
        df_subject[subject_name] = final_grade
        all_data.append(df_subject)
    
    if not all_data:
        st.error("❌ لم يتم العثور على بيانات!")
        st.stop()
    
    progress.progress(60, text="دمج البيانات...")
    
    merged = all_data[0]
    for df_sub in all_data[1:]:
        merged = pd.merge(merged, df_sub, on=['_key', 'الاسم_الأصلي'], how='outer')
    
    merged['الاسم'] = merged['الاسم_الأصلي']
    merged.drop(columns=['الاسم_الأصلي'], inplace=True)
    
    subject_cols = [col for col in merged.columns if col not in ['_key', 'الاسم']]
    for col in subject_cols:
        merged[col] = pd.to_numeric(merged[col], errors='coerce')
    
    merged['عدد المواد'] = merged[subject_cols].notna().sum(axis=1)
    merged['المجموع'] = merged[subject_cols].sum(axis=1, skipna=True)
    merged['المعدل الفصلي'] = (merged['المجموع'] / merged['عدد المواد'].replace(0, np.nan)).round(2)
    merged['التقدير'] = merged['المعدل الفصلي'].apply(classify_student)
    
    merged = merged.sort_values('المعدل الفصلي', ascending=False).reset_index(drop=True)
    merged.insert(0, 'الترتيب', range(1, len(merged) + 1))
    
    progress.progress(100, text="✅ اكتمل الحساب!")
    st.session_state.final_result = merged
    st.session_state.subject_cols = subject_cols

# عرض وتحميل النتائج
if st.session_state.final_result is not None:
    final_df = st.session_state.final_result
    
    st.markdown("---")
    st.subheader("📊 كشف النقاط الإجمالي")
    
    display_cols = ['الترتيب', 'الاسم'] + st.session_state.subject_cols + ['المجموع', 'المعدل الفصلي', 'التقدير']
    st.dataframe(final_df[display_cols], use_container_width=True, height=450)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("عدد التلاميذ", len(final_df))
    with col2:
        st.metric("المعدل العام", round(final_df['المعدل الفصلي'].mean(), 2) if not final_df['المعدل الفصلي'].isna().all() else 0)
    with col3:
        st.metric("أعلى معدل", round(final_df['المعدل الفصلي'].max(), 2) if not final_df['المعدل الفصلي'].isna().all() else 0)
    with col4:
        st.metric("نسبة النجاح", f"{round((final_df['المعدل الفصلي'] >= 5).mean() * 100, 1)}%")
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, index=False, sheet_name="النتائج")
    
    st.download_button(
        "📥 تحميل النتائج (Excel)",
        data=output.getvalue(),
        file_name=f"النتائج_النهائية_{selected_level}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        use_container_width=True
    )

    # ══════════════════════════════════════════════════════════════
    # الخطوة 5: التحليل الذكي للنتائج (Mistral AI)
    # ══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("🧠 الخطوة 5: التحليل البيداغوجي المتقدم")
    
    if not mistral_api_key:
        st.info("💡 للقيام بتحليل ذكي معمق للنتائج باستخدام الذكاء الاصطناعي، يرجى إدخال مفتاح `MISTRAL_API_KEY` في القائمة الجانبية.")
    else:
        st.write("اضغط على الزر أدناه ليقوم الذكاء الاصطناعي بقراءة معدلات القسم وإعطاء توصيات للأساتذة.")
        if st.button("✨ توليد التقرير التحليلي", type="secondary"):
            with st.spinner("🤖 جاري تحليل البيانات واستنباط التوصيات البيداغوجية..."):
                
                # تجميع البيانات الإحصائية وإرسالها بدلاً من كل القائمة لحفظ الخصوصية وتقليل حجم الطلب
                subject_avgs = final_df[st.session_state.subject_cols].mean().round(2).to_dict()
                class_avg = round(final_df['المعدل الفصلي'].mean(), 2)
                pass_rate = round((final_df['المعدل الفصلي'] >= 5).mean() * 100, 1)
                grades_dist = final_df['التقدير'].value_counts().to_dict()
                
                summary_data = f"""
                مستوى القسم: {selected_level}
                عدد التلاميذ: {len(final_df)}
                المعدل العام للقسم: {class_avg} / 10
                نسبة النجاح (المتحصلين على 5 فما فوق): {pass_rate}%
                
                معدلات المواد الدراسية (من 10):
                {json.dumps(subject_avgs, ensure_ascii=False, indent=2)}
                
                توزيع التقديرات في القسم:
                {json.dumps(grades_dist, ensure_ascii=False, indent=2)}
                """
                
                prompt = f"""أنت مفتش تربوي جزائري خبير في مرحلة التعليم الابتدائي.
                بناءً على الإحصائيات التالية لنتائج الفصل الدراسي، قم بتقديم تقرير مفصل:
                
                البيانات:
                {summary_data}
                
                المطلوب:
                1. قراءة تحليلية عامة لمستوى القسم ونسبة النجاح.
                2. تحديد دقيق لنقاط القوة (المواد ذات الأداء العالي).
                3. تحديد دقيق لنقاط الضعف (المواد التي تحتاج تدخلاً عاجلاً).
                4. تقديم 3 توصيات بيداغوجية عملية وواقعية للأساتذة (معلم القسم وأساتذة التخصص) لمعالجة الضعف في الفصل القادم.
                
                يرجى الرد باللغة العربية، بأسلوب احترافي ومهني، واستخدام التنسيق بخط عريض (Markdown) لجعله سهل القراءة.
                """
                
                ai_response = call_mistral_api(mistral_api_key, prompt)
                
                st.markdown('<div class="analysis-box">', unsafe_allow_html=True)
                st.markdown(ai_response)
                st.markdown('</div>', unsafe_allow_html=True)


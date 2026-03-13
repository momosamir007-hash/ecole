import streamlit as st
import pandas as pd
import numpy as np
import io
import re
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
.mapping-box { background: #e8f4fd; border-radius: 10px; padding: 15px; margin: 8px 0; border-right: 4px solid #2196F3; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ai-box">
    <h1 style="color:white; text-align:center;">🏫🤖 النظام الذكي لحساب معدلات التلاميذ</h1>
    <p style="text-align:center; font-size:16px;"> متوافق كلياً مع مستخرجات الأرضية الرقمية (الرقمنة) | المرحلة الابتدائية </p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# تعريف المواد الدراسية لكل مستوى (محدثة لتشمل كلمات الرقمنة)
# ══════════════════════════════════════════════════════════════
LEVELS = {
    "السنة الأولى": {
        "total_subjects": 6,
        "subjects": [
            {"name": "اللغة العربية", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج"]}},
            {"name": "الرياضيات", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["أعداد", "حساب", "مقادير", "قياس", "معطيات", "فضاء", "هندسة"]}},
            {"name": "التربية الإسلامية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية الموسيقية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية التشكيلية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية البدنية", "type": "secondary", "teacher": "أستاذ التربية البدنية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}}
        ]
    },
    "السنة الثانية": {
        "total_subjects": 6,
        "subjects": [
            {"name": "اللغة العربية", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج"]}},
            {"name": "الرياضيات", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["أعداد", "حساب", "مقادير", "قياس", "معطيات", "فضاء", "هندسة"]}},
            {"name": "التربية الإسلامية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية الموسيقية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية التشكيلية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية البدنية", "type": "secondary", "teacher": "أستاذ التربية البدنية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}}
        ]
    },
    "السنة الثالثة": {
        "total_subjects": 10,
        "subjects": [
            {"name": "اللغة العربية", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج"]}},
            {"name": "الرياضيات", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["أعداد", "حساب", "مقادير", "قياس", "معطيات", "فضاء", "هندسة"]}},
            {"name": "اللغة الفرنسية", "type": "main", "teacher": "أستاذ اللغة الفرنسية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "إنتاج", "قراءة", "تواصل", "كتابي", "شفهي"]}},
            {"name": "اللغة الإنجليزية", "type": "main", "teacher": "أستاذ اللغة الإنجليزية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "إنتاج", "قراءة", "تواصل", "كتابي", "شفهي"]}},
            {"name": "التربية الإسلامية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية العلمية والتكنولوجية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التاريخ", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية التشكيلية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية الموسيقية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية البدنية", "type": "secondary", "teacher": "أستاذ التربية البدنية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}}
        ]
    },
    "السنة الرابعة": {
        "total_subjects": 11,
        "subjects": [
            {"name": "اللغة العربية", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج"]}},
            {"name": "الرياضيات", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["أعداد", "حساب", "مقادير", "قياس", "معطيات", "فضاء", "هندسة"]}},
            {"name": "اللغة الفرنسية", "type": "main", "teacher": "أستاذ اللغة الفرنسية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "إنتاج", "قراءة", "تواصل", "كتابي", "شفهي"]}},
            {"name": "اللغة الإنجليزية", "type": "main", "teacher": "أستاذ اللغة الإنجليزية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "إنتاج", "قراءة", "تواصل", "كتابي", "شفهي"]}},
            {"name": "التربية الإسلامية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية العلمية والتكنولوجية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية المدنية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التاريخ والجغرافيا", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية التشكيلية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية الموسيقية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية البدنية", "type": "secondary", "teacher": "أستاذ التربية البدنية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}}
        ]
    },
    "السنة الخامسة": {
        "total_subjects": 11,
        "subjects": [
            {"name": "اللغة العربية", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "تواصل", "قراءة", "محفوظات", "كتابة", "املاء", "إنتاج"]}},
            {"name": "الرياضيات", "type": "main", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["أعداد", "حساب", "مقادير", "قياس", "معطيات", "فضاء", "هندسة"]}},
            {"name": "اللغة الفرنسية", "type": "main", "teacher": "أستاذ اللغة الفرنسية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "إنتاج", "قراءة", "تواصل", "كتابي", "شفهي"]}},
            {"name": "اللغة الإنجليزية", "type": "main", "teacher": "أستاذ اللغة الإنجليزية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تعبير", "إنتاج", "قراءة", "تواصل", "كتابي", "شفهي"]}},
            {"name": "التربية الإسلامية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية العلمية والتكنولوجية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية المدنية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التاريخ والجغرافيا", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية التشكيلية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية الموسيقية", "type": "secondary", "teacher": "معلم القسم", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}},
            {"name": "التربية البدنية", "type": "secondary", "teacher": "أستاذ التربية البدنية", "keywords": {"tests": ["اختبار", "امتحان"], "quizzes": ["تقويم", "مستمر"]}}
        ]
    }
}

# ══════════════════════════════════════════════════════════════
# دوال مساعدة (معدلة خصيصاً للرقمنة)
# ══════════════════════════════════════════════════════════════
def normalize_arabic(text):
    if pd.isna(text): return ""
    text = str(text).strip()
    text = re.sub(r'\s+', ' ', text)
    for old, new in [('أ','ا'),('إ','ا'),('آ','ا'), ('ة','ه'),('ى','ي'),('ئ','ي'),('ؤ','و')]:
        text = text.replace(old, new)
    return text

def process_names(df):
    """ دمج اللقب والاسم إذا كانا في عمودين منفصلين (كما في الرقمنة) """
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
    """ قراءة الملف وتجاوز الترويسة المزدوجة الفرنسية/العربية """
    file.seek(0)
    temp_df = pd.read_excel(file, sheet_name=sheet_name, header=None)
    header_idx = 0
    
    # البحث عن صف العناوين (نفضل العناوين العربية)
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
    
    # إذا كان الصف الأول بعد العناوين هو أيضاً عناوين بلغة أخرى، يتم حذفه
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

# ══════════════════════════════════════════════════════════════
# إدارة حالة الجلسة
# ══════════════════════════════════════════════════════════════
if 'subject_mappings' not in st.session_state:
    st.session_state.subject_mappings = {}
if 'final_result' not in st.session_state:
    st.session_state.final_result = None
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = {}
if 'selected_level' not in st.session_state:
    st.session_state.selected_level = list(LEVELS.keys())[0]

# ══════════════════════════════════════════════════════════════
# الخطوة 1: اختيار المستوى
# ══════════════════════════════════════════════════════════════
st.subheader("📚 الخطوة 1: اختر المستوى الدراسي")
selected_level = st.selectbox("🎓 المستوى:", list(LEVELS.keys()), index=list(LEVELS.keys()).index(st.session_state.selected_level))
st.session_state.selected_level = selected_level
level_config = LEVELS[selected_level]

st.markdown(f"#### 📋 مواد {selected_level} ({level_config['total_subjects']} مادة)")
teachers_list = {}
for subject in level_config['subjects']:
    t = subject['teacher']
    teachers_list.setdefault(t, []).append(subject['name'])

cols = st.columns(len(teachers_list))
for i, (teacher, subs) in enumerate(teachers_list.items()):
    with cols[i]:
        st.markdown(f"**{teacher}**")
        for s in subs:
            st.markdown(f"- {s}")

# ══════════════════════════════════════════════════════════════
# الخطوة 2: رفع ملفات الأساتذة
# ══════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════
# الخطوة 3: ربط المواد بالشيتات والأعمدة
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("🔗 الخطوة 3: ربط المواد بملفات الأساتذة وتحديد الأعمدة")

subjects_by_teacher = {}
for subject in level_config['subjects']:
    subjects_by_teacher.setdefault(subject['teacher'], []).append(subject)

subject_mappings = {}

for teacher, subjects in subjects_by_teacher.items():
    st.markdown(f"### {teacher}")
    file = uploaded_files[teacher]
    sheet_names = get_sheet_names(file)
    
    for subject in subjects:
        subject_name = subject['name']
        st.markdown(f"#### 📘 {subject_name}")
        
        suggested_sheet = 0
        norm_subj = normalize_arabic(subject_name)
        for idx, sh in enumerate(sheet_names):
            if norm_subj in normalize_arabic(sh) or normalize_arabic(sh) in norm_subj:
                suggested_sheet = idx
                break
        
        selected_sheet = st.selectbox(
            f"اختر الشيت الخاص بـ {subject_name}:",
            sheet_names,
            index=suggested_sheet,
            key=f"sheet_{teacher}_{subject_name}"
        )
        
        df_sheet = read_sheet_safe(file, selected_sheet)
        
        # استبعاد الأعمدة غير المتعلقة بالنقاط
        ignore_cols = ['رقم', 'matricule', 'تاريخ', 'date', 'اللقب', 'الاسم', 'nom', 'prenom', 'obs', 'ملاحظات']
        numeric_cols = [c for c in df_sheet.select_dtypes(include='number').columns.tolist() 
                        if not any(ign in c.lower() for ign in ignore_cols)]
                        
        quiz_cols, test_col = detect_subject_columns(df_sheet, subject['keywords'])
        
        col1, col2 = st.columns(2)
        with col1:
            default_quizzes = quiz_cols if quiz_cols else numeric_cols
            selected_quizzes = st.multiselect(
                "🧪 أعمدة الفروض / التقويم:",
                options=numeric_cols,
                default=[q for q in default_quizzes if q in numeric_cols],
                key=f"quizzes_{teacher}_{subject_name}"
            )
        with col2:
            test_options = [None] + numeric_cols
            test_index = 0
            if test_col and test_col in numeric_cols:
                test_index = numeric_cols.index(test_col) + 1
                
            selected_test = st.selectbox(
                "📝 عمود الاختبار (إن وُجد):",
                options=test_options,
                index=test_index,
                format_func=lambda x: "بدون اختبار (يعتمد على الفروض فقط)" if x is None else x,
                key=f"test_{teacher}_{subject_name}"
            )
        
        subject_mappings[(teacher, subject_name)] = {
            'sheet': selected_sheet,
            'quiz_cols': selected_quizzes,
            'test_col': selected_test
        }
        
        with st.expander(f"👁️ معاينة الشيت ({selected_sheet})"):
            st.dataframe(df_sheet.head(3), use_container_width=True)
        
        st.markdown("---")

st.session_state.subject_mappings = subject_mappings

# ══════════════════════════════════════════════════════════════
# الخطوة 4: الدمج وحساب المعدلات
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("⚙️ الخطوة 4: الدمج وحساب المعدلات")

if st.button("🚀 بدء الحساب", type="primary", use_container_width=True):
    progress = st.progress(0, text="بدء المعالجة...")
    
    if "معلم القسم" not in uploaded_files:
        st.error("❌ لم يتم رفع ملف معلم القسم!")
        st.stop()
    
    all_data = [] 
    step = 0
    total_steps = len(subject_mappings)
    
    for (teacher, subject_name), mapping in subject_mappings.items():
        step += 1
        progress.progress(int(step / total_steps * 50), text=f"معالجة {subject_name}...")
        
        file = uploaded_files[teacher]
        sheet = mapping['sheet']
        quiz_cols = mapping['quiz_cols']
        test_col = mapping['test_col']
        
        df = read_sheet_safe(file, sheet)
        name_col = process_names(df) # استخدام الدالة الجديدة لدمج الاسم واللقب
        
        if name_col is None or name_col not in df.columns:
            st.warning(f"⚠️ لم يتم العثور على أعمدة الأسماء في شيت {sheet}. سيتم تخطي هذه المادة.")
            continue
        
        df['_key'] = df[name_col].apply(normalize_arabic)
        df['الاسم_الأصلي'] = df[name_col].astype(str)
        
        quiz_scores = []
        for qcol in quiz_cols:
            if qcol in df.columns:
                quiz_scores.append(df[qcol].apply(clean_grade_value))
                
        if quiz_scores:
            quiz_avg = pd.concat(quiz_scores, axis=1).mean(axis=1, skipna=True)
        else:
            quiz_avg = pd.Series(np.nan, index=df.index)
        
        if test_col and test_col in df.columns:
            test_score = df[test_col].apply(clean_grade_value)
        else:
            test_score = pd.Series(np.nan, index=df.index)
        
        # حساب المعدل النهائي للمادة بناءً على القاعدة الجزائرية
        subject_info = next((s for s in level_config['subjects'] if s['name'] == subject_name), None)
        
        if subject_info and subject_info['type'] == 'main':
            # معدل المادة = (معدل التقويم + الاختبار) / 2
            final_grade = (quiz_avg + test_score) / 2
            final_grade = final_grade.fillna(quiz_avg).fillna(test_score)
        else:
            # المواد بدون تقويم مستمر، أو المواد التي فيها تقويم مستمر فقط
            final_grade = test_score if test_col else quiz_avg
        
        df_subject = df[['_key', 'الاسم_الأصلي']].copy()
        df_subject[subject_name] = final_grade
        
        all_data.append(df_subject)
    
    if not all_data:
        st.error("❌ لم يتم العثور على أي بيانات صحيحة!")
        st.stop()
    
    progress.progress(60, text="دمج المواد وتوحيد الأسماء...")
    
    # دمج متسلسل (Outer Join) لتفادي فقدان أي تلميذ
    merged = all_data[0]
    for df_sub in all_data[1:]:
        merged = pd.merge(merged, df_sub, on=['_key', 'الاسم_الأصلي'], how='outer')
    
    merged['الاسم'] = merged['الاسم_الأصلي']
    merged.drop(columns=['الاسم_الأصلي'], inplace=True)
    
    # أعمدة المواد
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

# ══════════════════════════════════════════════════════════════
# عرض النتائج وتحميلها
# ══════════════════════════════════════════════════════════════
if st.session_state.final_result is not None:
    final_df = st.session_state.final_result
    subject_cols = st.session_state.subject_cols
    
    st.markdown("---")
    st.subheader("📊 النتائج النهائية (كشف النقاط الإجمالي)")
    
    display_cols = ['الترتيب', 'الاسم'] + subject_cols + ['عدد المواد', 'المجموع', 'المعدل الفصلي', 'التقدير']
    st.dataframe(final_df[[c for c in display_cols if c in final_df.columns]], use_container_width=True, height=450)
    
    st.markdown("#### 📈 إحصائيات القسم")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("عدد التلاميذ", len(final_df))
    with col2:
        st.metric("المعدل العام", round(final_df['المعدل الفصلي'].mean(), 2) if not final_df['المعدل الفصلي'].isna().all() else 0)
    with col3:
        st.metric("أعلى معدل", round(final_df['المعدل الفصلي'].max(), 2) if not final_df['المعدل الفصلي'].isna().all() else 0)
    with col4:
        st.metric("أدنى معدل", round(final_df['المعدل الفصلي'].min(), 2) if not final_df['المعدل الفصلي'].isna().all() else 0)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, index=False, sheet_name="النتائج")
        workbook = writer.book
        worksheet = writer.sheets["النتائج"]
        for i, col in enumerate(final_df.columns):
            max_len = max(final_df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, min(max_len, 35))
            
    st.download_button(
        "📥 تحميل النتائج النهائية بصيغة (Excel)",
        data=output.getvalue(),
        file_name=f"النتائج_النهائية_{selected_level}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        use_container_width=True
    )

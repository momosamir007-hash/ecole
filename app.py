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
.analysis-box { background: #f8f9fa; border-radius: 10px; padding: 20px; border-right: 5px solid #6c5ce7; margin-top: 15px; direction: rtl; line-height: 2;}
.fix-badge { background: #d4edda; color: #155724; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# القائمة الجانبية - إعدادات الذكاء الاصطناعي
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("🤖 إعدادات الذكاء الاصطناعي")
    st.markdown("أدخل مفتاح **Mistral AI** لتفعيل ميزة التحليل البيداغوجي المتقدم للنتائج.")
    mistral_api_key = st.text_input(
        "MISTRAL_API_KEY:",
        type="password",
        help="احصل على المفتاح من console.mistral.ai"
    )
    if mistral_api_key:
        st.success("✅ المفتاح متوفر")
    else:
        st.warning("⚠️ اختياري — لتفعيل التحليل الذكي")

st.markdown("""
<div class="ai-box">
    <h1 style="color:white; text-align:center;">🏫🤖 النظام الذكي لحساب معدلات التلاميذ</h1>
    <p style="text-align:center; font-size:16px;"> متوافق كلياً مع مستخرجات الأرضية الرقمية (الرقمنة) | مدعوم بالتحليل البيداغوجي لـ Mistral AI </p>
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
# الدوال المساعدة (مُصحَّحة)
# ══════════════════════════════════════════════════════════════
def normalize_arabic(text):
    """توحيد النص العربي لتسهيل المقارنة"""
    if pd.isna(text): return ""
    text = str(text).strip()
    text = re.sub(r'\s+', ' ', text)
    for old, new in [('أ', 'ا'), ('إ', 'ا'), ('آ', 'ا'), ('ة', 'ه'), ('ى', 'ي'), ('ئ', 'ي'), ('ؤ', 'و')]:
        text = text.replace(old, new)
    return text

def get_expected_sheet_name(level, subject_name):
    """اقتراح اسم الشيت المتوقع حسب المستوى والمادة (للأرضية الرقمية)"""
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
        }
    }
    return mapping.get(subject_name, {}).get(level, subject_name)

# ── إصلاح #3: دالة أكثر أماناً لاكتشاف عمود الاسم ──
def process_names(df):
    """
    البحث عن عمود الاسم أو إنشاؤه من عمودي اللقب والاسم.
    الأولوية: عمود مدمج > عمودين منفصلين > أول عمود نصي.
    """
    nom_col, prenom_col, combined_col = None, None, None
    for col in df.columns:
        c_str = str(col).strip()
        c_norm = normalize_arabic(c_str)
        # 1) البحث عن عمود مدمج أولاً (أعلى أولوية)
        if any(kw in c_norm for kw in ['لقب والاسم', 'اسم واللقب', 'اسم ولقب', 'لقب واسم', 'التلميذ', 'الطالب']):
            combined_col = col
        # 2) عمود اللقب
        elif c_norm in ['اللقب', 'لقب'] or c_str.lower() == 'nom':
            nom_col = col
        # 3) عمود الاسم
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

    # احتياطي: أول عمود نصي ليس رقمياً/تقنياً
    skip_kw = ['رقم', 'ملاحظ', 'تاريخ', 'قرار', 'ترتيب', 'معدل', 'مجموع', '#', 'num', 'id']
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].notna().sum() > 0:
            if not any(kw in normalize_arabic(str(col)) for kw in skip_kw):
                return col
    return None

def clean_grade_value(val):
    """تحويل خلية نقطة إلى رقم مع معالجة (غائب / معفى / الفاصلة)"""
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
            return v if v <= 20 else np.nan  # حاجز أمان
        except ValueError:
            return np.nan
    return np.nan

# ── إصلاح #7: اكتشاف الأعمدة الرقمية بعد التنظيف ──
def get_gradeable_columns(df, name_col=None):
    """
    اكتشاف الأعمدة التي تحتوي فعلاً على نقاط قابلة للحساب (بعد تنظيف القيم النصية مثل 'غائب')
    """
    ignore_patterns = ['رقم', 'matricule', 'تاريخ', 'date', 'لقب', 'اسم', 'nom', 'prenom', 'obs', 'ملاحظ', 'قرار', 'ترتيب', 'معدل', 'مجموع', 'عدد']
    result = []
    for col in df.columns:
        if col == name_col:
            continue
        col_norm = normalize_arabic(str(col)).lower()
        if any(ign in col_norm for ign in ignore_patterns):
            continue
        # نُنظّف ثم نتحقق
        cleaned = df[col].apply(clean_grade_value)
        valid_count = cleaned.notna().sum()
        if valid_count >= max(1, len(df) * 0.1):
            result.append(col)
    return result

# ── إصلاح #5: اكتشاف أعمدة الفروض والاختبار بشكل أدق ──
def detect_subject_columns(df, subject_keywords, gradeable_cols):
    """
    يبحث فقط ضمن الأعمدة القابلة للحساب (gradeable_cols) ويعيد أول عمود اختبار (وليس آخر عمود).
    """
    quiz_cols = []
    test_col = None
    for col in gradeable_cols:
        col_norm = normalize_arabic(str(col))
        is_test = any(normalize_arabic(kw) in col_norm for kw in subject_keywords.get('tests', []))
        is_quiz = any(normalize_arabic(kw) in col_norm for kw in subject_keywords.get('quizzes', []))
        if is_quiz:
            quiz_cols.append(col)
        elif is_test and test_col is None:  # ← نحتفظ بأول عمود اختبار
            test_col = col
    return quiz_cols, test_col

# ── إصلاح #3: قراءة الشيت بدون حذف أسطر بيانات ──
def read_sheet_safe(file, sheet_name):
    """قراءة ورقة Excel مع الكشف التلقائي عن سطر العناوين"""
    file.seek(0)
    try:
        temp_df = pd.read_excel(file, sheet_name=sheet_name, header=None, dtype=str)
    except Exception as e:
        st.error(f"❌ خطأ في قراءة الورقة «{sheet_name}»: {e}")
        return pd.DataFrame()
    
    header_idx = 0
    for i, row in temp_df.head(15).iterrows():
        row_str = ' '.join(row.dropna().astype(str))
        row_norm = normalize_arabic(row_str)
        # نبحث عن سطر يحتوي على مفاتيح ترويسة حقيقية
        if (('لقب' in row_norm and 'اسم' in row_norm) or ('nom' in row_str.lower() and 'prenom' in row_str.lower())):
            header_idx = i
            break
            
    file.seek(0)
    df = pd.read_excel(file, sheet_name=sheet_name, header=header_idx)
    df.columns = df.columns.astype(str).str.replace('\n', ' ').str.strip()
    df = df.dropna(how='all').reset_index(drop=True)
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

# ── إصلاح #6: إضافة timeout لطلب API ──
def call_mistral_api(api_key, prompt):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "system", "content": ("أنت مفتش تربوي جزائري خبير في التعليم الابتدائي. "
                                           "مهمتك تقديم تحليلات دقيقة وتوصيات بيداغوجية "
                                           "لتحسين مستوى التلاميذ بناءً على إحصائيات معدلاتهم.")},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return f"❌ خطأ {response.status_code}: {response.text}"
    except requests.exceptions.Timeout:
        return "❌ انتهت مهلة الاتصال بالخادم. حاول مجدداً."
    except Exception as e:
        return f"❌ خطأ في الاتصال: {e}"

# ══════════════════════════════════════════════════════════════
# إدارة حالة الجلسة
# ══════════════════════════════════════════════════════════════
for key, default in [('subject_mappings', {}), ('final_result', None), ('selected_level', list(LEVELS.keys())[0]), ('subject_cols', [])]:
    if key not in st.session_state:
        st.session_state[key] = default

# ══════════════════════════════════════════════════════════════
# الخطوة 1: اختيار المستوى الدراسي
# ══════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════
# الخطوة 2: رفع ملفات الأساتذة
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📁 الخطوة 2: رفع ملفات الأساتذة")

# ── إصلاح #4: استخدام قائمة مرتبة بدلاً من set ──
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

# ══════════════════════════════════════════════════════════════
# الخطوة 3: ربط المواد بالشيتات والأعمدة
# ══════════════════════════════════════════════════════════════
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
        
        # اقتراح ذكي لاسم الشيت
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
            
        # اكتشاف الأعمدة القابلة للحساب (بعد التنظيف)
        local_name_col = process_names(df_sheet)
        gradeable_cols = get_gradeable_columns(df_sheet, local_name_col)
        
        quiz_cols_detected, test_col_detected = detect_subject_columns(
            df_sheet, subject['keywords'], gradeable_cols
        )
        
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
                # افتراضياً: آخر عمود رقمي (عادةً يكون الاختبار)
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
            'type': subject['type']
        }
        
        with st.expander(f"👁️ معاينة «{selected_sheet}»"):
            st.dataframe(df_sheet.head(4), use_container_width=True)
        st.markdown("---")

st.session_state.subject_mappings = subject_mappings

# ══════════════════════════════════════════════════════════════
# الخطوة 4: الدمج وحساب المعدلات (الإصلاح الجوهري)
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("⚙️ الخطوة 4: الدمج وحساب المعدلات")

if st.button("🚀 بدء الحساب", type="primary", use_container_width=True):
    progress = st.progress(0, text="بدء المعالجة...")
    
    # ── المرحلة 1: حساب نقطة كل مادة لكل تلميذ ──
    subject_grades = {}  # subject_name → DataFrame(_key, grade)
    master_names = None  # DataFrame(_key, الاسم) من ملف معلم القسم
    computation_log = [] # سجل العمليات للعرض
    
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
        
        # ── بناء القائمة المرجعية من ملف معلم القسم ──
        if teacher == "معلم القسم" and master_names is None:
            master_names = (df[['_key', name_col]]
                            .rename(columns={name_col: 'الاسم'})
                            .drop_duplicates('_key')
                            .reset_index(drop=True))
        elif master_names is None:
            # احتياطي: إذا لم يُعالَج معلم القسم بعد
            master_names = (df[['_key', name_col]]
                            .rename(columns={name_col: 'الاسم'})
                            .drop_duplicates('_key')
                            .reset_index(drop=True))
                            
        # ── حساب النقطة النهائية للمادة ──
        test_col = mapping['test_col']
        test_score = (df[test_col].apply(clean_grade_value) if test_col and test_col in df.columns else pd.Series(np.nan, index=df.index))
        
        if mapping['type'] == 'main' and mapping['quiz_cols']:
            # مادة أساسية: معدل = (معدل الفروض + الاختبار) / 2
            quiz_scores = [df[qc].apply(clean_grade_value) for qc in mapping['quiz_cols'] if qc in df.columns]
            if quiz_scores:
                quiz_avg = pd.concat(quiz_scores, axis=1).mean(axis=1, skipna=True)
            else:
                quiz_avg = pd.Series(np.nan, index=df.index)
                
            both_ok = quiz_avg.notna() & test_score.notna()
            final_grade = pd.Series(np.nan, index=df.index)
            final_grade[both_ok] = ((quiz_avg[both_ok] + test_score[both_ok]) / 2)
            
            # احتياطي: إذا توفر جزء واحد فقط
            final_grade = final_grade.fillna(quiz_avg).fillna(test_score)
            
            computation_log.append(
                f"✅ {subject_name} (أساسية): "
                f"فروض={len(quiz_scores)} أعمدة + اختبار → معدل المادة"
            )
        else:
            # مادة ثانوية: النقطة النهائية مباشرة
            final_grade = test_score
            computation_log.append(f"✅ {subject_name} (ثانوية): نقطة واحدة مباشرة")
            
        # ── إصلاح #1 و #2: نخزن فقط _key + النقطة ──
        sg = pd.DataFrame({
            '_key': df['_key'],
            subject_name: final_grade
        }).drop_duplicates('_key')
        
        subject_grades[subject_name] = sg
        
    # ── التحقق ──
    if not subject_grades:
        st.error("❌ لم يتم حساب أي مادة!")
        st.stop()
        
    if master_names is None or master_names.empty:
        st.error("❌ لم يتم العثور على قائمة أسماء التلاميذ!")
        st.stop()
        
    # ── عرض سجل العمليات ──
    with st.expander("📋 سجل العمليات"):
        for log in computation_log:
            st.write(log)
            
    # ── المرحلة 2: الدمج على _key فقط ──
    progress.progress(60, text="دمج البيانات...")
    merged = master_names.copy()
    
    for subj_name, sg_df in subject_grades.items():
        merged = pd.merge(
            merged, sg_df[['_key', subj_name]],  # فقط المفتاح + النقطة
            on='_key',
            how='left'
        )
        
    # إضافة التلاميذ الموجودين في ملفات أخرى وغير موجودين عند معلم القسم
    all_extra_keys = set()
    for subj_name, sg_df in subject_grades.items():
        all_extra_keys.update(sg_df['_key'].tolist())
        
    missing_keys = all_extra_keys - set(merged['_key'].tolist())
    
    if missing_keys:
        # محاولة جلب أسماء هؤلاء التلاميذ من أي ملف متوفر
        extra_rows = []
        for mk in missing_keys:
            name_found = mk  # افتراضي
            for subj_name, sg_df in subject_grades.items():
                # نعود للملف الأصلي للبحث عن الاسم الحقيقي
                pass  # الاسم المعياري يكفي كاحتياطي
                
            row = {'_key': mk, 'الاسم': mk}
            for subj_name, sg_df in subject_grades.items():
                match = sg_df[sg_df['_key'] == mk]
                row[subj_name] = (match[subj_name].iloc[0] if not match.empty else np.nan)
            extra_rows.append(row)
            
        if extra_rows:
            extra_df = pd.DataFrame(extra_rows)
            merged = pd.concat([merged, extra_df], ignore_index=True)
            
    # ── المرحلة 3: الحسابات النهائية ──
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
    
    # الترتيب
    merged = (merged
              .sort_values('المعدل الفصلي', ascending=False)
              .reset_index(drop=True))
    merged.insert(0, 'الترتيب', range(1, len(merged) + 1))
    merged = merged.drop(columns=['_key'], errors='ignore')
    
    progress.progress(100, text="✅ اكتمل الحساب!")
    st.session_state.final_result = merged
    st.session_state.subject_cols = subject_col_names

# ══════════════════════════════════════════════════════════════
# عرض النتائج وتحميلها
# ══════════════════════════════════════════════════════════════
if st.session_state.final_result is not None:
    final_df = st.session_state.final_result
    subject_cols = st.session_state.subject_cols
    
    st.markdown("---")
    st.subheader("📊 كشف النقاط الإجمالي")
    
    display_cols = (['الترتيب', 'الاسم'] + subject_cols + ['عدد المواد', 'المجموع', 'المعدل الفصلي', 'التقدير'])
    display_cols = [c for c in display_cols if c in final_df.columns]
    
    st.dataframe(final_df[display_cols], use_container_width=True, height=450)
    
    # ── إحصائيات ──
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
        
    # ── تحميل Excel ──
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        export_df = final_df[display_cols]
        export_df.to_excel(writer, index=False, sheet_name="النتائج")
        ws = writer.sheets["النتائج"]
        for i, col in enumerate(display_cols):
            max_len = max(
                export_df[col].astype(str).map(len).max(), len(str(col))
            ) + 2
            ws.set_column(i, i, min(max_len, 35))
            
    st.download_button(
        "📥 تحميل النتائج (Excel)",
        data=output.getvalue(),
        file_name=(f"النتائج_{selected_level}_" f"{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"),
        use_container_width=True
    )

    # ══════════════════════════════════════════════════════════
    # الخطوة 5: التحليل البيداغوجي بالذكاء الاصطناعي
    # ══════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("🧠 الخطوة 5: التحليل البيداغوجي المتقدم")
    
    if not mistral_api_key:
        st.info("💡 أدخل مفتاح Mistral API في القائمة الجانبية " "لتفعيل التحليل الذكي للنتائج.")
    else:
        st.write("اضغط على الزر ليقوم الذكاء الاصطناعي بتحليل النتائج " "وإعطاء توصيات بيداغوجية.")
        if st.button("✨ توليد التقرير التحليلي", type="secondary"):
            with st.spinner("🤖 جاري التحليل..."):
                subject_avgs = (final_df[subject_cols]
                                .mean().round(2).to_dict())
                class_avg = round(final_df['المعدل الفصلي'].mean(), 2)
                pass_r = round(
                    (final_df['المعدل الفصلي'] >= 5).mean() * 100, 1
                )
                grades_dist = (final_df['التقدير']
                               .value_counts().to_dict())
                               
                prompt = f"""أنت مفتش تربوي جزائري خبير في مرحلة التعليم الابتدائي.
                بناءً على الإحصائيات التالية لنتائج الفصل الدراسي، قم بتقديم تقرير مفصل:
                
                **البيانات:**
                - المستوى: {selected_level}
                - عدد التلاميذ: {len(final_df)}
                - المعدل العام للقسم: {class_avg} / 10
                - نسبة النجاح (≥ 5): {pass_r}%
                
                معدلات المواد (من 10):
                {json.dumps(subject_avgs, ensure_ascii=False, indent=2)}
                
                توزيع التقديرات:
                {json.dumps(grades_dist, ensure_ascii=False, indent=2)}
                
                **المطلوب:**
                1. قراءة تحليلية عامة لمستوى القسم ونسبة النجاح.
                2. تحديد نقاط القوة (المواد ذات الأداء العالي).
                3. تحديد نقاط الضعف (المواد التي تحتاج تدخلاً).
                4. تقديم 3 توصيات بيداغوجية عملية وواقعية.
                الرد باللغة العربية بأسلوب احترافي مع تنسيق Markdown."""
                
                ai_response = call_mistral_api(mistral_api_key, prompt)
                
                st.markdown(
                    f'<div class="analysis-box">{ai_response}</div>',
                    unsafe_allow_html=True
                )

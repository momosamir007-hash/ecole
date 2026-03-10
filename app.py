import streamlit as st
import pandas as pd
import io
import re
import json
import requests
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
.ai-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; padding: 20px; margin: 15px 0; color: white; box-shadow: 0 8px 32px rgba(102,126,234,0.3); }
.ai-response { background: #f8f9ff; border-radius: 12px; padding: 20px; margin: 10px 0; border-right: 5px solid #667eea; line-height: 2; direction: rtl; }
.mapping-box { background: #e8f4fd; border-radius: 10px; padding: 15px; margin: 8px 0; border-right: 4px solid #2196F3; }
.subject-box { background: #f0f8e8; border-radius: 10px; padding: 12px; margin: 5px 0; border-right: 4px solid #4CAF50; }
.warn-box { background: #fff8e1; border-radius: 10px; padding: 12px; margin: 5px 0; border-right: 4px solid #FF9800; }
.student-card { background: white; border-radius: 10px; padding: 15px; margin: 8px 0; border: 1px solid #e0e0e0; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ai-box">
    <h1 style="color:white; text-align:center;">🏫🤖 النظام الذكي لحساب معدلات التلاميذ</h1>
    <p style="text-align:center; font-size:16px;"> المرحلة الابتدائية — الجمهورية الجزائرية | مدعوم بـ Mistral AI </p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 🗂️ تعريف المواد لكل مستوى دراسي
# ══════════════════════════════════════════════════════════════
LEVELS = {
    "السنة الأولى": {
        "files": {
            "معلم القسم": {
                "required": True, "icon": "📄",
                "subjects": ["اللغة العربية", "الرياضيات", "التربية الإسلامية", "التربية الموسيقية", "التربية التشكيلية"]
            },
            "أستاذ التربية البدنية": {
                "required": True, "icon": "🏃",
                "subjects": ["ت البدنية والرياضية"]
            },
        },
        "total_subjects": 6
    },
    "السنة الثانية": {
        "files": {
            "معلم القسم": {
                "required": True, "icon": "📄",
                "subjects": ["اللغة العربية", "الرياضيات", "التربية الإسلامية", "التربية الموسيقية", "التربية التشكيلية"]
            },
            "أستاذ التربية البدنية": {
                "required": True, "icon": "🏃",
                "subjects": ["ت البدنية والرياضية"]
            },
        },
        "total_subjects": 6
    },
    "السنة الثالثة": {
        "files": {
            "معلم القسم": {
                "required": True, "icon": "📄",
                "subjects": ["اللغة العربية", "الرياضيات", "التربية الإسلامية", "ت العلمية و التكنولوجية", "التاريخ", "التربية التشكيلية", "التربية الموسيقية"]
            },
            "أستاذ التربية البدنية": {
                "required": True, "icon": "🏃", "subjects": ["ت البدنية والرياضية"]
            },
            "أستاذ اللغة الفرنسية": {
                "required": True, "icon": "🇫🇷", "subjects": ["اللغة الفرنسية"]
            },
            "أستاذ اللغة الإنجليزية": {
                "required": True, "icon": "🇬🇧", "subjects": ["اللغة الإنجليزية"]
            },
        },
        "total_subjects": 10
    },
    "السنة الرابعة": {
        "files": {
            "معلم القسم": {
                "required": True, "icon": "📄",
                "subjects": ["اللغة العربية", "الرياضيات", "التربية الإسلامية", "ت العلمية و التكنولوجية", "التربية المدنية", "التاريخ و الجغرافيا", "التربية التشكيلية", "التربية الموسيقية"]
            },
            "أستاذ التربية البدنية": {
                "required": True, "icon": "🏃", "subjects": ["ت البدنية والرياضية"]
            },
            "أستاذ اللغة الفرنسية": {
                "required": True, "icon": "🇫🇷", "subjects": ["اللغة الفرنسية"]
            },
            "أستاذ اللغة الإنجليزية": {
                "required": True, "icon": "🇬🇧", "subjects": ["اللغة الإنجليزية"]
            },
        },
        "total_subjects": 11
    },
    "السنة الخامسة": {
        "files": {
            "معلم القسم": {
                "required": True, "icon": "📄",
                "subjects": ["اللغة العربية", "الرياضيات", "التربية الإسلامية", "ت العلمية و التكنولوجية", "التربية المدنية", "التاريخ و الجغرافيا", "التربية التشكيلية", "التربية الموسيقية"]
            },
            "أستاذ التربية البدنية": {
                "required": True, "icon": "🏃", "subjects": ["ت البدنية والرياضية"]
            },
            "أستاذ اللغة الفرنسية": {
                "required": True, "icon": "🇫🇷", "subjects": ["اللغة الفرنسية"]
            },
            "أستاذ اللغة الإنجليزية": {
                "required": True, "icon": "🇬🇧", "subjects": ["اللغة الإنجليزية"]
            },
        },
        "total_subjects": 11
    }
}

# ══════════════════════════════════════════════════════════════
# Mistral AI — الإعداد
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ إعدادات الذكاء الاصطناعي")
    api_key = None
    try:
        api_key = st.secrets["MISTRAL_API_KEY"]
    except:
        pass
        
    if not api_key:
        api_key = st.text_input("🔑 مفتاح Mistral API", type="password")
        
    if api_key:
        st.success("✅ API مُفعّل")
    else:
        st.info("💡 اختياري — لتفعيل التحليل الذكي")
        
    ai_model = st.selectbox("🧠 النموذج", ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest", "open-mistral-nemo"])
    ai_temp = st.slider("🌡️ الإبداعية", 0.0, 1.0, 0.7)

# ══════════════════════════════════════════════════════════════
# الدوال المساعدة الذكية
# ══════════════════════════════════════════════════════════════
def normalize_arabic(text):
    if pd.isna(text): return ""
    text = str(text).strip()
    text = re.sub(r'\s+', ' ', text)
    for old, new in [('أ','ا'),('إ','ا'),('آ','ا'), ('ة','ه'),('ى','ي'),('ئ','ي'),('ؤ','و')]:
        text = text.replace(old, new)
    return text

def find_name_column(df):
    keywords = ['اللقب والاسم','الاسم واللقب','لقب واسم', 'اسم ولقب','اسم','لقب','الاسم','اللقب', 'التلميذ','الطالب','nom','name','élève']
    for col in df.columns:
        col_str = str(col).strip()
        for kw in keywords:
            if kw in col_str: return col
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].notna().sum() > 0: return col
    return None

def clean_and_extract_grades(df, exclude_cols=None):
    """ تنظيف متقدم: يزيل (غائب/معفى)، ويصلح الفواصل (15,5 -> 15.5) ويستخرج أعمدة النقاط """
    if exclude_cols is None: exclude_cols = []
    skip = ['رقم','ترتيب','تسلسل','ميلاد','تاريخ','ملاحظ','قسم','فوج','سنة','جنس','هاتف','ولي','#','num','id','قرار','مواظبة','سلوك']
    
    grade_cols = []
    cleaned_df = df.copy()
    
    for col in cleaned_df.columns:
        if col in exclude_cols: continue
        col_lower = str(col).strip().lower()
        if any(kw in col_lower for kw in skip): continue
        
        # تحويل القيم لنصوص، إصلاح الفاصلة، والبحث عن أول رقم
        s_str = cleaned_df[col].astype(str).str.replace(',', '.')
        extracted = s_str.str.extract(r'(\d+\.?\d*)')[0]
        s_num = pd.to_numeric(extracted, errors='coerce')
        
        valid_count = s_num.notna().sum()
        # نعتبره عمود نقاط إذا كان فيه أرقام صالحة (على الأقل 3 تلاميذ أو 10% من القسم)
        if valid_count > 0 and (valid_count >= len(cleaned_df) * 0.1 or valid_count >= 3):
            if s_num.max() <= 100: # تجنب أعمدة كأرقام الهواتف أو السنوات
                grade_cols.append(col)
                cleaned_df[col] = s_num # تعويض العمود بالقيم الرقمية النظيفة
                
    return cleaned_df, grade_cols

def get_subject_aliases(subject):
    """ قاموس مرادفات المواد الذكي لتفادي مشاكل اختلاف التسميات """
    aliases = {
        "اللغة العربية": ["لغة", "عربية", "قراءة", "تعبير", "املاء"],
        "الرياضيات": ["رياضيات", "حساب", "هندسة"],
        "التربية الإسلامية": ["اسلامية", "إسلامية", "دين", "قرآن"],
        "ت العلمية و التكنولوجية": ["علمية", "تكنولوجيا", "علوم", "تكنولوجية"],
        "التربية المدنية": ["مدنية", "تربية مدنية"],
        "التاريخ و الجغرافيا": ["تاريخ", "جغرافيا", "اجتماعيات"],
        "التاريخ": ["تاريخ"],
        "التربية التشكيلية": ["تشكيلية", "رسم", "فنية"],
        "التربية الموسيقية": ["موسيقية", "موسيقى", "انشاد", "محفوظات"],
        "ت البدنية والرياضية": ["بدنية", "رياضة", "تربية بدنية", "بدنيه", "رياضيه"],
        "اللغة الفرنسية": ["فرنسية", "fr", "francais", "français"],
        "اللغة الإنجليزية": ["انجليزية", "en", "eng", "english"]
    }
    return aliases.get(subject, [subject])

def match_subject_columns(df_columns, expected_subjects):
    matched = {}
    remaining_cols = list(df_columns)
    
    for subject in expected_subjects:
        aliases = get_subject_aliases(subject)
        best_col = None
        best_score = 0
        
        for col in remaining_cols:
            col_norm = normalize_arabic(str(col))
            for alias in aliases:
                alias_norm = normalize_arabic(alias)
                if col_norm == alias_norm:
                    score = 100
                elif alias_norm in col_norm or col_norm in alias_norm:
                    score = 80
                else:
                    score = len(set(alias_norm.split()) & set(col_norm.split())) * 30
                    
                if score > best_score:
                    best_score = score
                    best_col = col
                    
        if best_col and best_score >= 30:
            matched[best_col] = subject
            remaining_cols.remove(best_col)
            
    return matched

def read_sheet_safe(file, sheet_name):
    """ قراءة الملف مع الكشف التلقائي عن ترويسة الجدول (Headers) لتخطي العناوين الكبيرة """
    file.seek(0)
    # نقرأ أول 15 سطر بحثاً عن كلمة الاسم أو اللقب
    temp_df = pd.read_excel(file, sheet_name=sheet_name, header=None)
    header_idx = 0
    for i, row in temp_df.head(15).iterrows():
        row_str = ' '.join(row.dropna().astype(str)).lower()
        if any(kw in row_str for kw in ['اسم', 'لقب', 'الاسم', 'اللقب', 'nom', 'eleve']):
            header_idx = i
            break
            
    file.seek(0)
    df = pd.read_excel(file, sheet_name=sheet_name, header=header_idx)
    df.columns = df.columns.astype(str).str.replace('\n', ' ').str.strip()
    df = df.dropna(how='all')
    return df

def get_sheet_names_safe(file):
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
# الخطوة 1: اختيار المستوى الدراسي
# ══════════════════════════════════════════════════════════════
st.subheader("📚 الخطوة 1: اختر المستوى الدراسي")
selected_level = st.selectbox("🎓 المستوى:", list(LEVELS.keys()))
level_config = LEVELS[selected_level]

st.markdown(f"""
<div class="subject-box">
<strong>📋 مواد {selected_level} ({level_config['total_subjects']} مادة):</strong><br>
""", unsafe_allow_html=True)
for teacher, info in level_config["files"].items():
    st.markdown(f"**{info['icon']} {teacher}**: {' ، '.join(info['subjects'])}")

# ══════════════════════════════════════════════════════════════
# الخطوة 2: رفع الملفات
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📁 الخطوة 2: رفع ملفات الأساتذة")
uploaded_files = {}
required_files = level_config["files"]
cols = st.columns(min(len(required_files), 4))

for i, (teacher_name, teacher_info) in enumerate(required_files.items()):
    with cols[i % len(cols)]:
        f = st.file_uploader(f"{teacher_info['icon']} {teacher_name}", type=['xlsx', 'xls'], key=f"up_{teacher_name}")
        if f: uploaded_files[teacher_name] = f
        elif teacher_info["required"]: st.caption("⏳ مطلوب")

missing = [t for t, info in required_files.items() if info["required"] and t not in uploaded_files]
if missing:
    st.warning(f"⏳ في انتظار رفع: **{' ، '.join(missing)}**")
    st.stop()

st.success("✅ تم رفع جميع الملفات المطلوبة!")

# ══════════════════════════════════════════════════════════════
# الخطوة 3: ربط الأوراق (Sheets)
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("🔗 الخطوة 3: ربط أوراق العمل بين الملفات")
all_sheets = {t: get_sheet_names_safe(f) for t, f in uploaded_files.items()}

sheet_mapping = {}
st.write("#### 1️⃣ ملف معلم القسم (المرجع الأساسي)")
selected_ref_sheet = st.selectbox("📄 اختر ورقة القسم:", all_sheets["معلم القسم"], key="ref_sheet")
sheet_mapping["معلم القسم"] = selected_ref_sheet

with st.expander(f"👁️ معاينة وتأكد من البيانات: «{selected_ref_sheet}»"):
    preview = read_sheet_safe(uploaded_files["معلم القسم"], selected_ref_sheet)
    nc = find_name_column(preview)
    preview_clean, gc = clean_and_extract_grades(preview, [nc] if nc else [])
    st.write(f"**{len(preview_clean)} تلميذ** | عمود الاسم: `{nc}` | أعمدة النقاط المكتشفة: `{gc}`")
    st.dataframe(preview_clean.head(5), use_container_width=True)

if len(uploaded_files) > 1:
    st.write("#### 2️⃣ ملفات الأساتذة الآخرين")
    for teacher_name, file in uploaded_files.items():
        if teacher_name == "معلم القسم": continue
        teacher_sheets = all_sheets[teacher_name]
        
        # اقتراح ذكي
        suggested_idx = 0
        ref_norm = normalize_arabic(selected_ref_sheet.lower())
        for idx, sh in enumerate(teacher_sheets):
            if ref_norm in normalize_arabic(sh.lower()):
                suggested_idx = idx; break
            if set(re.findall(r'\d+', selected_ref_sheet)) & set(re.findall(r'\d+', sh)):
                suggested_idx = idx; break
                
        col_a, col_b = st.columns([4, 1])
        with col_a:
            selected = st.selectbox(
                f"{required_files[teacher_name]['icon']} **{teacher_name}**:", 
                teacher_sheets, index=suggested_idx, key=f"map_{teacher_name}"
            )
            sheet_mapping[teacher_name] = selected
        with col_b:
            st.markdown("<br>", unsafe_allow_html=True)
            if suggested_idx > 0: st.success("🤖 مقترحة")

# ══════════════════════════════════════════════════════════════
# الخطوة 4: الدمج وحساب المعدلات
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("⚙️ الخطوة 4: الدمج وحساب المعدلات")

if st.button("🚀 بدء الدمج وحساب المعدلات", type="primary", use_container_width=True):
    progress = st.progress(0, text="بدء المعالجة...")
    raw_data = {}
    
    # قراءة الملفات
    for step, (teacher_name, file) in enumerate(uploaded_files.items()):
        progress.progress(int((step+1) / (len(uploaded_files)+4) * 100), text=f"قراءة {teacher_name}...")
        try:
            df = read_sheet_safe(file, sheet_mapping[teacher_name])
            if len(df) > 0: raw_data[teacher_name] = df
        except Exception as e:
            st.error(f"❌ خطأ في {teacher_name}: {e}")
            
    if "معلم القسم" not in raw_data: st.stop()

    # تحديد الاسم والتنظيف
    ref_df = raw_data["معلم القسم"]
    name_col = find_name_column(ref_df)
    if not name_col:
        st.error("❌ لم يُعثر على عمود يحتوي على أسماء التلاميذ!")
        st.stop()
        
    ref_df['_key'] = ref_df[name_col].apply(normalize_arabic)
    
    # تنظيف واستخراج النقاط لمعلم القسم
    ref_df, ref_grade_cols = clean_and_extract_grades(ref_df, [name_col, '_key'])
    ref_col_mapping = match_subject_columns(ref_grade_cols, required_files["معلم القسم"]["subjects"])
    if ref_col_mapping: ref_df = ref_df.rename(columns=ref_col_mapping)
    
    found_subjects = list(ref_col_mapping.values()) if ref_col_mapping else ref_grade_cols
    final_df = ref_df.copy()
    
    st.write("### 🔍 مسار دمج المواد")
    st.write(f"📄 **معلم القسم:** تم جلب `{found_subjects}`")

    # دمج البقية
    for teacher_name, df in raw_data.items():
        if teacher_name == "معلم القسم": continue
        icon = required_files[teacher_name]["icon"]
        expected = required_files[teacher_name]["subjects"]
        
        other_name_col = find_name_column(df)
        if not other_name_col: continue
        
        # التنظيف الذكي لملف الأستاذ (سيحول "غائب" لـ NaN، ويصلح الفواصل)
        df, other_grade_cols = clean_and_extract_grades(df, [other_name_col])
        col_mapping = match_subject_columns(other_grade_cols, expected)
        
        # إذا كانت مادة واحدة ولم يتعرف على الاسم (مثلا التربية البدنية اسمها "المعدل")، نفرضها
        if not col_mapping and len(other_grade_cols) >= 1 and len(expected) == 1:
            col_mapping = {other_grade_cols[0]: expected[0]}
        elif not col_mapping:
            col_mapping = {c: c for c in other_grade_cols}
            
        st.write(f"{icon} **{teacher_name}:** تم جلب `{list(col_mapping.values())}`")
        
        merge_cols = [other_name_col] + list(col_mapping.keys())
        merge_df = df[merge_cols].rename(columns=col_mapping)
        merge_df['_key'] = merge_df[other_name_col].apply(normalize_arabic).drop(columns=[other_name_col], errors='ignore')
        
        final_df = pd.merge(final_df, merge_df, on='_key', how='left')
        found_subjects.extend(col_mapping.values())

    # الحساب النهائي
    final_df = final_df.drop(columns=['_key'], errors='ignore')
    final_subject_cols = [c for c in final_df.columns if c in found_subjects or (pd.api.types.is_numeric_dtype(final_df[c]) and final_df[c].max() <= 100)]
    final_subject_cols = [c for c in final_subject_cols if c not in [name_col, 'الترتيب','المجموع','المعدل','التقدير','عدد المواد']]

    if not final_subject_cols:
        st.error("❌ لم يتم العثور على أي نقاط للحساب (تأكد من اختيار الأوراق الصحيحة).")
        st.stop()
        
    final_df['عدد المواد'] = final_df[final_subject_cols].notna().sum(axis=1)
    final_df['المجموع'] = final_df[final_subject_cols].sum(axis=1)
    # تجنب القسمة على صفر
    final_df['المعدل'] = (final_df['المجموع'] / final_df['عدد المواد'].replace(0, pd.NA)).round(2)
    final_df['التقدير'] = final_df['المعدل'].apply(classify_student)
    final_df = final_df.sort_values('المعدل', ascending=False).reset_index(drop=True)
    final_df.insert(0, 'الترتيب', range(1, len(final_df) + 1))
    
    progress.progress(100, text="✅ تمت العملية بنجاح!")
    
    st.session_state['final_df'] = final_df
    st.session_state['name_col'] = name_col
    st.session_state['subject_cols'] = final_subject_cols
    st.session_state['selected_sheet'] = sheet_mapping["معلم القسم"]
    st.session_state['selected_level'] = selected_level
    st.session_state['done'] = True

# ══════════════════════════════════════════════════════════════
# عرض وتصدير النتائج
# ══════════════════════════════════════════════════════════════
if st.session_state.get('done'):
    final_df = st.session_state['final_df']
    name_col = st.session_state['name_col']
    subject_cols = st.session_state['subject_cols']
    
    st.markdown("---")
    st.write("### 📊 كشف النقاط والمعدلات")
    display_cols = ['الترتيب', name_col] + subject_cols + ['عدد المواد', 'المجموع', 'المعدل', 'التقدير']
    st.dataframe(final_df[[c for c in display_cols if c in final_df.columns]], use_container_width=True, height=400)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        final_df[[c for c in display_cols if c in final_df.columns]].to_excel(writer, index=False, sheet_name="النتائج")
    st.download_button("📥 تحميل النتائج (Excel)", data=output.getvalue(), file_name="النتائج_النهائية.xlsx", use_container_width=True)



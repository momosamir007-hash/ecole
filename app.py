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
                "required": True,
                "icon": "📄",
                "subjects": [
                    "اللغة العربية", "الرياضيات", "التربية الإسلامية", "التربية الموسيقية", "التربية التشكيلية"
                ]
            },
            "أستاذ التربية البدنية": {
                "required": True,
                "icon": "🏃",
                "subjects": ["ت البدنية والرياضية"]
            },
        },
        "total_subjects": 6
    },
    "السنة الثانية": {
        "files": {
            "معلم القسم": {
                "required": True,
                "icon": "📄",
                "subjects": [
                    "اللغة العربية", "الرياضيات", "التربية الإسلامية", "التربية الموسيقية", "التربية التشكيلية"
                ]
            },
            "أستاذ التربية البدنية": {
                "required": True,
                "icon": "🏃",
                "subjects": ["ت البدنية والرياضية"]
            },
        },
        "total_subjects": 6
    },
    "السنة الثالثة": {
        "files": {
            "معلم القسم": {
                "required": True,
                "icon": "📄",
                "subjects": [
                    "اللغة العربية", "الرياضيات", "التربية الإسلامية", "ت العلمية و التكنولوجية", 
                    "التاريخ", "التربية التشكيلية", "التربية الموسيقية"
                ]
            },
            "أستاذ التربية البدنية": {
                "required": True,
                "icon": "🏃",
                "subjects": ["ت البدنية والرياضية"]
            },
            "أستاذ اللغة الفرنسية": {
                "required": True,
                "icon": "🇫🇷",
                "subjects": ["اللغة الفرنسية"]
            },
            "أستاذ اللغة الإنجليزية": {
                "required": True,
                "icon": "🇬🇧",
                "subjects": ["اللغة الإنجليزية"]
            },
        },
        "total_subjects": 10
    },
    "السنة الرابعة": {
        "files": {
            "معلم القسم": {
                "required": True,
                "icon": "📄",
                "subjects": [
                    "اللغة العربية", "الرياضيات", "التربية الإسلامية", "ت العلمية و التكنولوجية", 
                    "التربية المدنية", "التاريخ و الجغرافيا", "التربية التشكيلية", "التربية الموسيقية"
                ]
            },
            "أستاذ التربية البدنية": {
                "required": True,
                "icon": "🏃",
                "subjects": ["ت البدنية والرياضية"]
            },
            "أستاذ اللغة الفرنسية": {
                "required": True,
                "icon": "🇫🇷",
                "subjects": ["اللغة الفرنسية"]
            },
            "أستاذ اللغة الإنجليزية": {
                "required": True,
                "icon": "🇬🇧",
                "subjects": ["اللغة الإنجليزية"]
            },
        },
        "total_subjects": 11
    },
    "السنة الخامسة": {
        "files": {
            "معلم القسم": {
                "required": True,
                "icon": "📄",
                "subjects": [
                    "اللغة العربية", "الرياضيات", "التربية الإسلامية", "ت العلمية و التكنولوجية", 
                    "التربية المدنية", "التاريخ و الجغرافيا", "التربية التشكيلية", "التربية الموسيقية"
                ]
            },
            "أستاذ التربية البدنية": {
                "required": True,
                "icon": "🏃",
                "subjects": ["ت البدنية والرياضية"]
            },
            "أستاذ اللغة الفرنسية": {
                "required": True,
                "icon": "🇫🇷",
                "subjects": ["اللغة الفرنسية"]
            },
            "أستاذ اللغة الإنجليزية": {
                "required": True,
                "icon": "🇬🇧",
                "subjects": ["اللغة الإنجليزية"]
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
        
    ai_model = st.selectbox("🧠 النموذج", [
        "mistral-large-latest", "mistral-medium-latest", "mistral-small-latest", "open-mistral-nemo"
    ])
    ai_temp = st.slider("🌡️ الإبداعية", 0.0, 1.0, 0.7)

# ══════════════════════════════════════════════════════════════
# الدوال المساعدة
# ══════════════════════════════════════════════════════════════
def normalize_arabic(text):
    """توحيد النصوص العربية للمطابقة"""
    if pd.isna(text): return ""
    text = str(text).strip()
    text = re.sub(r'\s+', ' ', text)
    for old, new in [('أ','ا'),('إ','ا'),('آ','ا'), ('ة','ه'),('ى','ي'),('ئ','ي'),('ؤ','و')]:
        text = text.replace(old, new)
    return text

def find_name_column(df):
    """البحث عن عمود الاسم"""
    keywords = ['اللقب والاسم','الاسم واللقب','لقب واسم', 'اسم ولقب','اسم','لقب','الاسم','اللقب', 'التلميذ','الطالب','nom','name','élève']
    for col in df.columns:
        col_str = str(col).strip()
        for kw in keywords:
            if kw in col_str:
                return col
    # احتياطي: أول عمود نصي
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].notna().sum() > 0:
            return col
    return None

def find_grade_columns(df, exclude_cols=None):
    """استخراج أعمدة النقاط"""
    if exclude_cols is None: exclude_cols = []
    skip = ['رقم','ترتيب','تسلسل','ميلاد','تاريخ','ملاحظ', 'قسم','فوج','سنة','جنس','عنوان','هاتف','ولي', '#','num','id','مجموع','معدل','تقدير','عدد', 'الترتيب','المجموع','المعدل','التقدير']
    grade_cols = []
    for col in df.columns:
        if col in exclude_cols: continue
        col_lower = str(col).strip().lower()
        if any(kw in col_lower for kw in skip): continue
        if pd.api.types.is_numeric_dtype(df[col]):
            col_max = df[col].max()
            if pd.notna(col_max) and 0 < col_max <= 20:
                grade_cols.append(col)
    return grade_cols

def match_subject_columns(df_columns, expected_subjects):
    """ ✨ مطابقة ذكية بين أعمدة الملف والمواد المتوقعة """
    matched = {}
    remaining_cols = list(df_columns)
    for subject in expected_subjects:
        subj_norm = normalize_arabic(subject)
        best_col = None
        best_score = 0
        for col in remaining_cols:
            col_norm = normalize_arabic(str(col))
            # تطابق تام
            if col_norm == subj_norm:
                best_col = col
                best_score = 100
                break
            # احتواء
            if subj_norm in col_norm or col_norm in subj_norm:
                score = 80
                if score > best_score:
                    best_score = score
                    best_col = col
            # كلمات مشتركة
            subj_words = set(subj_norm.split())
            col_words = set(col_norm.split())
            common = len(subj_words & col_words)
            if common > 0:
                score = common * 30
                if score > best_score:
                    best_score = score
                    best_col = col
        if best_col and best_score >= 30:
            matched[best_col] = subject
            remaining_cols.remove(best_col)
    return matched

def read_sheet_safe(file, sheet_name):
    """قراءة آمنة مع إعادة المؤشر"""
    file.seek(0)
    df = pd.read_excel(file, sheet_name=sheet_name)
    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(how='all')
    return df

def get_sheet_names_safe(file):
    """استخراج أسماء الأوراق"""
    file.seek(0)
    return pd.ExcelFile(file).sheet_names

def classify_student(avg):
    """تصنيف حسب المعدل"""
    if pd.isna(avg): return "—"
    if avg >= 9: return "ممتاز 🌟"
    if avg >= 8: return "جيد جداً ✅"
    if avg >= 7: return "جيد 👍"
    if avg >= 5: return "مقبول 📗"
    if avg >= 3.5: return "ضعيف ⚠️"
    return "ضعيف جداً ❌"

def call_mistral(prompt, system_prompt=None):
    """استدعاء Mistral AI"""
    if not api_key: return "⚠️ أدخل مفتاح Mistral API"
    if not system_prompt:
        system_prompt = """أنت مستشار تربوي خبير في المرحلة الابتدائية بالجزائر. المعدل من 10. النجاح من 5/10. قدّم تحليلات دقيقة بالعربية مع أرقام."""
    try:
        r = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": ai_model,
                "temperature": ai_temp,
                "max_tokens": 4000,
                "messages": [
                    {"role":"system","content":system_prompt},
                    {"role":"user","content":prompt}
                ]
            },
            timeout=60
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return f"❌ خطأ {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"❌ {str(e)}"

def ai_analyze_class(df, name_col, subject_cols, section):
    """تحليل AI شامل"""
    stats = {
        "القسم": section,
        "التلاميذ": len(df),
        "معدل_القسم": round(df['المعدل'].mean(), 2),
        "أعلى": round(df['المعدل'].max(), 2),
        "أدنى": round(df['المعدل'].min(), 2),
        "نسبة_النجاح": round((df['المعدل'] >= 5).sum() / len(df) * 100, 1),
        "متفوقون_فوق_8": int((df['المعدل'] >= 8).sum()),
        "ضعفاء_تحت_3.5": int((df['المعدل'] < 3.5).sum()),
    }
    subj_stats = {}
    for col in subject_cols:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            subj_stats[col] = {
                "المعدل": round(df[col].mean(), 2),
                "أعلى": round(df[col].max(), 2),
                "أدنى": round(df[col].min(), 2),
                "ضعفاء": int((df[col] < 5).sum())
            }
    top3 = df.nlargest(3, 'المعدل')[[name_col, 'المعدل']].to_dict('records')
    bot3 = df.nsmallest(3, 'المعدل')[[name_col, 'المعدل']].to_dict('records')
    
    prompt = f"""حلّل نتائج هذا القسم تحليلاً تربوياً شاملاً:
📊 الإحصائيات: {json.dumps(stats, ensure_ascii=False, indent=2)}
📚 المواد: {json.dumps(subj_stats, ensure_ascii=False, indent=2)}
🏆 الأوائل: {json.dumps(top3, ensure_ascii=False)}
⚠️ الأضعف: {json.dumps(bot3, ensure_ascii=False)}
قدّم: 1. تقييم عام لمستوى القسم مع التبرير 2. تحليل كل مادة وتحديد المواد التي تحتاج دعماً 3. نقاط القوة ونقاط الضعف 4. توصيات عملية محددة للمعلم 5. أهداف للفصل القادم
استخدم الإيموجي والأرقام."""
    return call_mistral(prompt)

def ai_student_report(row, name_col, subject_cols, class_avg):
    """تقرير فردي"""
    data = {
        "الاسم": str(row[name_col]),
        "المعدل": round(float(row['المعدل']), 2),
        "معدل_القسم": round(float(class_avg), 2),
        "الترتيب": int(row.get('الترتيب', 0)),
        "النقاط": {}
    }
    for col in subject_cols:
        if col in row.index and pd.notna(row[col]):
            data["النقاط"][col] = round(float(row[col]), 2)
            
    prompt = f"""اكتب تقريراً تربوياً لهذا التلميذ:
{json.dumps(data, ensure_ascii=False, indent=2)}
المطلوب: 1) تقييم عام 2) المواد القوية/الضعيفة 3) نصيحتان عمليتان 4) ملاحظة لولي الأمر
كن مشجعاً."""
    return call_mistral(prompt)

# ══════════════════════════════════════════════════════════════
# الخطوة 1: اختيار المستوى الدراسي
# ══════════════════════════════════════════════════════════════
st.subheader("📚 الخطوة 1: اختر المستوى الدراسي")
selected_level = st.selectbox(
    "🎓 المستوى:", list(LEVELS.keys()), help="حسب اختيارك ستتحدد المواد والملفات المطلوبة"
)
level_config = LEVELS[selected_level]

# عرض المواد المطلوبة لهذا المستوى
st.markdown(f"""
<div class="subject-box">
<strong>📋 مواد {selected_level} ({level_config['total_subjects']} مادة):</strong><br>
""", unsafe_allow_html=True)

for teacher, info in level_config["files"].items():
    subjects_str = " ، ".join(info["subjects"])
    st.markdown(f"**{info['icon']} {teacher}**: {subjects_str}")

# ══════════════════════════════════════════════════════════════
# الخطوة 2: رفع الملفات حسب المستوى
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📁 الخطوة 2: رفع ملفات الأساتذة")
uploaded_files = {}
required_files = level_config["files"]

# إنشاء أعمدة ديناميكية حسب عدد الملفات
num_files = len(required_files)
cols = st.columns(min(num_files, 4))

for i, (teacher_name, teacher_info) in enumerate(required_files.items()):
    col_idx = i % len(cols)
    with cols[col_idx]:
        subjects_preview = " + ".join([s[:10] for s in teacher_info["subjects"]])
        f = st.file_uploader(
            f"{teacher_info['icon']} {teacher_name}",
            type=['xlsx', 'xls'],
            help=f"المواد: {', '.join(teacher_info['subjects'])}",
            key=f"upload_{teacher_name}"
        )
        if f:
            uploaded_files[teacher_name] = f
            st.caption(f"✅ {len(teacher_info['subjects'])} مادة")
        elif teacher_info["required"]:
            st.caption("⏳ مطلوب")

# التحقق من اكتمال الملفات
missing = [t for t, info in required_files.items() if info["required"] and t not in uploaded_files]
if missing:
    st.warning(f"⏳ في انتظار رفع: **{' ، '.join(missing)}**")
    st.stop()

st.success(f"✅ تم رفع جميع الملفات المطلوبة ({len(uploaded_files)} ملف)")

# ══════════════════════════════════════════════════════════════
# الخطوة 3: ربط أوراق العمل (Sheets) بين الملفات
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("🔗 الخطوة 3: ربط أوراق العمل بين الملفات")
st.markdown("""
<div class="mapping-box">
<strong>📌 لماذا؟</strong> كل أستاذ يسمّي أوراقه بطريقته:<br>
• معلم القسم: <b>"السنة الأولى أ"</b><br>
• أستاذ الرياضة: <b>"ت البدنية والرياضية"</b><br>
• أستاذ الفرنسية: <b>"3AP-A"</b><br>
👈 حدد الورقة الصحيحة من كل ملف لنفس القسم المراد دمجه.
</div>
""", unsafe_allow_html=True)

# استخراج أوراق كل ملف
all_sheets = {}
for teacher_name, file in uploaded_files.items():
    all_sheets[teacher_name] = get_sheet_names_safe(file)

# عرض ملخص
with st.expander("🔍 عرض أوراق كل ملف"):
    for teacher, sheets in all_sheets.items():
        icon = required_files[teacher]["icon"]
        st.write(f"**{icon} {teacher}**: {len(sheets)} ورقة → `{sheets}`")
    st.markdown("---")

# ═══ اختيار الأوراق ═══
sheet_mapping = {}
st.write("### 🎯 حدد الورقة المناسبة من كل ملف")

# الملف المرجعي أولاً
ref_sheets = all_sheets["معلم القسم"]
st.write("#### 1️⃣ ملف معلم القسم (المرجع الأساسي)")
selected_ref_sheet = st.selectbox(
    "📄 اختر ورقة القسم المراد حساب معدلاته:", ref_sheets, key="ref_sheet_select"
)
sheet_mapping["معلم القسم"] = selected_ref_sheet

# معاينة
with st.expander(f"👁️ معاينة: «{selected_ref_sheet}» — معلم القسم"):
    preview = read_sheet_safe(uploaded_files["معلم القسم"], selected_ref_sheet)
    nc = find_name_column(preview)
    gc = find_grade_columns(preview, [nc] if nc else [])
    st.write(f"**{len(preview)} تلميذ** | عمود الاسم: `{nc}` | أعمدة النقاط: `{gc}`")
    st.dataframe(preview.head(8), use_container_width=True)

# باقي الملفات
if len(uploaded_files) > 1:
    st.write("#### 2️⃣ ملفات الأساتذة الآخرين")
    for teacher_name, file in uploaded_files.items():
        if teacher_name == "معلم القسم":
            continue
            
        teacher_sheets = all_sheets[teacher_name]
        icon = required_files[teacher_name]["icon"]
        expected_subjs = required_files[teacher_name]["subjects"]
        
        col_a, col_b = st.columns([4, 1])
        with col_a:
            # اقتراح ذكي: البحث عن ورقة مشابهة
            suggested_idx = 0
            ref_norm = normalize_arabic(selected_ref_sheet.lower())
            
            for idx, sh in enumerate(teacher_sheets):
                sh_norm = normalize_arabic(sh.lower())
                # مطابقة بالأرقام أو الحروف المشتركة
                if ref_norm in sh_norm or sh_norm in ref_norm:
                    suggested_idx = idx
                    break
                ref_nums = set(re.findall(r'\d+', selected_ref_sheet))
                sh_nums = set(re.findall(r'\d+', sh))
                if ref_nums and ref_nums & sh_nums:
                    suggested_idx = idx
                    break
                    
            selected = st.selectbox(
                f"{icon} **{teacher_name}** — المواد: {', '.join(expected_subjs)}",
                teacher_sheets,
                index=suggested_idx,
                key=f"sheet_map_{teacher_name}"
            )
            sheet_mapping[teacher_name] = selected
            
        with col_b:
            st.markdown("<br>", unsafe_allow_html=True)
            if suggested_idx > 0:
                st.success("🤖 مقترحة")
            else:
                st.info("✋ يدوي")
                
        # معاينة
        with st.expander(f"👁️ معاينة: «{selected}» — {teacher_name}"):
            prev = read_sheet_safe(file, selected)
            nc2 = find_name_column(prev)
            gc2 = find_grade_columns(prev, [nc2] if nc2 else [])
            st.write(f"**{len(prev)} تلميذ** | عمود الاسم: `{nc2}` | نقاط: `{gc2}`")
            st.dataframe(prev.head(5), use_container_width=True)

# ═══ ملخص الربط ═══
st.markdown("---")
st.write("### ✅ ملخص الربط")
summary_data = []
for teacher, sheet in sheet_mapping.items():
    icon = required_files[teacher]["icon"]
    subjs = required_files[teacher]["subjects"]
    summary_data.append({
        "الملف": f"{icon} {teacher}",
        "الورقة المحددة": sheet,
        "المواد المتوقعة": " ، ".join(subjs),
        "عدد المواد": len(subjs)
    })
st.table(pd.DataFrame(summary_data))

# ══════════════════════════════════════════════════════════════
# الخطوة 4: الدمج وحساب المعدلات
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("⚙️ الخطوة 4: الدمج وحساب المعدلات")

if st.button("🚀 بدء الدمج وحساب المعدلات", type="primary", use_container_width=True):
    progress = st.progress(0, text="بدء المعالجة...")
    
    # ─── 4.1 قراءة الورقة المحددة من كل ملف ───
    raw_data = {} # {teacher: DataFrame}
    step = 0
    for teacher_name, file in uploaded_files.items():
        step += 1
        target_sheet = sheet_mapping[teacher_name]
        progress.progress(
            int(step / (len(uploaded_files) + 4) * 100), 
            text=f"قراءة «{target_sheet}» من {teacher_name}..."
        )
        try:
            df = read_sheet_safe(file, target_sheet)
            if len(df) == 0:
                st.warning(f"⚠️ الورقة «{target_sheet}» في {teacher_name} فارغة!")
                continue
            raw_data[teacher_name] = df
            st.caption(f"✅ {teacher_name}: {len(df)} تلميذ من «{target_sheet}»")
        except Exception as e:
            st.error(f"❌ خطأ في {teacher_name}: {e}")
            continue
            
    if "معلم القسم" not in raw_data:
        st.error("❌ فشل في قراءة ملف معلم القسم!")
        st.stop()
        
    # ─── 4.2 تحديد عمود الاسم في الملف المرجعي ───
    progress.progress(40, text="تحديد أعمدة الأسماء...")
    ref_df = raw_data["معلم القسم"].copy()
    name_col = find_name_column(ref_df)
    
    if not name_col:
        st.error("❌ لم يُعثر على عمود الاسم!")
        st.write("الأعمدة:", list(ref_df.columns))
        st.stop()
        
    # مفتاح المطابقة
    ref_df['_key'] = ref_df[name_col].apply(normalize_arabic)
    
    # ─── 4.3 مطابقة أعمدة النقاط مع المواد المتوقعة ───
    progress.progress(50, text="مطابقة المواد...")
    st.write("### 🔍 نتائج مطابقة المواد")
    
    # معلم القسم
    ref_expected = required_files["معلم القسم"]["subjects"]
    ref_grade_cols = find_grade_columns(ref_df, [name_col, '_key'])
    ref_col_mapping = match_subject_columns(ref_grade_cols, ref_expected)
    
    # إعادة تسمية الأعمدة لتطابق أسماء المواد الرسمية
    if ref_col_mapping:
        ref_df = ref_df.rename(columns=ref_col_mapping)
        
    st.write("**📄 معلم القسم:**")
    for old, new in ref_col_mapping.items():
        if old != new:
            st.caption(f" `{old}` → **{new}**")
        else:
            st.caption(f" ✅ `{new}`")
            
    # المواد غير الموجودة
    found_subjects = list(ref_col_mapping.values()) if ref_col_mapping else ref_grade_cols
    missing_from_ref = [s for s in ref_expected if s not in found_subjects]
    if missing_from_ref:
        st.warning(f"⚠️ مواد غير موجودة في ملف معلم القسم: {missing_from_ref}")
        
    # ─── 4.4 دمج ملفات الأساتذة الآخرين ───
    progress.progress(60, text="دمج البيانات...")
    final_df = ref_df.copy()
    all_merged_subjects = list(found_subjects)
    
    for teacher_name, df in raw_data.items():
        if teacher_name == "معلم القسم":
            continue
            
        teacher_icon = required_files[teacher_name]["icon"]
        teacher_expected = required_files[teacher_name]["subjects"]
        
        # عمود الاسم
        other_name_col = find_name_column(df)
        if not other_name_col:
            st.warning(f"⚠️ لم يُعثر على عمود الاسم في {teacher_name}")
            continue
            
        # أعمدة النقاط
        other_grade_cols = find_grade_columns(df, [other_name_col])
        if not other_grade_cols:
            st.warning(f"⚠️ لم يُعثر على نقاط في {teacher_name}")
            continue
            
        # مطابقة أسماء الأعمدة مع المواد
        col_mapping = match_subject_columns(other_grade_cols, teacher_expected)
        
        # إذا لم تنجح المطابقة التلقائية ولديه مادة واحدة
        if not col_mapping and len(other_grade_cols) == 1 and len(teacher_expected) == 1:
            col_mapping = {other_grade_cols[0]: teacher_expected[0]}
            
        # إذا عدة أعمدة ولم تتطابق، نأخذها كما هي
        if not col_mapping:
            col_mapping = {c: c for c in other_grade_cols}
            
        st.write(f"**{teacher_icon} {teacher_name}:**")
        for old, new in col_mapping.items():
            st.caption(f" `{old}` → **{new}**")
            
        # تحضير جدول الدمج
        merge_cols = [other_name_col] + list(col_mapping.keys())
        merge_df = df[merge_cols].copy()
        merge_df = merge_df.rename(columns=col_mapping)
        merge_df['_key'] = merge_df[other_name_col].apply(normalize_arabic)
        merge_df = merge_df.drop(columns=[other_name_col])
        
        # التأكد من عدم تكرار الأعمدة
        for col in col_mapping.values():
            if col in final_df.columns and col != '_key':
                merge_df = merge_df.rename(columns={col: f"{col}_dup"})
                
        # الدمج
        before = len(final_df)
        final_df = pd.merge(final_df, merge_df, on='_key', how='left')
        matched_count = merge_df['_key'].isin(final_df['_key']).sum()
        st.caption(f" ↳ مطابقة: {matched_count}/{len(merge_df)} تلميذ")
        
        all_merged_subjects.extend(col_mapping.values())
        
    # حذف المفتاح المساعد
    final_df = final_df.drop(columns=['_key'], errors='ignore')
    
    # ─── 4.5 حساب المعدل ───
    progress.progress(85, text="حساب المعدلات...")
    
    # تحديد أعمدة النقاط النهائية
    final_subject_cols = []
    for col in final_df.columns:
        if col == name_col:
            continue
        if col in ['الترتيب','المجموع','المعدل','التقدير','عدد المواد','_key']:
            continue
        if pd.api.types.is_numeric_dtype(final_df[col]):
            col_max = final_df[col].max()
            if pd.notna(col_max) and 0 < col_max <= 20:
                final_subject_cols.append(col)
                
    if not final_subject_cols:
        st.error("❌ لم يتم العثور على أعمدة نقاط!")
        st.stop()
        
    # الحساب
    final_df['عدد المواد'] = final_df[final_subject_cols].notna().sum(axis=1)
    final_df['المجموع'] = final_df[final_subject_cols].sum(axis=1)
    final_df['المعدل'] = (final_df['المجموع'] / final_df['عدد المواد']).round(2)
    final_df['التقدير'] = final_df['المعدل'].apply(classify_student)
    
    # الترتيب
    final_df = final_df.sort_values('المعدل', ascending=False).reset_index(drop=True)
    final_df.insert(0, 'الترتيب', range(1, len(final_df) + 1))
    
    progress.progress(100, text="✅ تم بنجاح!")
    
    # ═══ ملخص المواد المدمجة ═══
    st.markdown(f"""
<div class="subject-box">
<strong>✅ تم دمج {len(final_subject_cols)} مادة من أصل {level_config['total_subjects']} متوقعة:</strong><br>
{" ، ".join(final_subject_cols)}
</div>
    """, unsafe_allow_html=True)
    
    if len(final_subject_cols) < level_config['total_subjects']:
        missing_count = level_config['total_subjects'] - len(final_subject_cols)
        st.markdown(f"""
<div class="warn-box">
⚠️ <b>{missing_count} مادة</b> لم يتم العثور عليها. تحقق من أسماء الأعمدة في ملفات الأساتذة.
</div>
        """, unsafe_allow_html=True)
        
    # حفظ في Session
    st.session_state['final_df'] = final_df
    st.session_state['name_col'] = name_col
    st.session_state['subject_cols'] = final_subject_cols
    st.session_state['selected_sheet'] = selected_ref_sheet
    st.session_state['selected_level'] = selected_level
    st.session_state['done'] = True

# ══════════════════════════════════════════════════════════════
# عرض النتائج
# ══════════════════════════════════════════════════════════════
if st.session_state.get('done'):
    final_df = st.session_state['final_df']
    name_col = st.session_state['name_col']
    subject_cols = st.session_state['subject_cols']
    selected_sheet = st.session_state['selected_sheet']
    selected_level = st.session_state['selected_level']
    
    st.markdown("---")
    st.write(f"### 📊 كشف نقاط ومعدلات «{selected_sheet}» — {selected_level}")
    
    # ترتيب الأعمدة بشكل منطقي
    display_cols = ['الترتيب', name_col] + subject_cols + ['عدد المواد', 'المجموع', 'المعدل', 'التقدير']
    display_cols = [c for c in display_cols if c in final_df.columns]
    
    st.dataframe(
        final_df[display_cols], use_container_width=True, height=500
    )
    
    # ═══ الإحصائيات ═══
    if 'المعدل' in final_df.columns:
        st.write("### 📈 إحصائيات القسم")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            st.metric("👥 العدد", len(final_df))
        with c2:
            st.metric("📚 المواد", len(subject_cols))
        with c3:
            st.metric("🏆 الأعلى", final_df['المعدل'].max())
        with c4:
            st.metric("📉 الأدنى", final_df['المعدل'].min())
        with c5:
            st.metric("📊 المعدل", round(final_df['المعدل'].mean(), 2))
        with c6:
            pct = round((final_df['المعدل'] >= 5).sum() / len(final_df) * 100, 1)
            st.metric("✅ النجاح", f"{pct}%")
            
        # معدل كل مادة
        st.write("#### 📚 معدل كل مادة")
        subject_avgs = {}
        for col in subject_cols:
            if pd.api.types.is_numeric_dtype(final_df[col]):
                subject_avgs[col] = round(final_df[col].mean(), 2)
                
        if subject_avgs:
            avg_df = pd.DataFrame({
                "المادة": subject_avgs.keys(),
                "المعدل": subject_avgs.values()
            }).sort_values("المعدل", ascending=True)
            st.bar_chart(avg_df.set_index("المادة"), height=300)
            
        # رسم معدلات التلاميذ
        st.write("#### 👥 معدلات التلاميذ")
        chart_df = final_df[[name_col, 'المعدل']].set_index(name_col).sort_values('المعدل', ascending=False)
        st.bar_chart(chart_df, height=350)
        
    # ══════════════════════════════════════════════════════
    # 🤖 قسم الذكاء الاصطناعي
    # ══════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("""
<div class="ai-box">
<h2 style="color:white; text-align:center;">🤖 التحليل بالذكاء الاصطناعي</h2>
<p style="text-align:center;">تحليلات تربوية مدعومة بـ Mistral AI</p>
</div>
    """, unsafe_allow_html=True)
    
    if not api_key:
        st.warning("⚠️ أدخل مفتاح Mistral API في الشريط الجانبي")
    else:
        ai_tabs = st.tabs([
            "📊 تحليل القسم", "👤 تقرير فردي", "🔍 حالات استثنائية", "💡 توصيات", "💬 اسأل AI"
        ])
        
        with ai_tabs[0]:
            if st.button("🤖 تحليل شامل", key="ai1"):
                with st.spinner("🤖 جاري التحليل..."):
                    r = ai_analyze_class(final_df, name_col, subject_cols, selected_sheet)
                    st.markdown(f'<div class="ai-response">{r}</div>', unsafe_allow_html=True)
                    st.session_state['analysis'] = r
                    
        with ai_tabs[1]:
            names_list = final_df[name_col].tolist()
            sel_student = st.selectbox("اختر التلميذ:", names_list, key="ai_s")
            if st.button("📝 تقرير فردي", key="ai2"):
                row = final_df[final_df[name_col] == sel_student].iloc[0]
                with st.spinner(f"🤖 تقرير {sel_student}..."):
                    r = ai_student_report(row, name_col, subject_cols, final_df['المعدل'].mean())
                    st.markdown(f'<div class="student-card"><h4>📋 {sel_student}</h4><hr>{r}</div>', unsafe_allow_html=True)
                    
        with ai_tabs[2]:
            if st.button("🔍 فحص الحالات", key="ai3"):
                anomalies = []
                for _, row in final_df.iterrows():
                    grades = [float(row[c]) for c in subject_cols if c in row.index and pd.notna(row[c])]
                    if len(grades) >= 2 and max(grades) - min(grades) >= 5:
                        anomalies.append(f"• **{row[name_col]}**: تفاوت كبير ({min(grades)}-{max(grades)})")
                    if pd.notna(row.get('المعدل')) and float(row['المعدل']) < 3:
                        anomalies.append(f"• **{row[name_col]}**: معدل ضعيف جداً ({row['المعدل']})")
                        
                if anomalies:
                    prompt = f"حلّل هذه الحالات الاستثنائية واقترح حلولاً:\n" + "\n".join(anomalies)
                    with st.spinner("🤖 ..."):
                        r = call_mistral(prompt)
                        st.markdown(f'<div class="ai-response">{r}</div>', unsafe_allow_html=True)
                else:
                    st.success("✅ لا توجد حالات استثنائية")
                    
        with ai_tabs[3]:
            if st.button("💡 توصيات تربوية", key="ai4"):
                weak = {}
                for col in subject_cols:
                    b = (final_df[col] < 5).sum()
                    weak[col] = {"معدل": round(final_df[col].mean(), 2), "ضعفاء": int(b)}
                    
                prompt = f"""خطة عمل تربوية لقسم {selected_sheet} ({selected_level}):
المواد: {json.dumps(weak, ensure_ascii=False, indent=2)}
معدل القسم: {round(final_df['المعدل'].mean(), 2)}
قدّم: دعم المواد الضعيفة + مجموعات مستوى + نصائح أولياء + أنشطة تحفيزية"""
                with st.spinner("🤖 ..."):
                    r = call_mistral(prompt)
                    st.markdown(f'<div class="ai-response">{r}</div>', unsafe_allow_html=True)
                    
        with ai_tabs[4]:
            ctx = f"""قسم «{selected_sheet}» — {selected_level}
تلاميذ: {len(final_df)} | معدل: {round(final_df['المعدل'].mean(),2)} | نجاح: {round((final_df['المعدل']>=5).sum()/len(final_df)*100,1)}%
المواد: {subject_cols}
البيانات:\n{final_df[display_cols].head(15).to_string()}"""

            if 'chat' not in st.session_state:
                st.session_state.chat = []
                
            for msg in st.session_state.chat:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
                    
            q = st.chat_input("اكتب سؤالك...")
            if q:
                st.session_state.chat.append({"role": "user", "content": q})
                with st.chat_message("user"):
                    st.write(q)
                with st.chat_message("assistant"):
                    with st.spinner("🤖"):
                        ans = call_mistral(f"{ctx}\n\nسؤال: {q}")
                        st.write(ans)
                        st.session_state.chat.append({"role": "assistant", "content": ans})
                        
                if st.button("🗑️ مسح"):
                    st.session_state.chat = []
                    st.rerun()

    # ══════════════════════════════════════════════════════
    # التصدير
    # ══════════════════════════════════════════════════════
    st.markdown("---")
    st.write("### 📥 تصدير النتائج")
    col_e1, col_e2 = st.columns(2)
    
    with col_e1:
        output = io.BytesIO()
        sheet_export_name = selected_sheet[:31] # حد إكسيل 31 حرف
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            export_df = final_df[display_cols] if display_cols else final_df
            export_df.to_excel(writer, index=False, sheet_name=sheet_export_name)
            wb = writer.book
            ws = writer.sheets[sheet_export_name]
            
            # تنسيق الرأس
            hfmt = wb.add_format({
                'bold': True, 'bg_color': '#2E86AB', 'font_color': 'white', 
                'border': 1, 'align': 'center', 'valign': 'vcenter'
            })
            
            # تنسيق الناجحين
            pass_fmt = wb.add_format({'bg_color': '#d4edda'})
            fail_fmt = wb.add_format({'bg_color': '#f8d7da'})
            
            for i, col in enumerate(export_df.columns):
                ws.write(0, i, col, hfmt)
                ws.set_column(i, i, max(len(str(col)) + 4, 13))
                
            # تلوين صفوف حسب النتيجة
            if 'المعدل' in export_df.columns:
                avg_col_idx = list(export_df.columns).index('المعدل')
                for row_idx in range(1, len(export_df) + 1):
                    val = export_df.iloc[row_idx - 1]['المعدل']
                    if pd.notna(val):
                        fmt = pass_fmt if val >= 5 else fail_fmt
                        ws.set_row(row_idx, None, fmt)
                        
        st.download_button(
            "📥 تحميل كشف النقاط (Excel)",
            data=output.getvalue(),
            file_name=f"كشف_نقاط_{selected_level}_{selected_sheet}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    with col_e2:
        if st.session_state.get('analysis'):
            txt = f"""
تقرير الذكاء الاصطناعي
{'='*60}
المستوى: {selected_level}
القسم: {selected_sheet}
التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
عدد التلاميذ: {len(final_df)}
عدد المواد: {len(subject_cols)}
المواد: {', '.join(subject_cols)}
{'='*60}
{st.session_state['analysis']}
"""
            st.download_button(
                "📥 تحميل تقرير AI (نصي)",
                data=txt.encode('utf-8'),
                file_name=f"تقرير_AI_{selected_sheet}.txt",
                mime="text/plain",
                use_container_width=True
            )



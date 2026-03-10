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
    page_title="نظام حساب المعدلات بالذكاء الاصطناعي",
    layout="wide",
    page_icon="🤖"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
.main .block-container {direction: rtl; text-align: right; font-family: 'Cairo', sans-serif;}
h1, h2, h3, h4, p, li, span, label {direction: rtl; text-align: right;}
.stMetric {direction: ltr;}
.ai-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; padding: 20px; margin: 15px 0; color: white; box-shadow: 0 8px 32px rgba(102,126,234,0.3); }
.ai-response { background: #f8f9ff; border-radius: 12px; padding: 20px; margin: 10px 0; border-right: 5px solid #667eea; line-height: 2; font-size: 15px; direction: rtl; }
.mapping-box { background: #e8f4fd; border-radius: 10px; padding: 15px; margin: 8px 0; border-right: 4px solid #2196F3; }
.success-box { background: #d4edda; border-radius: 10px; padding: 15px; margin: 10px 0; border-right: 5px solid #28a745; }
.student-card { background: white; border-radius: 10px; padding: 15px; margin: 8px 0; border: 1px solid #e0e0e0; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ai-box">
<h1 style="color:white; text-align:center;">🤖🏫 النظام الذكي لحساب معدلات التلاميذ</h1>
<p style="text-align:center; font-size:18px;">مدعوم بالذكاء الاصطناعي Mistral AI — ربط ذكي للأوراق</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# إعداد Mistral AI
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ إعدادات الذكاء الاصطناعي")
    api_key = None
    try:
        api_key = st.secrets["MISTRAL_API_KEY"]
    except:
        pass
    if not api_key:
        api_key = st.text_input(
            "🔑 مفتاح Mistral API", type="password", help="من https://console.mistral.ai/"
        )
    if api_key:
        st.success("✅ مفتاح API مُفعّل")
    else:
        st.warning("⚠️ أدخل المفتاح لتفعيل AI")
        
    st.markdown("---")
    ai_model = st.selectbox(
        "🧠 النموذج", ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest", "open-mistral-nemo"]
    )
    ai_temperature = st.slider("🌡️ الإبداعية", 0.0, 1.0, 0.7)
    
    st.markdown("---")
    st.markdown("### 🤖 ميزات AI")
    enable_class_analysis = st.checkbox("📊 تحليل شامل للقسم", value=True)
    enable_student_reports = st.checkbox("👤 تقارير فردية", value=True)
    enable_anomaly_detection = st.checkbox("🔍 كشف حالات استثنائية", value=True)
    enable_recommendations = st.checkbox("💡 توصيات تربوية", value=True)

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
    """البحث الذكي عن عمود الاسم"""
    keywords = ['اللقب والاسم','الاسم واللقب','اسم','لقب', 'الاسم','اللقب','التلميذ','الطالب','nom','name']
    for col in df.columns:
        for kw in keywords:
            if kw in str(col).strip():
                return col
    # احتياط: أول عمود نصي يحتوي بيانات
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].notna().sum() > 0:
            return col
    return None

def find_grade_columns(df, exclude_cols):
    """استخراج أعمدة النقاط فقط"""
    skip = ['رقم','ترتيب','تسلسل','ميلاد','تاريخ','ملاحظ', 'قسم','فوج','سنة','جنس','عنوان','هاتف','ولي', '#','num','id','مجموع','معدل','تقدير','عدد']
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

def read_sheet_safe(file, sheet_name):
    """قراءة آمنة مع إعادة المؤشر"""
    file.seek(0)
    df = pd.read_excel(file, sheet_name=sheet_name)
    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(how='all')
    return df

def get_sheet_names_safe(file):
    """استخراج أسماء الأوراق بأمان"""
    file.seek(0)
    xls = pd.ExcelFile(file)
    return xls.sheet_names

def classify_student(avg):
    """تصنيف التلميذ حسب المعدل"""
    if pd.isna(avg): return "—"
    if avg >= 9: return "ممتاز 🌟"
    if avg >= 8: return "جيد جداً ✅"
    if avg >= 7: return "جيد 👍"
    if avg >= 5: return "مقبول 📗"
    if avg >= 3.5: return "ضعيف ⚠️"
    return "ضعيف جداً ❌"

def fuzzy_match_sheet(target_name, candidate_names):
    """ ✨ المطابقة الذكية لأسماء الأوراق تبحث عن أقرب اسم ورقة مطابق """
    target_norm = normalize_arabic(target_name.lower())
    
    # 1. تطابق تام
    for name in candidate_names:
        if normalize_arabic(name.lower()) == target_norm:
            return name
            
    # 2. أحدهما يحتوي الآخر
    for name in candidate_names:
        norm = normalize_arabic(name.lower())
        if target_norm in norm or norm in target_norm:
            return name
            
    # 3. كلمات مشتركة
    target_words = set(target_norm.split())
    best_match = None
    best_score = 0
    for name in candidate_names:
        norm_words = set(normalize_arabic(name.lower()).split())
        common = len(target_words & norm_words)
        if common > best_score:
            best_score = common
            best_match = name
    if best_score > 0:
        return best_match
        
    # 4. أرقام مشتركة (مثل "1" في "السنة 1" و "1AP")
    target_nums = set(re.findall(r'\d+', target_name))
    for name in candidate_names:
        name_nums = set(re.findall(r'\d+', name))
        if target_nums and target_nums & name_nums:
            return name
            
    return candidate_names[0] if candidate_names else None

# ══════════════════════════════════════════════════════════════
# دوال Mistral AI
# ══════════════════════════════════════════════════════════════
def call_mistral(prompt, system_prompt=None):
    """استدعاء Mistral AI"""
    if not api_key:
        return "⚠️ أدخل مفتاح Mistral API في الشريط الجانبي"
    if not system_prompt:
        system_prompt = """أنت مستشار تربوي ذكي متخصص في تحليل نتائج تلاميذ المرحلة الابتدائية في النظام التعليمي الجزائري. المعدل من 10. الحد الأدنى للنجاح 5/10. قدّم تحليلات دقيقة بالعربية الفصحى مع أرقام ونسب."""
    try:
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": ai_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": ai_temperature,
                "max_tokens": 4000
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return f"❌ خطأ {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return f"❌ خطأ: {str(e)}"

def ai_analyze_class(df, name_col, grade_cols, section_name):
    """تحليل شامل للقسم"""
    stats = {
        "القسم": section_name,
        "عدد_التلاميذ": len(df),
        "معدل_القسم": round(df['المعدل'].mean(), 2),
        "أعلى_معدل": round(df['المعدل'].max(), 2),
        "أدنى_معدل": round(df['المعدل'].min(), 2),
        "نسبة_النجاح": round((df['المعدل'] >= 5).sum() / len(df) * 100, 1),
        "عدد_المتفوقين": int((df['المعدل'] >= 8).sum()),
        "عدد_الضعفاء": int((df['المعدل'] < 3.5).sum()),
    }
    subject_stats = {}
    for col in grade_cols:
        if col in df.columns:
            subject_stats[col] = {
                "المعدل": round(df[col].mean(), 2),
                "أعلى": round(df[col].max(), 2),
                "أدنى": round(df[col].min(), 2)
            }
    top3 = df.nlargest(3, 'المعدل')[[name_col, 'المعدل']].to_dict('records')
    bot3 = df.nsmallest(3, 'المعدل')[[name_col, 'المعدل']].to_dict('records')
    prompt = f"""حلّل نتائج هذا القسم تحليلاً تربوياً:
📊 الإحصائيات: {json.dumps(stats, ensure_ascii=False, indent=2)}
📚 المواد: {json.dumps(subject_stats, ensure_ascii=False, indent=2)}
🏆 الأوائل: {json.dumps(top3, ensure_ascii=False)}
⚠️ الأضعف: {json.dumps(bot3, ensure_ascii=False)}
قدّم: 1) تقييم عام 2) تحليل كل مادة 3) نقاط القوة والضعف 4) توصيات عملية 5) أهداف الفصل القادم"""
    return call_mistral(prompt)

def ai_student_report(student_row, name_col, grade_cols, class_avg):
    """تقرير فردي"""
    data = {
        "الاسم": str(student_row[name_col]),
        "المعدل": round(float(student_row['المعدل']), 2),
        "معدل_القسم": round(float(class_avg), 2),
        "الترتيب": int(student_row.get('الترتيب', 0)),
        "النقاط": {}
    }
    for col in grade_cols:
        if col in student_row.index and pd.notna(student_row[col]):
            data["النقاط"][col] = round(float(student_row[col]), 2)
    prompt = f"""اكتب تقريراً تربوياً لهذا التلميذ:
{json.dumps(data, ensure_ascii=False, indent=2)}
المطلوب: 1) تقييم عام 2) المواد القوية/الضعيفة 3) نصيحتان 4) ملاحظة لولي الأمر
كن مشجعاً حتى مع الضعفاء."""
    return call_mistral(prompt)

def ai_detect_anomalies(df, name_col, grade_cols):
    """كشف حالات استثنائية"""
    anomalies = []
    for _, row in df.iterrows():
        grades = [float(row[c]) for c in grade_cols if c in row.index and pd.notna(row[c])]
        if len(grades) >= 2 and max(grades) - min(grades) >= 6:
            anomalies.append({
                "الاسم": str(row[name_col]),
                "النوع": "تفاوت كبير",
                "أعلى": max(grades),
                "أدنى": min(grades)
            })
        if pd.notna(row.get('المعدل')) and float(row['المعدل']) < 3:
            anomalies.append({
                "الاسم": str(row[name_col]),
                "النوع": "ضعف شديد",
                "المعدل": round(float(row['المعدل']), 2)
            })
    if not anomalies:
        return "✅ لا توجد حالات استثنائية."
    prompt = f"""حلّل هذه الحالات الاستثنائية واقترح إجراءات:
{json.dumps(anomalies, ensure_ascii=False, indent=2)}"""
    return call_mistral(prompt)

def ai_recommendations(df, name_col, grade_cols):
    """توصيات تربوية"""
    weak = {}
    for col in grade_cols:
        if col in df.columns:
            below = (df[col] < 5).sum()
            weak[col] = {"معدل": round(df[col].mean(), 2), "ضعفاء": int(below), "نسبة": round(below/len(df)*100, 1)}
    prompt = f"""بناءً على تحليل {len(df)} تلميذاً:
📚 المواد: {json.dumps(weak, ensure_ascii=False, indent=2)}
📊 معدل القسم: {round(df['المعدل'].mean(), 2)}
قدّم خطة عمل: 1) دعم المواد الضعيفة 2) مجموعات مستوى 3) جدول دعم 4) نصائح للأولياء 5) أنشطة تحفيزية"""
    return call_mistral(prompt)

# ══════════════════════════════════════════════════════════════
# الخطوة 1: المستوى الدراسي
# ══════════════════════════════════════════════════════════════
st.subheader("📚 الخطوة 1: المستوى الدراسي")
level = st.radio(
    "حدد المستوى:", ["السنة الأولى والثانية", "السنة الثالثة والرابعة والخامسة"], horizontal=True
)

# ══════════════════════════════════════════════════════════════
# الخطوة 2: رفع الملفات
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📁 الخطوة 2: رفع ملفات الأساتذة")
uploaded_files = {}
col1, col2 = st.columns(2)
with col1:
    uploaded_files['معلم القسم'] = st.file_uploader(
        "📄 ملف معلّم القسم (المرجع الأساسي)", type=['xlsx', 'xls']
    )
with col2:
    uploaded_files['التربية البدنية'] = st.file_uploader(
        "🏃 ملف أستاذ التربية البدنية", type=['xlsx', 'xls']
    )
if level == "السنة الثالثة والرابعة والخامسة":
    col3, col4 = st.columns(2)
    with col3:
        uploaded_files['اللغة الفرنسية'] = st.file_uploader(
            "🇫🇷 ملف أستاذ اللغة الفرنسية", type=['xlsx', 'xls']
        )
    with col4:
        uploaded_files['اللغة الإنجليزية'] = st.file_uploader(
            "🇬🇧 ملف أستاذ اللغة الإنجليزية", type=['xlsx', 'xls']
        )

# حذف الملفات غير المرفوعة
uploaded_files = {k: v for k, v in uploaded_files.items() if v is not None}
if 'معلم القسم' not in uploaded_files:
    st.info("⏳ يرجى رفع ملف معلّم القسم على الأقل (الملف المرجعي)")
    st.stop()
st.success(f"✅ تم رفع {len(uploaded_files)} ملف(ات)")

# ══════════════════════════════════════════════════════════════
# 🌟 الخطوة 3: ربط الأوراق — الحل الجذري للمشكلة
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📋 الخطوة 3: ربط أوراق العمل بين الملفات")
st.markdown("""
<div class="mapping-box">
<strong>📌 لماذا هذه الخطوة مهمة؟</strong><br>
كل أستاذ يسمّي أوراق ملفه بطريقته الخاصة. مثلاً:<br>
• معلم القسم قد يسمّي الورقة: <b>"التربية الإسلامية"</b> أو <b>"السنة الأولى أ"</b><br>
• أستاذ الرياضة قد يسمّيها: <b>"1AP-A"</b> أو <b>"السنة الأولى"</b><br>
لذلك يجب أن تحدد يدوياً أي ورقة من كل ملف تخص نفس القسم.
</div>
""", unsafe_allow_html=True)

try:
    # ═══ استخراج أوراق كل ملف ═══
    all_file_sheets = {}
    for subject, file in uploaded_files.items():
        sheets = get_sheet_names_safe(file)
        all_file_sheets[subject] = sheets
        
    # ═══ عرض ملخص الأوراق لكل ملف ═══
    with st.expander("🔍 عرض جميع أوراق العمل في كل ملف"):
        for subject, sheets in all_file_sheets.items():
            st.write(f"**📘 {subject}**: {len(sheets)} ورقة → `{sheets}`")
        st.markdown("---")
        
    # ═══ اختيار الورقة المرجعية ═══
    ref_sheets = all_file_sheets['معلم القسم']
    st.write("#### 1️⃣ اختر الورقة من ملف معلّم القسم (المرجع)")
    selected_ref_sheet = st.selectbox(
        "📄 الورقة المرجعية:", ref_sheets, key="ref_sheet"
    )
    
    # ═══ معاينة الورقة المرجعية ═══
    with st.expander(f"👁️ معاينة: {selected_ref_sheet} (معلم القسم)"):
        preview_ref = read_sheet_safe(uploaded_files['معلم القسم'], selected_ref_sheet)
        st.write(f"**{len(preview_ref)} تلميذ** — الأعمدة: `{list(preview_ref.columns)}`")
        st.dataframe(preview_ref.head(8), use_container_width=True)
        
    # ═══ ربط الأوراق لباقي الملفات ═══
    st.markdown("---")
    st.write("#### 2️⃣ حدد الورقة المقابلة في كل ملف أستاذ")
    sheet_mapping = {'معلم القسم': selected_ref_sheet}
    
    for subject, file in uploaded_files.items():
        if subject == 'معلم القسم':
            continue
        other_sheets = all_file_sheets[subject]
        
        # ✨ المطابقة الذكية التلقائية
        suggested = fuzzy_match_sheet(selected_ref_sheet, other_sheets)
        suggested_idx = other_sheets.index(suggested) if suggested and suggested in other_sheets else 0
        
        col_a, col_b = st.columns([3, 1])
        with col_a:
            selected = st.selectbox(
                f"📗 ورقة **{subject}** المقابلة لـ «{selected_ref_sheet}»:", 
                other_sheets, 
                index=suggested_idx, 
                key=f"sheet_{subject}"
            )
            sheet_mapping[subject] = selected
        with col_b:
            if suggested and suggested == selected:
                st.markdown("<br>", unsafe_allow_html=True)
                st.success("🤖 مطابقة تلقائية")
            else:
                st.markdown("<br>", unsafe_allow_html=True)
                st.info("✋ اختيار يدوي")
                
        # معاينة صغيرة
        with st.expander(f"👁️ معاينة: {selected} ({subject})"):
            preview = read_sheet_safe(file, selected)
            st.write(f"**{len(preview)} تلميذ** — الأعمدة: `{list(preview.columns)}`")
            st.dataframe(preview.head(5), use_container_width=True)
            
    # ═══ ملخص الربط ═══
    st.markdown("---")
    st.write("#### ✅ ملخص الربط النهائي")
    mapping_summary = ""
    for subject, sheet in sheet_mapping.items():
        mapping_summary += f"| **{subject}** | `{sheet}` |\n"
        
    st.markdown(f"""
| الملف | الورقة المحددة |
|-------|---------------|
{mapping_summary}
    """)
    
except Exception as e:
    st.error(f"❌ خطأ في قراءة الملفات: {e}")
    st.stop()

# ══════════════════════════════════════════════════════════════
# الخطوة 4: الدمج وحساب المعدلات
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("⚙️ الخطوة 4: الدمج وحساب المعدلات")

if st.button("🚀 بدء الدمج وحساب المعدلات", type="primary", use_container_width=True):
    progress = st.progress(0, text="جاري التهيئة...")
    
    # ═══ 4.1 قراءة الورقة المحددة من كل ملف ═══
    dataframes = {}
    step = 0
    for subject, file in uploaded_files.items():
        step += 1
        target_sheet = sheet_mapping[subject] # ⬅️ الورقة التي اختارها المستخدم
        progress.progress(
            int((step / (len(uploaded_files) + 3)) * 100), 
            text=f"قراءة «{target_sheet}» من ملف {subject}..."
        )
        try:
            df = read_sheet_safe(file, target_sheet)
            if len(df) == 0:
                st.warning(f"⚠️ الورقة «{target_sheet}» في ملف {subject} فارغة!")
                continue
            dataframes[subject] = df
            st.caption(f"✅ {subject}: تم قراءة {len(df)} سطر من «{target_sheet}»")
        except Exception as e:
            st.error(f"❌ خطأ في قراءة «{target_sheet}» من {subject}: {e}")
            continue
            
    if 'معلم القسم' not in dataframes:
        st.error("❌ فشل في قراءة الملف المرجعي!")
        st.stop()
        
    # ═══ 4.2 تحديد عمود الاسم ═══
    progress.progress(50, text="تحديد أعمدة الأسماء والنقاط...")
    ref_df = dataframes['معلم القسم'].copy()
    name_col = find_name_column(ref_df)
    
    if not name_col:
        st.error("❌ لم يُعثر على عمود الاسم في الملف المرجعي!")
        st.write("الأعمدة المتاحة:", list(ref_df.columns))
        st.stop()
        
    st.info(f"🔎 عمود الاسم المكتشف: **{name_col}**")
    
    # عمود مطابقة موحّد
    ref_df['_match_key'] = ref_df[name_col].apply(normalize_arabic)
    ref_grade_cols = find_grade_columns(ref_df, [name_col, '_match_key'])
    st.write(f"📘 **معلم القسم** — نقاط: `{ref_grade_cols}`")
    
    # ═══ 4.3 دمج ملفات الأساتذة الآخرين ═══
    progress.progress(65, text="دمج البيانات...")
    final_df = ref_df.copy()
    all_grade_cols_names = list(ref_grade_cols)
    
    for subject, df in dataframes.items():
        if subject == 'معلم القسم':
            continue
            
        other_name_col = find_name_column(df)
        if not other_name_col:
            st.warning(f"⚠️ لم يُعثر على عمود الاسم في {subject} — تم تخطيه")
            continue
            
        other_grade_cols = find_grade_columns(df, [other_name_col])
        if not other_grade_cols:
            st.warning(f"⚠️ لم يُعثر على أعمدة نقاط في {subject}")
            continue
            
        st.write(f"📗 **{subject}** — نقاط: `{other_grade_cols}`")
        
        # تحضير الدمج
        merge_df = df[[other_name_col] + other_grade_cols].copy()
        merge_df['_match_key'] = merge_df[other_name_col].apply(normalize_arabic)
        
        # إعادة تسمية لتجنب التكرار
        rename_map = {}
        for col in other_grade_cols:
            if col in all_grade_cols_names or col in final_df.columns:
                new_name = f"{col} ({subject})"
            else:
                new_name = col
            rename_map[col] = new_name
            
        merge_df = merge_df.rename(columns=rename_map)
        all_grade_cols_names.extend(rename_map.values())
        merge_df = merge_df.drop(columns=[other_name_col])
        
        # الدمج
        before_count = len(final_df)
        final_df = pd.merge(final_df, merge_df, on='_match_key', how='left')
        
        # عرض نتيجة المطابقة
        matched = merge_df['_match_key'].isin(final_df['_match_key']).sum()
        st.caption(f" ↳ تم مطابقة {matched}/{len(merge_df)} تلميذ")
        
    # حذف عمود المطابقة
    final_df = final_df.drop(columns=['_match_key'], errors='ignore')
    
    # ═══ 4.4 حساب المعدل ═══
    progress.progress(85, text="حساب المعدلات...")
    final_grade_cols = find_grade_columns(
        final_df, [name_col] + [c for c in final_df.columns if c in ['المجموع','المعدل','التقدير','عدد المواد','الترتيب']]
    )
    
    if final_grade_cols:
        final_df['عدد المواد'] = final_df[final_grade_cols].notna().sum(axis=1)
        final_df['المجموع'] = final_df[final_grade_cols].sum(axis=1)
        final_df['المعدل'] = (final_df['المجموع'] / final_df['عدد المواد']).round(2)
        final_df['التقدير'] = final_df['المعدل'].apply(classify_student)
        final_df = final_df.sort_values('المعدل', ascending=False).reset_index(drop=True)
        final_df.insert(0, 'الترتيب', range(1, len(final_df) + 1))
        
        st.write(f"📊 تم حساب المعدل باستخدام **{len(final_grade_cols)}** مادة: `{final_grade_cols}`")
    else:
        st.error("❌ لم يتم العثور على أعمدة نقاط لحساب المعدل!")
        st.stop()
        
    progress.progress(100, text="✅ اكتمل بنجاح!")
    
    # حفظ في Session
    st.session_state['final_df'] = final_df
    st.session_state['name_col'] = name_col
    st.session_state['grade_cols'] = final_grade_cols
    st.session_state['selected_sheet'] = selected_ref_sheet
    st.session_state['done'] = True

# ══════════════════════════════════════════════════════════════
# عرض النتائج
# ══════════════════════════════════════════════════════════════
if st.session_state.get('done'):
    final_df = st.session_state['final_df']
    name_col = st.session_state['name_col']
    grade_cols = st.session_state['grade_cols']
    selected_sheet = st.session_state['selected_sheet']
    
    st.markdown("---")
    st.write(f"### 📊 النتائج النهائية — «{selected_sheet}»")
    st.dataframe(final_df, use_container_width=True, height=450)
    
    # ═══ إحصائيات ═══
    if 'المعدل' in final_df.columns:
        st.write("### 📈 إحصائيات القسم")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("👥 العدد", len(final_df))
        with c2:
            st.metric("🏆 الأعلى", final_df['المعدل'].max())
        with c3:
            st.metric("📉 الأدنى", final_df['المعدل'].min())
        with c4:
            st.metric("📊 المعدل", round(final_df['المعدل'].mean(), 2))
        with c5:
            pct = round((final_df['المعدل'] >= 5).sum() / len(final_df) * 100, 1)
            st.metric("✅ النجاح", f"{pct}%")
            
        # رسم بياني
        chart_df = final_df[[name_col, 'المعدل']].set_index(name_col)
        st.bar_chart(chart_df, height=300)
        
    # ══════════════════════════════════════════════════════
    # 🤖 الذكاء الاصطناعي
    # ══════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("""
<div class="ai-box">
<h2 style="color:white; text-align:center;">🤖 التحليل بالذكاء الاصطناعي Mistral</h2>
</div>
    """, unsafe_allow_html=True)
    
    if not api_key:
        st.warning("⚠️ أدخل مفتاح Mistral API في الشريط الجانبي")
    else:
        ai_tabs = st.tabs([
            "📊 تحليل القسم", "👤 تقرير فردي", "🔍 حالات استثنائية", "💡 توصيات", "💬 محادثة حرة"
        ])
        
        # ─── تحليل القسم ───
        with ai_tabs[0]:
            if st.button("🤖 تحليل شامل للقسم", key="ai_class"):
                with st.spinner("🤖 جاري التحليل..."):
                    result = ai_analyze_class(final_df, name_col, grade_cols, selected_sheet)
                    st.markdown(f'<div class="ai-response">{result}</div>', unsafe_allow_html=True)
                    st.session_state['class_analysis'] = result
                    
        # ─── تقرير فردي ───
        with ai_tabs[1]:
            names = final_df[name_col].tolist()
            sel = st.selectbox("اختر التلميذ:", names, key="ai_student")
            if st.button("📝 إنشاء تقرير", key="ai_report"):
                row = final_df[final_df[name_col] == sel].iloc[0]
                with st.spinner(f"🤖 تقرير {sel}..."):
                    result = ai_student_report(row, name_col, grade_cols, final_df['المعدل'].mean())
                    st.markdown(f'<div class="student-card"><h4>📋 {sel}</h4><hr>{result}</div>', unsafe_allow_html=True)
                    
        # ─── حالات استثنائية ───
        with ai_tabs[2]:
            if st.button("🔍 كشف الحالات", key="ai_anomaly"):
                with st.spinner("🤖 جاري الفحص..."):
                    result = ai_detect_anomalies(final_df, name_col, grade_cols)
                    st.markdown(f'<div class="ai-response">{result}</div>', unsafe_allow_html=True)
                    
        # ─── توصيات ───
        with ai_tabs[3]:
            if st.button("💡 خطة عمل تربوية", key="ai_recs"):
                with st.spinner("🤖 جاري الإعداد..."):
                    result = ai_recommendations(final_df, name_col, grade_cols)
                    st.markdown(f'<div class="ai-response">{result}</div>', unsafe_allow_html=True)
                    
        # ─── محادثة حرة ───
        with ai_tabs[4]:
            st.caption("اسأل أي سؤال حول نتائج القسم")
            context = f"""بيانات القسم «{selected_sheet}»:
- عدد التلاميذ: {len(final_df)}
- معدل القسم: {round(final_df['المعدل'].mean(), 2)}
- نسبة النجاح: {round((final_df['المعدل']>=5).sum()/len(final_df)*100,1)}%
- المواد: {grade_cols}
- أول 10 تلاميذ:\n{final_df.head(10).to_string()}"""

            if 'chat' not in st.session_state:
                st.session_state.chat = []
                
            for msg in st.session_state.chat:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
                    
            user_q = st.chat_input("اكتب سؤالك...")
            if user_q:
                st.session_state.chat.append({"role": "user", "content": user_q})
                with st.chat_message("user"):
                    st.write(user_q)
                with st.chat_message("assistant"):
                    with st.spinner("🤖 ..."):
                        ans = call_mistral(f"{context}\n\nسؤال: {user_q}")
                    st.write(ans)
                    st.session_state.chat.append({"role": "assistant", "content": ans})
                    
                if st.button("🗑️ مسح المحادثة"):
                    st.session_state.chat = []
                    st.rerun()

    # ══════════════════════════════════════════════════════
    # التصدير
    # ══════════════════════════════════════════════════════
    st.markdown("---")
    st.write("### 📥 تصدير النتائج")
    c_e1, c_e2 = st.columns(2)
    with c_e1:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, index=False, sheet_name=selected_sheet[:31])
            wb = writer.book
            ws = writer.sheets[selected_sheet[:31]]
            hfmt = wb.add_format({'bold': True, 'bg_color': '#4472C4', 'font_color': 'white', 'border': 1, 'align': 'center'})
            for i, col in enumerate(final_df.columns):
                ws.write(0, i, col, hfmt)
                ws.set_column(i, i, max(len(str(col)) + 5, 12))
        st.download_button(
            "📥 تحميل Excel",
            data=output.getvalue(),
            file_name=f"نتائج_{selected_sheet}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with c_e2:
        if st.session_state.get('class_analysis'):
            txt = f"تقرير {selected_sheet}\n{'='*50}\n{st.session_state['class_analysis']}"
            st.download_button(
                "📥 تحميل تقرير AI",
                data=txt.encode('utf-8'),
                file_name=f"تقرير_AI_{selected_sheet}.txt",
                mime="text/plain",
                use_container_width=True
            )


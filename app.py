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
h1, h2, h3, h4, p, li, span {direction: rtl; text-align: right;}
.stMetric {direction: ltr;}
.ai-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; padding: 20px; margin: 15px 0; color: white; box-shadow: 0 8px 32px rgba(102,126,234,0.3); }
.ai-response { background: #f8f9ff; border-radius: 12px; padding: 20px; margin: 10px 0; border-right: 5px solid #667eea; line-height: 2; font-size: 15px; }
.success-box { background: #d4edda; border-radius: 10px; padding: 15px; margin: 10px 0; border-right: 5px solid #28a745; }
.warning-box { background: #fff3cd; border-radius: 10px; padding: 15px; margin: 10px 0; border-right: 5px solid #ffc107; }
.student-card { background: white; border-radius: 10px; padding: 15px; margin: 8px 0; border: 1px solid #e0e0e0; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.metric-card { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 12px; padding: 20px; text-align: center; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ai-box">
    <h1 style="color:white; text-align:center;">🤖🏫 النظام الذكي لحساب وتحليل معدلات التلاميذ</h1>
    <p style="text-align:center; font-size:18px;">مدعوم بالذكاء الاصطناعي Mistral AI — تحليل تربوي متقدم</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# إعداد Mistral AI API
# ══════════════════════════════════════════════════════════════
def get_mistral_key():
    """الحصول على مفتاح API من مصادر متعددة"""
    try:
        return st.secrets["MISTRAL_API_KEY"]
    except:
        pass
    return None

# الشريط الجانبي لإعدادات AI
with st.sidebar:
    st.markdown("## ⚙️ إعدادات الذكاء الاصطناعي")
    api_key = get_mistral_key()
    if not api_key:
        api_key = st.text_input(
            "🔑 مفتاح Mistral API", type="password", help="أدخل مفتاح API من https://console.mistral.ai/"
        )
    if api_key:
        st.success("✅ مفتاح API مُفعّل")
    else:
        st.warning("⚠️ أدخل المفتاح لتفعيل التحليل الذكي")
        
    st.markdown("---")
    ai_model = st.selectbox(
        "🧠 نموذج الذكاء الاصطناعي", [
            "mistral-large-latest",
            "mistral-medium-latest",
            "mistral-small-latest",
            "open-mistral-nemo"
        ], help="النموذج الأكبر = تحليل أدق لكن أبطأ"
    )
    ai_temperature = st.slider(
        "🌡️ درجة الإبداعية", 0.0, 1.0, 0.7, help="0 = دقيق ومحافظ، 1 = إبداعي ومتنوع"
    )
    
    st.markdown("---")
    st.markdown("### 🤖 ميزات AI المتاحة")
    enable_class_analysis = st.checkbox("📊 تحليل شامل للقسم", value=True)
    enable_student_reports = st.checkbox("👤 تقارير فردية للتلاميذ", value=True)
    enable_anomaly_detection = st.checkbox("🔍 كشف الحالات الاستثنائية", value=True)
    enable_recommendations = st.checkbox("💡 توصيات تربوية", value=True)
    enable_parent_report = st.checkbox("📋 تقرير لأولياء الأمور", value=False)

# ══════════════════════════════════════════════════════════════
# دوال الذكاء الاصطناعي Mistral AI
# ══════════════════════════════════════════════════════════════
def call_mistral(prompt, system_prompt=None, api_key=api_key):
    """استدعاء Mistral AI API"""
    if not api_key:
        return "⚠️ يرجى إدخال مفتاح Mistral API في الشريط الجانبي"
        
    if not system_prompt:
        system_prompt = """أنت مستشار تربوي ذكي متخصص في تحليل نتائج تلاميذ المرحلة الابتدائية في النظام التعليمي الجزائري. تقدم تحليلات دقيقة وعملية باللغة العربية الفصحى. استخدم الأرقام والنسب في تحليلك. كن محدداً وعملياً في توصياتك. المعدل من 10 نقاط. 5/10 هو الحد الأدنى للنجاح."""
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": ai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": ai_temperature,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions", headers=headers, json=payload, timeout=60
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        elif response.status_code == 401:
            return "❌ مفتاح API غير صالح. يرجى التحقق منه."
        elif response.status_code == 429:
            return "⏳ تم تجاوز حد الطلبات. يرجى الانتظار قليلاً."
        else:
            return f"❌ خطأ من الخادم: {response.status_code} — {response.text}"
    except requests.exceptions.Timeout:
        return "⏳ انتهت مهلة الاتصال. يرجى المحاولة مرة أخرى."
    except requests.exceptions.ConnectionError:
        return "❌ لا يوجد اتصال بالإنترنت."
    except Exception as e:
        return f"❌ خطأ غير متوقع: {str(e)}"

def ai_analyze_class(df, name_col, grade_cols, section_name):
    """تحليل شامل لأداء القسم"""
    stats = {
        "القسم": section_name,
        "عدد_التلاميذ": len(df),
        "معدل_القسم": round(df['المعدل'].mean(), 2),
        "أعلى_معدل": round(df['المعدل'].max(), 2),
        "أدنى_معدل": round(df['المعدل'].min(), 2),
        "نسبة_النجاح": round((df['المعدل'] >= 5).sum() / len(df) * 100, 1),
        "عدد_الناجحين": int((df['المعدل'] >= 5).sum()),
        "عدد_الراسبين": int((df['المعدل'] < 5).sum()),
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
            
    top_3 = df.nlargest(3, 'المعدل')[[name_col, 'المعدل']].to_dict('records')
    bottom_3 = df.nsmallest(3, 'المعدل')[[name_col, 'المعدل']].to_dict('records')
    
    prompt = f"""
    حلّل نتائج هذا القسم تحليلاً تربوياً شاملاً ومهنياً:
    📊 الإحصائيات العامة: {json.dumps(stats, ensure_ascii=False, indent=2)}
    📚 إحصائيات المواد: {json.dumps(subject_stats, ensure_ascii=False, indent=2)}
    🏆 أفضل 3 تلاميذ: {json.dumps(top_3, ensure_ascii=False)}
    ⚠️ أضعف 3 تلاميذ: {json.dumps(bottom_3, ensure_ascii=False)}
    المطلوب:
    1. 📈 تحليل عام لمستوى القسم (ممتاز/جيد/متوسط/ضعيف) مع التبرير
    2. 📚 تحليل أداء كل مادة وتحديد المواد التي تحتاج تعزيزاً
    3. 📊 تحليل توزيع المعدلات (هل يوجد تفاوت كبير؟ تجمعات؟)
    4. ⚡ نقاط القوة ونقاط الضعف في القسم
    5. 💡 توصيات عملية ومحددة للمعلم
    6. 🎯 أهداف مقترحة للفصل القادم
    استخدم الإيموجي والتنسيق الواضح. كن محدداً بالأرقام.
    """
    return call_mistral(prompt)

def ai_student_report(student_row, name_col, grade_cols, class_avg):
    """تقرير فردي لتلميذ"""
    student_data = {
        "الاسم": str(student_row[name_col]),
        "المعدل": round(float(student_row['المعدل']), 2),
        "معدل_القسم": round(float(class_avg), 2),
        "الترتيب": int(student_row.get('الترتيب', 0)),
        "التقدير": str(student_row.get('التقدير', '')),
    }
    
    grades = {}
    for col in grade_cols:
        if col in student_row.index and pd.notna(student_row[col]):
            grades[col] = round(float(student_row[col]), 2)
    student_data["النقاط"] = grades
    
    prompt = f"""
    اكتب تقريراً تربوياً موجزاً وعملياً لهذا التلميذ:
    {json.dumps(student_data, ensure_ascii=False, indent=2)}
    المطلوب (في 8-10 أسطر):
    1. تقييم عام للمستوى مقارنة بمعدل القسم
    2. المواد القوية والمواد التي تحتاج تحسيناً
    3. نصيحتان عمليتان للتلميذ
    4. ملاحظة موجهة لولي الأمر
    كن إيجابياً ومشجعاً حتى مع التلاميذ الضعفاء.
    """
    return call_mistral(prompt)

def ai_detect_anomalies(df, name_col, grade_cols):
    """كشف الحالات الاستثنائية"""
    anomalies = []
    for _, row in df.iterrows():
        student_grades = []
        for col in grade_cols:
            if col in row.index and pd.notna(row[col]):
                student_grades.append(float(row[col]))
                
        if len(student_grades) >= 2:
            max_g = max(student_grades)
            min_g = min(student_grades)
            if max_g - min_g >= 6:
                anomalies.append({
                    "الاسم": str(row[name_col]),
                    "النوع": "تفاوت كبير بين المواد",
                    "أعلى_نقطة": max_g,
                    "أدنى_نقطة": min_g,
                    "الفرق": round(max_g - min_g, 2)
                })
                
        if pd.notna(row.get('المعدل')) and float(row['المعدل']) < 3:
            anomalies.append({
                "الاسم": str(row[name_col]),
                "النوع": "معدل ضعيف جداً يستدعي تدخلاً",
                "المعدل": round(float(row['المعدل']), 2)
            })
            
        if pd.notna(row.get('المعدل')) and float(row['المعدل']) >= 9:
            anomalies.append({
                "الاسم": str(row[name_col]),
                "النوع": "تلميذ متفوق يحتاج تحديات إضافية",
                "المعدل": round(float(row['المعدل']), 2)
            })
            
    if not anomalies:
        return "✅ لم يتم رصد حالات استثنائية تستدعي التنبيه."
        
    prompt = f"""
    تم رصد الحالات الاستثنائية التالية في القسم:
    {json.dumps(anomalies, ensure_ascii=False, indent=2)}
    المطلوب:
    1. تحليل كل حالة وشرح دلالتها التربوية
    2. اقتراح إجراءات عملية لكل حالة
    3. تحديد الأولويات (أي الحالات تحتاج تدخلاً فورياً)
    رتّب الحالات حسب الأولوية. كن عملياً ومحدداً.
    """
    return call_mistral(prompt)

def ai_generate_recommendations(df, name_col, grade_cols):
    """توصيات تربوية ذكية"""
    weak_subjects = {}
    for col in grade_cols:
        if col in df.columns:
            avg = df[col].mean()
            below_avg = (df[col] < 5).sum()
            weak_subjects[col] = {
                "معدل_المادة": round(avg, 2),
                "عدد_أقل_من_5": int(below_avg),
                "نسبة_الضعفاء": round(below_avg / len(df) * 100, 1)
            }
            
    prompt = f"""
    بناءً على تحليل نتائج {len(df)} تلميذاً:
    📚 أداء المواد: {json.dumps(weak_subjects, ensure_ascii=False, indent=2)}
    📊 معدل القسم: {round(df['المعدل'].mean(), 2)}
    📊 نسبة النجاح: {round((df['المعدل'] >= 5).sum() / len(df) * 100, 1)}%
    قدّم خطة عمل تربوية متكاملة تشمل:
    1. 📋 خطة دعم للمواد الضعيفة (أنشطة محددة لكل مادة)
    2. 👥 اقتراح تقسيم التلاميذ إلى مجموعات مستوى
    3. 📅 جدول زمني مقترح لحصص الدعم والمعالجة
    4. 🏠 نصائح للأولياء لمتابعة أبنائهم في المنزل
    5. 🎮 أنشطة تحفيزية وألعاب تعليمية مقترحة
    6. 📝 مؤشرات قياس التحسن للفترة القادمة
    اجعل الخطة عملية وقابلة للتطبيق في الواقع الجزائري.
    """
    return call_mistral(prompt)

def ai_parent_report(student_row, name_col, grade_cols, class_avg):
    """تقرير موجه لولي الأمر"""
    student_data = {
        "الاسم": str(student_row[name_col]),
        "المعدل": round(float(student_row['المعدل']), 2),
        "معدل_القسم": round(float(class_avg), 2),
        "الترتيب": int(student_row.get('الترتيب', 0)),
    }
    
    grades = {}
    for col in grade_cols:
        if col in student_row.index and pd.notna(student_row[col]):
            grades[col] = round(float(student_row[col]), 2)
    student_data["النقاط"] = grades
    
    prompt = f"""
    اكتب رسالة مهنية وودية موجهة لولي أمر هذا التلميذ:
    {json.dumps(student_data, ensure_ascii=False, indent=2)}
    يجب أن تتضمن الرسالة:
    1. تحية وترحيب
    2. ملخص عن مستوى التلميذ بلغة بسيطة ومفهومة
    3. النقاط الإيجابية (حتى لو كان المستوى ضعيفاً)
    4. المجالات التي تحتاج تحسيناً
    5. 3 نصائح عملية يمكن لولي الأمر تطبيقها في المنزل
    6. خاتمة مشجعة
    اللهجة: مهنية، محترمة، مشجعة، غير جارحة.
    اللغة: عربية فصحى بسيطة.
    الطول: 10-15 سطراً.
    """
    system = """أنت معلم خبير في المرحلة الابتدائية بالجزائر. تكتب رسائل مهنية وودية لأولياء الأمور. تستخدم لغة بسيطة ومشجعة."""
    return call_mistral(prompt, system_prompt=system)

def ai_smart_column_detection(columns_list):
    """استخدام AI لتحديد أعمدة النقاط بذكاء"""
    prompt = f"""
    لديّ ملف إكسيل لنقاط تلاميذ المرحلة الابتدائية في الجزائر. أسماء الأعمدة هي:
    {json.dumps(columns_list, ensure_ascii=False)}
    صنّف كل عمود إلى:
    - "اسم": عمود يحتوي اسم التلميذ أو لقبه
    - "نقطة": عمود يحتوي نقطة مادة دراسية
    - "معلومة": عمود معلومات أخرى (رقم، تاريخ، ملاحظة...)
    - "تجاهل": عمود فارغ أو غير مفيد
    أجب بصيغة JSON فقط بدون أي نص إضافي:
    {{"عمود1": "تصنيف", "عمود2": "تصنيف"}}
    """
    system = "أنت محلل بيانات. أجب بصيغة JSON فقط بدون أي شرح."
    result = call_mistral(prompt, system_prompt=system)
    try:
        json_match = re.search(r'\{[^{}]+\}', result, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass
    return None

# ══════════════════════════════════════════════════════════════
# الدوال المساعدة (Helper Functions)
# ══════════════════════════════════════════════════════════════
def normalize_arabic(text):
    """توحيد الأسماء العربية"""
    if pd.isna(text):
        return ""
    text = str(text).strip()
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    text = text.replace('ئ', 'ي').replace('ؤ', 'و')
    return text

def find_name_column(df):
    """البحث عن عمود الاسم"""
    keywords = [
        'اللقب والاسم', 'الاسم واللقب', 'اسم', 'لقب', 'الاسم', 'اللقب', 
        'التلميذ', 'الطالب', 'nom', 'name'
    ]
    for col in df.columns:
        col_clean = str(col).strip()
        for kw in keywords:
            if kw in col_clean:
                return col
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].notna().sum() > 0:
            return col
    return None

def find_grade_columns(df, exclude_cols):
    """استخراج أعمدة النقاط"""
    skip_keywords = [
        'رقم', 'ترتيب', 'تسلسل', 'ميلاد', 'تاريخ', 'ملاحظ', 'قسم', 'فوج', 
        'سنة', 'جنس', 'عنوان', 'هاتف', 'ولي', '#', 'num', 'id', 'مجموع', 
        'معدل', 'تقدير', 'عدد'
    ]
    grade_cols = []
    for col in df.columns:
        if col in exclude_cols:
            continue
        col_lower = str(col).strip().lower()
        if any(kw in col_lower for kw in skip_keywords):
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            col_max = df[col].max()
            if pd.notna(col_max) and col_max <= 20:
                grade_cols.append(col)
    return grade_cols

def read_sheet_safe(file, sheet_name):
    """قراءة آمنة لورقة عمل"""
    file.seek(0)
    df = pd.read_excel(file, sheet_name=sheet_name)
    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(how='all')
    return df

def get_sheet_names_safe(file):
    """استخراج أسماء الأوراق"""
    file.seek(0)
    xls = pd.ExcelFile(file)
    return xls.sheet_names

def classify_student(avg):
    """تصنيف التلميذ"""
    if pd.isna(avg):
        return "—"
    if avg >= 9:
        return "ممتاز 🌟"
    elif avg >= 8:
        return "جيد جداً ✅"
    elif avg >= 7:
        return "جيد 👍"
    elif avg >= 5:
        return "مقبول 📗"
    elif avg >= 3.5:
        return "ضعيف ⚠️"
    else:
        return "ضعيف جداً ❌"

# ══════════════════════════════════════════════════════════════
# الخطوة 1: تحديد المستوى الدراسي
# ══════════════════════════════════════════════════════════════
st.subheader("📚 الخطوة 1: تحديد المستوى الدراسي")
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
        "📄 ملف معلّم القسم (المرجع)", type=['xlsx', 'xls']
    )
with col2:
    uploaded_files['التربية البدنية'] = st.file_uploader(
        "🏃 ملف التربية البدنية", type=['xlsx', 'xls']
    )

if level == "السنة الثالثة والرابعة والخامسة":
    col3, col4 = st.columns(2)
    with col3:
        uploaded_files['اللغة الفرنسية'] = st.file_uploader(
            "🇫🇷 ملف اللغة الفرنسية", type=['xlsx', 'xls']
        )
    with col4:
        uploaded_files['اللغة الإنجليزية'] = st.file_uploader(
            "🇬🇧 ملف اللغة الإنجليزية", type=['xlsx', 'xls']
        )

# التحقق من الرفع
missing = [s for s, f in uploaded_files.items() if f is None]
if missing:
    if any(f is not None for f in uploaded_files.values()):
        st.info(f"⏳ في انتظار: **{' ، '.join(missing)}**")
    st.stop()
    
uploaded_files = {k: v for k, v in uploaded_files.items() if v is not None}
st.success(f"✅ تم رفع {len(uploaded_files)} ملفات!")

# ══════════════════════════════════════════════════════════════
# الخطوة 3: اختيار القسم
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📋 الخطوة 3: اختيار القسم")
try:
    sheet_names = get_sheet_names_safe(uploaded_files['معلم القسم'])
    if not sheet_names:
        st.error("❌ الملف المرجعي فارغ!")
        st.stop()
        
    selected_sheet = st.selectbox("🎯 اختر القسم:", sheet_names)

    # ═══ الكشف الذكي بالـ AI عن الأعمدة ═══
    if api_key:
        with st.expander("🤖 الكشف الذكي عن الأعمدة (AI)"):
            if st.button("🔍 تحليل هيكل الملف بالذكاء الاصطناعي"):
                preview = read_sheet_safe(uploaded_files['معلم القسم'], selected_sheet)
                cols = list(preview.columns)
                with st.spinner("🤖 جاري التحليل الذكي للأعمدة..."):
                    result = ai_smart_column_detection(cols)
                    if result:
                        st.json(result)
                    else:
                        st.write("لم يتمكن AI من تصنيف الأعمدة تلقائياً")
                        
except Exception as e:
    st.error(f"❌ خطأ: {e}")
    st.stop()

# ══════════════════════════════════════════════════════════════
# الخطوة 4: الدمج والحساب
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("⚙️ الخطوة 4: الدمج وحساب المعدلات")

if st.button("🚀 بدء المعالجة", type="primary", use_container_width=True):
    progress = st.progress(0, text="جاري التهيئة...")

    # 4.1 قراءة الأوراق
    dataframes = {}
    step = 0
    for subject, file in uploaded_files.items():
        step += 1
        progress.progress(
            int((step / (len(uploaded_files) + 3)) * 100), text=f"جاري قراءة {subject}..."
        )
        try:
            other_sheets = get_sheet_names_safe(file)
            if selected_sheet not in other_sheets:
                st.warning(f"⚠️ '{selected_sheet}' غير موجودة في {subject}")
                continue
            df = read_sheet_safe(file, selected_sheet)
            dataframes[subject] = df
        except Exception as e:
            st.error(f"❌ خطأ في {subject}: {e}")
            st.stop()
            
    if 'معلم القسم' not in dataframes:
        st.error("❌ فشل قراءة الملف المرجعي!")
        st.stop()

    # 4.2 تحديد عمود الاسم
    progress.progress(60, text="تحديد الأعمدة...")
    ref_df = dataframes['معلم القسم'].copy()
    name_col = find_name_column(ref_df)
    
    if not name_col:
        st.error("❌ لم يُعثر على عمود الاسم!")
        st.stop()
        
    ref_df['_match_key'] = ref_df[name_col].apply(normalize_arabic)
    ref_grade_cols = find_grade_columns(ref_df, [name_col, '_match_key'])

    # 4.3 الدمج
    progress.progress(75, text="دمج البيانات...")
    final_df = ref_df.copy()
    all_grade_cols = list(ref_grade_cols)
    
    for subject, df in dataframes.items():
        if subject == 'معلم القسم':
            continue
            
        other_name_col = find_name_column(df)
        if not other_name_col:
            continue
            
        other_grade_cols = find_grade_columns(df, [other_name_col])
        if not other_grade_cols:
            continue
            
        merge_df = df[[other_name_col] + other_grade_cols].copy()
        merge_df['_match_key'] = merge_df[other_name_col].apply(normalize_arabic)
        
        rename_map = {}
        for col in other_grade_cols:
            new_name = f"{col} ({subject})" if col in all_grade_cols else col
            rename_map[col] = new_name
            
        merge_df = merge_df.rename(columns=rename_map)
        all_grade_cols.extend(rename_map.values())
        merge_df = merge_df.drop(columns=[other_name_col])
        
        final_df = pd.merge(final_df, merge_df, on='_match_key', how='left')
        
    final_df = final_df.drop(columns=['_match_key'], errors='ignore')

    # 4.4 حساب المعدل
    progress.progress(90, text="حساب المعدلات...")
    final_grade_cols = find_grade_columns(
        final_df, [name_col] + [c for c in final_df.columns if c in ['المجموع', 'المعدل', 'التقدير', 'عدد المواد', 'الترتيب']]
    )
    
    if final_grade_cols:
        final_df['المجموع'] = final_df[final_grade_cols].sum(axis=1)
        final_df['عدد المواد'] = final_df[final_grade_cols].notna().sum(axis=1)
        final_df['المعدل'] = (final_df['المجموع'] / final_df['عدد المواد']).round(2)
        final_df['التقدير'] = final_df['المعدل'].apply(classify_student)
        final_df = final_df.sort_values('المعدل', ascending=False)
        final_df.insert(0, 'الترتيب', range(1, len(final_df) + 1))
        
    progress.progress(100, text="✅ اكتمل!")

    # ══════════════════════════════════════════════════════
    # حفظ النتائج في Session
    # ══════════════════════════════════════════════════════
    st.session_state['final_df'] = final_df
    st.session_state['name_col'] = name_col
    st.session_state['grade_cols'] = final_grade_cols
    st.session_state['selected_sheet'] = selected_sheet
    st.session_state['processing_done'] = True

# ══════════════════════════════════════════════════════════════
# عرض النتائج + AI
# ══════════════════════════════════════════════════════════════
if st.session_state.get('processing_done'):
    final_df = st.session_state['final_df']
    name_col = st.session_state['name_col']
    grade_cols = st.session_state['grade_cols']
    selected_sheet = st.session_state['selected_sheet']
    
    st.markdown("---")
    st.write(f"### 📊 النتائج — القسم: **{selected_sheet}**")
    st.dataframe(final_df, use_container_width=True, height=400)

    # ═══ الإحصائيات ═══
    if 'المعدل' in final_df.columns:
        st.write("### 📈 إحصائيات القسم")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("👥 العدد", len(final_df))
        with c2:
            st.metric("🏆 أعلى معدل", final_df['المعدل'].max())
        with c3:
            st.metric("📉 أدنى معدل", final_df['المعدل'].min())
        with c4:
            st.metric("📊 معدل القسم", round(final_df['المعدل'].mean(), 2))
        with c5:
            pct = round((final_df['المعدل'] >= 5).sum() / len(final_df) * 100, 1)
            st.metric("✅ نسبة النجاح", f"{pct}%")
            
        st.bar_chart(
            final_df.set_index(name_col)['المعدل'] if name_col else final_df['المعدل'], height=300
        )

    # ══════════════════════════════════════════════════════
    # 🤖 قسم الذكاء الاصطناعي
    # ══════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("""
    <div class="ai-box">
        <h2 style="color:white; text-align:center;">🤖 التحليل بالذكاء الاصطناعي</h2>
        <p style="text-align:center;">تحليلات تربوية متقدمة مدعومة بـ Mistral AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not api_key:
        st.warning("⚠️ أدخل مفتاح Mistral API في الشريط الجانبي لتفعيل هذه الميزات")
    else:
        # ═══ تبويبات AI ═══
        ai_tabs = st.tabs([
            "📊 تحليل القسم", "👤 تقارير فردية", "🔍 حالات استثنائية", 
            "💡 توصيات تربوية", "📋 رسائل الأولياء", "💬 محادثة حرة"
        ])

        # ─────── تبويب 1: تحليل القسم ───────
        with ai_tabs[0]:
            st.write("### 📊 التحليل الشامل لأداء القسم")
            if st.button("🤖 بدء التحليل الشامل", key="analyze_class"):
                with st.spinner("🤖 جاري التحليل... قد يستغرق 30 ثانية"):
                    analysis = ai_analyze_class(
                        final_df, name_col, grade_cols, selected_sheet
                    )
                st.markdown(f"""
                <div class="ai-response">
                    {analysis}
                </div>
                """, unsafe_allow_html=True)
                st.session_state['class_analysis'] = analysis

        # ─────── تبويب 2: تقارير فردية ───────
        with ai_tabs[1]:
            st.write("### 👤 تقارير فردية للتلاميذ")
            student_names = final_df[name_col].tolist()
            selected_student = st.selectbox(
                "اختر التلميذ:", student_names, key="student_select"
            )
            
            if st.button("📝 إنشاء تقرير فردي", key="student_report"):
                student_row = final_df[final_df[name_col] == selected_student].iloc[0]
                class_avg = final_df['المعدل'].mean()
                with st.spinner(f"🤖 جاري إعداد تقرير {selected_student}..."):
                    report = ai_student_report(
                        student_row, name_col, grade_cols, class_avg
                    )
                st.markdown(f"""
                <div class="student-card">
                    <h4>📋 تقرير: {selected_student}</h4>
                    <hr>
                    {report}
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("---")
            if st.button("📝 إنشاء تقارير لجميع التلاميذ", key="all_reports"):
                all_reports = {}
                progress_bar = st.progress(0)
                for i, (_, row) in enumerate(final_df.iterrows()):
                    name = row[name_col]
                    progress_bar.progress(
                        int((i + 1) / len(final_df) * 100), text=f"تقرير {name}..."
                    )
                    with st.spinner(f"📝 {name}..."):
                        report = ai_student_report(
                            row, name_col, grade_cols, final_df['المعدل'].mean()
                        )
                    all_reports[name] = report
                st.session_state['all_reports'] = all_reports
                
                for name, report in all_reports.items():
                    with st.expander(f"📋 {name}"):
                        st.markdown(report)

        # ─────── تبويب 3: حالات استثنائية ───────
        with ai_tabs[2]:
            st.write("### 🔍 كشف الحالات الاستثنائية")
            if st.button("🔍 تحليل الحالات", key="anomalies"):
                with st.spinner("🤖 جاري فحص البيانات..."):
                    anomalies = ai_detect_anomalies(
                        final_df, name_col, grade_cols
                    )
                st.markdown(f"""
                <div class="ai-response">
                    {anomalies}
                </div>
                """, unsafe_allow_html=True)

        # ─────── تبويب 4: توصيات ───────
        with ai_tabs[3]:
            st.write("### 💡 التوصيات التربوية")
            if st.button("💡 إنشاء خطة عمل", key="recommendations"):
                with st.spinner("🤖 جاري إعداد التوصيات..."):
                    recs = ai_generate_recommendations(
                        final_df, name_col, grade_cols
                    )
                st.markdown(f"""
                <div class="ai-response">
                    {recs}
                </div>
                """, unsafe_allow_html=True)

        # ─────── تبويب 5: رسائل الأولياء ───────
        with ai_tabs[4]:
            st.write("### 📋 رسائل لأولياء الأمور")
            parent_student = st.selectbox(
                "اختر التلميذ:", student_names, key="parent_select"
            )
            if st.button("📋 إنشاء رسالة لولي الأمر", key="parent_report"):
                student_row = final_df[
                    final_df[name_col] == parent_student
                ].iloc[0]
                with st.spinner("🤖 جاري كتابة الرسالة..."):
                    letter = ai_parent_report(
                        student_row, name_col, grade_cols, final_df['المعدل'].mean()
                    )
                st.markdown(f"""
                <div class="student-card">
                    <h4>📨 رسالة لولي أمر: {parent_student}</h4>
                    <hr>
                    {letter}
                </div>
                """, unsafe_allow_html=True)
                
                # زر نسخ الرسالة
                st.text_area(
                    "📋 انسخ الرسالة من هنا:", letter, height=300
                )

        # ─────── تبويب 6: محادثة حرة ───────
        with ai_tabs[5]:
            st.write("### 💬 اسأل الذكاء الاصطناعي")
            st.caption("اطرح أي سؤال حول نتائج التلاميذ أو استشارة تربوية")
            
            # تحضير سياق البيانات
            context = f"""
            بيانات القسم المتاحة:
            - القسم: {selected_sheet}
            - عدد التلاميذ: {len(final_df)}
            - معدل القسم: {round(final_df['المعدل'].mean(), 2)}
            - نسبة النجاح: {round((final_df['المعدل'] >= 5).sum() / len(final_df) * 100, 1)}%
            - أعلى معدل: {final_df['المعدل'].max()}
            - أدنى معدل: {final_df['المعدل'].min()}
            - المواد: {grade_cols}
            """
            
            # سجل المحادثة
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = []
                
            # عرض المحادثات السابقة
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
                    
            # إدخال المستخدم
            user_input = st.chat_input("اكتب سؤالك هنا...")
            if user_input:
                st.session_state.chat_history.append({
                    "role": "user", "content": user_input
                })
                with st.chat_message("user"):
                    st.write(user_input)
                    
                full_prompt = f"""
                {context}
                بيانات التلاميذ (أول 10):
                {final_df.head(10).to_string()}
                سؤال المستخدم: {user_input}
                """
                
                with st.chat_message("assistant"):
                    with st.spinner("🤖 جاري التفكير..."):
                        response = call_mistral(full_prompt)
                    st.write(response)
                    st.session_state.chat_history.append({
                        "role": "assistant", "content": response
                    })
                    
                if st.button("🗑️ مسح المحادثة"):
                    st.session_state.chat_history = []
                    st.rerun()

    # ══════════════════════════════════════════════════════
    # التصدير
    # ══════════════════════════════════════════════════════
    st.markdown("---")
    st.write("### 📥 تصدير النتائج")
    
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, index=False, sheet_name=selected_sheet)
            workbook = writer.book
            worksheet = writer.sheets[selected_sheet]
            
            header_fmt = workbook.add_format({
                'bold': True, 'bg_color': '#4472C4', 'font_color': 'white', 
                'border': 1, 'align': 'center'
            })
            for i, col in enumerate(final_df.columns):
                worksheet.write(0, i, col, header_fmt)
                worksheet.set_column(i, i, max(len(str(col)) + 5, 12))
                
        st.download_button(
            "📥 تحميل النتائج (Excel)",
            data=output.getvalue(),
            file_name=f"نتائج_{selected_sheet}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    with col_exp2:
        # تصدير تقرير AI كاملاً
        if st.session_state.get('class_analysis'):
            report_text = f"""
            تقرير القسم: {selected_sheet}
            التاريخ: {datetime.now().strftime('%Y-%m-%d')}
            {'='*50}
            {st.session_state.get('class_analysis', '')}
            """
            st.download_button(
                "📥 تحميل تقرير AI (نصي)",
                data=report_text.encode('utf-8'),
                file_name=f"تقرير_AI_{selected_sheet}.txt",
                mime="text/plain",
                use_container_width=True
            )

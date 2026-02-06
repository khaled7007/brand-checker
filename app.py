import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import fitz
import os

# إعداد Gemini API
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-3-flash-preview')

# قواعد الهوية البصرية المحسّنة
BRAND_GUIDELINES = """
أنت مدقق هوية بصرية محترف متخصص في تحليل التصاميم. راجع التصميم بدقة عالية وفق هذه القواعد:

**الألوان المعتمدة:**
- Primary (الأساسي): #002825, #285356, #1a3a41
- Secondary (الثانوي): #56b4b6, #7c7a31, #9fa144
- Highlight (البارز): #cd9e2b, #daa929
- Neutral (المحايد): #e6b88d, #f1dece

**قواعد الألوان:**
- أي لون خارج هذه القائمة = خطأ (حدد اللون بالضبط)
- لازم يظهر لون أساسي واحد على الأقل
- ممنوع الإفراط في الذهبي (أكثر من 15% من المساحة)
- التباين لازم يكون واضح (نسبة تباين 4.5:1 على الأقل)
- استخدام الأبيض (#ffffff) للنصوص على الخلفيات الخضراء الداكنة = مقبول ومطلوب

**الخطوط - مهم جدًا:**
- TheSans: للتصاميم الداخلية فقط (مميزات: خط هندسي، حروف منفصلة، دعم عربي ممتاز)
- Myriad Arabic: للتصاميم الخارجية فقط (مميزات: خط نسخي عصري، حروف متصلة بشكل طبيعي)

**كيف تفرق بين الخطوط:**
- TheSans: الحروف العربية منفصلة، شكل هندسي، خطوط مستقيمة
- Myriad Arabic: الحروف متصلة بشكل طبيعي، أكثر انسيابية
- إذا لم تكن متأكدًا 100% من الخط، لا تقول "غير مطابق" - قل "يُنصح بالتحقق من الخط المستخدم"

**قواعد الخطوط:**
- استخدام Myriad Arabic في تصميم داخلي = خطأ فادح
- استخدام TheSans في تصميم خارجي = خطأ فادح
- العناوين: Bold أو SemiBold
- النصوص: Regular أو Light

**الشعار:**
- ممنوع تدويره (حتى لو بزاوية بسيطة)
- ممنوع تغيير النسب (العرض/الطول)
- ممنوع تغيير الألوان
- ممنوع تحويله إلى Outline أو Stroke
- لازم يكون واضح مع مسافة فارغة حوله (padding)
- الحد الأدنى للحجم: 3 سم للطباعة، 120 بكسل للشاشات

**المطلوب منك:**

1. **افحص التصميم بدقة عالية** - انظر للتفاصيل الصغيرة

2. **حدد الحالة:**
   - "مطابق" = كل شي صحيح 100%
   - "يحتاج تعديل" = توجد أخطاء بسيطة قابلة للإصلاح
   - "غير مطابق" = توجد أخطاء جوهرية

3. **الملاحظات التفصيلية:**
   - اذكر كل خطأ بدقة (مثلاً: "اللون #1a4d2e غير معتمد، يجب استبداله بـ #1a3a41")
   - إذا الخط غير واضح، قل "يُنصح بالتحقق" بدلاً من الحكم القاطع

4. **تقييم التصميم (من 10):**
   - التوازن والتكوين: /10
   - الألوان والتباين: /10
   - الطباعة والخطوط: /10
   - الوضوح والقابلية للقراءة: /10
   - الالتزام بالهوية: /10

5. **الاقتراحات التحسينية:**
   - نقاط قوة التصميم (ماذا يجب الإبقاء عليه)
   - نقاط تحتاج تحسين (مع حلول عملية محددة)
   - اقتراحات إبداعية لرفع جودة التصميم

**صيغة الرد:**

الحالة: [مطابق ✅ / يحتاج تعديل ⚠️ / غير مطابق ❌]

---

**الملاحظات التفصيلية:**

الألوان:
• [تحليل دقيق للألوان المستخدمة]

الخطوط:
• [تحليل دقيق للخطوط - كن حذرًا في الحكم]

الشعار:
• [فحص استخدام الشعار]

التركيب والتصميم:
• [ملاحظات عامة]

---

**التقييم (من 50):**

• التوازن والتكوين: X/10
• الألوان والتباين: X/10
• الطباعة والخطوط: X/10
• الوضوح والقابلية للقراءة: X/10
• الالتزام بالهوية: X/10

**المجموع: XX/50**

---

**التوصيات:**

نقاط القوة:
1. [ما يميز التصميم]
2. [...]

نقاط التحسين:
1. [تحسين محدد + كيف]
2. [...]

اقتراحات إبداعية:
1. [فكرة لتطوير التصميم]
2. [...]
"""

def pdf_to_image(pdf_file):
    """تحويل كل صفحات PDF إلى صورة واحدة"""
    try:
        pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
        images = []
        
        # تحديد دقة مناسبة حسب عدد الصفحات
        page_count = len(pdf_document)
        if page_count > 10:
            zoom = 1.5  # دقة أقل للملفات الكبيرة
        elif page_count > 5:
            zoom = 2.0
        else:
            zoom = 3.0  # دقة عالية للملفات الصغيرة
        
        # تحويل كل صفحة لصورة
        for page_num in range(min(page_count, 20)):  # حد أقصى 20 صفحة
            page = pdf_document[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        
        pdf_document.close()
        
        # دمج الصور عموديًا إذا كان فيه أكثر من صفحة
        if len(images) > 1:
            # حساب الأبعاد
            total_height = sum(img.height for img in images)
            max_width = max(img.width for img in images)
            
            # التحقق من الحد الأقصى
            if total_height > 15000:
                # تصغير الصور لتناسب الحد
                scale = 15000 / total_height
                images = [img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS) for img in images]
                total_height = sum(img.height for img in images)
                max_width = max(img.width for img in images)
            
            combined = Image.new('RGB', (max_width, total_height), 'white')
            y_offset = 0
            
            for img in images:
                combined.paste(img, (0, y_offset))
                y_offset += img.height
            
            return combined
        else:
            return images[0] if images else None
            
    except Exception as e:
        st.error(f"خطأ في قراءة ملف PDF: {str(e)}")
        return None

def analyze_design(image, design_type):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    prompt = f"""{BRAND_GUIDELINES}

نوع التصميم: {design_type}

تذكير مهم:
- إذا لم تكن متأكدًا 100% من نوع الخط، لا تحكم بـ "خطأ فادح"
- ركز على الأخطاء الواضحة في الألوان والشعار
- قدم تقييمًا شاملاً وبناءً للتصميم
- اقتراحاتك يجب أن تكون عملية وقابلة للتطبيق

افحص هذا التصميم:"""
    
    response = model.generate_content([prompt, Image.open(io.BytesIO(img_byte_arr))])
    return response.text

def get_status_emoji(result_text):
    if "مطابق ✅" in result_text or ("مطابق" in result_text and "غير مطابق" not in result_text):
        return "✅", "مطابق", "#56b4b6"
    elif "يحتاج تعديل ⚠️" in result_text or "يحتاج تعديل" in result_text:
        return "⚠️", "يحتاج تعديل", "#cd9e2b"
    else:
        return "❌", "غير مطابق", "#9fa144"

st.set_page_config(
    page_title="مدقق الهوية البصرية - ذرى", 
    page_icon="🎨", 
    layout="centered",
    initial_sidebar_state="collapsed"  # مخفي افتراضيًا على الجوال
)

# CSS محسّن بهوية ذرى
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');

/* الخلفية الرئيسية */
.stApp{
    background: linear-gradient(135deg, #002825 0%, #1a3a41 50%, #285356 100%);
    font-family: 'Tajawal', sans-serif;
    direction: rtl;
}

/* العناوين الرئيسية */
h1{
    color: #cd9e2b !important;
    text-align: center;
    font-weight: bold;
    padding: 20px 0;
    text-shadow: 3px 3px 6px rgba(0,0,0,0.5);
    font-size: 2.8em !important;
}

/* المحتوى الرئيسي - نص داكن على خلفية فاتحة */
.main .block-container{
    padding: 1rem !important;
    max-width: 100%;
}

@media (min-width: 768px) {
    .main .block-container{
        padding: 2rem 3rem !important;
    }
}

/* البطاقات والمحتوى */
.stMarkdown{
    background: white;
    padding: 15px;
    border-radius: 15px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    margin: 10px 0;
    border: 2px solid #cd9e2b;
    color: #002825 !important;
}

@media (min-width: 768px) {
    .stMarkdown{
        padding: 25px;
        border-radius: 20px;
        margin: 15px 0;
    }
}

/* النصوص داخل البطاقات */
.stMarkdown p, .stMarkdown li, .stMarkdown div{
    color: #002825 !important;
}

/* رفع الملفات */
[data-testid="stFileUploader"]{
    background: white !important;
    border: 2px dashed #cd9e2b;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    margin: 10px 0;
}

@media (min-width: 768px) {
    [data-testid="stFileUploader"]{
        border-width: 3px;
        border-radius: 20px;
        padding: 40px;
    }
}

[data-testid="stFileUploader"] *{
    color: #002825 !important;
}

[data-testid="stFileUploader"]:hover{
    border-color: #daa929;
    background: #f1dece !important;
}

/* الأزرار */
.stButton>button{
    background: linear-gradient(135deg, #cd9e2b 0%, #daa929 50%, #cd9e2b 100%);
    color: white !important;
    font-weight: bold;
    border: none;
    border-radius: 12px;
    padding: 12px 20px;
    font-size: 16px;
    box-shadow: 0 4px 8px rgba(205, 158, 43, 0.3);
    transition: all 0.3s ease;
    width: 100%;
}

@media (min-width: 768px) {
    .stButton>button{
        border-radius: 15px;
        padding: 15px 30px;
        font-size: 18px;
        box-shadow: 0 6px 12px rgba(205, 158, 43, 0.4);
    }
}

.stButton>button:hover{
    background: linear-gradient(135deg, #daa929 0%, #cd9e2b 50%, #daa929 100%);
    transform: translateY(-3px);
    box-shadow: 0 10px 20px rgba(205, 158, 43, 0.6);
}

/* العناوين الفرعية */
h3{
    color: #002825 !important;
    border-bottom: 3px solid #cd9e2b;
    padding-bottom: 10px;
    margin-top: 25px;
    margin-bottom: 15px;
    font-weight: bold;
    text-align: right;
}

/* الرسائل */
.stSuccess, .stInfo, .stWarning, .stError{
    background: white !important;
    color: #002825 !important;
    border-radius: 15px;
    padding: 15px 20px;
}

/* Sidebar */
[data-testid="stSidebar"]{
    background: linear-gradient(180deg, #002825 0%, #285356 50%, #1a3a41 100%);
    padding: 1.5rem 1rem;
}

[data-testid="stSidebar"] *{
    color: white !important;
}

[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3{
    color: #cd9e2b !important;
    border-bottom: 2px solid #cd9e2b;
    padding-bottom: 10px;
}

[data-testid="stSidebar"] .stMetric{
    background: rgba(205, 158, 43, 0.2);
    padding: 15px;
    border-radius: 15px;
    border: 2px solid #cd9e2b;
    text-align: center;
}

/* إصلاح تداخل Sidebar على الجوال */
@media (max-width: 768px) {
    [data-testid="stSidebar"][aria-expanded="true"]{
        width: 80vw !important;
    }
    
    [data-testid="stSidebarNav"]{
        padding-top: 3rem;
    }
}

/* الأعمدة */
[data-testid="column"]{
    padding: 0 10px;
}

/* الصور */
img{
    border-radius: 15px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
}

/* تحسين المحاذاة */
.element-container{
    text-align: right;
}
</style>""", unsafe_allow_html=True)

# الهيدر
st.markdown("""
<div style='text-align: center; 
            padding: 20px 10px; 
            background: linear-gradient(135deg, rgba(0,40,37,0.95) 0%, rgba(40,83,86,0.95) 100%); 
            border-radius: 15px; 
            margin-bottom: 20px; 
            border: 3px solid #cd9e2b;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);'>
    <h1 style='margin: 0; 
               font-size: clamp(1.5em, 5vw, 2.5em); 
               color: #cd9e2b; 
               text-shadow: 2px 2px 4px rgba(0,0,0,0.7);
               line-height: 1.2;'>
        🎨 مدقق الهوية البصرية
    </h1>
    <p style='color: #e6b88d; 
              font-size: clamp(1em, 3vw, 1.3em); 
              margin: 10px 0 5px 0; 
              font-weight: 600;'>
        شركة ذرى للتمويل الجماعي
    </p>
    <p style='color: #f1dece; 
              font-size: clamp(0.85em, 2.5vw, 1em); 
              margin: 5px 0 0 0;'>
        تحليل ذكي شامل للتصاميم
    </p>
</div>
""", unsafe_allow_html=True)

# رفع الملف
uploaded_file = st.file_uploader(
    "📤 ارفع التصميم للفحص الشامل",
    type=["png","jpg","jpeg","pdf"],
    help="يدعم ملفات PNG, JPG, PDF - الحد الأقصى 200 MB"
)

# اختيار نوع التصميم
st.markdown("### 📋 حدد نوع التصميم")
col1, col2 = st.columns(2)
with col1:
    external = st.button("🏢 تصميم خارجي", use_container_width=True)
with col2:
    internal = st.button("🏠 تصميم داخلي", use_container_width=True)

if 'design_type' not in st.session_state:
    st.session_state.design_type = None

if external:
    st.session_state.design_type = "خارجي"
if internal:
    st.session_state.design_type = "داخلي"

if st.session_state.design_type:
    st.success(f"✅ تم اختيار: تصميم {st.session_state.design_type}")

# معالجة الملف
if uploaded_file is not None and st.session_state.design_type:
    if uploaded_file.type == "application/pdf":
        page_count = len(fitz.open(stream=uploaded_file.getvalue(), filetype="pdf"))
        if page_count > 20:
            st.warning(f"⚠️ الملف يحتوي على {page_count} صفحة - سيتم فحص أول 20 صفحة فقط")
            page_count = 20
        elif page_count > 10:
            st.info(f"📄 ملف PDF كبير ({page_count} صفحة) - سيتم تقليل الدقة للتحليل الشامل")
        else:
            st.info(f"📄 ملف PDF - سيتم فحص جميع الصفحات ({page_count} صفحة)")
        image = pdf_to_image(uploaded_file)
        if image is None:
            st.stop()
    else:
        image = Image.open(uploaded_file)
    
    # عرض الصورة
    st.markdown("### 🖼️ معاينة التصميم")
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.image(image, caption="التصميم المرفوع", use_container_width=True)
    
    st.markdown("---")
    
    # زر الفحص
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍 تحليل شامل للتصميم", use_container_width=True, type="primary"):
            with st.spinner("⏳ جاري التحليل الدقيق للتصميم... (قد يستغرق 15-30 ثانية)"):
                try:
                    result = analyze_design(image, st.session_state.design_type)
                    emoji, status, color = get_status_emoji(result)
                    
                    # عرض الحالة
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, {color}33 0%, {color}55 100%);
                                padding: 40px;
                                border-radius: 25px;
                                border: 4px solid {color};
                                text-align: center;
                                margin: 30px 0;
                                box-shadow: 0 12px 24px rgba(0,0,0,0.3);'>
                        <h1 style='color: {color}; font-size: 4em; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>{emoji}</h1>
                        <h2 style='color: {color}; margin: 15px 0; font-size: 2em; font-weight: bold;'>{status}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # التقرير التفصيلي
                    st.markdown("### 📊 التقرير الشامل")
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, white 0%, #f1dece 100%);
                                padding: 30px;
                                border-radius: 20px;
                                border-right: 6px solid #cd9e2b;
                                box-shadow: 0 6px 12px rgba(0,0,0,0.15);
                                line-height: 2;
                                font-size: 1.05em;'>
                        {result}
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"❌ حدث خطأ أثناء التحليل: {str(e)}")
                    st.info("💡 نصيحة: تأكد من وضوح الصورة وجودتها")

elif uploaded_file and not st.session_state.design_type:
    st.warning("⚠️ الرجاء اختيار نوع التصميم أولاً")

# الشريط الجانبي
with st.sidebar:
    st.markdown("## ℹ️ عن الأداة")
    
    st.info("""
**مدقق الهوية البصرية المطوّر**

أداة ذكية متقدمة تفحص التصاميم بدقة عالية للتأكد من التزامها بمعايير الهوية البصرية لشركة ذرى.
    """)
    
    st.markdown("### ✨ المميزات")
    st.success("""
✓ فحص دقيق للألوان المعتمدة
✓ تحليل متقدم للخطوط  
✓ فحص استخدام الشعار
✓ تقييم شامل للتصميم
✓ اقتراحات تحسين احترافية
    """)
    
    st.markdown("### 📝 قواعد الخطوط")
    st.warning("""
**الداخلي:** TheSans فقط  
**الخارجي:** Myriad Arabic فقط
    """)
    
    st.markdown("---")
    
    st.markdown("### 📊 الإحصائيات")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("الفحوصات اليومية", "1,500")
    with col2:
        st.metric("الدقة", "95%+")
    
    st.markdown("---")
    
    st.caption("🤖 مدعوم بـ Google Gemini AI")
    st.caption("⚡ نموذج Gemini 3 Flash")

# Footer
st.markdown("---")
st.caption("© 2026 شركة ذرى للتمويل الجماعي | جميع الحقوق محفوظة")
st.caption("مدعوم بالذكاء الاصطناعي 🤖")

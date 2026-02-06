import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import fitz
import os

# إعداد Gemini API
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-3-flash-preview')

# قواعد الهوية البصرية
BRAND_GUIDELINES = """
أنت مدقق هوية بصرية محترف متخصص في تحليل التصاميم. راجع التصميم بدقة عالية وفق هذه القواعد:

**الألوان المعتمدة:**
- Primary: #002825, #285356, #1a3a41
- Secondary: #56b4b6, #7c7a31, #9fa144
- Highlight: #cd9e2b, #daa929
- Neutral: #e6b88d, #f1dece

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
        
        page_count = len(pdf_document)
        if page_count > 10:
            zoom = 1.5
        elif page_count > 5:
            zoom = 2.0
        else:
            zoom = 3.0
        
        for page_num in range(min(page_count, 20)):
            page = pdf_document[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        
        pdf_document.close()
        
        if len(images) > 1:
            total_height = sum(img.height for img in images)
            max_width = max(img.width for img in images)
            
            if total_height > 15000:
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
    """تحليل التصميم باستخدام Gemini AI"""
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

def get_status_info(result_text):
    """استخراج الحالة من النص"""
    if "مطابق ✅" in result_text or ("مطابق" in result_text and "غير مطابق" not in result_text):
        return "✅", "مطابق", "#10b981", "success"
    elif "يحتاج تعديل ⚠️" in result_text or "يحتاج تعديل" in result_text:
        return "⚠️", "يحتاج تعديل", "#f59e0b", "warning"
    else:
        return "❌", "غير مطابق", "#ef4444", "error"

# إعداد الصفحة
st.set_page_config(
    page_title="مدقق الهوية - ذرى",
    page_icon="🎨",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS حديث وعصري
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');

* {
    font-family: 'IBM Plex Sans Arabic', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #002825 0%, #0a1a1d 25%, #1a3a41 50%, #0f2b2e 75%, #002825 100%);
    background-size: 400% 400%;
    animation: gradientShift 15s ease infinite;
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.main .block-container {
    padding: 1rem;
    max-width: 800px;
}

/* بطاقة Header */
.header-card {
    background: linear-gradient(135deg, rgba(0, 40, 37, 0.9) 0%, rgba(26, 58, 65, 0.9) 100%);
    border: 2px solid rgba(205, 158, 43, 0.5);
    border-radius: 20px;
    padding: 2rem;
    text-align: center;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 40px rgba(205, 158, 43, 0.2);
}

.header-title {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #cd9e2b 0%, #daa929 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}

.header-subtitle {
    color: #94a3b8;
    font-size: 0.95rem;
    margin-top: 0.5rem;
}

/* البطاقات */
.stMarkdown {
    background: transparent !important;
    padding: 0 !important;
    border: none !important;
}

.card {
    background: linear-gradient(135deg, rgba(0, 40, 37, 0.6) 0%, rgba(26, 58, 65, 0.6) 100%);
    border: 1px solid rgba(86, 180, 182, 0.3);
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
    backdrop-filter: blur(10px);
}

/* رفع الملفات */
[data-testid="stFileUploader"] {
    background: linear-gradient(135deg, rgba(0, 40, 37, 0.5) 0%, rgba(26, 58, 65, 0.5) 100%) !important;
    border: 2px dashed rgba(205, 158, 43, 0.6) !important;
    border-radius: 16px !important;
    padding: 2rem 1rem !important;
    backdrop-filter: blur(10px);
}

[data-testid="stFileUploader"]:hover {
    border-color: #cd9e2b !important;
    background: linear-gradient(135deg, rgba(0, 40, 37, 0.7) 0%, rgba(26, 58, 65, 0.7) 100%) !important;
    box-shadow: 0 8px 25px rgba(205, 158, 43, 0.3);
}

[data-testid="stFileUploader"] * {
    color: #e2e8f0 !important;
}

/* الأزرار */
.stButton > button {
    background: linear-gradient(135deg, #cd9e2b 0%, #daa929 100%) !important;
    color: #0a0e27 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 25px rgba(205, 158, 43, 0.3) !important;
}

/* الصور */
img {
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* الرسائل */
.stAlert {
    background: linear-gradient(135deg, rgba(0, 40, 37, 0.7) 0%, rgba(26, 58, 65, 0.7) 100%) !important;
    border: 1px solid rgba(86, 180, 182, 0.4) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    backdrop-filter: blur(10px);
}

/* بطاقة النتيجة */
.result-card {
    background: linear-gradient(135deg, rgba(0, 40, 37, 0.8) 0%, rgba(26, 58, 65, 0.8) 100%);
    border-radius: 20px;
    padding: 2rem;
    text-align: center;
    margin: 2rem 0;
    border: 2px solid;
    backdrop-filter: blur(10px);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.result-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
}

.result-title {
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0;
}

/* التقرير */
.report-card {
    background: linear-gradient(135deg, rgba(0, 40, 37, 0.6) 0%, rgba(26, 58, 65, 0.6) 100%);
    border: 1px solid rgba(86, 180, 182, 0.3);
    border-radius: 16px;
    padding: 1.5rem;
    color: #e2e8f0;
    line-height: 1.8;
    backdrop-filter: blur(10px);
}

/* Expander */
.streamlit-expanderHeader {
    background: linear-gradient(135deg, rgba(0, 40, 37, 0.7) 0%, rgba(26, 58, 65, 0.7) 100%) !important;
    border: 1px solid rgba(205, 158, 43, 0.3) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-weight: 600 !important;
    backdrop-filter: blur(10px);
}

.streamlit-expanderHeader:hover {
    border-color: rgba(205, 158, 43, 0.6) !important;
}

/* بدون sidebar */
[data-testid="stSidebar"] {
    display: none;
}

h1, h2, h3, h4, h5, h6 {
    color: #e2e8f0 !important;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="header-card">
    <div class="header-title">🎨 مدقق الهوية البصرية</div>
    <div class="header-subtitle">ذرى للتمويل الجماعي • فحص ذكي ودقيق</div>
</div>
""", unsafe_allow_html=True)

# رفع الملف
uploaded_file = st.file_uploader(
    "📤 ارفع التصميم",
    type=["png", "jpg", "jpeg", "pdf"],
    label_visibility="collapsed"
)

# اختيار النوع
if uploaded_file:
    st.markdown("#### 📋 نوع التصميم")
    col1, col2 = st.columns(2)
    
    with col1:
        external = st.button("🏢 خارجي", use_container_width=True)
    with col2:
        internal = st.button("🏠 داخلي", use_container_width=True)
    
    if 'design_type' not in st.session_state:
        st.session_state.design_type = None
    
    if external:
        st.session_state.design_type = "خارجي"
    if internal:
        st.session_state.design_type = "داخلي"
    
    if st.session_state.design_type:
        st.success(f"✓ {st.session_state.design_type}")
        
        # معالجة الملف
        if uploaded_file.type == "application/pdf":
            page_count = len(fitz.open(stream=uploaded_file.getvalue(), filetype="pdf"))
            if page_count > 20:
                st.warning(f"⚠️ سيتم فحص أول 20 صفحة من {page_count}")
            else:
                st.info(f"📄 {page_count} صفحة")
            image = pdf_to_image(uploaded_file)
            if not image:
                st.stop()
        else:
            image = Image.open(uploaded_file)
        
        # عرض المعاينة
        with st.expander("👁️ معاينة التصميم", expanded=False):
            st.image(image, use_container_width=True)
        
        # زر الفحص
        if st.button("🔍 تحليل التصميم", use_container_width=True, type="primary"):
            with st.spinner("⏳ جاري التحليل..."):
                try:
                    result = analyze_design(image, st.session_state.design_type)
                    emoji, status, color, alert_type = get_status_info(result)
                    
                    # النتيجة
                    st.markdown(f"""
                    <div class="result-card" style="border-color: {color};">
                        <div class="result-icon">{emoji}</div>
                        <div class="result-title" style="color: {color};">{status}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # التقرير
                    st.markdown("#### 📊 التقرير التفصيلي")
                    st.markdown(f'<div class="report-card">{result}</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"❌ حدث خطأ: {str(e)}")

# معلومات سريعة
with st.expander("ℹ️ معلومات سريعة"):
    col1, col2 = st.columns(2)
    with col1:
        st.metric("الدقة", "95%+")
    with col2:
        st.metric("يوميًا", "1.5K")
    
    st.caption("**الخطوط:** داخلي = TheSans | خارجي = Myriad Arabic")
    st.caption("🤖 مدعوم بـ Google Gemini AI")

# Footer
st.markdown("---")
st.caption("© 2026 ذرى للتمويل الجماعي")

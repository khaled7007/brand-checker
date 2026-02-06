import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import fitz  # PyMuPDF for PDF support

# إعداد Gemini API
genai.configure(api_key="AIzaSyBvvE7vknPgZOSwOVsJZX6X_lWjGTiW9oM")
model = genai.GenerativeModel('gemini-3-flash-preview')

# قواعد الهوية البصرية
BRAND_GUIDELINES = """
أنت مدقق هوية بصرية محترف. راجع التصميم وفق هذه القواعد:

**الألوان المعتمدة:**
- Primary: #002825, #285356, #1a3a41
- Secondary: #56b4b6, #7c7a31, #9fa144
- Highlight: #cd9e2b, #daa929
- Neutral: #e6b88d, #f1dece

**القواعد:**
- أي لون خارج هذه القائمة = خطأ
- لازم يظهر لون أساسي واحد على الأقل
- ممنوع الإفراط في الذهبي (#cd9e2b, #daa929)
- التباين لازم يكون واضح
- استخدام الأبيض (#ffffff أو #fff) للنصوص على الخلفيات الخضراء (Primary colors) = مقبول ومطلوب للتباين

**الخطوط:**
- TheSans: كل التصاميم الداخلية فقط
- Myriad Arabic: التصاميم الخارجية فقط
- استخدام Myriad Arabic في تصميم داخلي = خطأ فادح
- استخدام TheSans في تصميم خارجي = خطأ فادح
- العناوين: Bold
- النصوص: Regular

**الشعار:**
- ممنوع تدويره
- ممنوع تغيير أبعاده (النسب)
- ممنوع تغيير لونه
- ممنوع تحويله إلى Outline
- لازم يكون واضح ومتباين مع الخلفية

**المطلوب منك:**
1. افحص التصميم بدقة
2. حدد الحالة: "مطابق" أو "يحتاج تعديل" أو "غير مطابق"
3. اذكر الملاحظات بنقاط واضحة
4. قدّم اقتراحات تصحيح عملية
5. استخدم لغة بسيطة غير تقنية

**صيغة الرد:**
الحالة: [مطابق / يحتاج تعديل / غير مطابق]

الملاحظات:
• [ملاحظة 1]
• [ملاحظة 2]

الاقتراحات:
1. [اقتراح 1]
2. [اقتراح 2]
"""

def pdf_to_image(pdf_file):
    """تحويل PDF إلى صورة (الصفحة الأولى)"""
    try:
        # فتح ملف PDF
        pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
        
        # الحصول على الصفحة الأولى
        first_page = pdf_document[0]
        
        # تحويل الصفحة إلى صورة (بدقة عالية)
        pix = first_page.get_pixmap(matrix=fitz.Matrix(2, 2))
        
        # تحويل إلى PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        pdf_document.close()
        return img
    except Exception as e:
        st.error(f"خطأ في قراءة ملف PDF: {str(e)}")
        return None

def analyze_design(image, design_type):
    """تحليل التصميم باستخدام Gemini AI"""
    
    # تحويل الصورة لـ bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    # إنشاء الـ prompt
    prompt = f"{BRAND_GUIDELINES}\n\nنوع التصميم: {design_type}\n\nافحص هذا التصميم:"
    
    # استدعاء Gemini
    response = model.generate_content([prompt, Image.open(io.BytesIO(img_byte_arr))])
    
    return response.text

def get_status_emoji(result_text):
    """استخراج الحالة من النص"""
    if "مطابق" in result_text and "غير مطابق" not in result_text:
        return "✅", "مطابق", "#28a745"
    elif "يحتاج تعديل" in result_text:
        return "⚠️", "يحتاج تعديل", "#ffc107"
    else:
        return "❌", "غير مطابق", "#dc3545"

# إعداد واجهة Streamlit
st.set_page_config(
    page_title="مدقق الهوية البصرية",
    page_icon="🎨",
    layout="centered"
)

# العنوان
st.title("🎨 مدقق الهوية البصرية")
st.markdown("---")

# رفع الملف
uploaded_file = st.file_uploader(
    "ارفع التصميم (PNG, JPG, PDF)",
    type=["png", "jpg", "jpeg", "pdf"],
    help="اسحب الملف هنا أو اضغط للاختيار"
)

# اختيار نوع التصميم
col1, col2 = st.columns(2)
with col1:
    design_type = st.radio(
        "نوع التصميم:",
        ["خارجي", "داخلي"],
        horizontal=True
    )

# عرض الصورة المرفوعة
if uploaded_file is not None:
    # معالجة الملف حسب نوعه
    if uploaded_file.type == "application/pdf":
        st.info("📄 ملف PDF - سيتم فحص الصفحة الأولى")
        image = pdf_to_image(uploaded_file)
        
        if image is None:
            st.stop()
    else:
        image = Image.open(uploaded_file)
    
    # عرض الصورة
    st.image(image, caption="التصميم المرفوع", use_container_width=True)
    
    st.markdown("---")
    
    # زر الفحص
    if st.button("🔍 فحص التصميم", type="primary", use_container_width=True):
        with st.spinner("جاري التحليل..."):
            try:
                # تحليل التصميم
                result = analyze_design(image, design_type)
                
                # استخراج الحالة
                emoji, status, color = get_status_emoji(result)
                
                # عرض النتيجة
                st.markdown("### النتيجة:")
                st.markdown(
                    f"<h2 style='text-align: center; color: {color};'>{emoji} {status}</h2>",
                    unsafe_allow_html=True
                )
                
                st.markdown("---")
                
                # عرض التقرير الكامل
                st.markdown("### التقرير التفصيلي:")
                st.markdown(result)
                
            except Exception as e:
                st.error(f"حدث خطأ أثناء التحليل: {str(e)}")
                st.info("تأكد من اتصالك بالإنترنت وصحة API Key")

# معلومات في الشريط الجانبي
with st.sidebar:
    st.markdown("### ℹ️ عن الأداة")
    st.info("""
    **مدقق الهوية البصرية**
    
    يفحص التصاميم للتأكد من التزامها بمعايير الهوية البصرية:
    
    ✓ الألوان المعتمدة
    ✓ الخطوط الصحيحة
    ✓ استخدام الشعار
    ✓ التباين والوضوح
    
    **الخطوط:**
    • الداخلي: TheSans
    • الخارجي: Myriad Arabic
    """)
    
    st.markdown("---")
    st.markdown("### 📊 الإحصائيات")
    st.metric("عدد الفحوصات اليوم", "مجاني حتى 1,500")
    
    st.markdown("---")
    st.caption("مدعوم بـ Google Gemini AI")

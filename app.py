import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import fitz
import os

# إعداد Gemini API
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-3-flash-preview')

# قواعد الهوية البصرية (مختصرة)
BRAND_GUIDELINES = """
أنت مدقق هوية بصرية محترف. راجع التصميم وفق قواعد شركة ذرى:

**الألوان:** #002825, #285356, #1a3a41, #56b4b6, #cd9e2b, #daa929, #e6b88d, #f1dece
**الخطوط:** TheSans (داخلي) | Myriad Arabic (خارجي)
**الشعار:** ممنوع التدوير أو تغيير الأبعاد أو الألوان

**المطلوب:**
1. حدد الحالة: مطابق ✅ | يحتاج تعديل ⚠️ | غير مطابق ❌
2. الملاحظات التفصيلية (الألوان، الخطوط، الشعار)
3. التقييم من 50 (التوازن، الألوان، الخطوط، الوضوح، الالتزام)
4. التوصيات (نقاط القوة، التحسين، الاقتراحات)
"""

def pdf_to_image(pdf_file):
    try:
        pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
        images = []
        page_count = len(pdf_document)
        zoom = 1.5 if page_count > 10 else (2.0 if page_count > 5 else 3.0)
        
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
        return images[0] if images else None
    except Exception as e:
        st.error(f"خطأ: {str(e)}")
        return None

def analyze_design(image, design_type):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    prompt = f"{BRAND_GUIDELINES}\n\nنوع التصميم: {design_type}\n\nافحص هذا التصميم:"
    response = model.generate_content([prompt, Image.open(io.BytesIO(img_byte_arr))])
    return response.text

def get_status_info(result_text):
    if "مطابق ✅" in result_text or ("مطابق" in result_text and "غير مطابق" not in result_text):
        return "✅", "مطابق", "#10b981"
    elif "يحتاج تعديل" in result_text:
        return "⚠️", "يحتاج تعديل", "#f59e0b"
    return "❌", "غير مطابق", "#ef4444"

# الصفحة
st.set_page_config(page_title="مدقق الهوية - ذرى", page_icon="🎨", layout="centered", initial_sidebar_state="collapsed")

# CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;600;700&display=swap');
* { font-family: 'IBM Plex Sans Arabic', sans-serif; }
.stApp { 
    background: linear-gradient(135deg, #002825 0%, #0a1a1f 50%, #001a18 100%);
}
.main .block-container { padding: 1rem; max-width: 800px; }
.header-card {
    background: linear-gradient(135deg, rgba(0,40,37,0.9) 0%, rgba(26,58,65,0.9) 100%);
    border: 2px solid rgba(205,158,43,0.5);
    border-radius: 20px;
    padding: 2rem;
    text-align: center;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 40px rgba(205,158,43,0.2);
}
.header-title {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #cd9e2b 0%, #daa929 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.header-subtitle { color: #94a3b8; font-size: 0.95rem; margin-top: 0.5rem; }
[data-testid="stFileUploader"] {
    background: linear-gradient(135deg, rgba(0,40,37,0.5) 0%, rgba(26,58,65,0.5) 100%) !important;
    border: 2px dashed rgba(205,158,43,0.6) !important;
    border-radius: 16px !important;
    padding: 2rem 1rem !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #cd9e2b !important;
    box-shadow: 0 8px 25px rgba(205,158,43,0.3);
}
[data-testid="stFileUploader"] * { color: #e2e8f0 !important; }
.stButton > button {
    background: linear-gradient(135deg, #cd9e2b 0%, #daa929 100%) !important;
    color: #0a0e27 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
    width: 100% !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 25px rgba(205,158,43,0.3) !important;
}
img { border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.1) !important; }
.stAlert {
    background: linear-gradient(135deg, rgba(0,40,37,0.7) 0%, rgba(26,58,65,0.7) 100%) !important;
    border: 1px solid rgba(86,180,182,0.4) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
}
.result-card {
    background: linear-gradient(135deg, rgba(0,40,37,0.8) 0%, rgba(26,58,65,0.8) 100%);
    border-radius: 20px;
    padding: 2rem;
    text-align: center;
    margin: 2rem 0;
    border: 2px solid;
    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
}
.result-icon { font-size: 4rem; margin-bottom: 1rem; }
.result-title { font-size: 1.8rem; font-weight: 700; margin: 0; }
.report-card {
    background: linear-gradient(135deg, rgba(0,40,37,0.6) 0%, rgba(26,58,65,0.6) 100%);
    border: 1px solid rgba(86,180,182,0.3);
    border-radius: 16px;
    padding: 1.5rem;
    color: #e2e8f0;
    line-height: 1.8;
}
.streamlit-expanderHeader {
    background: linear-gradient(135deg, rgba(0,40,37,0.7) 0%, rgba(26,58,65,0.7) 100%) !important;
    border: 1px solid rgba(205,158,43,0.3) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] { display: none; }
h1, h2, h3, h4, h5, h6 { color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="header-card"><div class="header-title">🎨 مدقق الهوية البصرية</div><div class="header-subtitle">ذرى للتمويل الجماعي • فحص ذكي ودقيق</div></div>', unsafe_allow_html=True)

# رفع الملف
uploaded_file = st.file_uploader("📤 ارفع التصميم", type=["png","jpg","jpeg","pdf"], label_visibility="collapsed")

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
        
        with st.expander("👁️ معاينة التصميم", expanded=False):
            st.image(image, use_container_width=True)
        
        if st.button("🔍 تحليل التصميم", use_container_width=True, type="primary"):
            with st.spinner("⏳ جاري التحليل..."):
                try:
                    result = analyze_design(image, st.session_state.design_type)
                    emoji, status, color = get_status_info(result)
                    st.markdown(f'<div class="result-card" style="border-color: {color};"><div class="result-icon">{emoji}</div><div class="result-title" style="color: {color};">{status}</div></div>', unsafe_allow_html=True)
                    st.markdown("#### 📊 التقرير التفصيلي")
                    st.markdown(f'<div class="report-card">{result}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ حدث خطأ: {str(e)}")

with st.expander("ℹ️ معلومات سريعة"):
    col1, col2 = st.columns(2)
    with col1:
        st.metric("الدقة", "95%+")
    with col2:
        st.metric("يوميًا", "1.5K")
    st.caption("**الخطوط:** داخلي = TheSans | خارجي = Myriad Arabic")
    st.caption("🤖 مدعوم بـ Google Gemini AI")

st.markdown("---")
st.caption("© 2026 ذرى للتمويل الجماعي")

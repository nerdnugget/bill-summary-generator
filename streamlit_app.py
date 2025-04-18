import streamlit as st
import anthropic
import os
import PyPDF2
import io
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import hmac
from dotenv import load_dotenv

# Must be the first Streamlit command
st.set_page_config(page_title="Bill Summary Generator", page_icon="📜", layout="wide")

# Load environment variables - make it work with both .env and Streamlit secrets
if os.path.exists(".env"):
    load_dotenv()

# Configure Anthropic
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass

app_password = os.getenv("APP_PASSWORD", "demo123")
if not app_password:
    try:
        app_password = st.secrets["APP_PASSWORD"]
    except (KeyError, FileNotFoundError):
        pass

if not api_key:
    st.error("""No Anthropic API key found! Please set up one of the following:
    1. Add ANTHROPIC_API_KEY to your .env file
    2. Add it to Streamlit secrets
    3. Set it as an environment variable""")
    st.stop()

try:
    client = anthropic.Client(api_key=api_key)
    st.sidebar.success("API key loaded successfully")
except Exception as e:
    st.error(f"Error initializing Anthropic client: {str(e)}")
    st.stop()

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], app_password):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error extracting PDF text: {str(e)}"

def extract_texts_from_pdfs(pdf_files):
    """Extract text from multiple PDF files"""
    texts = []
    for pdf_file in pdf_files:
        text = extract_text_from_pdf(pdf_file)
        if not text.startswith("Error"):
            texts.append({"name": pdf_file.name, "text": text})
    return texts

def fetch_ncga_bill(bill_number):
    try:
        # This is a placeholder URL - you'll need to adjust based on actual NCGA website structure
        base_url = "https://www.ncleg.gov/BillLookUp"
        response = requests.get(f"{base_url}/{bill_number}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # This would need to be adjusted based on actual NCGA website structure
            bill_text = soup.find('div', {'class': 'bill-text'})
            return bill_text.get_text() if bill_text else "Bill text not found"
        else:
            return "Failed to fetch bill"
    except Exception as e:
        return f"Error fetching bill: {str(e)}"

def format_summary(text):
    """Format the AI response into clean sections"""
    sections = text.split('\n')
    formatted = []
    in_key_points = False
    
    for line in sections:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('Bill Name') or line.startswith('Title'):
            formatted.append(f"**{line}**")
            in_key_points = False
        elif line.startswith('Purpose'):
            formatted.append(f"\n**{line}**")
            in_key_points = False
        elif line.startswith('Key Points'):
            formatted.append(f"\n**Key Points:**")
            in_key_points = True
        elif in_key_points:
            # Clean up and standardize bullet points
            if line.startswith('- ') or line.startswith('• ') or line.startswith('* '):
                # Remove any existing bullet point and add a clean one
                line = line.lstrip('- ').lstrip('•').lstrip('*').strip()
                formatted.append(f"• {line}")
            elif not any(line.startswith(prefix) for prefix in ['Bill Name', 'Title', 'Purpose', 'Key Points']):
                # If it's a continuation of a bullet point or a new point without a bullet
                formatted.append(f"• {line}")
        else:
            formatted.append(line)
    
    return '\n'.join(formatted)

def format_talking_points(text):
    """Format talking points into a clean list"""
    points = text.split('\n')
    formatted = []
    
    for point in points:
        point = point.strip()
        if not point:
            continue
        if not point.startswith('- ') and not point.startswith('• ') and not point.startswith('* '):
            point = f"• {point}"
        formatted.append(point)
    
    return '\n'.join(formatted)

def generate_bill_summary(bill_text):
    """Generate a summary of the bill using Claude."""
    try:
        response = client.complete(
            prompt=f"""You are an expert legislative analyst working for a Democratic NC State Senator. Your role is to:
1. Break down complex legislation into clear, actionable insights
2. Highlight implications for North Carolina constituents and communities
3. Consider impacts on working families and local economies
4. Identify opportunities for effective policy solutions
5. Use clear, accessible language while preserving technical accuracy
6. Note potential areas for bipartisan cooperation when relevant

Please analyze this bill and provide:

Bill Name/Title: [1 line]
Purpose: [1-2 sentences focusing on NC impact and community benefits]
Key Points:
• [3-4 bullet points emphasizing constituent impact, practical implications, and community effects]

Text: {bill_text}""",
            model="claude-2",
            max_tokens_to_sample=1500,
            temperature=0.5
        )
        return format_summary(response.completion)
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")
        return None

def generate_social_content(summary, platform):
    """Generate platform-specific content based on the bill summary."""
    try:
        platform_guidance = {
            "twitter": "Create concise, impactful points optimized for Twitter that resonate with NC constituents. Focus on community benefits and practical improvements.",
            "facebook": "Write slightly longer points for Facebook that highlight local impact and community stories. Include examples relevant to NC communities.",
            "newsletter": "Develop newsletter content that connects policy to community benefits. Focus on how legislation affects NC families and businesses.",
            "general": "Create talking points that emphasize positive community impact while maintaining broad appeal. Focus on practical benefits for NC constituents."
        }

        response = client.complete(
            prompt=f"""You are a skilled policy communications expert for a Democratic NC State Senator. Your role is to:
1. Translate legislation into compelling content that connects with constituents
2. Highlight impacts on NC communities and families
3. Frame issues in ways that emphasize practical solutions
4. Maintain professionalism while focusing on community benefits
5. Adapt tone and depth based on platform while staying informative

{platform_guidance.get(platform.lower(), platform_guidance["general"])}

Based on this summary, provide 3-4 key talking points that:
• Highlight benefits for NC communities
• Focus on practical solutions
• Use platform-appropriate language
• Emphasize positive local impact

Summary: {summary}""",
            model="claude-2",
            max_tokens_to_sample=1000,
            temperature=0.7
        )
        return format_talking_points(response.completion)
    except Exception as e:
        st.error(f"Error generating social content: {str(e)}")
        return None

def generate_key_takeaway(summary):
    """Generate a one-sentence key takeaway from the summary"""
    try:
        response = client.complete(
            prompt=f"""You are an expert at distilling complex information into clear, impactful takeaways.

Based on this summary, provide ONE clear, impactful sentence that captures the most important takeaway for NC constituents.

Summary: {summary}""",
            model="claude-2",
            max_tokens_to_sample=1000,
            temperature=0.5
        )
        return response.completion
    except Exception as e:
        st.error(f"Error generating key takeaway: {str(e)}")
        return None

def process_single_bill(bill):
    """Process a single bill for batch processing"""
    try:
        response = client.complete(
            prompt=f"""You are an expert legislative analyst working for a Democratic NC State Senator. Your role is to:
1. Break down complex legislation into clear, actionable insights
2. Highlight implications for North Carolina constituents and communities
3. Consider impacts on working families and local economies
4. Identify opportunities for effective policy solutions
5. Use clear, accessible language while preserving technical accuracy
6. Note potential areas for bipartisan cooperation when relevant

Please analyze this bill and provide:

Bill Name/Title: [1 line]
Purpose: [1-2 sentences focusing on NC impact and community benefits]
Key Points:
• [3-4 bullet points emphasizing constituent impact, practical implications, and community effects]

Text: {bill['text']}""",
            model="claude-2",
            max_tokens_to_sample=1000,
            temperature=0.5
        )
        return {
            "name": bill["name"],
            "summary": format_summary(response.completion)
        }
    except Exception as e:
        return {
            "name": bill["name"],
            "summary": f"Error processing bill: {str(e)}"
        }

def process_bill_batch(bills):
    """Process multiple bills concurrently using ThreadPoolExecutor"""
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(process_single_bill, bills))
    return results

# Streamlit UI
if not check_password():
    st.stop()  # Do not continue if check_password is not True.

st.title("📜 Bill Summary Generator")
st.markdown("Generate bill summaries and key talking points using AI.")

# Input methods
input_method = st.radio("Choose input method:", ["Text Input", "PDF Upload (Single)", "PDF Upload (Batch)", "NCGA Bill Number"])

bill_text = None
bills = None

if input_method == "Text Input":
    bill_text = st.text_area("Enter bill text:", height=200)
elif input_method == "PDF Upload (Single)":
    uploaded_file = st.file_uploader("Upload a PDF file:", type=['pdf'])
    if uploaded_file:
        bill_text = extract_text_from_pdf(uploaded_file)
elif input_method == "PDF Upload (Batch)":
    uploaded_files = st.file_uploader("Upload PDF files:", type=['pdf'], accept_multiple_files=True)
    if uploaded_files:
        bills = extract_texts_from_pdfs(uploaded_files)
        if bills:
            st.success(f"Successfully loaded {len(bills)} bills")
else:  # NCGA Bill Number
    bill_number = st.text_input("Enter NCGA bill number:")
    if bill_number:
        bill_text = fetch_ncga_bill(bill_number)

if input_method != "PDF Upload (Batch)" and bill_text and st.button("Generate Summary"):
    with st.spinner("Analyzing bill..."):
        summary = generate_bill_summary(bill_text)
        st.markdown("### Bill Summary")
        st.markdown(summary)
        
        st.markdown("\n### Quick Reference Points")
        platform = st.selectbox("Generate talking points for:", ["General", "Twitter", "Facebook", "Newsletter"])
        if platform:
            with st.spinner("Generating talking points..."):
                social_content = generate_social_content(summary, platform.lower())
                st.markdown(social_content)
        
        with st.spinner("Generating key takeaway..."):
            takeaway = generate_key_takeaway(summary)
            st.markdown("\n### Key Takeaway")
            st.info(takeaway)

elif input_method == "PDF Upload (Batch)" and bills and st.button("Process All Bills"):
    with st.spinner(f"Processing {len(bills)} bills..."):
        results = process_bill_batch(bills)
        
        # Display results
        for result in results:
            st.markdown(f"### {result['name']}")
            st.markdown(result['summary'])
            
            with st.spinner("Generating key takeaway..."):
                takeaway = generate_key_takeaway(result['summary'])
                st.info(takeaway)
            
            st.markdown("---")

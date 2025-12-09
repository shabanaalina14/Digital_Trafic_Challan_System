import streamlit as st
import google.generativeai as genai
import base64
import io
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image

# Google Gemini API Configuration
genai.configure(api_key="AIzaSyA8KpggPAGA9VRHIMebBEvsZOD5pgMDguk")  # Replace with your valid API key
model = genai.GenerativeModel("gemini-1.5-flash")

# List of traffic violations and their fines
violations = {
    "Speeding": 1000,
    "Red Light Jumping": 1500,
    "No Helmet": 500,
    "Drunk Driving": 2000,
    "Wrong Parking": 800
}

# Function to extract vehicle number from image using Gemini API
def extract_vehicle_number_gemini(image_path):
    with open(image_path, "rb") as img_file:
        image_base64 = base64.b64encode(img_file.read()).decode("utf-8")

    response = model.generate_content([
        {"mime_type": "image/jpeg", "data": image_base64},
        "Extract only the vehicle number from the given image."
    ])

    try:
        extracted_text = response.text.strip()
        # Use regex to extract vehicle number
        match = re.search(r'\b[A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,2}\s?\d{1,4}\b', extracted_text)
        if match:
            return match.group(0)
        else:
            return "Not Recognized"
    except:
        return "Not Recognized"

# Function to generate the challan PDF
def generate_challan(vehicle_number, vehicle_type, selected_violations, total_fine):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 750, " Traffic Challan Invoice")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, f"Vehicle Number: {vehicle_number}")
    c.drawString(100, 675, f"Vehicle Type: {vehicle_type}")

    y = 650
    c.setFont("Helvetica", 11)
    for v in selected_violations:
        c.drawString(100, y, f"Violation: {v} - Rs {violations[v]}")
        y -= 25

    c.setFont("Helvetica-Bold", 13)
    c.drawString(100, y, f"Total Fine: Rs {total_fine}")

    c.save()
    buffer.seek(0)  # Move the pointer back to the beginning
    return buffer

# Streamlit UI
st.title("\U0001F6A6 Traffic Challan Generator")
st.subheader("Enter Vehicle Details")

# Sidebar with app details
st.sidebar.title("ℹ️ App Information")
st.sidebar.write("This app allows users to generate traffic challans by extracting vehicle numbers from images or entering them manually.")
st.sidebar.write("Features:")
st.sidebar.markdown("- Automatic vehicle number extraction using AI")
st.sidebar.markdown("- Manual vehicle number input option")
st.sidebar.markdown("- Fine calculation based on selected violations")
st.sidebar.markdown("- PDF challan generation and download")
st.sidebar.write("\u00A9 Developed by Darshanikanta 2025")

# Option to upload an image or enter text manually
option = st.radio("Choose Input Method:", ["Enter Manually", "Upload Image"])

vehicle_number = ""

if option == "Enter Manually":
    vehicle_number = st.text_input("Enter Vehicle Number (e.g., MH12AB1234)")
else:
    uploaded_file = st.file_uploader("Upload Vehicle Image", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)

        # Convert RGBA to RGB (Fixes OSError issue)
        if image.mode == "RGBA":
            image = image.convert("RGB")

        # Save image as JPEG
        temp_image_path = "temp.jpg"
        image.save(temp_image_path, "JPEG")

        # Extract vehicle number
        vehicle_number = extract_vehicle_number_gemini(temp_image_path)
        st.success(f"Extracted Vehicle Number: {vehicle_number}")

# Select vehicle type
vehicle_type = st.selectbox("Select Vehicle Type", ["Select one","Car", "Bike", "Truck", "Bus"])

# Select violations
selected_violations = st.multiselect("Select Violations", list(violations.keys()))
total_fine = sum(violations[v] for v in selected_violations)

# Show total fine
st.markdown(f"<h3 style='color: red; text-align: center;'>\U0001F4B0 Total Fine: ₹{total_fine}</h3>", unsafe_allow_html=True)

# Generate Challan Button
if st.button("\U0001F694 Generate Challan"):
    if not vehicle_number or vehicle_number == "Not Recognized":
        st.error("Please enter a valid vehicle number.")
    elif not selected_violations:
        st.error("Please select at least one violation.")
    else:
        st.success("✅ Challan Generated Successfully!")

        # Generate PDF in memory
        challan_pdf = generate_challan(vehicle_number, vehicle_type, selected_violations, total_fine)

        # Display a preview of the challan
        st.markdown("### \U0001F4DC Challan Preview")
        st.markdown(f"**\U0001F697 Vehicle Number:** {vehicle_number}")
        st.markdown(f"**\U0001F698 Vehicle Type:** {vehicle_type}")
        st.markdown(f"**\U0001F6A6 Violations:**")
        for v in selected_violations:
            st.markdown(f"- {v} - ₹{violations[v]}")
        st.markdown(f"**\U0001F4B0 Total Fine:** ₹{total_fine}")

        # Download button for the generated challan
        st.download_button(
            label="\U0001F4E5 Download Challan",
            data=challan_pdf,
            file_name=f"challan_{vehicle_number}.pdf",
            mime="application/pdf"
        )

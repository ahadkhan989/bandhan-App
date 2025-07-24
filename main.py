import asyncio
import streamlit as st
import requests
import os
from agents import RunConfig, OpenAIChatCompletionsModel, AsyncOpenAI
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())
gemini_api_key = os.getenv("GEMINI_API_KEY")

# UltraMesg credentials
ULTRAMSG_API_TOKEN = os.getenv("ULTRAMSG_API_TOKEN")
ULTRAMSG_INSTANCE_ID = os.getenv("ULTRAMSG_INSTANCE_ID")


# Provider setup for agents library
provider = AsyncOpenAI(
    api_key=gemini_api_key, 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Model setup for agents library
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=provider
)

# RunConfig for agents
run_config = RunConfig(
    model=model,
    model_provider=provider,
    tracing_disabled=True
)

# Function tool for sending WhatsApp message
def send_whatsapp_mesg(to_number: str, message_text: str) -> dict:
    url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {
        'token': ULTRAMSG_API_TOKEN,
        'to': to_number,
        'body': message_text
    }

    try:
        response = requests.request("POST", url, data=payload, headers=headers)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"WhatsApp API call mein ghalti hui: {e}")
        return {"error": str(e)}



# Streamlit UI
st.set_page_config(page_title="Rishta Connect", page_icon="💍")
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F5F5F5;  
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Bandhan App 💍")
st.markdown("Find your perfect partner with an AI-generated profile tailored to you, delivered to your WhatsApp.")

# User input fields
st.header("Enter all info to meet your match.")

user_name = st.text_input("Your Name:", placeholder="e.g: Ahad Khanzada")
user_age = st.text_input("Your Age:", placeholder="e.g: 22")
user_gender= st.text_input("Gender:", placeholder="Male / Female")
whatsapp_number = st.text_input("WhatsApp Number:", placeholder="e.g: +923001234567")
rishta_details = st.text_area(
    "Description:",
    placeholder="Share details of your dream partner (e.g., age, city, qualities, profession).)"
)

# Statefull chat k liye

if "generated_profiles" not in st.session_state:
    st.session_state.generated_profiles = []


# Submit button
if st.button("Match Now"):
    if not user_name or not user_age or not user_gender or not whatsapp_number or not rishta_details:
        st.warning("All fields must be filled for matchmaking.")
    elif not whatsapp_number.startswith('+') or not whatsapp_number[1:].isdigit():
        st.warning("Invalid WhatsApp number. Include country code (e.g., +923001234567)")
    else:
        st.info("Building your match profile... Please wait")

        match_description = ""
        try:

            avoid_list_str = ""
            if st.session_state.generated_profiles:
                avoid_list_str = "\n\nPreviously generated profiles (DO NOT REPEAT ANY OF THESE):\n"
                for i, profile in enumerate(st.session_state.generated_profiles):
                    avoid_list_str += f"Profile {i+1}:\n{profile}\n---\n"
                avoid_list_str += "\nEnsure the new profile is COMPLETELY different from these."


            agent_instructions = f"""
            Aap ek professional matchmaker hain. Aapko ek user ({user_name}) ne apni zindagi ke saathi ke liye darj zail maloomaat aur pasand batai hai:

            User ka Naam: {user_name}
            User ki Umar: {user_age}
            User ka Gender: {user_gender}
            Rishte ki Maloomaat (Partner ki Pasand): {rishta_details}

            User ki di hui pasand ke mutabiq ek suitable partner ki *sirf* details generate karni hain.
            **Har baar, chahe user ki details same hon ya mukhtalif, aapko hamesha ek NAYA, UNIQUE naam aur mukhtalif details generate karni hain.**
            **Pehle generate kiye gaye kisi bhi naam, umar, education, profession, location, languages, ya hobbies ko DUHRAYEIN (repeat) mat.**
            Aapka jawab *sirf* ek partner ki details par mushtamil hona chahiye, bilkul neeche diye gaye format ki tarah.
            Details k baad neeche 2 lines ki uss ki description/qualities bhi likhna jo user define kre uss k according, zyada pure urdu k words use nhi krna bus baat ko simple rkhna aur jisa user discription me partner chahta hai usse wesa hi partner aur uss ki details share krna.

            Agar user ka gender 'Male' ya 'male' hai, toh aapko 'Female' partner ki details generate karni hain.
            Agar user ka gender 'Female' ya 'female' hai, toh aapko 'Male' partner ki details generate karni hain.

            Format:
            Name: [Partner's Name]
            Age: [Partner's Age]
            Education: [Partner's Education]
            Profession: [Partner's Profession]
            Location: [Partner's City]
            Languages: [Languages spoken]
            Hobbies: [Hobbies list]
            Martial status: Single
            [2 lines of description/qualities based on user's preference]
            """
            
            messages = [
                {"role": "user", "content": agent_instructions}
            ]

            agent_response_object =asyncio.run (provider.chat.completions.create(
                model=model.model, 
                messages=messages
            ))
            
            if agent_response_object and agent_response_object.choices and agent_response_object.choices[0].message.content:
                match_description = agent_response_object.choices[0].message.content.strip()
               
                st.session_state.generated_profiles.append(match_description)
            else:
                match_description = "Sorry for inconvenience. AI could not generate match details."

            # WhatsApp message body
            whatsapp_message_body = (
                f"Assalam-o-Alaikum {user_name},\n\n"
                f"Your request is processed! Match found for you.\n"
                f"Here are the details for you:\n\n"
                f"{match_description}\n\n"
                f"Hope the details meet your expectations! 😊\n"
                f"If interested, reply to arrange next steps.\n\n"
                f"Powered by Ahad Khanzada ⚔"
            )

            # Send WhatsApp message
            whatsapp_response = send_whatsapp_mesg(whatsapp_number, whatsapp_message_body)

            if whatsapp_response and "error" not in whatsapp_response:
                st.success(f"Match details delivered to {whatsapp_number} on WhatsApp.")
            else:
                st.error(f"WhatsApp message bhejte waqt ghalti hui hai. Mazeed tafseelat ke liye console check karein. Error: {whatsapp_response.get('error', 'Unknown API Error')}")

        except Exception as e:
            st.error(f"AI ya API se baat karte waqt ghalti hui hai: {e}")

st.markdown("---")
st.markdown("Powered by Ahad Khanzada ⚔")
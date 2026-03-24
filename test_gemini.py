
import os
from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai

genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model_name = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
print('Using model:', model_name)
try:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content('Say hello')
    print('Response:', response.text)
except Exception as e:
    import traceback
    traceback.print_exc()


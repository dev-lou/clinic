
from dotenv import load_dotenv
load_dotenv()
import os
import google.generativeai as genai

api_key = os.environ.get('GEMINI_API_KEY')
print('API KEY:', repr(api_key))
genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content('Say hello')
    print('Raw response:', response.text)
except Exception as e:
    import traceback
    traceback.print_exc()


import os
import tempfile
import speech_recognition as sr
import google.generativeai as genai
from gtts import gTTS
from playsound import playsound
from langdetect import detect
import json
from datetime import datetime
from dotenv import load_dotenv

# Configure Google Gemini API
load_dotenv() # This loads the variables from your .env file
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

r = sr.Recognizer()

# Conversation memory to store chat history
conversation_history = []

def detect_language(text):
    """Detect the language of the input text"""
    try:
        return detect(text)
    except:
        return 'en'  # Default to English

def get_health_prompt(query, language):
    """Get health-focused prompts in Indian languages"""
    language_prompts = {
        'en': f"You are a professional health expert. Provide concise, clear medical advice. Keep responses under 80 words. Be direct and helpful. User query: {query}",
        'hi': f"आप एक पेशेवर स्वास्थ्य विशेषज्ञ हैं। संक्षिप्त, स्पष्ट चिकित्सा सलाह दें। प्रतिक्रिया 80 शब्दों से कम रखें। सीधे और सहायक बनें। उपयोगकर्ता प्रश्न: {query}",
        'bn': f"আপনি একজন পেশাদার স্বাস্থ্য বিশেষজ্ঞ। সংক্ষিপ্ত, স্পষ্ট চিকিৎসা পরামর্শ দিন। ৮০ শব্দের কম উত্তর রাখুন। সরাসরি এবং সহায়ক হন। ব্যবহারকারীর প্রশ্ন: {query}",
        'te': f"మీరు ఒక వృత్తిపరమైన ఆరోగ్య నిపుణుడు. సంక్షిప్తమైన, స్పష్టమైన వైద్య సలహాలను అందించండి. 80 పదాల కంటే తక్కువ సమాధానాలను ఉంచండి. నేరుగా మరియు సహాయకంగా ఉండండి. వినియోగదారు ప్రశ్న: {query}",
        'mr': f"तुम्ही एक व्यावसायिक आरोग्य तज्ञ आहात. संक्षिप्त, स्पष्ट वैद्यकीय सल्ले द्या. 80 शब्दांपेक्षा कमी उत्तरे ठेवा. थेट आणि उपयुक्त व्हा. वापरकर्ता प्रश्न: {query}",
        'ta': f"நீங்கள் ஒரு தொழில்முறை சுகாதார நிபுணர். சுருக்கமான, தெளிவான மருத்துவ ஆலோசனைகளை வழங்குங்கள். 80 வார்த்தைகளுக்கு குறைவான பதில்களை வைத்திருங்கள். நேரடியாகவும் உதவியாகவும் இருங்கள். பயனர் கேள்வி: {query}",
        'gu': f"તમે એક વ્યાવસાયિક આરોગ્ય નિષ્ણાત છો. સંક્ષિપ્ત, સ્પષ્ટ તબીબી સલાહ આપો. 80 શબ્દો કરતાં ઓછા જવાબો રાખો. સીધા અને મદદરૂપ બનો. વપરાશકર્તા પ્રશ્ન: {query}",
        'kn': f"ನೀವು ಒಬ್ಬ ವೃತ್ತಿಪರ ಆರೋಗ್ಯ ತಜ್ಞ. ಸಂಕ್ಷಿಪ್ತ, ಸ್ಪಷ್ಟ ವೈದ್ಯಕೀಯ ಸಲಹೆಗಳನ್ನು ನೀಡಿ. 80 ಪದಗಳಿಗಿಂತ ಕಡಿಮೆ ಉತ್ತರಗಳನ್ನು ಇರಿಸಿ. ನೇರ ಮತ್ತು ಸಹಾಯಕವಾಗಿರಿ. ಬಳಕೆದಾರರ ಪ್ರಶ್ನೆ: {query}",
        'ml': f"നിങ്ങൾ ഒരു പ്രൊഫഷണൽ ആരോഗ്യ വിദഗ്ധനാണ്. ചുരുങ്ങിയ, വ്യക്തമായ മെഡിക്കൽ ഉപദേശങ്ങൾ നൽകുക. 80 വാക്കുകൾക്ക് താഴെ ഉത്തരങ്ങൾ നിലനിർത്തുക. നേരിട്ടും സഹായകരവുമായിരിക്കുക. ഉപയോക്താവിന്റെ ചോദ്യം: {query}",
        'pa': f"ਤੁਸੀਂ ਇੱਕ ਪੇਸ਼ੇਵਰ ਸਿਹਤ ਮਾਹਿਰ ਹੋ। ਸੰਖੇਪ, ਸਪਸ਼ਟ ਡਾਕਟਰੀ ਸਲਾਹ ਦਿਓ। 80 ਸ਼ਬਦਾਂ ਤੋਂ ਘੱਟ ਜਵਾਬ ਰੱਖੋ। ਸਿੱਧੇ ਅਤੇ ਮਦਦਗਾਰ ਬਣੋ। ਵਰਤੋਂਕਾਰ ਦਾ ਸਵਾਲ: {query}",
        'or': f"ଆପଣ ଜଣେ ବୃତ୍ତିଗତ ସ୍ୱାସ୍ଥ୍ୟ ବିଶେଷଜ୍ଞ। ସଂକ୍ଷିପ୍ତ, ସ୍ପଷ୍ଟ ଚିକିତ୍ସା ପରାମର୍ଶ ଦିଅନ୍ତୁ। ୮୦ ଶବ୍ଦରୁ କମ୍ ଉତ୍ତର ରଖନ୍ତୁ। ସିଧା ଏବଂ ସହାୟକ ହୁଅନ୍ତୁ। ବ୍ୟବହାରକାରୀ ପ୍ରଶ୍ନ: {query}",
        'as': f"আপুনি এজন পেছাদাৰী স্বাস্থ্য বিশেষজ্ঞ। সংক্ষিপ্ত, স্পষ্ট চিকিৎসা পৰামৰ্শ দিয়ক। ৮০ শব্দতকৈ কম উত্তৰ ৰাখক। পোনপটীয়াকৈ আৰু সহায়ক হ'ক। ব্যৱহাৰকাৰীৰ প্ৰশ্ন: {query}"
    }
    return language_prompts.get(language, language_prompts['en'])

def get_language_code(language):
    """Convert detected language to gTTS language code for Indian languages"""
    language_map = {
        'en': 'en',
        'hi': 'hi',
        'bn': 'bn',
        'te': 'te',
        'mr': 'mr',
        'ta': 'ta',
        'gu': 'gu',
        'kn': 'kn',
        'ml': 'ml',
        'pa': 'pa',
        'or': 'or',
        'as': 'as'
    }
    return language_map.get(language, 'en')

def speak_fast(text, language='en'):
    """Convert text to speech with faster speed"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tf:
        tmp_path = tf.name
    
    try:
        tts_lang = get_language_code(language)
        # Use slow=False for faster speech and add speed parameter
        tts = gTTS(text=text, lang=tts_lang, slow=False)
        tts.save(tmp_path)
        playsound(tmp_path)
    finally:
        try:
            os.remove(tmp_path)
        except:
            pass

def log_interaction(query, response, language, detected_lang):
    """Log the interaction for analytics"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'query': query,
        'response': response,
        'language': language,
        'detected_language': detected_lang
    }
    
    # Save to log file
    try:
        with open('health_bot_logs.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    except:
        pass

def select_language():
    """Ask user to select language with voice prompts"""
    print("\n🏥 HealthBot - भाषा चुनें / Select Language")
    print("=" * 50)
    
    # Speak the language selection menu in Hindi first (shorter version)
    welcome_text = "नमस्ते! भाषा चुनें। हिंदी 1, English 2, Bengali 3, Telugu 4, Marathi 5, Tamil 6, Gujarati 7, Kannada 8, Malayalam 9, Punjabi 0।"
    speak_fast(welcome_text, 'hi')
    
    print("हिंदी के लिए 1 दबाएं / Press 1 for Hindi")
    print("English के लिए 2 दबाएं / Press 2 for English")
    print("বাংলা জন্য 3 চাপুন / Press 3 for Bengali")
    print("తెలుగు కోసం 4 నొక్కండి / Press 4 for Telugu")
    print("मराठी के लिए 5 दबाएं / Press 5 for Marathi")
    print("தமிழ் க்கு 6 அழுத்தவும் / Press 6 for Tamil")
    print("ગુજરાતી માટે 7 દબાવો / Press 7 for Gujarati")
    print("ಕನ್ನಡಕ್ಕೆ 8 ಒತ್ತಿ / Press 8 for Kannada")
    print("മലയാളത്തിന് 9 അമർത്തുക / Press 9 for Malayalam")
    print("ਪੰਜਾਬੀ ਲਈ 0 ਦਬਾਓ / Press 0 for Punjabi")
    print("=" * 50)
    
    language_map = {
        '1': 'hi', '2': 'en', '3': 'bn', '4': 'te', '5': 'mr',
        '6': 'ta', '7': 'gu', '8': 'kn', '9': 'ml', '0': 'pa'
    }
    
    while True:
        try:
            choice = input("अपनी भाषा चुनें / Choose your language: ").strip()
            if choice in language_map:
                selected_lang = language_map[choice]
                # Confirm selection with voice (shorter version)
                confirmation_texts = {
                    'hi': "हिंदी चुना। अब स्वास्थ्य प्रश्न पूछें।",
                    'en': "English selected. Ask your health question.",
                    'bn': "বাংলা নির্বাচিত। স্বাস্থ্য প্রশ্ন জিজ্ঞাসা করুন।",
                    'te': "తెలుగు ఎంచుకున్నారు। ఆరోగ్య ప్రశ్న అడగండి।",
                    'mr': "मराठी निवडले। आरोग्य प्रश्न विचारा।",
                    'ta': "தமிழ் தேர்ந்தெடுக்கப்பட்டது। சுகாதார கேள்வியைக் கேளுங்கள்।",
                    'gu': "ગુજરાતી પસંદ કર્યું। આરોગ્ય પ્રશ્ન પૂછો।",
                    'kn': "ಕನ್ನಡ ಆಯ್ಕೆ ಮಾಡಲಾಗಿದೆ। ಆರೋಗ್ಯ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ।",
                    'ml': "മലയാളം തിരഞ്ഞെടുത്തു। ആരോഗ്യ ചോദ്യം ചോദിക്കുക।",
                    'pa': "ਪੰਜਾਬੀ ਚੁਣਿਆ। ਸਿਹਤ ਸਵਾਲ ਪੁੱਛੋ।"
                }
                confirmation_text = confirmation_texts.get(selected_lang, "Language selected. You can now ask your health question.")
                speak_fast(confirmation_text, selected_lang)
                return selected_lang
            else:
                print(" Invalid choice. Please select 1-9 or 0")
                # Speak error message in Hindi
                error_text = "गलत विकल्प। कृपया 1 से 9 या 0 दबाएं।"
                speak_fast(error_text, 'hi')
        except KeyboardInterrupt:
            return None

def get_follow_up_questions_prompt(query, language):
    """Get follow-up questions prompt in different languages"""
    follow_up_prompts = {
        'en': f"You are a professional health expert. Ask 2-3 specific follow-up questions to better understand the patient's condition. Then provide a comprehensive diagnosis and treatment advice. Keep response under 100 words. Patient query: {query}",
        'hi': f"आप एक पेशेवर स्वास्थ्य विशेषज्ञ हैं। रोगी की स्थिति को बेहतर समझने के लिए 2-3 विशिष्ट अनुवर्ती प्रश्न पूछें। फिर एक व्यापक निदान और उपचार सलाह प्रदान करें। प्रतिक्रिया 100 शब्दों से कम रखें। रोगी प्रश्न: {query}",
        'bn': f"আপনি একজন পেশাদার স্বাস্থ্য বিশেষজ্ঞ। রোগীর অবস্থা আরও ভালোভাবে বুঝতে ২-৩টি নির্দিষ্ট অনুসরণ প্রশ্ন করুন। তারপর একটি ব্যাপক রোগ নির্ণয় এবং চিকিৎসা পরামর্শ প্রদান করুন। ১০০ শব্দের কম উত্তর রাখুন। রোগীর প্রশ্ন: {query}",
        'te': f"మీరు ఒక వృత్తిపరమైన ఆరోగ్య నిపుణుడు. రోగి పరిస్థితిని మరింత బాగా అర్థం చేసుకోవడానికి 2-3 నిర్దిష్ట అనుసరణ ప్రశ్నలు అడగండి. తర్వాత సమగ్ర నిర్ధారణ మరియు చికిత్స సలహా అందించండి. 100 పదాల కంటే తక్కువ సమాధానం ఉంచండి. రోగి ప్రశ్న: {query}",
        'mr': f"तुम्ही एक व्यावसायिक आरोग्य तज्ञ आहात. रुग्णाची स्थिती अधिक चांगल्या प्रकारे समजून घेण्यासाठी 2-3 विशिष्ट अनुवर्ती प्रश्न विचारा. नंतर एक व्यापक निदान आणि उपचार सल्ला द्या. 100 शब्दांपेक्षा कमी उत्तर ठेवा. रुग्ण प्रश्न: {query}",
        'ta': f"நீங்கள் ஒரு தொழில்முறை சுகாதார நிபுணர். நோயாளியின் நிலையை சிறப்பாக புரிந்துகொள்ள 2-3 குறிப்பிட்ட தொடர்ந்து வரும் கேள்விகளைக் கேளுங்கள். பின்னர் ஒரு விரிவான நோயறிதல் மற்றும் சிகிச்சை ஆலோசனையை வழங்குங்கள். 100 வார்த்தைகளுக்கு குறைவான பதிலை வைத்திருங்கள். நோயாளி கேள்வி: {query}",
        'gu': f"તમે એક વ્યાવસાયિક આરોગ્ય નિષ્ણાત છો. રોગીની સ્થિતિને વધુ સારી રીતે સમજવા માટે 2-3 ચોક્કસ અનુસરણ પ્રશ્નો પૂછો. પછી એક વ્યાપક નિદાન અને સારવારની સલાહ આપો. 100 શબ્દો કરતાં ઓછા જવાબ રાખો. રોગી પ્રશ્ન: {query}",
        'kn': f"ನೀವು ಒಬ್ಬ ವೃತ್ತಿಪರ ಆರೋಗ್ಯ ತಜ್ಞ. ರೋಗಿಯ ಸ್ಥಿತಿಯನ್ನು ಉತ್ತಮವಾಗಿ ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲು 2-3 ನಿರ್ದಿಷ್ಟ ಅನುಸರಣ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳಿ. ನಂತರ ಸಮಗ್ರ ರೋಗನಿರ್ಣಯ ಮತ್ತು ಚಿಕಿತ್ಸೆ ಸಲಹೆ ನೀಡಿ. 100 ಪದಗಳಿಗಿಂತ ಕಡಿಮೆ ಉತ್ತರಗಳನ್ನು ಇರಿಸಿ. ರೋಗಿ ಪ್ರಶ್ನೆ: {query}",
        'ml': f"നിങ്ങൾ ഒരു പ്രൊഫഷണൽ ആരോഗ്യ വിദഗ്ധനാണ്. രോഗിയുടെ അവസ്ഥ മെച്ചപ്പെടുത്താൻ 2-3 നിർദ്ദിഷ്ട ഫോളോ-അപ്പ് ചോദ്യങ്ങൾ ചോദിക്കുക. പിന്നീട് സമഗ്ര രോഗനിർണയവും ചികിത്സാ ഉപദേശവും നൽകുക. 100 വാക്കുകൾക്ക് താഴെ ഉത്തരങ്ങൾ നിലനിർത്തുക. രോഗി ചോദ്യം: {query}",
        'pa': f"ਤੁਸੀਂ ਇੱਕ ਪੇਸ਼ੇਵਰ ਸਿਹਤ ਮਾਹਿਰ ਹੋ। ਮਰੀਜ਼ ਦੀ ਹਾਲਤ ਨੂੰ ਬਿਹਤਰ ਸਮਝਣ ਲਈ 2-3 ਖਾਸ ਫਾਲੋ-ਅਪ ਸਵਾਲ ਪੁੱਛੋ। ਫਿਰ ਇੱਕ ਵਿਆਪਕ ਰੋਗ ਦਾ ਨਿਰਣਾ ਅਤੇ ਇਲਾਜ ਦੀ ਸਲਾਹ ਦਿਓ। 100 ਸ਼ਬਦਾਂ ਤੋਂ ਘੱਟ ਜਵਾਬ ਰੱਖੋ। ਮਰੀਜ਼ ਦਾ ਸਵਾਲ: {query}"
    }
    return follow_up_prompts.get(language, follow_up_prompts['en'])

def add_to_conversation(user_query, ai_response, language):
    """Add conversation to memory"""
    conversation_history.append({
        'user': user_query,
        'ai': ai_response,
        'language': language,
        'timestamp': datetime.now().isoformat()
    })

def get_conversation_context(language):
    """Get conversation history as context"""
    if not conversation_history:
        return ""
    
    context_parts = []
    for entry in conversation_history[-3:]:  # Last 3 conversations for context
        context_parts.append(f"User: {entry['user']}")
        context_parts.append(f"AI: {entry['ai']}")
    
    context = "\n".join(context_parts)
    
    context_prompts = {
        'en': f"Previous conversation context:\n{context}\n\nBased on this conversation history, ",
        'hi': f"पिछली बातचीत का संदर्भ:\n{context}\n\nइस बातचीत के इतिहास के आधार पर, ",
        'bn': f"পূর্ববর্তী কথোপকথনের প্রসঙ্গ:\n{context}\n\nএই কথোপকথনের ইতিহাসের ভিত্তিতে, ",
        'te': f"మునుపటి సంభాషణ సందర్భం:\n{context}\n\nఈ సంభాషణ చరిత్ర ఆధారంగా, ",
        'mr': f"मागील संभाषण संदर्भ:\n{context}\n\nया संभाषणाच्या इतिहासावर आधारित, ",
        'ta': f"முந்தைய உரையாடல் சூழல்:\n{context}\n\nஇந்த உரையாடல் வரலாற்றின் அடிப்படையில், ",
        'gu': f"પાછલી વાતચીતનો સંદર્ભ:\n{context}\n\nઆ વાતચીતના ઇતિહાસના આધારે, ",
        'kn': f"ಹಿಂದಿನ ಸಂಭಾಷಣೆ ಸಂದರ್ಭ:\n{context}\n\nಈ ಸಂಭಾಷಣೆಯ ಇತಿಹಾಸದ ಆಧಾರದ ಮೇಲೆ, ",
        'ml': f"മുമ്പത്തെ സംഭാഷണ സന്ദർഭം:\n{context}\n\nഈ സംഭാഷണ ചരിത്രത്തിന്റെ അടിസ്ഥാനത്തിൽ, ",
        'pa': f"ਪਿਛਲੀ ਗੱਲਬਾਤ ਦਾ ਸੰਦਰਭ:\n{context}\n\nਇਸ ਗੱਲਬਾਤ ਦੇ ਇਤਿਹਾਸ ਦੇ ਆਧਾਰ 'ਤੇ, "
    }
    return context_prompts.get(language, context_prompts['en'])

def get_initial_prompt(query, language):
    """Get initial prompt with one follow-up question and then provide answer"""
    initial_prompts = {
        'en': f"You are a professional health expert. Ask 1 specific follow-up question to better understand the patient's condition, then provide a comprehensive diagnosis and treatment advice. Keep response under 100 words. Patient query: {query}",
        'hi': f"आप एक पेशेवर स्वास्थ्य विशेषज्ञ हैं। रोगी की स्थिति को बेहतर समझने के लिए 1 विशिष्ट अनुवर्ती प्रश्न पूछें, फिर एक व्यापक निदान और उपचार सलाह प्रदान करें। प्रतिक्रिया 100 शब्दों से कम रखें। रोगी प्रश्न: {query}",
        'bn': f"আপনি একজন পেশাদার স্বাস্থ্য বিশেষজ্ঞ। রোগীর অবস্থা আরও ভালোভাবে বুঝতে ১টি নির্দিষ্ট অনুসরণ প্রশ্ন করুন, তারপর একটি ব্যাপক রোগ নির্ণয় এবং চিকিৎসা পরামর্শ প্রদান করুন। ১০০ শব্দের কম উত্তর রাখুন। রোগীর প্রশ্ন: {query}",
        'te': f"మీరు ఒక వృత్తిపరమైన ఆరోగ్య నిపుణుడు. రోగి పరిస్థితిని మరింత బాగా అర్థం చేసుకోవడానికి 1 నిర్దిష్ట అనుసరణ ప్రశ్న అడగండి, తర్వాత సమగ్ర నిర్ధారణ మరియు చికిత్స సలహా అందించండి. 100 పదాల కంటే తక్కువ సమాధానం ఉంచండి. రోగి ప్రశ్న: {query}",
        'mr': f"तुम्ही एक व्यावसायिक आरोग्य तज्ञ आहात. रुग्णाची स्थिती अधिक चांगल्या प्रकारे समजून घेण्यासाठी 1 विशिष्ट अनुवर्ती प्रश्न विचारा, नंतर एक व्यापक निदान आणि उपचार सल्ला द्या. 100 शब्दांपेक्षा कमी उत्तर ठेवा. रुग्ण प्रश्न: {query}",
        'ta': f"நீங்கள் ஒரு தொழில்முறை சுகாதார நிபுணர். நோயாளியின் நிலையை சிறப்பாக புரிந்துகொள்ள 1 குறிப்பிட்ட தொடர்ந்து வரும் கேள்வியைக் கேளுங்கள், பின்னர் ஒரு விரிவான நோயறிதல் மற்றும் சிகிச்சை ஆலோசனையை வழங்குங்கள்। 100 வார்த்தைகளுக்கு குறைவான பதிலை வைத்திருங்கள்। நோயாளி கேள்வி: {query}",
        'gu': f"તમે એક વ્યાવસાયિક આરોગ્ય નિષ્ણાત છો. રોગીની સ્થિતિને વધુ સારી રીતે સમજવા માટે 1 ચોક્કસ અનુસરણ પ્રશ્ન પૂછો, પછી એક વ્યાપક નિદાન અને સારવારની સલાહ આપો. 100 શબ્દો કરતાં ઓછા જવાબ રાખો. રોગી પ્રશ્ન: {query}",
        'kn': f"ನೀವು ಒಬ್ಬ ವೃತ್ತಿಪರ ಆರೋಗ್ಯ ತಜ್ಞ. ರೋಗಿಯ ಸ್ಥಿತಿಯನ್ನು ಉತ್ತಮವಾಗಿ ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲು 1 ನಿರ್ದಿಷ್ಟ ಅನುಸರಣ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ, ನಂತರ ಸಮಗ್ರ ರೋಗನಿರ್ಣಯ ಮತ್ತು ಚಿಕಿತ್ಸೆ ಸಲಹೆ ನೀಡಿ. 100 ಪದಗಳಿಗಿಂತ ಕಡಿಮೆ ಉತ್ತರಗಳನ್ನು ಇರಿಸಿ. ರೋಗಿ ಪ್ರಶ್ನೆ: {query}",
        'ml': f"നിങ്ങൾ ഒരു പ്രൊഫഷണൽ ആരോഗ്യ വിദഗ്ധനാണ്. രോഗിയുടെ അവസ്ഥ മെച്ചപ്പെടുത്താൻ 1 നിർദ്ദിഷ്ട ഫോളോ-അപ്പ് ചോദ്യം ചോദിക്കുക, പിന്നീട് സമഗ്ര രോഗനിർണയവും ചികിത്സാ ഉപദേശവും നൽകുക. 100 വാക്കുകൾക്ക് താഴെ ഉത്തരങ്ങൾ നിലനിർത്തുക. രോഗി ചോദ്യം: {query}",
        'pa': f"ਤੁਸੀਂ ਇੱਕ ਪੇਸ਼ੇਵਰ ਸਿਹਤ ਮਾਹਿਰ ਹੋ। ਮਰੀਜ਼ ਦੀ ਹਾਲਤ ਨੂੰ ਬਿਹਤਰ ਸਮਝਣ ਲਈ 1 ਖਾਸ ਫਾਲੋ-ਅਪ ਸਵਾਲ ਪੁੱਛੋ, ਫਿਰ ਇੱਕ ਵਿਆਪਕ ਰੋਗ ਦਾ ਨਿਰਣਾ ਅਤੇ ਇਲਾਜ ਦੀ ਸਲਾਹ ਦਿਓ। 100 ਸ਼ਬਦਾਂ ਤੋਂ ਘੱਟ ਜਵਾਬ ਰੱਖੋ। ਮਰੀਜ਼ ਦਾ ਸਵਾਲ: {query}"
    }
    return initial_prompts.get(language, initial_prompts['en'])

def get_contextual_prompt(query, language):
    """Get contextual prompt with conversation history (for subsequent queries)"""
    context = get_conversation_context(language)
    
    contextual_prompts = {
        'en': f"You are a professional health expert. {context}Provide a comprehensive diagnosis and treatment advice based on the conversation history. Keep response under 100 words. Current patient query: {query}",
        'hi': f"आप एक पेशेवर स्वास्थ्य विशेषज्ञ हैं। {context}बातचीत के इतिहास के आधार पर एक व्यापक निदान और उपचार सलाह प्रदान करें। प्रतिक्रिया 100 शब्दों से कम रखें। वर्तमान रोगी प्रश्न: {query}",
        'bn': f"আপনি একজন পেশাদার স্বাস্থ্য বিশেষজ্ঞ। {context}কথোপকথনের ইতিহাসের ভিত্তিতে একটি ব্যাপক রোগ নির্ণয় এবং চিকিৎসা পরামর্শ প্রদান করুন। ১০০ শব্দের কম উত্তর রাখুন। বর্তমান রোগীর প্রশ্ন: {query}",
        'te': f"మీరు ఒక వృత్తిపరమైన ఆరోగ్య నిపుణుడు. {context}సంభాషణ చరిత్ర ఆధారంగా సమగ్ర నిర్ధారణ మరియు చికిత్స సలహా అందించండి. 100 పదాల కంటే తక్కువ సమాధానం ఉంచండి. ప్రస్తుత రోగి ప్రశ్న: {query}",
        'mr': f"तुम्ही एक व्यावसायिक आरोग्य तज्ञ आहात. {context}संभाषणाच्या इतिहासावर आधारित एक व्यापक निदान आणि उपचार सल्ला द्या. 100 शब्दांपेक्षा कमी उत्तर ठेवा. सध्याचा रुग्ण प्रश्न: {query}",
        'ta': f"நீங்கள் ஒரு தொழில்முறை சுகாதார நிபுணர். {context}உரையாடல் வரலாற்றின் அடிப்படையில் ஒரு விரிவான நோயறிதல் மற்றும் சிகிச்சை ஆலோசனையை வழங்குங்கள்। 100 வார்த்தைகளுக்கு குறைவான பதிலை வைத்திருங்கள்। தற்போதைய நோயாளி கேள்வி: {query}",
        'gu': f"તમે એક વ્યાવસાયિક આરોગ્ય નિષ્ણાત છો. {context}વાતચીતના ઇતિહાસના આધારે એક વ્યાપક નિદાન અને સારવારની સલાહ આપો. 100 શબ્દો કરતાં ઓછા જવાબ રાખો. વર્તમાન રોગી પ્રશ્ન: {query}",
        'kn': f"ನೀವು ಒಬ್ಬ ವೃತ್ತಿಪರ ಆರೋಗ್ಯ ತಜ್ಞ. {context}ಸಂಭಾಷಣೆಯ ಇತಿಹಾಸದ ಆಧಾರದ ಮೇಲೆ ಸಮಗ್ರ ರೋಗನಿರ್ಣಯ ಮತ್ತು ಚಿಕಿತ್ಸೆ ಸಲಹೆ ನೀಡಿ. 100 ಪದಗಳಿಗಿಂತ ಕಡಿಮೆ ಉತ್ತರಗಳನ್ನು ಇರಿಸಿ. ಪ್ರಸ್ತುತ ರೋಗಿ ಪ್ರಶ್ನೆ: {query}",
        'ml': f"നിങ്ങൾ ഒരു പ്രൊഫഷണൽ ആരോഗ്യ വിദഗ്ധനാണ്. {context}സംഭാഷണ ചരിത്രത്തിന്റെ അടിസ്ഥാനത്തിൽ സമഗ്ര രോഗനിർണയവും ചികിത്സാ ഉപദേശവും നൽകുക. 100 വാക്കുകൾക്ക് താഴെ ഉത്തരങ്ങൾ നിലനിർത്തുക. നിലവിലെ രോഗി ചോദ്യം: {query}",
        'pa': f"ਤੁਸੀਂ ਇੱਕ ਪੇਸ਼ੇਵਰ ਸਿਹਤ ਮਾਹਿਰ ਹੋ। {context}ਗੱਲਬਾਤ ਦੇ ਇਤਿਹਾਸ ਦੇ ਆਧਾਰ 'ਤੇ ਇੱਕ ਵਿਆਪਕ ਰੋਗ ਦਾ ਨਿਰਣਾ ਅਤੇ ਇਲਾਜ ਦੀ ਸਲਾਹ ਦਿਓ। 100 ਸ਼ਬਦਾਂ ਤੋਂ ਘੱਟ ਜਵਾਬ ਰੱਖੋ। ਮੌਜੂਦਾ ਮਰੀਜ਼ ਦਾ ਸਵਾਲ: {query}"
    }
    return contextual_prompts.get(language, contextual_prompts['en'])

def get_diagnosis_prompt(language):
    """Get diagnosis prompt after all questions are answered"""
    diagnosis_prompts = {
        'en': f"You are a professional health expert. Based on the complete conversation history, provide a comprehensive diagnosis and treatment advice. Keep response under 100 words. Give specific recommendations.",
        'hi': f"आप एक पेशेवर स्वास्थ्य विशेषज्ञ हैं। पूरी बातचीत के इतिहास के आधार पर, एक व्यापक निदान और उपचार सलाह प्रदान करें। प्रतिक्रिया 100 शब्दों से कम रखें। विशिष्ट सिफारिशें दें।",
        'bn': f"আপনি একজন পেশাদার স্বাস্থ্য বিশেষজ্ঞ। সম্পূর্ণ কথোপকথনের ইতিহাসের ভিত্তিতে, একটি ব্যাপক রোগ নির্ণয় এবং চিকিৎসা পরামর্শ প্রদান করুন। ১০০ শব্দের কম উত্তর রাখুন। নির্দিষ্ট সুপারিশ দিন।",
        'te': f"మీరు ఒక వృత్తిపరమైన ఆరోగ్య నిపుణుడు. పూర్తి సంభాషణ చరిత్ర ఆధారంగా, సమగ్ర నిర్ధారణ మరియు చికిత్స సలహా అందించండి. 100 పదాల కంటే తక్కువ సమాధానం ఉంచండి. నిర్దిష్ట సిఫారసులు ఇవ్వండి.",
        'mr': f"तुम्ही एक व्यावसायिक आरोग्य तज्ञ आहात. संपूर्ण संभाषणाच्या इतिहासावर आधारित, एक व्यापक निदान आणि उपचार सल्ला द्या. 100 शब्दांपेक्षा कमी उत्तर ठेवा. विशिष्ट शिफारसी द्या.",
        'ta': f"நீங்கள் ஒரு தொழில்முறை சுகாதார நிபுணர். முழு உரையாடல் வரலாற்றின் அடிப்படையில், ஒரு விரிவான நோயறிதல் மற்றும் சிகிச்சை ஆலோசனையை வழங்குங்கள்। 100 வார்த்தைகளுக்கு குறைவான பதிலை வைத்திருங்கள்। குறிப்பிட்ட பரிந்துரைகளைக் கொடுங்கள்।",
        'gu': f"તમે એક વ્યાવસાયિક આરોગ્ય નિષ્ણાત છો. સંપૂર્ણ વાતચીતના ઇતિહાસના આધારે, એક વ્યાપક નિદાન અને સારવારની સલાહ આપો. 100 શબ્દો કરતાં ઓછા જવાબ રાખો. ચોક્કસ ભલામણો આપો.",
        'kn': f"ನೀವು ಒಬ್ಬ ವೃತ್ತಿಪರ ಆರೋಗ್ಯ ತಜ್ಞ. ಸಂಪೂರ್ಣ ಸಂಭಾಷಣೆಯ ಇತಿಹಾಸದ ಆಧಾರದ ಮೇಲೆ, ಸಮಗ್ರ ರೋಗನಿರ್ಣಯ ಮತ್ತು ಚಿಕಿತ್ಸೆ ಸಲಹೆ ನೀಡಿ. 100 ಪದಗಳಿಗಿಂತ ಕಡಿಮೆ ಉತ್ತರಗಳನ್ನು ಇರಿಸಿ. ನಿರ್ದಿಷ್ಟ ಶಿಫಾರಸುಗಳನ್ನು ನೀಡಿ.",
        'ml': f"നിങ്ങൾ ഒരു പ്രൊഫഷണൽ ആരോഗ്യ വിദഗ്ധനാണ്. പൂർണ്ണ സംഭാഷണ ചരിത്രത്തിന്റെ അടിസ്ഥാനത്തിൽ, സമഗ്ര രോഗനിർണയവും ചികിത്സാ ഉപദേശവും നൽകുക. 100 വാക്കുകൾക്ക് താഴെ ഉത്തരങ്ങൾ നിലനിർത്തുക. നിർദ്ദിഷ്ട ശുപാർശകൾ നൽകുക.",
        'pa': f"ਤੁਸੀਂ ਇੱਕ ਪੇਸ਼ੇਵਰ ਸਿਹਤ ਮਾਹਿਰ ਹੋ। ਪੂਰੀ ਗੱਲਬਾਤ ਦੇ ਇਤਿਹਾਸ ਦੇ ਆਧਾਰ 'ਤੇ, ਇੱਕ ਵਿਆਪਕ ਰੋਗ ਦਾ ਨਿਰਣਾ ਅਤੇ ਇਲਾਜ ਦੀ ਸਲਾਹ ਦਿਓ। 100 ਸ਼ਬਦਾਂ ਤੋਂ ਘੱਟ ਜਵਾਬ ਰੱਖੋ। ਖਾਸ ਸਿਫਾਰਸ਼ਾਂ ਦਿਓ।"
    }
    return diagnosis_prompts.get(language, diagnosis_prompts['en'])

def should_provide_diagnosis():
    """Check if enough information has been gathered to provide diagnosis"""
    # Provide diagnosis after 1 exchange (1 initial + 1 follow-up answer)
    return len(conversation_history) >= 2

def listen_and_respond(selected_language):
    """Main function to listen and respond to health queries"""
    with sr.Microphone() as source:
        print(f"\n🏥 HealthBot Ready - Speak your health question in {selected_language.upper()}...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        print("🎙️ Listening...")
        
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            print(" Processing your health question...")
        except sr.WaitTimeoutError:
            print("No speech detected within timeout")
            return

        try:
            query = r.recognize_google(audio)
            print(f" You said: {query}")

            # Initialize ai_reply
            ai_reply = ""
            
            # Add user query to conversation first
            add_to_conversation(query, "", selected_language)
            
            # Check conversation flow
            if len(conversation_history) == 1:
                # First query - ask follow-up questions only
                prompt = get_initial_prompt(query, selected_language)
            elif should_provide_diagnosis():
                # Enough information gathered - provide diagnosis
                prompt = get_diagnosis_prompt(selected_language)
            else:
                # Still gathering information - ask more questions
                prompt = get_contextual_prompt(query, selected_language)
            
            # Generate health expert response
            try:
                response = model.generate_content(prompt)
                ai_reply = response.text
                print(f" Health Expert Response: {ai_reply}")
            except Exception as api_error:
                print(f" API Error: {api_error}")
                ai_reply = "Sorry, I'm having trouble processing your request. Please try again."
                print(f" Health Expert Response: {ai_reply}")
            
            # Update the last conversation entry with AI response
            if conversation_history:
                conversation_history[-1]['ai'] = ai_reply
            
            # Log the interaction
            log_interaction(query, ai_reply, selected_language, selected_language)
            
            # Speak response in selected language with faster speed
            speak_fast(ai_reply, selected_language)

        except sr.UnknownValueError:
            print(" Sorry, couldn't understand your voice. Please speak clearly.")
        except Exception as e:
            print(f" Error: {e}")

def show_conversation_history():
    """Show conversation history"""
    if not conversation_history:
        print(" No conversation history yet.")
        return
    
    print(f"\n Conversation History ({len(conversation_history)} exchanges):")
    print("=" * 60)
    for i, entry in enumerate(conversation_history, 1):
        print(f"\n{i}. [{entry['timestamp']}]")
        print(f"   User: {entry['user']}")
        print(f"   AI: {entry['ai'][:100]}{'...' if len(entry['ai']) > 100 else ''}")
    print("=" * 60)

def show_help():
    """Show available commands and features"""
    print("\n HealthBot - AI Health Assistant (India)")
    print("=" * 60)
    print("Supported Indian Languages:")
    print("• English (EN) • Hindi (हिंदी) • Bengali (বাংলা)")
    print("• Telugu (తెలుగు) • Marathi (मराठी) • Tamil (தமிழ்)")
    print("• Gujarati (ગુજરાતી) • Kannada (ಕನ್ನಡ) • Malayalam (മലയാളം)")
    print("• Punjabi (ਪੰਜਾਬੀ) • Odia (ଓଡ଼ିଆ) • Assamese (অসমীয়া)")
    print("\nFeatures:")
    print("• Health expert responses in your language")
    print("• Fast speech synthesis")
    print("• Contextual conversation memory")
    print("• Follow-up questions for better diagnosis")
    print("• Call logging for analytics")
    print("\nCommands:")
    print("• Just speak your health question in any Indian language")
    print("• Press Ctrl+C to exit")
    print("• Make sure your microphone is working")
    print("=" * 60)

if __name__ == "__main__":
    show_help()
    
    # First, ask user to select language
    selected_language = select_language()
    if selected_language is None:
        print("\n HealthBot stopped. Thank you for using our service!")
        exit()
    
    print(f"\n Language selected: {selected_language.upper()}")
    print(" HealthBot is now ready in your selected language!")
    
    try:
        while True:
            listen_and_respond(selected_language)
            print("\n" + "="*60)
            print("Ready for next question...")
    except KeyboardInterrupt:
        print("\n HealthBot stopped. Thank you for using our service!")
        show_conversation_history()




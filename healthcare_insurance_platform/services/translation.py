"""Multilingual translation service with context-aware LLM translation."""

import re
from enum import Enum
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field

from healthcare_insurance_platform.services.base import BaseService
from healthcare_insurance_platform.services.llm_client import LLMClient, PromptTemplate


class SupportedLanguage(str, Enum):
    """Supported languages for translation."""
    
    ENGLISH = "en"
    HINDI = "hi"
    TAMIL = "ta"
    TELUGU = "te"
    BENGALI = "bn"
    MARATHI = "mr"
    GUJARATI = "gu"


class TechnicalTerm(BaseModel):
    """Technical or legal term with explanation."""
    
    original_term: str = Field(description="Original term in source language")
    translated_term: Optional[str] = Field(
        default=None,
        description="Translated term if available"
    )
    explanation: str = Field(
        description="Explanation of the term in target language"
    )


class TranslatedText(BaseModel):
    """Translation result with preserved terminology."""
    
    translated_content: str = Field(description="Translated text")
    source_language: str = Field(description="Source language code")
    target_language: str = Field(description="Target language code")
    technical_terms: List[TechnicalTerm] = Field(
        default_factory=list,
        description="Technical terms with explanations"
    )
    confidence_score: Optional[float] = Field(
        default=None,
        description="Translation confidence (0-1)"
    )


class TranslatedTextWithGlossary(BaseModel):
    """Translation result with comprehensive glossary of preserved terms."""
    
    translated_content: str = Field(description="Translated text with preserved terms")
    source_language: str = Field(description="Source language code")
    target_language: str = Field(description="Target language code")
    glossary: List[TechnicalTerm] = Field(
        description="Glossary of all technical terms preserved in translation"
    )
    confidence_score: Optional[float] = Field(
        default=None,
        description="Translation confidence (0-1)"
    )


class TranslationService(BaseService):
    """Multilingual translation service.
    
    Provides context-aware translation using LLM while preserving
    technical and legal terminology. Supports multiple Indian languages.
    """
    
    # Language names for prompts
    LANGUAGE_NAMES = {
        SupportedLanguage.ENGLISH: "English",
        SupportedLanguage.HINDI: "Hindi (हिंदी)",
        SupportedLanguage.TAMIL: "Tamil (தமிழ்)",
        SupportedLanguage.TELUGU: "Telugu (తెలుగు)",
        SupportedLanguage.BENGALI: "Bengali (বাংলা)",
        SupportedLanguage.MARATHI: "Marathi (मराठी)",
        SupportedLanguage.GUJARATI: "Gujarati (ગુજરાતી)",
    }
    
    # Technical term glossary with explanations in different languages
    # Format: {term: {language_code: explanation}}
    TECHNICAL_GLOSSARY: Dict[str, Dict[str, str]] = {
        # Insurance terms
        "pre-existing disease": {
            "en": "A medical condition that existed before purchasing insurance",
            "hi": "बीमा खरीदने से पहले मौजूद चिकित्सा स्थिति",
            "ta": "காப்பீடு வாங்குவதற்கு முன்பு இருந்த மருத்துவ நிலை",
            "te": "బీమా కొనుగోలు చేయడానికి ముందు ఉన్న వైద్య పరిస్థితి",
            "bn": "বীমা কেনার আগে বিদ্যমান চিকিৎসা অবস্থা",
            "mr": "विमा खरेदी करण्यापूर्वी अस्तित्वात असलेली वैद्यकीय स्थिती",
            "gu": "વીમો ખરીદતા પહેલા અસ્તિત્વમાં રહેલી તબીબી સ્થિતિ",
        },
        "PED": {
            "en": "Pre-Existing Disease - a medical condition that existed before insurance purchase",
            "hi": "पूर्व-मौजूदा बीमारी - बीमा खरीदने से पहले मौजूद चिकित्सा स्थिति",
            "ta": "முன்பே இருந்த நோய் - காப்பீடு வாங்குவதற்கு முன்பு இருந்த மருத்துவ நிலை",
            "te": "ముందుగా ఉన్న వ్యాధి - బీమా కొనుగోలు చేయడానికి ముందు ఉన్న వైద్య పరిస్థితి",
            "bn": "পূর্ব-বিদ্যমান রোগ - বীমা কেনার আগে বিদ্যমান চিকিৎসা অবস্থা",
            "mr": "पूर्व-अस्तित्वातील रोग - विमा खरेदी करण्यापूर्वी अस्तित्वात असलेली वैद्यकीय स्थिती",
            "gu": "પહેલાથી અસ્તિત્વમાં રહેલો રોગ - વીમો ખરીદતા પહેલા અસ્તિત્વમાં રહેલી તબીબી સ્થિતિ",
        },
        "waiting period": {
            "en": "Time period after policy purchase during which certain claims are not covered",
            "hi": "पॉलिसी खरीद के बाद की अवधि जिसमें कुछ दावे कवर नहीं होते",
            "ta": "பாலிசி வாங்கிய பிறகு சில கோரிக்கைகள் பாதுகாக்கப்படாத காலம்",
            "te": "పాలసీ కొనుగోలు తర్వాత కొన్ని క్లెయిమ్‌లు కవర్ చేయబడని కాలం",
            "bn": "পলিসি কেনার পর সময়কাল যখন কিছু দাবি কভার করা হয় না",
            "mr": "पॉलिसी खरेदीनंतरचा कालावधी ज्यामध्ये काही दावे कव्हर केले जात नाहीत",
            "gu": "પોલિસી ખરીદ્યા પછીનો સમયગાળો જ્યારે અમુક દાવાઓ આવરી લેવામાં આવતા નથી",
        },
        "copayment": {
            "en": "Percentage of medical expenses that the insured must pay from their own pocket",
            "hi": "चिकित्सा खर्च का प्रतिशत जो बीमाधारक को अपनी जेब से देना होता है",
            "ta": "காப்பீடு செய்தவர் தங்கள் சொந்த பாக்கெட்டில் இருந்து செலுத்த வேண்டிய மருத்துவ செலவுகளின் சதவீதம்",
            "te": "బీమా చేసుకున్నవారు తమ సొంత జేబు నుండి చెల్లించాల్సిన వైద్య ఖర్చుల శాతం",
            "bn": "চিকিৎসা খরচের শতাংশ যা বীমাকৃত ব্যক্তিকে নিজের পকেট থেকে দিতে হবে",
            "mr": "वैद्यकीय खर्चाची टक्केवारी जी विमाधारकाने स्वतःच्या खिशातून द्यावी लागते",
            "gu": "તબીબી ખર્ચની ટકાવારી જે વીમાધારકે પોતાના ખિસ્સામાંથી ચૂકવવી પડે છે",
        },
        "deductible": {
            "en": "Fixed amount the insured must pay before insurance coverage begins",
            "hi": "निश्चित राशि जो बीमाधारक को बीमा कवरेज शुरू होने से पहले देनी होती है",
            "ta": "காப்பீடு தொடங்குவதற்கு முன் காப்பீடு செய்தவர் செலுத்த வேண்டிய நிலையான தொகை",
            "te": "బీమా కవరేజ్ ప్రారంభమయ్యే ముందు బీమా చేసుకున్నవారు చెల్లించాల్సిన స్థిర మొత్తం",
            "bn": "বীমা কভারেজ শুরু হওয়ার আগে বীমাকৃত ব্যক্তিকে যে নির্দিষ্ট পরিমাণ দিতে হবে",
            "mr": "विमा कव्हरेज सुरू होण्यापूर्वी विमाधारकाने द्यावी लागणारी निश्चित रक्कम",
            "gu": "વીમા કવરેજ શરૂ થાય તે પહેલાં વીમાધારકે ચૂકવવી પડતી નિશ્ચિત રકમ",
        },
        "exclusion": {
            "en": "Medical conditions or treatments that are not covered by the insurance policy",
            "hi": "चिकित्सा स्थितियां या उपचार जो बीमा पॉलिसी द्वारा कवर नहीं किए जाते",
            "ta": "காப்பீட்டு பாலிசியால் பாதுகாக்கப்படாத மருத்துவ நிலைகள் அல்லது சிகிச்சைகள்",
            "te": "బీమా పాలసీ ద్వారా కవర్ చేయబడని వైద్య పరిస్థితులు లేదా చికిత్సలు",
            "bn": "চিকিৎসা অবস্থা বা চিকিৎসা যা বীমা পলিসি দ্বারা কভার করা হয় না",
            "mr": "वैद्यकीय स्थिती किंवा उपचार जे विमा पॉलिसीद्वारे कव्हर केले जात नाहीत",
            "gu": "તબીબી સ્થિતિઓ અથવા સારવાર જે વીમા પોલિસી દ્વારા આવરી લેવામાં આવતી નથી",
        },
        "claim settlement ratio": {
            "en": "Percentage of insurance claims approved and paid by the insurance company",
            "hi": "बीमा कंपनी द्वारा स्वीकृत और भुगतान किए गए बीमा दावों का प्रतिशत",
            "ta": "காப்பீட்டு நிறுவனத்தால் அங்கீகரிக்கப்பட்டு செலுத்தப்பட்ட காப்பீட்டு கோரிக்கைகளின் சதவீதம்",
            "te": "బీమా కంపెనీ ద్వారా ఆమోదించబడిన మరియు చెల్లించబడిన బీమా క్లెయిమ్‌ల శాతం",
            "bn": "বীমা কোম্পানি দ্বারা অনুমোদিত এবং প্রদত্ত বীমা দাবির শতাংশ",
            "mr": "विमा कंपनीद्वारे मंजूर आणि भरलेल्या विमा दाव्यांची टक्केवारी",
            "gu": "વીમા કંપની દ્વારા મંજૂર અને ચૂકવવામાં આવેલા વીમા દાવાઓની ટકાવારી",
        },
        # Medical terms
        "hypertension": {
            "en": "High blood pressure - a condition where blood pressure is consistently elevated",
            "hi": "उच्च रक्तचाप - एक स्थिति जहां रक्तचाप लगातार बढ़ा हुआ रहता है",
            "ta": "உயர் இரத்த அழுத்தம் - இரத்த அழுத்தம் தொடர்ந்து உயர்ந்திருக்கும் நிலை",
            "te": "అధిక రక్తపోటు - రక్తపోటు నిరంతరం పెరిగిన పరిస్థితి",
            "bn": "উচ্চ রক্তচাপ - একটি অবস্থা যেখানে রক্তচাপ ধারাবাহিকভাবে উচ্চ থাকে",
            "mr": "उच्च रक्तदाब - एक स्थिती जिथे रक्तदाब सतत वाढलेला असतो",
            "gu": "ઉચ્ચ રક્તચાપ - એક સ્થિતિ જ્યાં રક્તચાપ સતત વધેલું હોય છે",
        },
        "diabetes mellitus": {
            "en": "Diabetes - a chronic condition affecting blood sugar regulation",
            "hi": "मधुमेह - रक्त शर्करा नियमन को प्रभावित करने वाली एक पुरानी स्थिति",
            "ta": "நீரிழிவு - இரத்த சர்க்கரை ஒழுங்குமுறையை பாதிக்கும் நாள்பட்ட நிலை",
            "te": "మధుమేహం - రక్త చక్కెర నియంత్రణను ప్రభావితం చేసే దీర్ఘకాలిక పరిస్థితి",
            "bn": "ডায়াবেটিস - রক্তে শর্করা নিয়ন্ত্রণকে প্রভাবিত করে এমন একটি দীর্ঘস্থায়ী অবস্থা",
            "mr": "मधुमेह - रक्तातील साखर नियमन प्रभावित करणारी एक जुनाट स्थिती",
            "gu": "ડાયાબિટીસ - લોહીમાં ખાંડના નિયમનને અસર કરતી લાંબી સ્થિતિ",
        },
        "cardiovascular disease": {
            "en": "Heart and blood vessel diseases including heart attacks and strokes",
            "hi": "हृदय और रक्त वाहिका रोग जिसमें दिल का दौरा और स्ट्रोक शामिल हैं",
            "ta": "இதய மற்றும் இரத்த நாள நோய்கள் இதய தாக்குதல்கள் மற்றும் பக்கவாதம் உட்பட",
            "te": "గుండె మరియు రక్త నాళాల వ్యాధులు గుండెపోటు మరియు స్ట్రోక్‌లతో సహా",
            "bn": "হৃদয় এবং রক্তনালীর রোগ যার মধ্যে হার্ট অ্যাটাক এবং স্ট্রোক রয়েছে",
            "mr": "हृदय आणि रक्तवाहिन्या रोग ज्यात हृदयविकाराचा झटका आणि पक्षाघात यांचा समावेश आहे",
            "gu": "હૃદય અને રક્ત વાહિનીઓના રોગો જેમાં હાર્ટ એટેક અને સ્ટ્રોક શામેલ છે",
        },
        "chemotherapy": {
            "en": "Cancer treatment using drugs to destroy cancer cells",
            "hi": "कैंसर कोशिकाओं को नष्ट करने के लिए दवाओं का उपयोग करके कैंसर उपचार",
            "ta": "புற்றுநோய் செல்களை அழிக்க மருந்துகளைப் பயன்படுத்தி புற்றுநோய் சிகிச்சை",
            "te": "క్యాన్సర్ కణాలను నాశనం చేయడానికి మందులను ఉపయోగించి క్యాన్సర్ చికిత్స",
            "bn": "ক্যান্সার কোষ ধ্বংস করতে ওষুধ ব্যবহার করে ক্যান্সার চিকিৎসা",
            "mr": "कर्करोगाच्या पेशी नष्ट करण्यासाठी औषधे वापरून कर्करोग उपचार",
            "gu": "કેન્સર કોષોને નષ્ટ કરવા માટે દવાઓનો ઉપયોગ કરીને કેન્સર સારવાર",
        },
    }
    
    # Patterns to identify technical terms (case-insensitive)
    TECHNICAL_TERM_PATTERNS = [
        # Insurance terms
        r'\b(?:pre-?existing\s+(?:disease|condition|illness)s?|PED)\b',
        r'\bwaiting\s+period\b',
        r'\bco-?payment\b',
        r'\bdeductible\b',
        r'\bexclusion\b',
        r'\bclaim\s+settlement\s+ratio\b',
        r'\bsum\s+insured\b',
        r'\bpremium\b',
        r'\bpolicy\s+holder\b',
        r'\bnominee\b',
        r'\bmaternity\s+(?:coverage|benefit)\b',
        r'\broom\s+rent\s+limit\b',
        r'\bsub-?limits?\b',
        r'\bcashless\s+(?:treatment|facility)\b',
        r'\breimbursement\b',
        r'\bnetwork\s+hospital\b',
        r'\bday\s+care\s+(?:procedure|treatment)\b',
        r'\bdomiciliary\s+(?:hospitalization|treatment)\b',
        # Medical terms
        r'\bhypertension\b',
        r'\bdiabetes\s+mellitus\b',
        r'\bcardiovascular\s+disease\b',
        r'\bchemotherapy\b',
        r'\bradiotherapy\b',
        r'\bdialysis\b',
        r'\bcoronary\s+(?:artery|bypass)\b',
        r'\bangioplasty\b',
        r'\bmalignant\b',
        r'\bbenign\b',
        r'\bchronic\b',
        r'\bacute\b',
    ]
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        db=None,
        vector_store=None,
    ):
        """Initialize translation service.
        
        Args:
            llm_client: LLM client for translation (creates default if None)
            db: Database session
            vector_store: Vector store
        """
        super().__init__(db=db, vector_store=vector_store)
        self.llm_client = llm_client or LLMClient()
        self._register_translation_templates()
    
    def _register_translation_templates(self) -> None:
        """Register translation prompt templates."""
        
        # General translation template
        general_translation_template = PromptTemplate(
            name="general_translation",
            system_message=(
                "You are an expert translator specializing in healthcare and insurance content. "
                "Translate text accurately while preserving meaning and context. "
                "For technical or legal terms without direct translations, provide the original term "
                "followed by an explanation in the target language."
            ),
            user_template=(
                "Translate the following text from {source_language} to {target_language}:\n\n"
                "{text}\n\n"
                "Provide the translation and list any technical/legal terms that needed special handling."
            ),
            variables=["source_language", "target_language", "text"],
        )
        
        # Policy document translation template
        policy_translation_template = PromptTemplate(
            name="policy_translation",
            system_message=(
                "You are an expert translator specializing in insurance policy documents. "
                "Translate policy text while preserving legal meaning and implications. "
                "For legal and technical insurance terms, provide the original term with explanation "
                "rather than potentially inaccurate translations. Maintain the formal tone of legal documents."
            ),
            user_template=(
                "Translate this insurance policy text from {source_language} to {target_language}:\n\n"
                "{text}\n\n"
                "Preserve legal terminology and provide explanations for technical terms. "
                "List all technical/legal terms that were preserved with their explanations."
            ),
            variables=["source_language", "target_language", "text"],
        )
        
        # Medical content translation template
        medical_translation_template = PromptTemplate(
            name="medical_translation",
            system_message=(
                "You are an expert translator specializing in medical content. "
                "Translate medical text accurately while preserving clinical meaning. "
                "For medical terms without direct translations, provide the original term "
                "with a clear explanation in the target language."
            ),
            user_template=(
                "Translate this medical content from {source_language} to {target_language}:\n\n"
                "{text}\n\n"
                "Preserve medical terminology and provide explanations for technical terms. "
                "List all medical terms that needed special handling."
            ),
            variables=["source_language", "target_language", "text"],
        )
        
        # Register templates
        for template in [
            general_translation_template,
            policy_translation_template,
            medical_translation_template,
        ]:
            self.llm_client.register_template(template)
        
        self.logger.info("Translation templates registered")
    
    def is_language_supported(self, language_code: str) -> bool:
        """Check if a language is supported.
        
        Args:
            language_code: ISO language code
            
        Returns:
            True if language is supported
        """
        try:
            SupportedLanguage(language_code)
            return True
        except ValueError:
            return False
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes.
        
        Returns:
            List of ISO language codes
        """
        return [lang.value for lang in SupportedLanguage]
    
    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context_type: str = "general",
    ) -> TranslatedText:
        """Translate text from source to target language.
        
        Args:
            text: Text to translate
            source_language: Source language ISO code
            target_language: Target language ISO code
            context_type: Type of content (general, policy, medical)
            
        Returns:
            Translation result with preserved terminology
            
        Raises:
            ValueError: If language not supported or invalid context type
        """
        # Validate languages
        if not self.is_language_supported(source_language):
            raise ValueError(
                f"Source language '{source_language}' not supported. "
                f"Supported: {self.get_supported_languages()}"
            )
        
        if not self.is_language_supported(target_language):
            raise ValueError(
                f"Target language '{target_language}' not supported. "
                f"Supported: {self.get_supported_languages()}"
            )
        
        # If same language, return as-is
        if source_language == target_language:
            return TranslatedText(
                translated_content=text,
                source_language=source_language,
                target_language=target_language,
                technical_terms=[],
                confidence_score=1.0,
            )
        
        # Select template based on context
        template_map = {
            "general": "general_translation",
            "policy": "policy_translation",
            "medical": "medical_translation",
        }
        
        template_name = template_map.get(context_type)
        if not template_name:
            raise ValueError(
                f"Invalid context_type '{context_type}'. "
                f"Must be one of: {list(template_map.keys())}"
            )
        
        # Get language names for prompt
        source_lang_name = self.LANGUAGE_NAMES[SupportedLanguage(source_language)]
        target_lang_name = self.LANGUAGE_NAMES[SupportedLanguage(target_language)]
        
        self._log_operation(
            "translate",
            source_language=source_language,
            target_language=target_language,
            context_type=context_type,
            text_length=len(text),
        )
        
        try:
            # Generate translation using template
            template = self.llm_client.get_template(template_name)
            system_message, user_message = template.format(
                source_language=source_lang_name,
                target_language=target_lang_name,
                text=text,
            )
            
            response = await self.llm_client.generate(
                prompt=user_message,
                system_message=system_message,
                temperature=0.3,  # Lower temperature for more consistent translation
            )
            
            # Parse response to extract translation and technical terms
            translated_content, technical_terms = self._parse_translation_response(
                response.content
            )
            
            result = TranslatedText(
                translated_content=translated_content,
                source_language=source_language,
                target_language=target_language,
                technical_terms=technical_terms,
                confidence_score=response.confidence_score,
            )
            
            self.logger.info(
                "Translation completed",
                source_language=source_language,
                target_language=target_language,
                technical_terms_count=len(technical_terms),
            )
            
            return result
        
        except Exception as e:
            self._log_error("translate", e)
            raise
    
    async def translate_with_glossary(
        self,
        text: str,
        source_language: str,
        target_language: str,
        glossary: Dict[str, str],
        context_type: str = "general",
    ) -> TranslatedText:
        """Translate text with a custom glossary of terms.
        
        Args:
            text: Text to translate
            source_language: Source language ISO code
            target_language: Target language ISO code
            glossary: Dictionary mapping terms to their translations
            context_type: Type of content (general, policy, medical)
            
        Returns:
            Translation result
        """
        # Build glossary section for prompt
        glossary_text = "\n".join(
            f"- {term}: {translation}"
            for term, translation in glossary.items()
        )
        
        # Get base template
        template_map = {
            "general": "general_translation",
            "policy": "policy_translation",
            "medical": "medical_translation",
        }
        template_name = template_map.get(context_type, "general_translation")
        
        source_lang_name = self.LANGUAGE_NAMES[SupportedLanguage(source_language)]
        target_lang_name = self.LANGUAGE_NAMES[SupportedLanguage(target_language)]
        
        # Create custom prompt with glossary
        template = self.llm_client.get_template(template_name)
        system_message, user_message = template.format(
            source_language=source_lang_name,
            target_language=target_lang_name,
            text=text,
        )
        
        # Add glossary to user message
        user_message_with_glossary = (
            f"{user_message}\n\n"
            f"Use these specific translations for the following terms:\n{glossary_text}"
        )
        
        try:
            response = await self.llm_client.generate(
                prompt=user_message_with_glossary,
                system_message=system_message,
                temperature=0.3,
            )
            
            translated_content, technical_terms = self._parse_translation_response(
                response.content
            )
            
            return TranslatedText(
                translated_content=translated_content,
                source_language=source_language,
                target_language=target_language,
                technical_terms=technical_terms,
                confidence_score=response.confidence_score,
            )
        
        except Exception as e:
            self._log_error("translate_with_glossary", e)
            raise
    
    def identify_technical_terms(self, text: str) -> Set[str]:
        """Identify technical terms in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Set of identified technical terms
        """
        identified_terms = set()
        text_lower = text.lower()
        
        # Check against patterns
        for pattern in self.TECHNICAL_TERM_PATTERNS:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                term = match.group(0).strip()
                identified_terms.add(term)
        
        # Check against glossary keys
        for glossary_term in self.TECHNICAL_GLOSSARY.keys():
            if glossary_term.lower() in text_lower:
                identified_terms.add(glossary_term)
        
        return identified_terms
    
    def get_term_explanation(
        self,
        term: str,
        target_language: str,
    ) -> Optional[str]:
        """Get explanation for a technical term in target language.
        
        Args:
            term: Technical term
            target_language: Target language ISO code
            
        Returns:
            Explanation in target language, or None if not found
        """
        # Normalize term for lookup
        term_lower = term.lower().strip()
        
        # Check glossary
        for glossary_term, explanations in self.TECHNICAL_GLOSSARY.items():
            if glossary_term.lower() == term_lower:
                return explanations.get(target_language)
        
        return None
    
    async def preserve_terminology(
        self,
        text: str,
        target_language: str,
        source_language: str = "en",
    ) -> TranslatedTextWithGlossary:
        """Translate text while preserving technical terminology.
        
        This method identifies technical terms in the source text,
        preserves them in the translation, and provides a glossary
        with explanations in the target language.
        
        Args:
            text: Text to translate
            target_language: Target language ISO code
            source_language: Source language ISO code (default: English)
            
        Returns:
            Translation with comprehensive glossary
            
        Raises:
            ValueError: If language not supported
        """
        # Validate languages
        if not self.is_language_supported(source_language):
            raise ValueError(
                f"Source language '{source_language}' not supported. "
                f"Supported: {self.get_supported_languages()}"
            )
        
        if not self.is_language_supported(target_language):
            raise ValueError(
                f"Target language '{target_language}' not supported. "
                f"Supported: {self.get_supported_languages()}"
            )
        
        # If same language, return as-is with empty glossary
        if source_language == target_language:
            return TranslatedTextWithGlossary(
                translated_content=text,
                source_language=source_language,
                target_language=target_language,
                glossary=[],
                confidence_score=1.0,
            )
        
        self._log_operation(
            "preserve_terminology",
            source_language=source_language,
            target_language=target_language,
            text_length=len(text),
        )
        
        try:
            # Identify technical terms in the text
            identified_terms = self.identify_technical_terms(text)
            
            self.logger.info(
                "Identified technical terms",
                count=len(identified_terms),
                terms=list(identified_terms)[:10],  # Log first 10
            )
            
            # Build glossary with explanations
            glossary: List[TechnicalTerm] = []
            glossary_dict: Dict[str, str] = {}
            
            for term in identified_terms:
                explanation = self.get_term_explanation(term, target_language)
                
                if explanation:
                    # Term has explanation in glossary
                    glossary.append(
                        TechnicalTerm(
                            original_term=term,
                            translated_term=None,  # Keep original
                            explanation=explanation,
                        )
                    )
                    # Use original term in translation
                    glossary_dict[term] = term
                else:
                    # Term not in glossary - will need LLM to handle
                    self.logger.debug(
                        "Term not in glossary, will request LLM explanation",
                        term=term,
                    )
            
            # Get language names for prompt
            source_lang_name = self.LANGUAGE_NAMES[SupportedLanguage(source_language)]
            target_lang_name = self.LANGUAGE_NAMES[SupportedLanguage(target_language)]
            
            # Create specialized prompt for terminology preservation
            system_message = (
                "You are an expert translator specializing in healthcare and insurance content. "
                "Your task is to translate text while PRESERVING technical and medical terms. "
                "For technical terms that have no direct translation, keep the original term "
                "and provide a clear explanation in the target language. "
                "Format your response as:\n"
                "Translation:\n"
                "<translated text with preserved terms>\n\n"
                "Technical Terms:\n"
                "- <term>: <explanation in target language>"
            )
            
            # Build list of terms to preserve
            terms_to_preserve = "\n".join(f"- {term}" for term in identified_terms)
            
            user_message = (
                f"Translate the following text from {source_lang_name} to {target_lang_name}.\n\n"
                f"IMPORTANT: Preserve these technical terms in their original form:\n"
                f"{terms_to_preserve}\n\n"
                f"For each preserved term, provide an explanation in {target_lang_name}.\n\n"
                f"Text to translate:\n{text}\n\n"
                f"Remember: Keep technical terms in their original language and explain them."
            )
            
            response = await self.llm_client.generate(
                prompt=user_message,
                system_message=system_message,
                temperature=0.3,
            )
            
            # Parse response
            translated_content, llm_terms = self._parse_translation_response(
                response.content
            )
            
            # Merge glossary terms with LLM-identified terms
            # LLM might identify additional terms or provide better explanations
            term_map = {term.original_term.lower(): term for term in glossary}
            
            for llm_term in llm_terms:
                term_key = llm_term.original_term.lower()
                if term_key not in term_map:
                    # New term identified by LLM
                    glossary.append(llm_term)
                elif not term_map[term_key].explanation and llm_term.explanation:
                    # LLM provided explanation for term without one
                    term_map[term_key].explanation = llm_term.explanation
            
            result = TranslatedTextWithGlossary(
                translated_content=translated_content,
                source_language=source_language,
                target_language=target_language,
                glossary=glossary,
                confidence_score=response.confidence_score,
            )
            
            self.logger.info(
                "Terminology preservation completed",
                source_language=source_language,
                target_language=target_language,
                glossary_size=len(glossary),
            )
            
            return result
        
        except Exception as e:
            self._log_error("preserve_terminology", e)
            raise
    
    def _parse_translation_response(
        self,
        response: str,
    ) -> tuple[str, List[TechnicalTerm]]:
        """Parse LLM translation response to extract content and terms.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Tuple of (translated_content, technical_terms)
        """
        # Simple parsing: look for sections
        # Expected format:
        # Translation:
        # <translated text>
        #
        # Technical Terms:
        # - term: explanation
        
        lines = response.strip().split('\n')
        translated_lines = []
        technical_terms = []
        
        in_translation = False
        in_technical_terms = False
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check for section headers
            if 'translation:' in line_lower and not in_technical_terms:
                in_translation = True
                continue
            elif 'technical term' in line_lower or 'legal term' in line_lower:
                in_technical_terms = True
                in_translation = False
                continue
            
            # Collect content
            if in_translation and line.strip():
                translated_lines.append(line)
            elif in_technical_terms and line.strip().startswith('-'):
                # Parse technical term
                term_text = line.strip()[1:].strip()  # Remove leading '-'
                if ':' in term_text:
                    term, explanation = term_text.split(':', 1)
                    technical_terms.append(
                        TechnicalTerm(
                            original_term=term.strip(),
                            explanation=explanation.strip(),
                        )
                    )
        
        # If no clear sections found, treat entire response as translation
        if not translated_lines:
            translated_lines = [response]
        
        translated_content = '\n'.join(translated_lines).strip()
        
        return translated_content, technical_terms
    
    async def batch_translate(
        self,
        texts: List[str],
        source_language: str,
        target_language: str,
        context_type: str = "general",
    ) -> List[TranslatedText]:
        """Translate multiple texts in batch.
        
        Args:
            texts: List of texts to translate
            source_language: Source language ISO code
            target_language: Target language ISO code
            context_type: Type of content
            
        Returns:
            List of translation results
        """
        results = []
        
        for text in texts:
            try:
                result = await self.translate(
                    text=text,
                    source_language=source_language,
                    target_language=target_language,
                    context_type=context_type,
                )
                results.append(result)
            except Exception as e:
                self.logger.error(
                    "Batch translation item failed",
                    error=str(e),
                    text_preview=text[:100],
                )
                # Add error result
                results.append(
                    TranslatedText(
                        translated_content=f"[Translation Error: {str(e)}]",
                        source_language=source_language,
                        target_language=target_language,
                        technical_terms=[],
                        confidence_score=0.0,
                    )
                )
        
        return results

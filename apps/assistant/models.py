from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
import uuid
User = get_user_model()


class Assistant(models.Model):
    LANGUAGES_CHOICES = [
        ('af-ZA', 'Afrikaans (South Africa)'),
        ('am-ET', 'Amharic (Ethiopia)'),
        ('ar-AE', 'Arabic (U.A.E.)'),
        ('ar-BH', 'Arabic (Bahrain)'),
        ('ar-DZ', 'Arabic (Algeria)'),
        ('ar-EG', 'Arabic (Egypt)'),
        ('ar-IQ', 'Arabic (Iraq)'),
        ('ar-JO', 'Arabic (Jordan)'),
        ('ar-KW', 'Arabic (Kuwait)'),
        ('ar-LB', 'Arabic (Lebanon)'),
        ('ar-MA', 'Arabic (Morocco)'),
        ('ar-OM', 'Arabic (Oman)'),
        ('ar-QA', 'Arabic (Qatar)'),
        ('ar-SA', 'Arabic (Saudi Arabia)'),
        ('ar-TN', 'Arabic (Tunisia)'),
        ('ar-YE', 'Arabic (Yemen)'),
        ('az-AZ', 'Azerbaijani (Azerbaijan)'),
        ('bg-BG', 'Bulgarian (Bulgaria)'),
        ('bn-BD', 'Bangla (Bangladesh)'),
        ('bn-IN', 'Bangla (India)'),
        ('ca-ES', 'Catalan (Spain)'),
        ('cs-CZ', 'Czech (Czech Republic)'),
        ('da-DK', 'Danish (Denmark)'),
        ('de-DE', 'German (Germany)'),
        ('el-GR', 'Greek (Greece)'),
        ('en-AU', 'English (Australia)'),
        ('en-CA', 'English (Canada)'),
        ('en-GB', 'English (United Kingdom)'),
        ('en-IN', 'English (India)'),
        ('en-IE', 'English (Ireland)'),
        ('en-NZ', 'English (New Zealand)'),
        ('en-PH', 'English (Philippines)'),
        ('en-US', 'English (United States)'),
        ('en-ZA', 'English (South Africa)'),
        ('es-AR', 'Spanish (Argentina)'),
        ('es-BO', 'Spanish (Bolivia)'),
        ('es-CL', 'Spanish (Chile)'),
        ('es-CO', 'Spanish (Colombia)'),
        ('es-CR', 'Spanish (Costa Rica)'),
        ('es-DO', 'Spanish (Dominican Republic)'),
        ('es-EC', 'Spanish (Ecuador)'),
        ('es-ES', 'Spanish (Spain)'),
        ('es-GT', 'Spanish (Guatemala)'),
        ('es-HN', 'Spanish (Honduras)'),
        ('es-MX', 'Spanish (Mexico)'),
        ('es-NI', 'Spanish (Nicaragua)'),
        ('es-PA', 'Spanish (Panama)'),
        ('es-PE', 'Spanish (Peru)'),
        ('es-PR', 'Spanish (Puerto Rico)'),
        ('es-PY', 'Spanish (Paraguay)'),
        ('es-SV', 'Spanish (El Salvador)'),
        ('es-US', 'Spanish (United States)'),
        ('es-UY', 'Spanish (Uruguay)'),
        ('es-VE', 'Spanish (Venezuela)'),
        ('et-EE', 'Estonian (Estonia)'),
        ('eu-ES', 'Basque (Spain)'),
        ('fa-IR', 'Persian (Iran)'),
        ('fi-FI', 'Finnish (Finland)'),
        ('fil-PH', 'Filipino (Philippines)'),
        ('fr-BE', 'French (Belgium)'),
        ('fr-CA', 'French (Canada)'),
        ('fr-CH', 'French (Switzerland)'),
        ('fr-FR', 'French (France)'),
        ('gl-ES', 'Galician (Spain)'),
        ('gu-IN', 'Gujarati (India)'),
        ('he-IL', 'Hebrew (Israel)'),
        ('hi-IN', 'Hindi (India)'),
        ('hr-HR', 'Croatian (Croatia)'),
        ('hu-HU', 'Hungarian (Hungary)'),
        ('id-ID', 'Indonesian (Indonesia)'),
        ('is-IS', 'Icelandic (Iceland)'),
        ('it-CH', 'Italian (Switzerland)'),
        ('it-IT', 'Italian (Italy)'),
        ('ja-JP', 'Japanese (Japan)'),
        ('jv-ID', 'Javanese (Indonesia)'),
        ('kn-IN', 'Kannada (India)'),
        ('kk-KZ', 'Kazakh (Kazakhstan)'),
        ('km-KH', 'Khmer (Cambodia)'),
        ('ko-KR', 'Korean (South Korea)'),
        ('lo-LA', 'Lao (Laos)'),
        ('lt-LT', 'Lithuanian (Lithuania)'),
        ('lv-LV', 'Latvian (Latvia)'),
        ('mk-MK', 'Macedonian (North Macedonia)'),
        ('ml-IN', 'Malayalam (India)'),
        ('mn-MN', 'Mongolian (Mongolia)'),
        ('mr-IN', 'Marathi (India)'),
        ('ms-MY', 'Malay (Malaysia)'),
        ('my-MM', 'Myanmar (Burmese)'),
        ('ne-NP', 'Nepali (Nepal)'),
        ('nl-BE', 'Dutch (Belgium)'),
        ('nl-NL', 'Dutch (Netherlands)'),
        ('no-NO', 'Norwegian (Norway)'),
        ('pa-IN', 'Punjabi (India)'),
        ('pl-PL', 'Polish (Poland)'),
        ('pt-BR', 'Portuguese (Brazil)'),
        ('pt-PT', 'Portuguese (Portugal)'),
        ('ro-RO', 'Romanian (Romania)'),
        ('ru-RU', 'Russian (Russia)'),
        ('si-LK', 'Sinhala (Sri Lanka)'),
        ('sk-SK', 'Slovak (Slovakia)'),
        ('sl-SI', 'Slovenian (Slovenia)'),
        ('sr-RS', 'Serbian (Serbia)'),
        ('su-ID', 'Sundanese (Indonesia)'),
        ('sv-SE', 'Swedish (Sweden)'),
        ('sw-KE', 'Swahili (Kenya)'),
        ('ta-IN', 'Tamil (India)'),
        ('ta-LK', 'Tamil (Sri Lanka)'),
        ('te-IN', 'Telugu (India)'),
        ('th-TH', 'Thai (Thailand)'),
        ('tr-TR', 'Turkish (Turkey)'),
        ('uk-UA', 'Ukrainian (Ukraine)'),
        ('ur-PK', 'Urdu (Pakistan)'),
        ('uz-UZ', 'Uzbek (Uzbekistan)'),
        ('vi-VN', 'Vietnamese (Vietnam)'),
        ('zu-ZA', 'Zulu (South Africa)'),
        ('zh-CN', 'Chinese (Simplified, China)'),
        ('zh-HK', 'Chinese (Traditional, Hong Kong)'),
        ('zh-TW', 'Chinese (Traditional, Taiwan)'),
    ]
    MESSAGE_MODE = [
        ("assistant speaks first", "Assistant Speaks First"),
        ("assistant wait for user", "Assistant Waits for User"),
        ('assistant speaks first with model generated message', "Assistant Speaks First with Model Generated Message"),
    ]
    MODEL = [
        ('gpt-5-turbo', 'GPT-5 Turbo'),
        ("gpt-4", "GPT-4"),
        ("gpt-4o-mini", "GPT-4O Mini"),
        ("gpt-4o-turbo", "GPT-4O Turbo"),
        ("gpt-4o-32k", "GPT-4O 32K"),
        ("gpt-3.5-turbo", "GPT-3.5 Turbo"),
        ("gpt-3.5-turbo-16k", "GPT-3.5 Turbo 16K"),
        ("gpt-3.5-turbo-16k-0613", "GPT-3.5 Turbo 16K 0613"),
        ("gpt-3.5-turbo-0613", "GPT-3.5 Turbo 0613"),
        ("gpt-3.5-turbo-instruct", "GPT-3.5 Turbo Instruct"),
    ]


    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assistants")
    name = models.CharField(max_length=100)
    first_message_mode = models.CharField(max_length=100, choices=MESSAGE_MODE, default="assistant speaks first")
    first_message = models.TextField(blank=True, default="")
    system_prompt = models.TextField(blank=True, default="")
    voice = models.CharField(max_length=100, default="bn-BD-NabanitaNeural")
    language = models.CharField(max_length=10, default="bn", choices=LANGUAGES_CHOICES)
    enabled = models.BooleanField(default=False)
    model = models.CharField(max_length=100, choices=MODEL, default="gpt-4o-mini")
    max_tokens = models.IntegerField(default=250)
    temperature = models.FloatField(default=0.7)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    theme_primary = models.CharField(max_length=20, default="#16a34a")
    
    # Twillo number for call handling
    twilio_number = models.CharField(max_length=100, blank=True, default="")

    # Optional fields
    crisis_keywords = models.TextField(blank=True, default="")
    crisis_keywords_prompt = models.TextField(blank=True, default="")
    description = models.TextField(blank=True, default="")
    avatar_url = models.URLField(blank=True, null=True)
    config = models.JSONField(default=dict, blank=True)

    #widgets 
    embed_html = models.TextField(blank=True, null=True)
    
    #ElevenLabs agent id
    eleven_agent_id = models.CharField(max_length=100, blank=True, null=True)
    
    #agent type for call and chat
    agent_type = models.CharField(max_length=100, choices=(("chat", "Chat"), ("call", "Call")), default="chat")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "updated_at"]),
        ]
        unique_together = ("owner", "name", "language", "voice")

    def __str__(self):
        return f"{self.name}"
    
    
class AssistantFile(models.Model):
    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="assistants/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.assistant.name}"
    


class Transcript(models.Model):
    
    ENDED_REASON_CHOICES= (
        ('Customer ended call', 'Customer ended call'),
        ('Assistant ended call', 'Assistant ended call'),
        ('Assistand did not receive', 'Assistant did not receive'),
    )
    TYPE_CHOICES = (
        ('chat', 'Chat'),
        ('voice', 'Voice'),
        ('web', 'Web'),
        ('call', 'Call'),
    )
    call_id = models.CharField(max_length=100, null=True, blank=True, default=None)
    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE, related_name="transcripts")
    ended_reason = models.CharField(max_length=100, choices=ENDED_REASON_CHOICES, default="user")
    type = models.CharField(max_length=100, choices=TYPE_CHOICES, default="chat")
    successs_evalation = models.BooleanField(default=False)
    score = models.IntegerField( null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True, default=None)
    end_time = models.DateTimeField(null=True, blank=True, default=None)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None)


    @property
    def duration(self):
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return None
    
    def save(self, *args, **kwargs):
        if self.cost in ["", "None"]:
            self.cost = None
        if not self.call_id:
            self.call_id = str(uuid.uuid4()) 
            self.save()
        else:
            return super().save(*args, **kwargs)

class TranscriptChunk(models.Model):
    SENDER_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('admin', 'Admin'),
        ('bot', 'Bot'),
        ('system', 'System'),
        ('error', 'Error'),
        ('unknown', 'Unknown'),
    )

    transcript = models.ForeignKey(Transcript, on_delete=models.CASCADE, related_name="chunks")
    sender = models.CharField(max_length=100, choices=SENDER_CHOICES)
    text = models.TextField()
    chunk = models.BinaryField(blank=True, null=True)
    audio = models.FileField(upload_to="transcripts/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AssistantMamory(models.Model):
    assistant = models.OneToOneField(Assistant, on_delete=models.CASCADE, related_name="bot_memory")
    memory = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)
    
    
class AssistantHistory(models.Model):
    assistant = models.ForeignKey("Assistant", on_delete=models.CASCADE, related_name="history")
    changed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    # full snapshot (optional but useful)
    old_data = models.JSONField(default=dict, blank=True)
    new_data = models.JSONField(default=dict, blank=True)

    # only changed fields (diff)
    diff = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"History({self.assistant_id}) at {self.created_at}"




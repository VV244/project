"""Idempotent seed: creates missing records and never overwrites editorial changes."""
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import SiteSettings, FAQ, ContentPage
from poems.models import Language, ClassLevel, Category, Poem

LANGUAGES = [
    ('English', 'English', 'en', 'english'), ('Hindi', 'हिन्दी', 'hi', 'hindi'),
    ('Marathi', 'मराठी', 'mr', 'marathi'), ('Gujarati', 'ગુજરાતી', 'gu', 'gujarati'),
    ('Tamil', 'தமிழ்', 'ta', 'tamil'), ('Telugu', 'తెలుగు', 'te', 'telugu'),
    ('Kannada', 'ಕನ್ನಡ', 'kn', 'kannada'), ('Malayalam', 'മലയാളം', 'ml', 'malayalam'),
    ('Bengali', 'বাংলা', 'bn', 'bengali'), ('Punjabi', 'ਪੰਜਾਬੀ', 'pa', 'punjabi'),
    ('Odia', 'ଓଡ଼ିଆ', 'or', 'odia'), ('Assamese', 'অসমীয়া', 'as', 'assamese'),
    ('Urdu', 'اردو', 'ur', 'urdu'),
]
CLASSES = [
    ('Junior KG', 'junior-kg', 'First little words, playful sounds, and simple rhymes for curious beginners.'),
    ('Senior KG', 'senior-kg', 'Build confidence with cheerful repetition, little actions, and new words.'),
    ('Class 1', 'class-1', 'Discover short stories in verse and practice reading together.'),
    ('Class 2', 'class-2', 'Explore descriptive words, rhythm, and the world around us.'),
    ('Class 3', 'class-3', 'Find new ideas and expressive language through thoughtful little poems.'),
    ('Class 4', 'class-4', 'Grow imagination and independent reading with playful poetry.'),
]
CATEGORIES = [
    ('Nursery Rhymes', 'nursery-rhymes', 'Simple sounds and a happy rhythm.'),
    ('Alphabet Poems', 'alphabet-poems', 'A playful introduction to letters and sounds.'),
    ('Number Poems', 'number-poems', 'Count the little wonders around you.'),
    ('Animal Poems', 'animal-poems', 'Meet our feathered and furry friends.'),
    ('Nature Poems', 'nature-poems', 'Flowers, trees, sunshine, and the sky.'),
    ('Festival Poems', 'festival-poems', 'Celebrate together with joyful words.'),
    ('Patriotic Poems', 'patriotic-poems', 'Explore belonging, kindness, and care for our home.'),
    ('Educational Poems', 'educational-poems', 'Learn a little something with every verse.'),
    ('Moral Poems', 'moral-poems', 'Small lessons in kindness and friendship.'),
    ('Funny Poems', 'funny-poems', 'A little rhyme and a little giggle.'),
    ('Action Rhymes', 'action-rhymes', 'Clap, tap, move, and join in.'),
    ('Bedtime Poems', 'bedtime-poems', 'Quiet words for a gentle goodnight.'),
    ('Seasonal Poems', 'seasonal-poems', 'Discover the changing seasons.'),
]
# All texts below were composed for this application; no existing modern rhymes are reproduced.
POEMS = [
    ('pocketful-of-sunshine', 'A Pocketful of Sunshine', 'en', [0, 1], ['nature-poems', 'nursery-rhymes'], 'garden', 'A small seed, a little sunshine, and a very big hello.', 'I put a little seed to bed,\nWith soft brown earth above its head.\nThe sun said, “Wake! The sky is blue!”\nA tiny leaf said, “Hello, you!”'),
    ('nanha-suraj', 'नन्हा सूरज', 'hi', [0, 1, 2], ['nature-poems', 'nursery-rhymes'], 'garden', 'सुबह की धूप के साथ एक प्यारी शुरुआत।', 'नन्हा सूरज आया है,\nसंग उजाला लाया है।\nफूलों ने मुस्काकर बोला,\nनया सवेरा छाया है।'),
    ('chhotase-beej', 'छोटंसं बीज', 'mr', [0, 1, 2], ['nature-poems', 'nursery-rhymes'], 'garden', 'छोट्या बीजात दडलेली मोठी गंमत.', 'छोटंसं बीज मातीत झोपलं,\nपावसाचं गाणं ऐकून उठलं।\nहिरवं पान हळूच हसलं,\nसूर्याला पाहून डोलू लागलं।'),
    ('little-moon-lantern', 'The Moon’s Little Lantern', 'en', [1, 2], ['bedtime-poems', 'nature-poems'], 'night', 'A gentle goodnight beneath a sky full of possibilities.', 'The moon hangs up a lantern light,\nTo guide the sleepy clouds tonight.\nI tuck my busy thoughts away,\nAnd save my dreams for one more day.'),
    ('puddle-parade', 'The Puddle Parade', 'en', [2, 3], ['seasonal-poems', 'action-rhymes'], 'rain', 'Pull on your boots and join a splashy little adventure.', 'My boots have found a silver street,\nWhere little puddles kiss my feet.\nI tap, I hop, I splash, I spin,\nThe rainy-day parade begins!'),
    ('one-two-little-wonders', 'One, Two, Little Wonders', 'en', [0, 1, 2], ['number-poems', 'educational-poems'], 'numbers', 'Count tiny treasures, from a bright sun to fluttering bees.', 'One warm sun above a tree,\nTwo small birds that sing to me.\nThree bright leaves go dancing by,\nFour soft clouds sail through the sky.'),
    ('a-book-for-everywhere', 'A Book for Everywhere', 'en', [4, 5], ['educational-poems', 'moral-poems'], 'books', 'A story can take you somewhere new without leaving your chair.', 'A book can be a paper boat,\nWhere all my wondering questions float.\nI share a page, you share a smile,\nWe travel worlds and rest a while.'),
    ('tiny-wings-brave-things', 'Tiny Wings, Brave Things', 'en', [3, 4, 5], ['animal-poems', 'moral-poems'], 'bird', 'Sometimes a very small step is the start of something wonderful.', 'A little bird upon the wall,\nSaid, “I can try, although I’m small.”\nOne flutter first, then off it flew,\nThe world had room for something new.'),
    ('barish-ki-boonden', 'बारिश की बूँदें', 'hi', [1, 2, 3], ['seasonal-poems', 'action-rhymes'], 'rain', 'टप-टप बूँदों के संग गुनगुनाएँ।', 'टप-टप बूँदें आई हैं,\nठंडी हवा भी लाई हैं।\nपत्ते धोकर चमक रहे,\nबादल गीत सुनाते हैं।'),
    ('nanhi-chidiya-ka-geet', 'नन्ही चिड़िया का गीत', 'hi', [2, 3, 4], ['animal-poems', 'nature-poems'], 'bird', 'एक छोटी चिड़िया और खुशियों से भरा आँगन।', 'नन्ही चिड़िया डाल पे आई,\nसाथ सुनहरी धूप भी लाई।\nमीठे सुर में गाना गाकर,\nआँगन की रौनक बढ़ाई।'),
    ('meri-kitab-nayi-duniya', 'मेरी किताब, नई दुनिया', 'hi', [4, 5], ['educational-poems', 'alphabet-poems'], 'books', 'हर पन्ने के साथ एक नया सवाल और नई उड़ान।', 'मेरी किताब खुल जाती है,\nनई कहानी लाती है।\nअक्षर-अक्षर जोड़ूँ जब मैं,\nनई राह मिल जाती है।'),
    ('paus-ala', 'पाऊस आला', 'mr', [1, 2, 3], ['seasonal-poems', 'action-rhymes'], 'rain', 'थेंबांच्या तालावर एक छोटीशी कविता.', 'पाऊस आला, पाऊस आला,\nथंड वारा सोबत आला।\nपानांवरती थेंब नाचले,\nझाडांचे मग गाल हसले।'),
    ('maze-pustak', 'माझे पुस्तक', 'mr', [3, 4, 5], ['educational-poems', 'alphabet-poems'], 'books', 'पुस्तक उघडा आणि कल्पनेच्या सफरीला चला.', 'माझे पुस्तक रंगीत आहे,\nप्रत्येक पानावर गोष्ट नवी आहे।\nअक्षरांची मैत्री जुळते,\nवाचताना दुनिया खुलते।'),
    ('tare-luklukati', 'तारे लुकलुकती', 'mr', [0, 1, 2], ['bedtime-poems', 'nature-poems'], 'night', 'शांत रात्रीसाठी आकाशातील एक छोटी गोष्ट.', 'तारे लुकलुकती आभाळात,\nचंद्र हसतो शांत रात्रीत।\nडोळे मिटून स्वप्न पाहू,\nउद्या पुन्हा खेळत राहू।'),
    ('nanha-sitara', 'ننھا ستارہ', 'ur', [1, 2, 3], ['bedtime-poems', 'nature-poems'], 'night', 'A little star and a gentle wish. An original Urdu demonstration.', 'ننھا تارا چمکے رات،\nچاند سنائے میٹھی بات۔\nآنکھیں موندوں، خواب سجاؤں،\nصبح اٹھوں تو گیت سناؤں۔'),
    ('mera-pyara-bagh', 'میرا پیارا باغ', 'ur', [3, 4, 5], ['nature-poems', 'educational-poems'], 'garden', 'A colorful little garden. Read in Urdu from right to left.', 'میرے باغ میں پھول کھلے،\nرنگ برنگے دوست ملے۔\nتتلی آئی، گیت سنایا،\nسب نے مل کر دن مہکایا۔'),
]

PAGES = {
    'about': ('Our little story', 'A small space for poems. A big space for imagination.', 'Little Rhymes brings children, parents, and teachers together through the joy of poetry. Our library is arranged by class, language, and topic, so you can choose a comfortable starting point.\n\nWe celebrate the many languages spoken across India. A poem’s language is chosen separately from the website interface, and every language deserves its own voice.\n\nOur demonstration library uses original verses and illustrations created for this project. We encourage adults to read together, explore unfamiliar words, and adapt activities to each child. Demonstration class assignments are editorial suggestions, not a school-board syllabus.\n\nNo child account is needed. There are no public comments, direct messages, behavioral advertisements, or child profiles.'),
    'resources': ('Big ideas for little learners', 'Simple activities for parents, teachers, and happy reading circles.', 'Start with five happy minutes\nChoose a short poem in a familiar language. Read it once slowly, then invite your child to join in with a sound, an action, or a favorite word.\n\nClap the rhythm\nTap gently on your knees or clap with the words. Ask which words sound alike. There is no need to get everything right: listening and enjoying are the first steps.\n\nDraw a little story\nAfter reading, draw a character, a flower, or a scene from the poem. Invite your child to describe their picture in any language they feel comfortable using.\n\nMake a classroom circle\nRead one line, then let the group repeat it. Offer movement and quiet participation as equal choices. Use the print button on a poem page for an easy reading handout.\n\nGrow the challenge\nFor Classes 3 and 4, ask learners to find a new word, explain a picture in the poem, or write two original lines. Choose a shorter activity whenever it helps.\n\nExplore safely\nPreview external videos before showing them. Browser voices depend on the device and may use a device provider’s service. A shared reading voice is always welcome.'),
    'privacy': ('A safe little space', 'A parent-facing explanation of privacy on Little Rhymes.', 'Children can browse without an account. We do not provide child profiles, public comments, direct messages, behavioral advertising, or third-party analytics. Please do not send us children’s names, photos, school details, or other personal information.\n\nFavorites are stored in this browser’s local storage, with up to 100 poem IDs. They are not attached to an account and do not sync across devices. When you open your collection, the service receives the selected poem IDs to load those public poems. Clearing browser storage removes the collection.\n\nThe contact form is for adults. It collects the adult’s name, email, subject, and message only to respond and handle content concerns. Authorized staff can review these messages. We aim to delete resolved messages after 90 days; the operator must run the documented retention job. Unresolved rights requests may be kept until resolved.\n\nDjango uses essential cookies for form security, interface language, and staff sign-in. Infrastructure providers may process request metadata such as IP addresses. Form rate limits keep a keyed, non-reversible address identifier in the cache for up to 15 minutes. Staff login protection stores failed login records; the operator must run its documented cleanup job.\n\nYouTube players load only after you press Load video. This connects to YouTube’s privacy-enhanced domain, which can still process data and show recommendations. Direct external video and media files connect to the configured hosting provider when requested. Grown-ups should preview and supervise all external videos.\n\nOptional read-aloud uses your browser or device’s speech provider. Availability, pronunciation, and network processing depend on its installed voices and settings. No microphone permission is requested.\n\nFonts, interface files, and illustrations are served locally. We do not load Google Fonts or advertising scripts in visitors’ browsers.\n\nAdults can use Contact Us for access, correction, deletion, or privacy questions. The production operator must publish its real name, contact information, hosting providers, and applicable local privacy terms before launch.'),
    'terms': ('A few friendly ground rules', 'Please explore respectfully and with a grown-up when needed.', 'Little Rhymes is an educational reading library for children with support from parents, guardians, and educators. Class recommendations are suggestions and may differ from individual school curricula.\n\nYou may read and print content according to the content-specific rights statement on each poem. The original demonstration poems and vector illustrations are offered under CC0 1.0. Added content may have different licenses; check its credits before reusing it.\n\nPlease do not misuse the contact form, attempt unauthorized admin access, upload harmful files, or interfere with the service. Only authorized staff may publish or change content.\n\nExternal videos and optional device voices are controlled by their providers. Availability, accuracy, and recommendations can change. Adult supervision is recommended.\n\nWe work to keep the service useful and available, but educational resources are supplied without a guarantee of uninterrupted access or fitness for every learning need. Nothing here overrides rights granted by applicable law.\n\nBefore public launch, the operator must add its identity, governing terms, and contact information, and review these terms for its jurisdiction.'),
    'copyright': ('Content credits & removal', 'Respect for creators belongs in every little library.', 'We publish only original, public-domain, or properly licensed material. Administrators must record the source and permissions for text, illustrations, audio, and video, and confirm those rights before publishing. We do not automatically translate copyrighted poems.\n\nThe demonstration poems and SVG illustrations were created for this project and are offered under CC0 1.0. Third-party fonts and Bootstrap remain under their respective licenses, included in THIRD_PARTY_NOTICES.md and static/vendor/licenses. The bundled English sample recording is synthetic speech made with Flite and is explicitly credited on its poem.\n\nIf you own rights to material displayed here, use Contact Us and include the exact poem URL, identification of the protected work, your relationship to the rights holder, and your preferred contact email. Please explain what should be corrected or removed. Do not include children’s personal information.\n\nAuthorized staff can unpublish content while a request is reviewed. We will assess credible concerns and remove, correct, or appropriately attribute material where necessary. The operator must maintain an active contact process and review new submissions before publication.'),
}

FAQS = [
    ('Is Little Rhymes free to explore?', 'The demonstration library is free to read. Children do not need an account, and there are no advertisements.'),
    ('How do I choose the right poem?', 'Start with your child’s class, a familiar language, and a topic they enjoy. Class recommendations are suggestions; choose what feels comfortable.'),
    ('Can we listen to every poem?', 'Uploaded recordings appear in the audio player. Where no recording exists, read-aloud may be available if your device has a voice for the poem’s language.'),
    ('Where are my favorite poems saved?', 'Your collection stays in this browser’s local storage. It does not sync across devices. Clearing browser data removes it.'),
    ('Can teachers print the poems?', 'Use Print poem on a detail page. Check the content credits for reuse permissions. Original demonstration verses and illustrations are offered under CC0 1.0.'),
    ('Can I add another language?', 'Authorized administrators can create a language, set its native name, BCP 47 code and text direction, then assign poems to it. No application code changes are needed.'),
    ('Why are some language pages empty?', 'The demo registers regional languages so the library can grow. English, Hindi, Marathi and Urdu have original sample poems; administrators can add licensed content to every language.'),
    ('Does changing the website language translate poems?', 'No. Interface labels and poem content are independent. Only available interface translations change; a poem remains in the language its editor selected.'),
]

class Command(BaseCommand):
    help = 'Create missing demonstration content. Existing editorial changes are preserved.'

    @transaction.atomic
    def handle(self, *args, **options):
        languages = {}
        for name, native, code, slug in LANGUAGES:
            languages[code], _ = Language.objects.get_or_create(code=code, defaults={'name': name, 'native_name': native, 'slug': slug, 'text_direction': 'rtl' if code == 'ur' else 'ltr'})
        classes = []
        for order, (name, slug, description) in enumerate(CLASSES):
            level, _ = ClassLevel.objects.get_or_create(slug=slug, defaults={'name': name, 'description': description, 'display_order': order})
            classes.append(level)
        categories = {}
        for name, slug, description in CATEGORIES:
            categories[slug], _ = Category.objects.get_or_create(slug=slug, defaults={'name': name, 'description': description})
        created = 0
        for index, (slug, title, code, levels, tags, illustration, description, text) in enumerate(POEMS):
            poem, new = Poem.objects.get_or_create(slug=slug, defaults={
                'title': title, 'language': languages[code], 'poem_text': text,
                'author': 'Little Rhymes · original demonstration', 'illustration': illustration,
                'short_description': description, 'keywords': f'{illustration} {languages[code].name} children learning',
                'status': 'published', 'published_at': timezone.now() - timedelta(hours=index),
                'is_featured': index in (3, 5, 12), 'home_priority': 100-index if index < 3 else 0, 'rights_confirmed': True,
                'rights_statement': 'Original demonstration verse and original SVG illustration created for this project. CC0 1.0. No existing copyrighted poem has been copied.',
            })
            if new:
                poem.classes.set(classes[i] for i in levels)
                poem.categories.set(categories[tag] for tag in tags)
                audio = Path(settings.BASE_DIR) / 'demo_assets' / 'pocketful-of-sunshine.mp3'
                if index == 0 and audio.exists():
                    with audio.open('rb') as source:
                        poem.audio_file.save(audio.name, File(source), save=False)
                    poem.rights_statement += ' Synthetic English narration generated with Flite (CMU US SLT voice); third-party speech-engine notices are included in the project.'
                    poem.save()
                created += 1
        SiteSettings.objects.get_or_create(pk=1)
        for slug, (title, introduction, body) in PAGES.items():
            ContentPage.objects.get_or_create(slug=slug, defaults={'title': title, 'introduction': introduction, 'body': body})
        for order, (question, answer) in enumerate(FAQS):
            FAQ.objects.get_or_create(question=question, defaults={'answer': answer, 'display_order': order})
        self.stdout.write(self.style.SUCCESS(f'Created {created} poems. Library has {Poem.objects.count()} poems, {Language.objects.count()} languages and {ClassLevel.objects.count()} classes. Existing content was preserved.'))

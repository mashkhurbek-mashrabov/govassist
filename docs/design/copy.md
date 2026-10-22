# UI copy (uz-Latn + en)

Source of the `uz-Latn.json` and `en.json` locale files. The frontend lane adds `ru` and generates `uz-Cyrl` (see `03-frontend-plan.md` §7).

- Tone: friendly, short, second person (*siz*), no bureaucratic phrasing.
- Uzbek Latin uses **ʻ (U+02BB)** in *oʻ gʻ* and **ʼ (U+02BC)** for the tutuq belgisi (*maʼlumot*). Never a plain `'` or a backtick.
- `{name}` is an ICU-style placeholder. `max` is the uz-Latn length budget in characters; layouts are tested with ru strings ~40% longer (`prototype/type.html`).
- Language names are always written in their own language and script.
- Dates show as `DD.MM.YYYY`; times as `HH:MM` (Asia/Tashkent).

## app

| key | uz-Latn | en | max |
|---|---|---|---|
| `app.name` | GovAssist | GovAssist | 20 |
| `app.not_official` | Rasmiy davlat xizmati emas | Not an official government service | 50 |
| `app.not_official_long` | GovAssist — mustaqil talaba loyihasi, rasmiy davlat xizmati emas. | GovAssist is an independent student project, not an official government service. | 110 |
| `app.disclaimer` | Bu umumiy maʼlumot, yuridik maslahat emas. Rasmiy manbani tekshiring. | This is general information, not legal advice. Check the official source. | 120 |
| `app.may_be_wrong` | Javoblarda xato boʻlishi mumkin. | Answers can contain mistakes. | 60 |
| `app.skip_to_main` | Asosiy qismga oʻtish | Skip to main content | 40 |
| `app.about` | Loyiha haqida | About | 24 |

## common

| key | uz-Latn | en | max |
|---|---|---|---|
| `common.continue` | Davom etish | Continue | 24 |
| `common.back` | Orqaga | Back | 16 |
| `common.next` | Keyingi | Next | 16 |
| `common.cancel` | Bekor qilish | Cancel | 20 |
| `common.save` | Saqlash | Save | 16 |
| `common.saving` | Saqlanmoqda… | Saving… | 20 |
| `common.saved` | Saqlandi | Saved | 16 |
| `common.retry` | Qayta urinish | Try again | 20 |
| `common.close` | Yopish | Close | 16 |
| `common.loading` | Yuklanmoqda… | Loading… | 20 |
| `common.opens_new_tab` | (yangi oynada ochiladi) | (opens in a new tab) | 40 |
| `common.or` | yoki | or | 8 |
| `common.today` | Bugun | Today | 12 |
| `common.yesterday` | Kecha | Yesterday | 12 |

## lang

| key | uz-Latn | en | max |
|---|---|---|---|
| `lang.label` | Til | Language | 16 |
| `lang.menu_label` | Tilni tanlash | Choose language | 24 |
| `lang.switched` | Til oʻzgartirildi | Language changed | 30 |
| `lang.hint_latin` | Lotin yozuvi | Latin script | 20 |
| `lang.hint_cyrillic` | Кирилл ёзуви | Cyrillic script | 20 |
| `lang.name.uz-Latn` | Oʻzbekcha | Oʻzbekcha | 16 |
| `lang.name.uz-Cyrl` | Ўзбекча | Ўзбекча | 16 |
| `lang.name.ru` | Русский | Русский | 16 |
| `lang.name.en` | English | English | 16 |
| `lang.uz-Latn` | Oʻzbekcha (lotin) | Oʻzbekcha (lotin) | 24 |
| `lang.uz-Cyrl` | Ўзбекча (кирилл) | Ўзбекча (кирилл) | 24 |
| `lang.ru` | Русский | Русский | 16 |
| `lang.en` | English | English | 16 |

## auth

| key | uz-Latn | en | max |
|---|---|---|---|
| `auth.email` | Elektron pochta | Email | 24 |
| `auth.email_placeholder` | siz@example.com | you@example.com | 30 |
| `auth.password` | Parol | Password | 16 |
| `auth.password_hint` | Kamida 10 ta belgi. Harf, raqam va belgilarni aralashtiring. | At least 10 characters. Mix letters, numbers and symbols. | 90 |
| `auth.password_show` | Parolni koʻrsatish | Show password | 30 |
| `auth.password_hide` | Parolni yashirish | Hide password | 30 |
| `auth.strength_label` | Parol kuchi: | Password strength: | 24 |
| `auth.strength_weak` | kuchsiz | weak | 12 |
| `auth.strength_fair` | oʻrtacha | fair | 12 |
| `auth.strength_strong` | kuchli | strong | 12 |
| `auth.google` | Google orqali davom etish | Continue with Google | 36 |
| `auth.turnstile_note` | Robot emasligingizni tekshiramiz (Cloudflare Turnstile). | We check that you are not a robot (Cloudflare Turnstile). | 70 |
| `auth.privacy_note` | Savollaringizdagi shaxsiy maʼlumotlar (pasport raqami, JShShIR, telefon, email) saqlashdan oldin olib tashlanadi. | Personal data in your questions (passport number, PINFL, phone, email) is removed before anything is stored. | 160 |
| `auth.privacy_link` | Maxfiylik haqida | About privacy | 30 |

## signup

| key | uz-Latn | en | max |
|---|---|---|---|
| `signup.title` | Roʻyxatdan oʻting | Create your account | 40 |
| `signup.lead` | Savol berish uchun hisob kerak. Bu bir daqiqa oladi. | You need an account to ask questions. It takes a minute. | 90 |
| `signup.submit` | Hisob yaratish | Create account | 24 |
| `signup.submitting` | Hisob yaratilmoqda… | Creating account… | 30 |
| `signup.have_account` | Hisobingiz bormi? | Already have an account? | 30 |
| `signup.login_link` | Kirish | Log in | 16 |

## login

| key | uz-Latn | en | max |
|---|---|---|---|
| `login.title` | Hisobingizga kiring | Log in to your account | 40 |
| `login.lead` | Xush kelibsiz! | Welcome back. | 40 |
| `login.submit` | Kirish | Log in | 16 |
| `login.submitting` | Kirilmoqda… | Logging in… | 20 |
| `login.forgot` | Parolni unutdingizmi? | Forgot password? | 30 |
| `login.no_account` | Hisobingiz yoʻqmi? | No account yet? | 30 |
| `login.signup_link` | Roʻyxatdan oʻting | Sign up | 24 |

## error

| key | uz-Latn | en | max |
|---|---|---|---|
| `error.form_summary` | Formada xatolar bor. Quyida tuzating. | There are problems in the form. Fix them below. | 70 |
| `error.required` | Bu maydonni toʻldiring. | Fill in this field. | 40 |
| `error.email_invalid` | Toʻgʻri elektron pochta kiriting, masalan siz@example.com. | Enter a valid email, for example you@example.com. | 90 |
| `error.email_taken` | Bu elektron pochta bilan hisob allaqachon bor. Kiring yoki parolni tiklang. | An account with this email already exists. Log in or reset your password. | 110 |
| `error.password_short` | Parol kamida 10 ta belgidan iborat boʻlsin. | Password must be at least 10 characters. | 60 |
| `error.password_common` | Bu parol juda oddiy. Boshqasini tanlang. | This password is too common. Choose another one. | 60 |
| `error.turnstile` | Tekshiruvdan oʻtmadi. Qayta urinib koʻring. | The check did not pass. Please try again. | 60 |
| `error.password_numeric` | Parol faqat raqamlardan iborat boʻlmasin. | Your password can’t be only numbers. | 60 |
| `error.password_similar` | Parol elektron pochtangizga juda oʻxshash. Boshqasini tanlang. | Your password is too similar to your email. Choose another one. | 80 |
| `error.too_many_logins` | Juda koʻp urinish boʻldi. Birozdan soʻng qayta kiring. | Too many attempts. Please try logging in again later. | 70 |
| `error.server` | Nimadir xato ketdi. Birozdan soʻng qayta urinib koʻring. | Something went wrong. Please try again in a moment. | 80 |
| `error.login_failed` | Elektron pochta yoki parol notoʻgʻri. | The email or password is incorrect. | 60 |
| `error.social` | Google orqali kirib boʻlmadi. Qayta urinib koʻring yoki elektron pochta bilan kiring. | We could not log you in with Google. Try again or use your email. | 110 |
| `error.current_password_wrong` | Joriy parol notoʻgʻri. | The current password is incorrect. | 50 |

## check_email

| key | uz-Latn | en | max |
|---|---|---|---|
| `check_email.title` | Pochtangizni tekshiring | Check your email | 40 |
| `check_email.lead` | {email} manziliga havola yubordik. Hisobni tasdiqlash uchun uni oching. | We sent a link to {email}. Open it to confirm your account. | 110 |
| `check_email.spam` | Xat kelmadimi? “Spam” jildini tekshiring. | No email? Check your spam folder. | 60 |
| `check_email.resend` | Havolani qayta yuborish | Send the link again | 30 |
| `check_email.resent` | Havola qayta yuborildi. | We sent the link again. | 40 |
| `check_email.rate_limited` | Juda koʻp urinish. {minutes} daqiqadan soʻng qayta urinib koʻring. | Too many attempts. Try again in {minutes} min. | 80 |
| `check_email.change` | Boshqa elektron pochtadan foydalanish | Use a different email | 40 |

## verify

| key | uz-Latn | en | max |
|---|---|---|---|
| `verify.verifying` | Elektron pochtangiz tasdiqlanmoqda… | Confirming your email… | 50 |
| `verify.success_title` | Elektron pochta tasdiqlandi | Email confirmed | 40 |
| `verify.success_lead` | Endi hududingizni tanlang, shunda kerakli idorani koʻrsata olamiz. | Next, choose where you live so we can show the right office. | 110 |
| `verify.invalid_title` | Havola yaroqsiz yoki muddati oʻtgan | This link is invalid or has expired | 50 |
| `verify.invalid_lead` | Elektron pochtangizni kiriting, yangi havola yuboramiz. | Enter your email and we will send you a new link. | 70 |
| `verify.request_new` | Yangi havola yuborish | Send a new link | 30 |

## forgot

| key | uz-Latn | en | max |
|---|---|---|---|
| `forgot.title` | Parolni tiklash | Reset your password | 30 |
| `forgot.lead` | Elektron pochtangizni kiriting. Parolni tiklash havolasini yuboramiz. | Enter your email and we will send you a reset link. | 90 |
| `forgot.submit` | Havolani yuborish | Send reset link | 24 |
| `forgot.sent` | Agar bu manzil bilan hisob boʻlsa, havola yubordik. Pochtangizni tekshiring. | If an account exists for this email, we sent a link. Check your inbox. | 100 |
| `forgot.back_to_login` | Kirish sahifasiga qaytish | Back to log in | 30 |

## reset

| key | uz-Latn | en | max |
|---|---|---|---|
| `reset.title` | Yangi parol oʻrnating | Set a new password | 30 |
| `reset.new_password` | Yangi parol | New password | 20 |
| `reset.submit` | Parolni saqlash | Save password | 24 |
| `reset.invalid` | Bu havola yaroqsiz yoki muddati oʻtgan. Yangisini soʻrang. | This link is invalid or has expired. Request a new one. | 80 |
| `reset.success` | Parol yangilandi. Endi yangi parol bilan kiring. | Your password is updated. Log in with your new password. | 80 |

## landing

| key | uz-Latn | en | max |
|---|---|---|---|
| `landing.eyebrow` | Bepul · 4 tilda · Manbalari bilan | Free · 4 languages · With sources | 50 |
| `landing.title` | Qaysi hujjat, qaysi idora — aniq javob. | Which documents, which office: a clear answer. | 60 |
| `landing.lead` | Savolingizni oddiy soʻzlar bilan yozing. GovAssist qadamlar, kerakli hujjatlar va tumaningizdagi idorani rasmiy manbalar asosida koʻrsatadi. | Ask in plain words. GovAssist shows the steps, the documents to bring and the office in your district, based on official sources. | 160 |
| `landing.see_how` | Qanday ishlashini koʻrish | See how it works | 30 |
| `landing.signup` | Roʻyxatdan oʻtish | Sign up | 24 |
| `landing.login` | Kirish | Log in | 16 |
| `landing.cta_note` | Bepul. Roʻyxatdan oʻtish bir daqiqa oladi. | Free. Signing up takes a minute. | 60 |
| `landing.features_title` | Nega GovAssist | Why GovAssist | 30 |
| `landing.f1_title` | Aynan sizning tumaningizdagi idora | The exact office in your district | 50 |
| `landing.f1` | Manzil, ish vaqti, telefon va xaritadagi joyi — har bir javobda. | Address, hours, phone and map location in every answer. | 90 |
| `landing.f2_title` | Rasmiy hujjatlar asosida | Based on official documents | 40 |
| `landing.f2` | Har bir qadam yonida manba raqami. Bosib, asl sahifani oching. | Every step shows a source number. Tap it to open the original page. | 90 |
| `landing.f3_title` | 4 tilda | 4 languages | 20 |
| `landing.f3` | Oʻzbekcha (lotin va kirill), ruscha yoki inglizcha soʻrang. | Ask in Uzbek (Latin or Cyrillic), Russian or English. | 80 |
| `landing.f4_title` | Bepul | Free | 20 |
| `landing.f4` | Roʻyxatdan oʻting va savol bering — toʻlov yoʻq. | Sign up and ask. There is nothing to pay. | 70 |
| `landing.faq_title` | Koʻp soʻraladigan savollar | Frequently asked questions | 40 |
| `landing.q1` | Bu rasmiy davlat xizmatimi? | Is this an official government service? | 60 |
| `landing.a1` | Yoʻq. GovAssist — mustaqil talaba loyihasi. U ariza qabul qilmaydi va hech narsani sizning nomingizdan yubormaydi. | No. GovAssist is an independent student project. It doesn't accept applications or submit anything on your behalf. | 160 |
| `landing.q2` | Javoblar qayerdan olinadi? | Where do the answers come from? | 50 |
| `landing.a2` | Faqat koʻrib chiqilgan rasmiy manbalardan (lex.uz, my.gov.uz). Har bir javobda manbalar roʻyxati bor. | Only from reviewed official sources (lex.uz, my.gov.uz). Every answer lists its sources. | 140 |
| `landing.q3` | Shaxsiy maʼlumotlarim saqlanadimi? | Is my personal data stored? | 50 |
| `landing.a3` | Pasport raqami, JShShIR, telefon va email saqlashdan oldin olib tashlanadi. Hisobingizni istalgan vaqt oʻchirishingiz mumkin. | Passport numbers, PINFL, phone numbers and emails are removed before anything is stored. You can delete your account at any time. | 160 |
| `landing.q4` | Bu yuridik maslahatmi? | Is this legal advice? | 40 |
| `landing.a4` | Yoʻq. Bu umumiy maʼlumot. Muhim qaror oldidan rasmiy manbani tekshiring. | No. It is general information. Check the official source before an important decision. | 120 |
| `landing.band_title` | Birinchi safardayoq toʻgʻri idoraga boring. | Go to the right office the first time. | 60 |
| `landing.band_text` | Savolingizni bering va qadamlarni oling. | Ask your question and get the steps. | 60 |
| `landing.how_title` | Qanday ishlaydi | How it works | 30 |
| `landing.step_1_title` | Soʻrang | Ask | 24 |
| `landing.step_1` | Masalan: “Pasportimni qanday yangilayman?” | For example: “How do I renew my passport?” | 70 |
| `landing.step_2_title` | Qadamlarni oling | Get the steps | 30 |
| `landing.step_2` | Qadamlar, kerakli hujjatlar, toʻlov va muddat — manbalari bilan. | Steps, documents to bring, fee and time, with sources. | 90 |
| `landing.step_3_title` | Toʻgʻri idoraga boring | Go to the right office | 30 |
| `landing.step_3` | Tumaningizdagi idora manzili, ish vaqti va xaritadagi joyi. | The office in your district: address, hours and map. | 90 |
| `landing.preview_label` | Javob namunasi | Sample answer | 30 |

## footer

| key | uz-Latn | en | max |
|---|---|---|---|
| `footer.tagline` | Davlat xizmatlari boʻyicha mustaqil yordamchi. | An independent assistant for public services. | 60 |
| `footer.thesis` | ITPU magistratura dissertatsiyasi loyihasi · 2026 | MSc thesis project at ITPU · 2026 | 60 |
| `footer.sources` | Manbalar | Sources | 20 |

## password_change

| key | uz-Latn | en | max |
|---|---|---|---|
| `password_change.set_title` | Parol oʻrnatish | Set a password | 30 |
| `password_change.set_lead` | Hozir Google orqali kirasiz. Parol oʻrnatsangiz, elektron pochta bilan ham kira olasiz. | You log in with Google now. Set a password to also log in with your email. | 120 |
| `password_change.current` | Joriy parol | Current password | 24 |
| `password_change.saved` | Parol oʻzgartirildi. | Your password is changed. | 40 |

## onboarding

| key | uz-Latn | en | max |
|---|---|---|---|
| `onboarding.step` | {n}-qadam, jami {total} | Step {n} of {total} | 24 |
| `onboarding.lang_title` | Qaysi tilda gaplashamiz? | Which language do you prefer? | 40 |
| `onboarding.lang_lead` | Tilni keyin sozlamalarda oʻzgartirish mumkin. Savolni istalgan tilda yozishingiz mumkin. | You can change it later in Settings. You can ask in any language. | 120 |
| `onboarding.place_title` | Qayerda yashaysiz? | Where do you live? | 30 |
| `onboarding.region` | Viloyat | Region | 16 |
| `onboarding.district` | Tuman yoki shahar | District or city | 24 |
| `onboarding.search` | Qidirish… | Search… | 16 |
| `onboarding.choose_region_first` | Avval viloyatni tanlang | Choose a region first | 40 |
| `onboarding.loading_districts` | Tumanlar yuklanmoqda… | Loading districts… | 30 |
| `onboarding.no_results` | Hech narsa topilmadi | Nothing found | 30 |
| `onboarding.why_title` | Nima uchun soʻraymiz? | Why we ask | 30 |
| `onboarding.why` | Tumaningizni bilsak, aynan sizga kerakli idorani koʻrsatamiz. Uni sozlamalarda istalgan vaqt oʻzgartirishingiz mumkin. | Knowing your district lets us show the office you need. You can change it any time in Settings. | 140 |
| `onboarding.error_region` | Viloyatni tanlang. | Choose your region. | 30 |
| `onboarding.error_district` | Tuman yoki shaharni tanlang. | Choose your district or city. | 40 |
| `onboarding.submit` | Saqlash va boshlash | Save and start | 30 |

## chat

| key | uz-Latn | en | max |
|---|---|---|---|
| `chat.new` | Yangi suhbat | New chat | 20 |
| `chat.menu` | Menyu | Menu | 16 |
| `chat.greeting` | Salom! Qaysi davlat xizmati boʻyicha yordam kerak? | Hi! Which public service do you need help with? | 70 |
| `chat.greeting_lead` | Savolingizni oddiy soʻzlar bilan yozing. Koʻrib chiqilgan rasmiy manbalardan javob beraman va qaysi idoraga borishni aytaman. | Ask in plain words. I answer from reviewed official sources and tell you which office to visit. | 160 |
| `chat.can_help` | Nimalarda yordam beraman | What I can help with | 40 |
| `chat.help_1` | Hujjat olish yoki almashtirish tartibi, qadamma-qadam | How to get or replace a document, step by step | 70 |
| `chat.help_2` | Kerakli hujjatlar, toʻlov va muddat | Documents to bring, fee and processing time | 60 |
| `chat.help_3` | Tumaningizdagi idora: manzil, ish vaqti, telefon | The office in your district: address, hours, phone | 70 |
| `chat.help_4` | Qonunda nima deyilgani, manbasi bilan | What the law says, with the source | 60 |
| `chat.suggestions` | Masalan, soʻrang: | Try asking: | 30 |
| `chat.input_label` | Savolingiz | Your question | 20 |
| `chat.input_placeholder` | Savolingizni yozing… | Type your question… | 30 |
| `chat.send` | Yuborish | Send | 16 |
| `chat.stop` | Toʻxtatish | Stop | 16 |
| `chat.counter` | {n} / 1000 | {n} / 1000 | 12 |
| `chat.too_long` | Savol juda uzun. 1000 belgigacha qisqartiring. | Your question is too long. Keep it under 1000 characters. | 70 |
| `chat.you` | Siz | You | 8 |
| `chat.assistant` | GovAssist javobi | GovAssist answer | 24 |

## progress

| key | uz-Latn | en | max |
|---|---|---|---|
| `progress.searching` | Hujjatlar qidirilmoqda… | Searching documents… | 30 |
| `progress.found` | {count} ta manba topildi | Found {count} sources | 30 |
| `progress.writing` | Javob yozilmoqda… | Writing the answer… | 30 |
| `progress.stopped` | Javob toʻxtatildi. | Answer stopped. | 30 |
| `progress.stopped_hint` | Savolni qayta yuborishingiz mumkin. | You can send the question again. | 50 |

## answer

| key | uz-Latn | en | max |
|---|---|---|---|
| `answer.kind_service` | Davlat xizmati | Public service | 24 |
| `answer.kind_legal` | Huquqiy savol | Legal question | 24 |
| `answer.steps` | Nima qilish kerak | What to do | 30 |
| `answer.documents` | Oʻzingiz bilan oling | Documents to bring | 30 |
| `answer.documents_hint` | Tayyorlaganingizni belgilang. Belgilar saqlanmaydi. | Tick what you have ready. Ticks are not saved. | 70 |
| `answer.fee` | Toʻlov | Fee | 16 |
| `answer.processing_time` | Muddat | Processing time | 24 |
| `answer.not_stated` | Manbalarda koʻrsatilmagan | Not stated in the sources | 40 |
| `answer.where_to_go` | Qayerga borish kerak | Where to go | 30 |
| `answer.law_says` | Qonunda nima deyilgan | What the law says | 30 |
| `answer.quote_label` | Qonun matni | From the law | 20 |
| `answer.explanation_label` | Oddiy tilda | In plain words | 20 |
| `answer.what_you_can_do` | Nima qilishingiz mumkin | What you can do | 30 |
| `answer.sources` | Manbalar | Sources | 16 |
| `answer.source_n` | {n}-manba | Source {n} | 16 |
| `answer.source_fetched` | {date} holatiga olingan | Retrieved {date} | 40 |
| `answer.source_published` | Eʼlon qilingan: {date} | Published {date} | 30 |
| `answer.source_kind_law` | Qonun hujjati | Law | 20 |
| `answer.source_kind_service_page` | Xizmat sahifasi | Service page | 20 |
| `answer.source_kind_other` | Boshqa manba | Other source | 20 |
| `answer.source_kind_office` | Idoralar roʻyxati | Office list | 24 |
| `answer.followups` | Yana soʻrashingiz mumkin | You can also ask | 30 |
| `answer.not_found_help` | Savolni boshqa soʻzlar bilan yozib koʻring yoki mavzulardan birini tanlang. | Try different words, or pick one of these topics. | 90 |
| `answer.off_topic_help` | Men davlat xizmatlari va Oʻzbekiston qonunlari boʻyicha javob beraman. | I answer questions about public services and the laws of Uzbekistan. | 90 |

## feedback

| key | uz-Latn | en | max |
|---|---|---|---|
| `feedback.question` | Javob foydali boʻldimi? | Was this helpful? | 30 |
| `feedback.up` | Ha, foydali | Yes, helpful | 20 |
| `feedback.down` | Yoʻq, foydali emas | No, not helpful | 24 |
| `feedback.comment_label` | Nima yetishmadi? (ixtiyoriy) | What was missing? (optional) | 40 |
| `feedback.send` | Yuborish | Send | 16 |
| `feedback.saved` | Rahmat! Fikringiz saqlandi. | Thank you! Your feedback is saved. | 40 |

## office

| key | uz-Latn | en | max |
|---|---|---|---|
| `office.open_now` | Hozir ochiq | Open now | 20 |
| `office.closes_at` | {time} gacha | until {time} | 16 |
| `office.closed` | Yopiq | Closed | 12 |
| `office.opens_at` | {time} da ochiladi | Opens at {time} | 24 |
| `office.opens_on` | {day} {time} da ochiladi | Opens {day} at {time} | 36 |
| `office.break` | Tushlik tanaffusi | Lunch break | 24 |
| `office.hours` | Ish vaqti | Working hours | 20 |
| `office.hours_unknown` | Ish vaqti nomaʼlum | Hours not known | 30 |
| `office.day_off` | Dam olish kuni | Closed | 20 |
| `office.call` | Qoʻngʻiroq qilish | Call | 24 |
| `office.phone_unknown` | Telefon raqami nomaʼlum | Phone number not known | 30 |
| `office.map` | Google Xaritada ochish | Open in Google Maps | 30 |
| `office.data_as_of` | Maʼlumot {date} holatiga | Data as of {date} | 36 |
| `office.source` | Manba | Source | 12 |
| `office.match_region` | Tumaningizda bunday idora topilmadi, shuning uchun hududingizdagi boshqa idora koʻrsatildi. | No such office in your district, so we show one elsewhere in your region. | 110 |
| `office.match_none` | Bu idora manzili hozircha bazamizda yoʻq. | We do not have this office’s address yet. | 70 |
| `office.match_none_type` | Kerakli idora: {office_type}. | The office you need: {office_type}. | 70 |

## day

| key | uz-Latn | en | max |
|---|---|---|---|
| `day.mon` | Dushanba | Monday | 12 |
| `day.tue` | Seshanba | Tuesday | 12 |
| `day.wed` | Chorshanba | Wednesday | 12 |
| `day.thu` | Payshanba | Thursday | 12 |
| `day.fri` | Juma | Friday | 12 |
| `day.sat` | Shanba | Saturday | 12 |
| `day.sun` | Yakshanba | Sunday | 12 |

## chat_error

| key | uz-Latn | en | max |
|---|---|---|---|
| `chat_error.title` | Javob olinmadi | We could not get an answer | 40 |
| `chat_error.llm_unavailable` | Javob berish xizmati vaqtincha ishlamayapti. Birozdan soʻng qayta urinib koʻring. | The answer service is temporarily unavailable. Try again in a moment. | 100 |
| `chat_error.llm_timeout` | Javob juda uzoq kechikdi. Qayta urinib koʻring. | The answer took too long. Please try again. | 70 |
| `chat_error.invalid_answer` | Javobni toʻgʻri tuzib boʻlmadi. Qayta urinib koʻring. | We could not put the answer together. Please try again. | 70 |
| `chat_error.rate_limited` | Bir soatda {limit} tagacha savol berish mumkin. {minutes} daqiqadan soʻng yana soʻrang. | You can ask up to {limit} questions an hour. Ask again in {minutes} min. | 100 |
| `chat_error.quota_user` | Bugungi savollar chegarasiga yetdingiz. Ertaga yana soʻrang. | You have reached today’s question limit. Ask again tomorrow. | 80 |
| `chat_error.quota_global` | Bugun xizmatning umumiy chegarasiga yetildi. Ertaga qayta urinib koʻring. | The service has reached today’s overall limit. Please try again tomorrow. | 90 |
| `chat_error.stopped_title` | Javob toʻxtatildi | Answer stopped | 30 |
| `chat_error.stopped` | Siz javobni toʻxtatdingiz. Qayta soʻrash uchun “Qayta urinish”ni bosing. | You stopped this answer. Tap “Try again” to ask again. | 90 |
| `chat_error.stream_in_progress` | Oldingi javob hali yozilmoqda. U tugashini kuting. | The previous answer is still being written. Wait for it to finish. | 80 |
| `chat_error.offline` | Internet aloqasi yoʻq. Ulanganingizdan soʻng qayta urinib koʻring. | You are offline. Try again when you are connected. | 80 |
| `chat_error.back_online` | Aloqa tiklandi. | You are back online. | 30 |
| `chat_error.session_ended` | Sessiya tugadi. Qaytadan kiring. | Your session has ended. Please log in again. | 60 |

## history

| key | uz-Latn | en | max |
|---|---|---|---|
| `history.title` | Suhbatlar | Chats | 20 |
| `history.empty_title` | Hali suhbat yoʻq | No chats yet | 30 |
| `history.empty_lead` | Birinchi savolingizni bering. Suhbatlar shu yerda saqlanadi. | Ask your first question. Your chats are kept here. | 80 |
| `history.delete` | Oʻchirish | Delete | 16 |
| `history.delete_named` | “{title}” suhbatini oʻchirish | Delete chat “{title}” | 60 |
| `history.confirm_title` | Suhbat oʻchirilsinmi? | Delete this chat? | 30 |
| `history.confirm_body` | “{title}” va undagi barcha xabarlar oʻchiriladi. Buni qaytarib boʻlmaydi. | “{title}” and all its messages will be deleted. This cannot be undone. | 110 |
| `history.deleting` | Oʻchirilmoqda… | Deleting… | 20 |
| `history.deleted` | Suhbat oʻchirildi | Chat deleted | 30 |
| `history.load_more` | Yana koʻrsatish | Show more | 20 |
| `history.pii_note` | Shaxsiy maʼlumotlar [PASSPORT] kabi belgilar bilan almashtirilgan. | Personal data is replaced with markers like [PASSPORT]. | 80 |

## settings

| key | uz-Latn | en | max |
|---|---|---|---|
| `settings.title` | Sozlamalar | Settings | 20 |
| `settings.language` | Ilova tili | App language | 24 |
| `settings.place` | Hudud | Your area | 20 |
| `settings.place_hint` | Shu hududdagi idoralarni koʻrsatamiz. | We show offices in this area. | 50 |
| `settings.account` | Hisob | Account | 16 |
| `settings.display_name` | Ism (ixtiyoriy) | Name (optional) | 24 |
| `settings.change_password` | Parolni oʻzgartirish | Change password | 30 |
| `settings.logout` | Chiqish | Log out | 16 |
| `settings.delete_account` | Hisobni oʻchirish | Delete account | 24 |
| `settings.delete_title` | Hisob oʻchirilsinmi? | Delete your account? | 30 |
| `settings.delete_body` | Hisobingiz va barcha suhbatlaringiz butunlay oʻchiriladi. Buni qaytarib boʻlmaydi. | Your account and all your chats will be deleted for good. This cannot be undone. | 110 |
| `settings.delete_confirm_check` | Tushundim, hisobim oʻchirilsin | I understand, delete my account | 40 |
| `settings.delete_submit` | Ha, oʻchirish | Yes, delete | 20 |
| `settings.usage` | Foydalanish | Usage | 20 |
| `settings.usage_hour` | Shu soatda: {used} / {limit} savol | This hour: {used} of {limit} questions | 40 |
| `settings.usage_day` | Bugun: {used} / {limit} savol | Today: {used} of {limit} questions | 40 |
| `settings.usage_hint` | Chegaralar xizmat barqaror ishlashi uchun kerak. | Limits keep the service running smoothly. | 70 |

## about

| key | uz-Latn | en | max |
|---|---|---|---|
| `about.title` | GovAssist haqida | About GovAssist | 30 |
| `about.what_title` | Bu nima? | What is this? | 30 |
| `about.what` | GovAssist — davlat xizmatlari va qonunlar haqidagi savollarga javob beradigan yordamchi. U ITPU magistratura dissertatsiyasi doirasida yaratilgan. | GovAssist is an assistant that answers questions about public services and laws. It is built as part of an MSc thesis at ITPU. | 180 |
| `about.how_title` | Javoblar qanday tuziladi | How answers are made | 40 |
| `about.how_1` | Javob faqat koʻrib chiqilgan manbalardan (lex.uz, my.gov.uz va boshqalar) tuziladi. Internetdan jonli qidiruv qilinmaydi. | Answers come only from reviewed sources (lex.uz, my.gov.uz and others). There is no live web search. | 160 |
| `about.how_2` | Har bir fakt yonida manba raqami turadi. Uni bosib, asl sahifani oching. | Each fact shows a source number. Tap it to open the original page. | 110 |
| `about.how_3` | Idora manzili va ish vaqti bazadan olinadi, sunʼiy intellekt ularni yozmaydi. Har bir kartada maʼlumot sanasi koʻrsatiladi. | Office addresses and hours come from our database; the AI never writes them. Every card shows the date of the data. | 170 |
| `about.how_4` | Bu yuridik maslahat emas. Muhim qaror oldidan rasmiy manbani yoki mutaxassisni tekshiring. | This is not legal advice. Before an important decision, check the official source or ask a professional. | 140 |
| `about.privacy_title` | Maxfiylik | Privacy | 20 |
| `about.privacy_1` | Elektron pochtangiz, tanlangan hudud va suhbatlaringiz saqlanadi. | We store your email, your chosen area and your chats. | 100 |
| `about.privacy_2` | Pasport raqami, JShShIR, telefon va email kabi maʼlumotlar saqlash, qayta ishlash va jurnalga yozishdan oldin olib tashlanadi. | Passport numbers, PINFL, phone numbers and emails are removed before anything is stored, processed or logged. | 160 |
| `about.privacy_3` | Javob yozish uchun savol shaxsiy maʼlumotlarsiz Google Gemini xizmatiga yuboriladi. | To write the answer, your question is sent to Google Gemini without personal data. | 120 |
| `about.privacy_4` | Hisobingizni sozlamalarda istalgan vaqt oʻchirishingiz mumkin. | You can delete your account at any time in Settings. | 90 |
| `about.sources_title` | Manbalar roʻyxati | Source list | 30 |
| `about.sources_lead` | Bilimlar bazasidagi manbalar: | Sources in the knowledge base: | 50 |
| `about.source_docs` | {n} ta hujjat | {n} documents | 20 |
| `about.source_updated` | Yangilangan: {date} | Updated {date} | 30 |
| `about.not_official_title` | Rasmiy xizmat emas | Not an official service | 30 |

## notfound

| key | uz-Latn | en | max |
|---|---|---|---|
| `notfound.title` | Sahifa topilmadi | Page not found | 30 |
| `notfound.lead` | Havola notoʻgʻri yoki sahifa olib tashlangan. | The link is wrong or the page was removed. | 70 |
| `notfound.home` | Bosh sahifaga qaytish | Go to the home page | 30 |

## error_page

| key | uz-Latn | en | max |
|---|---|---|---|
| `error_page.title` | Nimadir buzildi | Something broke | 30 |
| `error_page.lead` | Sahifani yangilang. Muammo takrorlansa, birozdan soʻng qayta kiring. | Reload the page. If it keeps happening, come back a little later. | 90 |
| `error_page.reload` | Sahifani yangilash | Reload page | 24 |

## Error codes → copy keys

The SPA maps codes, never raw `message` text (contract §1, §2, §4). Unknown codes fall back to `error.server`.

| Source | `code` | Copy key |
|---|---|---|
| allauth 400 | `turnstile_failed` | `error.turnstile` |
| allauth 400 | `email_taken` | `error.email_taken` |
| allauth 400 | `email_password_mismatch` | `error.login_failed` |
| allauth 400 | `too_many_login_attempts` | `error.too_many_logins` |
| allauth 400 | `password_too_short` | `error.password_short` |
| allauth 400 | `password_too_common` | `error.password_common` |
| allauth 400 | `password_entirely_numeric` | `error.password_numeric` |
| allauth 400 | `password_too_similar` | `error.password_similar` |
| problem+json / SSE | `rate_limited` | `chat_error.rate_limited` (or `check_email.rate_limited` on resend) |
| problem+json / SSE | `quota_exceeded` + `scope: user` | `chat_error.quota_user` |
| problem+json / SSE | `quota_exceeded` + `scope: global` | `chat_error.quota_global` |
| problem+json | `stream_in_progress` | `chat_error.stream_in_progress` |
| SSE / `error_code` | `llm_unavailable` | `chat_error.llm_unavailable` |
| SSE / `error_code` | `llm_timeout` | `chat_error.llm_timeout` |
| SSE / `error_code` | `invalid_answer` | `chat_error.invalid_answer` |
| `error_code` | `stopped` | `chat_error.stopped_title` + `chat_error.stopped` |
| any | `internal_error`, unknown | `error.server` |
| any | 401 `not_authenticated` | `chat_error.session_ended` (on the login screen) |

# Yangi Lotin Android klaviaturasi (0.2.1 sinov)

Bu loyiha Windows dasturidagi uch yo‘nalishni Android klaviaturasiga olib
keladi. Ilova `InputMethodService` bo‘lib ishlaydi: foydalanuvchi uni telefon
sozlamasida yoqib, faol klaviatura sifatida tanlaydi. Klaviatura boshqa
ilovadagi joriy matn maydoniga `InputConnection` orqali yozadi.

## Hozirgi holat

- Kirill → yangi lotin, eski lotin → yangi lotin, lotin → kirill va OFF.
- Klaviatura ustida tezkor rejimlar; ortiqcha izoh satri yo‘q. Lotin qismida
  doimiy raqam qatori, kirill qismida o‘zbekcha maxsus harflar qatori bor.
  Ikkalasi ham bir xil balandlikdagi besh qatorli klaviatura.
- Emoji tugmasi va oflayn emoji paneli, Shift/Caps Lock, uzoq bosiladigan
  `ö/ğ/ş/ç`, boshqa klaviaturaga o‘tish tugmasi. Telegram stikerlari uchun
  Telegramning o‘z stiker panelidan foydalaniladi.
- Shift yoki Caps Lock yoqilganda uning tugmasi ko‘k rangda ko‘rinadi.
- Xabar maydonida Enter yangi qator ochadi; Enter’ni uzoq bosish maydonning
  yuborish/davom etish amalini bajaradi. Qidiruv kabi bir qatorli maydonlarda
  odatiy Enter amali saqlanadi.
- Android klaviaturasidagi `щ` bitta `ş`ga aylanadi.
- `sh → ş` kabi bitta harfga aylangan juftlik bir Backspace bilan o‘chadi.
- Maxfiy parol maydonida o‘girish avtomatik to‘xtaydi.
- Asosiy oynada matnni qo‘yish, o‘girish, nusxalash va tozalash.
- Internet ruxsati so‘ralmaydi; tugma bosishlari saqlanmaydi.
- Apostrof klaviaturada bevosita bor; belgilarga o‘tib qaytganda
  tugallanmagan so‘z konteksti saqlanadi (`o' → ö`, `g' → ğ`).

## Ishga tushirish

Telefon uchun [sinov APK’sini GitHub’dan yuklab oling](https://github.com/shohruhxaydarov750-oss/yangi-lotin/releases/download/android-v0.2.1-preview/YangiLotin-Android-v0.2.1-preview.apk).
APK’ni ochib o‘rnating; Android so‘rasa, fayl ochilgan ilovaga o‘rnatish
ruxsatini bering. **Yangi Lotin**ni oching, avval **1. Sozlamalarda yoqish**,
keyin **2. Klaviaturani tanlash**ni bosing. Matn yozadigan joyda klaviatura
ustidagi yo‘nalishni yoki **OFF**ni tanlang. Sinov APK’si debug kaliti bilan
imzolangan; keyingi nusxaga o‘tishda oldingisini o‘chirib qayta o‘rnatish
kerak bo‘lishi mumkin.

Manba kodidan yig‘ish uchun:

Android Studio’da shu `mobile/android` katalogini loyiha sifatida oching.
JDK 17 va Android 16 (API 36) SDK talab qilinadi. `app` modulini telefon yoki
emulyatorga o‘rnating. Ilovani ochib **Sozlamalarda yoqish**, so‘ng
**Klaviaturani tanlash** bosqichlarini bajaring.

Buyruq satrida loyiha ichidan (Gradle Wrapper kerakli versiyani o‘zi yuklaydi):

```text
gradlew.bat testDebugUnitTest assembleDebug
```

macOS/Linux uchun shu buyruq `./gradlew testDebugUnitTest assembleDebug`.

APK `app/build/outputs/apk/debug/app-debug.apk` manzilida chiqadi.
GitHub Actions qoidalar sinovi, APK yig‘ish va Android emulyatorida haqiqiy
tugmalarni bosib ko‘rish tekshiruvini bajaradi. Sinov APK’si artifact sifatida
saqlanadi. Bu **debug** APK umumiy tarqatish uchun imzolangan reliz emas.

## Sinov chegarasi

Klaviatura faqat o‘zi faol bo‘lganida kiritilgan tugmalarni o‘giradi.
Tashqi klaviaturada yozilgan, tizim tomonidan qo‘yilgan yoki ovoz bilan
kiritilgan matnni avtomatik ushlamaydi. Android 15 emulyatorida haqiqiy
tugmalar bilan `ş/ç/ö/ğ`, katta harf, uch yo‘nalish, OFF va Backspace
sinovdan o‘tdi. Emoji, raqam qatori, `щ → ş` va Enter’ning yangi qator amali
ham emulyatorda tekshirildi. Xabar maydonidagi Enter va uzoq bosib yuborish
amallari alohida sinov oynasida tekshiriladi. Turli ilovalardagi kursor, tanlangan matn,
avtomatik taklif, Enter va Backspace holatlari haqiqiy Android telefonida alohida sinovdan o‘tishi
kerak. APK’ni barqaror reliz deb e’lon qilishdan oldin shu sinovlar bajariladi.

Android klaviatura API’si: https://developer.android.com/develop/ui/views/touch-and-input/creating-input-method

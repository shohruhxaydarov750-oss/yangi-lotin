# Yangi Lotin Android klaviaturasi (ishlanmoqda)

Bu loyiha Windows dasturidagi uch yo‘nalishni Android klaviaturasiga olib
keladi. Ilova `InputMethodService` bo‘lib ishlaydi: foydalanuvchi uni telefon
sozlamasida yoqib, faol klaviatura sifatida tanlaydi. Klaviatura boshqa
ilovadagi joriy matn maydoniga `InputConnection` orqali yozadi.

## Hozirgi holat

- Kirill → yangi lotin, eski lotin → yangi lotin, lotin → kirill va OFF.
- Klaviatura ustida tezkor rejimlar, inglizcha va o‘zbekcha kirillcha tugmalar,
  raqamlar, Shift/Caps Lock, uzoq bosiladigan `ö/ğ/ş/ç`, boshqa klaviaturaga
  o‘tish tugmasi.
- `sh → ş` kabi bitta harfga aylangan juftlik bir Backspace bilan o‘chadi.
- Maxfiy parol maydonida o‘girish avtomatik to‘xtaydi.
- Asosiy oynada matnni qo‘yish, o‘girish, nusxalash va tozalash.
- Internet ruxsati so‘ralmaydi; tugma bosishlari saqlanmaydi.

## Ishga tushirish

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
GitHub Actions shu ikki tekshiruvni bajarib, sinov APK’sini artifact sifatida
saqlaydi. Bu **debug** APK umumiy tarqatish uchun imzolangan reliz emas.

## Sinov chegarasi

Klaviatura faqat o‘zi faol bo‘lganida kiritilgan tugmalarni o‘giradi.
Tashqi klaviaturada yozilgan, tizim tomonidan qo‘yilgan yoki ovoz bilan
kiritilgan matnni avtomatik ushlamaydi. Turli ilovalardagi kursor, tanlangan
matn, avtomatik taklif va Backspace holatlari haqiqiy Android telefonida
alohida sinovdan o‘tishi kerak. APK’ni barqaror reliz deb e’lon qilishdan
oldin shu sinovlar bajariladi.

Android klaviatura API’si: https://developer.android.com/develop/ui/views/touch-and-input/creating-input-method

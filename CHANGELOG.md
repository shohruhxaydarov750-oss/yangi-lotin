# O‘zgarishlar

## Android 0.2.0 (sinov) — 2026-11-11

- Klaviatura ustidagi ortiqcha izoh satri olib tashlandi.
- Lotin tugmalariga raqam qatori, pastki qatorga emoji tugmasi va emoji paneli qo‘shildi.
- Xabar maydonida Enter yangi qator ochadi; uzoq bosish yuborish amalini bajaradi.
- Android klaviaturasida `щ → ş` bo‘ldi.
- Bu Android o‘zgarishlari Windows 1.6.5 relizidagi `щ → şç` qoidasini o‘zgartirmaydi.

## 1.6.5 — 2026-11-10

- `sh → ş`, `ch → ç`, `o' → ö`, `g' → ğ` yozilgandan keyin bitta Backspace
  juftlikdan hosil bo‘lgan harfni to‘liq o‘chiradi. Oldingi birinchi harf
  qayta paydo bo‘lmaydi.
- Lotin → kirill rejimidagi `sh → ш`, `ch → ч`, `yo → ё` juftliklari ham
  bir marta Backspace bilan o‘chadi.
- Chrome manzil satrida `sş` chiqishi tuzalganini foydalanuvchi tasdiqladi;
  ko‘rinadigan matn va ichki yozish holati uchun yangi sinovlar qo‘shildi.

## 1.6.4 (sinov) — 2026-11-09

- Chrome manzil satrida tanlangan avtomatik taklifga duch kelganda,
  `sh/ch/o‘/g‘` uchun eski harf va taklif bitta tanlovga birlashtirilib,
  yangi harf bilan almashtiriladi. Ketma-ket Backspace yuborish olib tashlandi.
- Xuddi shu usul bir marta Backspace bilan yozilgan harfni o‘chirish va
  bosh harflarni saqlash uchun ham qo‘llanadi.
- Manba kodidan ishga tushirish yo‘riqnomasiga `comtypes` o‘rnatilishi
  qo‘shildi; EXE ichida u allaqachon mavjud.
- Chrome manzil satridagi amaliy natija bevosita tasdiqlanmaguncha bu reliz
  sinov maqomida qoladi.

## 1.6.3 (sinov) — 2026-11-05

- Chrome manzil satrida avtomatik taklif tanlanganida ilova tanlov
  chegaralarini Windows UI Automation orqali tekshiradi. Tanlangan taklif
  avval tozalanadi, keyin `sh/ch/o‘/g‘` birikmasi almashtiriladi.
- Tanlovni aniqlash matnni o‘qimaydi. Tekshiruv kechiksa yoki qo‘llanmasa,
  matn buzilmasligi uchun oddiy tugma kiritiladi. Backspace va bosh harf
  holatlari sinovlarga qo‘shildi.
- Chrome manzil satrida qo‘lda ishlashi tasdiqlanguncha bu reliz sinov
  maqomida qoladi.

## 1.6.2 — 2026-11-03

- Eski lotinda `sh/ch/o‘/g‘` yozishning birinchi harfi ham almashtirish bilan
  bir xil klaviatura oqimidan yuborildi. Chrome manzil satridagi avtomatik
  taklif muammosi bu versiyada saqlanib qoldi.
- Oynadagi tushunarsiz **Qo‘lda manba** ro‘yxati o‘rniga natija yozuvi uchun
  **→ Yangi lotin** va **→ Kirill** tugmalari qo‘shildi.
- Ctrl+V matnni chap maydonga qo‘yib darhol o‘giradi. Enter o‘giradi,
  Shift+Enter yangi qator kiritadi.

## 1.6.1 — 2026-11-02

- Dastur tray'da ishlab turganda EXE qayta ochilsa, mavjud oyna ko‘rsatiladi.

## 1.6.0 — 2026-11-02

- Standart Windows parol maydonlarida real-time o‘girish to‘xtatiladi.
- Qo‘lda manba tanlovi oxirgi ishlatilgan yo‘nalishga mos ochiladi; manba
  yoki matn o‘zgarsa, eskirgan natija tozalanadi.
- Juft qo‘shtirnoqdagi `o/g` hamda ayrim oy nomlari tuzatildi.
- Brendlangan Windows belgisi, GitHub tekshiruvlari va takrorlanuvchi
  EXE/ZIP chiqarish skripti qo‘shildi.

## 1.5.0 — 2026-11-02

- Eski va yangi lotindan kirillga qo‘lda hamda real vaqtda o‘girish qo‘shildi.
- Uch yo‘nalish tray menyusi va saqlanadigan rejimlarga ulandi.

## 1.4.0 — 2026-11-01

- Windows bilan avtomatik boshlash va portativ EXE nusxasini yangilash qo‘shildi.

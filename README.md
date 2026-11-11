# Yangi Lotin v1.6.5

[![Windows checks](https://github.com/shohruhxaydarov750-oss/yangi-lotin/actions/workflows/ci.yml/badge.svg)](https://github.com/shohruhxaydarov750-oss/yangi-lotin/actions/workflows/ci.yml)
[![Android keyboard checks](https://github.com/shohruhxaydarov750-oss/yangi-lotin/actions/workflows/android.yml/badge.svg)](https://github.com/shohruhxaydarov750-oss/yangi-lotin/actions/workflows/android.yml)

**Yuklab olish:** [v1.6.5 EXE va portable ZIP](https://github.com/shohruhxaydarov750-oss/yangi-lotin/releases/tag/v1.6.5).

**Android sinov klaviaturasi:** [APK’ni yuklab olish](https://github.com/shohruhxaydarov750-oss/yangi-lotin/releases/download/android-v0.2.0-preview/YangiLotin-Android-v0.2.0-preview.apk)
· [o‘rnatish yo‘riqnomasi](mobile/android/README.md). Android 8.0 yoki
yangiroq telefonda klaviaturani bir marta tanlang; keyin Telegram kabi
ilovalarda kirill → yangi lotin, eski lotin → yangi lotin va lotin → kirill
rejimlarini klaviaturaning o‘zidan almashtirasiz. OFF tugmasi ham bor. APK
emulyatorda sinovdan o‘tgan **preview** nusxa; haqiqiy telefonlar va turli
ilovalarda qo‘shimcha tekshiruv kerak.

Windows uchun oflayn o‘zbek yozuvi o‘girgichi: **kirill → yangi lotin**,
**eski lotin → yangi lotin** hamda **eski yoki yangi lotin → kirill**.

Ikki xil ishlash rejimi bor:

- **Avtomatik rejim:** Telegram, brauzer, Word va boshqa Windows
  dasturlarida yozayotgan matningiz tanlangan yo‘nalishda darhol o‘zgaradi.
  Kirill → yangi lotin va eski lotin → yangi lotin alohida yoqiladi.
  Lotin → kirill yoqilsa, qarama-qarshi ikki rejim o‘chadi.
- **Oynada o‘girish:** natija yozuvini **→ Yangi lotin** yoki **→ Kirill**
  qilib tanlang. Ctrl+V qo‘yilgan matnni darhol o‘giradi; yozilgan matn
  Enter bilan o‘giriladi.

Natijada quyidagi yangi harflar ishlatiladi:

| Kirill | Yangi lotin |
|---|---|
| Ў ў | Ö ö |
| Ғ ғ | Ğ ğ |
| Ш ш | Ş ş |
| Ч ч | Ç ç |

Eski lotindagi to‘rtta shakl ham avtomatik yangilanadi:

| Eski lotin | Yangi lotin |
|---|---|
| Sh sh | Ş ş |
| Ch ch | Ç ç |
| O‘ o‘, O' o' | Ö ö |
| G‘ g‘, G' g' | Ğ ğ |

`ng`, `yo`, `ya` va `yu` o‘zgarmaydi.

Lotin → kirill rejimi eski va yangi shakllarni qabul qiladi:
`sh/ş → ш`, `ch/ç → ч`, `o‘/ö → ў`, `g‘/ğ → ғ`.

## Huquqiy holat

Bu to‘rtta harf endi shunchaki loyiha emas. O‘zbekiston Respublikasining
2026-yil 21-oktabrdagi **O‘RQ-1184-son Qonuni** yangilangan, 28 harf va
1 tutuq belgili alifboni belgiladi. Qonun 2027-yil 22-apreldan kuchga
kiradi. Demak, 2026-yil 10-noyabr holatiga u qabul qilingan, ammo hali
kuchga kirmagan.

Rasmiy manbalar:

- Qonun matni va kuchga kirish sanasi: https://lex.uz/docs/8548754
- Hukumat xabari va to‘rtta almashtirish: https://gov.uz/oz/fvv/news/view/236033
- Amaldagi asosiy imlo qoidalari: https://www.lex.uz/uz/docs/-1625271
- Eski lotin va kirill harflari jadvali: https://lex.uz/uz/acts/112283
- Yangi to‘rtta harf bo‘yicha hukumat xabari: https://gov.uz/oz/yoshlar/news/view/238380

## Tayyor EXE bilan ishlash

1. `YangiLotin.exe` faylini oching. O‘rnatish va Python talab qilinmaydi.
2. Birinchi ishga tushganda ikki yangi lotin yo‘nalishi **ON**, lotin →
   kirill **OFF** bo‘ladi. Oldingi versiyadagi ON/OFF tanlovingiz saqlanadi.
3. Kirill yoki lotin klaviaturasida istalgan oddiy matn maydoniga yozing.
   Masalan, `салом → salom`, `shahar → şahar`, `o'zbek → özbek`.
4. Asosiy oynadagi uch yo‘nalish tugmasidan keraklisini tanlang. **LOTIN →
   KIRILL** yoqilsa, ikkala yangi lotin rejimi avtomatik OFF bo‘ladi;
   ulardan biri yoqilsa, lotin → kirill OFF bo‘ladi. Lotin → kirillda
   `shahar → шаҳар` va `şahar → шаҳар`.
5. Pastki o‘ng burchakdagi tray ikonkasiga bir marta chap bosing:
   ko‘k belgi — kamida bitta rejim **ON**, kulrang belgi — hammasi **OFF**.
   Ikkinchi bosish oxirgi faol rejimlar tanlovini tiklaydi.
6. Oddiy Windows parol maydonlari avtomatik chetlab o‘tiladi. Brauzer
   va maxsus dasturlarda parol yoki karta ma’lumotini yozishdan oldin
   tray ikonkasi orqali hammasini OFF qiling.

## Windows bilan avtomatik boshlash

Asosiy oynadagi **WINDOWS BILAN BOSHLASH** tugmasini bir marta
**ON** qilsangiz, keyingi kirishlarda dastur tray'da o‘zi ishga tushadi.
Oynani ko‘rish uchun tray ikonkasiga o‘ng bosib **Oynani oçiş**ni tanlang.
Windows uni kirgandan so‘ng biroz kechiktirib ishga tushirishi mumkin.
Dastur tray'da ishlab turganda portativ EXE qayta ochilsa, yangi nusxa
yaratilmaydi — mavjud oyna oldinga chiqadi.

Avtomatik ishga tushish faqat joriy Windows foydalanuvchisi uchun yoqiladi;
administrator huquqi kerak emas. Dastur portativ EXE'ning nusxasini
`%LOCALAPPDATA%\Programs\YangiLotin\YangiLotin.exe` manziliga saqlab,
Windows'ning `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
ro‘yxatiga shu nusxani qo‘shadi. Shu sabab dastlab ochilgan portativ EXE
keyin boshqa joyga ko‘chirilsa ham avtomatik ishga tushish saqlanadi.
Tugmani **OFF** qilish Windows'dan ishga tushish yozuvini olib tashlaydi;
saqlangan EXE nusxasi qoladi.

Yangiroq portativ EXE olsangiz, avval ishlayotgan eski nusxadan tray
menyusi orqali chiqing, so‘ng yangi EXE'ni oching. Avtomatik boshlash ON
bo‘lsa, Windows uchun saqlangan nusxa ham o‘zi yangilanadi. Windows'ga
kirganda tray ikonkasini yaratib bo‘lmasa, holatni ko‘rishingiz uchun
asosiy oyna ochiladi.

Uch yo‘nalishning oxirgi holati qayta tiklanadi. Hammasi
OFF qoldirilgan bo‘lsa, dastur tray'da ochiladi, lekin o‘girish OFF bo‘ladi;
tray ikonkasini bir marta bosib oldingi faol tanlovni tiklash mumkin.
Windows sozlamalaridagi **Apps → Startup** bo‘limida Yangi Lotin alohida
o‘chirib qo‘yilgan bo‘lsa, uni o‘sha yerda ham yoqish kerak.

Tray ikonkasiga o‘ng bosilganda uch o‘girish yo‘nalishi alohida
belgilangan menyu, umumiy ON/OFF, oynani ochish va dasturdan chiqish
buyruqlari chiqadi. Asosiy oynadagi `X` tugmasi
dasturdan chiqarmaydi — oyna yashirinadi va xizmat tray’da ishlashda davom
etadi. To‘liq yopish uchun tray menyusidagi **Çiqiş** buyrug‘ini tanlang.

Kichik harf kichikligicha qoladi: `sh → ş`, `ch → ç`, `ш → ş`, `ч → ç`.
Shift va Caps Lock bilan kiritilgan bosh harflar ham saqlanadi.
`sh → ş`, `ch → ç`, `o' → ö`, `g' → ğ` kabi bitta harfga aylangan
juftliklar bir marta Backspace bosilganda to‘liq o‘chadi.

EXE portativ: o‘rnatish va alohida Python talab qilmaydi. U Windows 10/11
x64 uchun yig‘ilgan. Dastur matnni internetga yubormaydi.

Eslatma: ochiq manbali, raqamli imzosiz EXE birinchi ishga tushishda
Windows SmartScreen ogohlantirishini ko‘rsatishi mumkin.

## Ikonkani pastki panelda doim ko‘rsatish

Windows dasturga tray ikonkasini majburan pin qilishga ruxsat bermaydi.
Buni faqat bir marta qo‘lda sozlash kerak:

1. Soat yonidagi `^` — yashirin ikonkalar tugmasini bosing.
2. **Yangi Lotin** ikonkasini sichqon bilan pastki tray qatoriga sudrang.
3. Windows bu joylashuvni eslab qoladi; keyingi ishga tushishlarda ikonka
   shu yerda ko‘rinadi.

## Parol va maxfiylik

- Standart Windows `Edit`/`RichEdit` parol maydonlarida dastur tugmalarni
  o‘zgartirmaydi. Brauzer va boshqa maxsus ilovalardagi maydonlarni
  ishonchli aniqlab bo‘lmaydi. U yerda parol, karta ma’lumoti yoki boshqa
  maxfiy matn yozishdan **oldin tray ikonkasi orqali real-time rejimni OFF
  qiling**.
- Dastur internetga ulanmaydi, tugmalarni jurnalga yozmaydi va faylga
  saqlamaydi.
- Faqat rejim tanlovlari Windows’dagi
  `%LOCALAPPDATA%\YangiLotin\settings.json` fayliga saqlanadi; u yerda
  yozgan matningiz bo‘lmaydi.
- Windows bilan boshlash yoqilganda faqat dastur nusxasi va ishga tushirish
  yozuvi saqlanadi; yozilgan matn saqlanmaydi.
- Kontekstli o‘girish uchun faqat tugallanmagan joriy so‘z vaqtincha
  operativ xotirada saqlanadi; bo‘shliq, sichqon bosilishi, oyna almashishi
  yoki rejim o‘chirilishi bilan bu kontekst tozalanadi.
- Ctrl, Alt yoki Windows tugmasi qatnashgan klaviatura yorliqlari o‘girilmaydi.
- Inglizcha matn, kod yoki URL yozganda `sh/ch` ham `ş/ç` bo‘lib ketishi
  mumkin. Lotin → kirill rejimi inglizcha so‘zlarni ham o‘zgartiradi.
  Bunday paytda tegishli avtomatik rejimni vaqtincha OFF qiling.

## Oynada o‘girish

1. **Natija yozuvi** uchun **→ Yangi lotin** yoki **→ Kirill**ni tanlang.
   Birinchi yo‘nalish kirill va eski lotin matnini, ikkinchisi eski va yangi
   lotin matnini qabul qiladi.
2. Chap maydonga matnni **Ctrl+V** bilan qo‘ying yoki **Qöyiş**ni bosing:
   natija o‘ngda darhol chiqadi. Chap maydonga matnni qo‘lda yozsangiz,
   **Enter** bosing.
3. Yangi qator kerak bo‘lsa **Shift+Enter** bosing.
4. **Nusxalaş** natijani oladi, **Tozala** ikkala maydonni bo‘shatadi.

Oynada o‘girish avtomatik rejimlar OFF bo‘lganda ham ishlaydi. Matn
o‘zgarsa eski natija tozalanadi; natija yo‘nalishini almashtirsangiz,
joriy matn yangi yo‘nalishda qayta o‘giriladi.
Buferdan birdaniga qo‘yilgan matn global avtomatik rejimda ushlanmaydi;
buning uchun shu oynadan foydalaning.

## Manba kodidan ishga tushirish

Talab: Windows va Tkinter bilan Python 3.10 yoki yangiroq.

~~~powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe app.py
~~~

Manba kodidan ishlatganda Windows matn tanlovini tekshirish uchun
`comtypes` kutubxonasi o‘rnatiladi. Portativ EXE barcha kerakli qismlarni
o‘z ichiga oladi. Manba kodidan avtomatik boshlash yoqilsa,
Windows `pythonw.exe` va `app.py` manzillarini saqlaydi; bu fayllarni
ko‘chirgandan keyin avtomatik boshlashni qayta yoqing.

## Testlar

~~~powershell
py -3 -m unittest discover -s tests -v
~~~

Testlar odatiy o‘zbek so‘zlari, bosh/mixed case, paragraflar, tinish
belgilari, Unicode, е, ё, ю, я, ц, ъ, ь, `sh/ch/o'/g'`, barcha qo‘llangan
apostrof variantlari, qo‘shtirnoq chegaralari, lotin → kirill, mustaqil
rejimlar, qo‘lda o‘girish natijasini tozalash, oddiy Windows parol maydoni,
avtomatik ishga tushish buyruqlari, Caps Lock holati, real-time
prefiksni qayta hisoblash, backspace va tasodifiy uzun so‘z holatlarini
qamrab oladi.

## EXE yig‘ish

~~~powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
~~~

Skript alohida .venv-build muhitini yaratadi, testlarni bajaradi va
natijani dist\YangiLotin.exe qilib chiqaradi. Birinchi yig‘ishda internet
PyInstaller paketini olish uchun kerak bo‘ladi.

GitHub uchun EXE, portativ ZIP, manba ZIP va SHA-256 yig‘indilarini birga
tayyorlash:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\release.ps1
~~~

Natija `release` papkasiga yoziladi. `.github/workflows/ci.yml` GitHub'da
Python 3.10 va 3.14 sinovlarini hamda Windows EXE yig‘ishni bajaradi.

## Klaviatura yorliqlari

| Amal | Yorliq |
|---|---|
| O‘girish | Matn maydonida Enter yoki Ctrl+Enter |
| Yangi qator kiritish | Shift+Enter |
| Buferdan qo‘yish va darhol o‘girish | Ctrl+V yoki Ctrl+Shift+V |
| Natijani nusxalash | Ctrl+Shift+C |
| Ikkala maydonni tozalash | Ctrl+L |

Ctrl+V oynaning qaysi qismi tanlanganidan qat’i nazar matnni chap maydonga
qo‘yadi. Matn maydonlarida Ctrl+A va Ctrl+C odatdagidek ishlaydi.

## O‘girish qoidalari

### Lotindan kirillga

- eski va yangi harflar bir xil o‘qiladi: `sh/ş → ш`, `ch/ç → ч`,
  `o‘/ö → ў`, `g‘/ğ → ғ`;
- `yo/yu/ya → ё/ю/я`, so‘z boshidagi `e → э`, `ye → е`;
- harf ichidagi alohida tutuq odatda `ъ`: `maʼno → маъно`;
- bosh va kichik harflar, satrlar, tinish belgilari saqlanadi.

Bu yo‘nalish **aniq teskari nusxa emas**. Masalan, `s` harfi avvalgi
kirill matnda `с` yoki `ц` bo‘lganini, `ts` esa `ц` yoki `тс` bo‘lganini
har doim bilib bo‘lmaydi. `ye` hamda lotinda tushib qolgan `ъ/ь` ayrim
so‘zlarda qo‘shimcha ma’no yoki lug‘at talab qiladi. Dastur qat’iy,
izchil qoidalarni qo‘llaydi; 2026-yilgi qonun to‘liq lotin → kirill
algoritmini rasmiy standart sifatida belgilamaydi.

### Eski lotindan yangi lotinga

- `sh → ş`: `shahar → şahar`;
- `ch → ç`: `chiroyli → çiroyli`;
- `o` dan keyin `'`, `‘`, `’`, `ʻ`, `ʼ`, backtick yoki `´` yozilsa `ö`;
- `'go'` yoki `‘o’` kabi juft qo‘shtirnoqning yopuvchi belgisi saqlanadi;
- shu apostrof variantlaridagi `g + apostrof → ğ`;
- bosh harflar saqlanadi: `SH → Ş`, `Ch → Ç`, `O' → Ö`, `G‘ → Ğ`;
- yangi `ş/ç/ö/ğ`, mos kelmagan apostroflar va qolgan lotin matn
  o‘zgarmaydi.

### Kirilldan yangi lotinga

Oddiy harflar to‘g‘ridan-to‘g‘ri moslanadi. Muhim maxsus qoidalar:

- е so‘z boshida, unlidan va ъ/ь dan keyin ye; undoshdan keyin e:
  ер → yer, поезд → poyezd, келди → keldi;
- ё, ю, я mos ravishda yo, yu, ya;
- ц so‘z boshida, undoshdan keyin va so‘z oxirida s; so‘z ichida
  unlidan keyin ts: цирк → sirk, концерт → konsert, лицей → litsey,
  милиция → militsiya, абзац → abzas;
- ъ odatda U+02BC tutuq belgisi ʼ bo‘ladi: маъно → maʼno;
- ў dan keyingi ъ alohida tutuq sifatida takrorlanmaydi:
  мўъжиза → möjiza;
- объект, субъект, подъезд, инъекция kabi o‘zlashmalardagi ъ yozilmaydi,
  ammo keyingi ye/yu/ya saqlanadi;
- ь odatda tushadi; keyingi unli y talab qilsa qo‘shiladi:
  альбом → albom, компьютер → kompyuter, почтальон → poçtalyon;
- butunlay bosh harfli so‘zlar bosh harfligicha qoladi:
  ЁШЛАР → YOŞLAR;
- o‘zbek alifbosiga kirmaydigan, lekin ayrim kirill matnlarida uchraydigan
  щ xavfsiz, yo‘qotishsiz tarzda şç bo‘ladi: ЩУКА → ŞÇUKA;
- tinish belgilari, raqamlar, bo‘shliqlar, emoji va satr/paragraflar
  o‘zgarmaydi;
- Unicode matn NFC ko‘rinishiga keltiriladi, shuning uchun ajratib
  yozilgan у + breve ham ў sifatida o‘qiladi.

ц uchun yonidagi harflardan bilinmaydigan bir nechta mashhur imlo
istisnolari ham kiritilgan: ацетон → aseton, ацетилен → asetilen va
телецентр → telesentr.

## Chegara

Bu deterministik **transliteratsiya**, tarjima yoki to‘liq imlo lug‘ati
emas. Masalan, ruscha o‘zlashmaning adabiy o‘zbekcha shakli harfma-harf
natijadan farq qilishi mumkin: сентябрь → sentyabr (adabiy shakli:
sentabr), бюджет → byudjet (adabiy shakli: budjet). Bunday lug‘aviy
me’yorlashtirish dastur vazifasiga kirmaydi. Noma’lum kirill belgisi
o‘chirilmaydi — xavfsiz tarzda o‘z holicha qoldiriladi.

Real-time rejim yozuv tilini lug‘at orqali aniqlamaydi. Shu sabab inglizcha
`shop/chat` ham eski lotin rejimi ON bo‘lsa `şop/çat` bo‘ladi. Inglizcha
matn, kod yoki URL yozganda **eski lotin** rejimini alohida OFF qilib,
kirill rejimini ishlatishda davom etish mumkin. Maxsus ilovalarda login,
parol yoki boshqa maxfiy matn yozayotganda barcha avtomatik rejimlarni OFF
qiling.
Lotin → kirill rejimida inglizcha yoki kod matni ham kirillga o‘tishi
mumkin; bunday matnda tray tugmasidan OFF qiling.

Windows xavfsizlik chegarasi sabab oddiy huquqda ishlayotgan Yangi Lotin
administrator huquqida ochilgan boshqa dastur ichiga tugma yubora olmaydi.
Shunday dasturda ishlatish kerak bo‘lsa, `YangiLotin.exe`ni ham **Run as
administrator** orqali oching.

Sichqon bosilishi, oynani almashtirish, navigatsiya tugmasi yoki
Ctrl/Alt/Win yorlig‘i joriy so‘z kontekstini tozalaydi. Bu matn kursorini
o‘zgartirgandan keyin eski so‘zning tasodifan tahrirlanishiga yo‘l qo‘ymaydi.

## Fayllar

- app.py — sodda ishga tushirgich;
- yangi_lotin/transliterator.py — yangi lotinga o‘girish mexanizmi;
- yangi_lotin/reverse.py — eski va yangi lotindan kirillga o‘girish;
- yangi_lotin/live_mode.py — Windows bo‘ylab real-time klaviatura xizmati;
- yangi_lotin/mode_state.py — mustaqil rejim tanlovi va saqlangan holat;
- yangi_lotin/autostart.py — Windows bilan avtomatik ishga tushirish;
- yangi_lotin/tray.py — bir bosishda umumiy ON/OFF va alohida rejimlar;
- yangi_lotin/gui.py — qo‘lda konverter va rejim boshqaruvi;
- tests/test_transliterator.py — asosiy o‘girish testlari;
- tests/test_old_latin.py — eski lotin va apostrof variantlari testlari;
- tests/test_reverse.py — lotindan kirillga o‘girish testlari;
- tests/test_live_mode.py — real-time kompozitsiya testlari;
- tests/test_mode_state.py — rejimlarni yoqish, o‘chirish va saqlash testlari;
- tests/test_autostart.py — Windows ishga tushish sozlamasi testlari;
- tests/test_gui.py — oynadagi yo‘nalish, qo‘yish, Enter va eskirgan natija testlari;
- build.ps1 — test va portativ EXE yig‘ish;
- release.ps1 — EXE, ikki ZIP va SHA-256 yig‘indilarini tayyorlash;
- packaging/version_info.txt — Windows fayl metama’lumoti;
- packaging/YangiLotin.ico — dastur belgisi;
- packaging/make_icon.py — belgini qayta yaratish skripti (Pillow kerak);
- .github/workflows/ci.yml — Windows avtomatik sinov va yig‘ish;
- pyproject.toml — loyiha metama’lumoti;
- CHANGELOG.md — versiyalar bo‘yicha o‘zgarishlar;
- LICENSE — MIT litsenziyasi.

## Dasturni olib tashlash

Avval **WINDOWS BILAN BOSHLASH**ni OFF qiling va tray menyusidan **Çiqiş**ni
tanlang. So‘ng portativ EXE faylini o‘chiring. Agar qolgan sozlamalar va
avtomatik boshlash uchun saqlangan nusxa ham kerak bo‘lmasa,
`%LOCALAPPDATA%\YangiLotin\settings.json` hamda
`%LOCALAPPDATA%\Programs\YangiLotin\YangiLotin.exe` fayllarini o‘chiring.
Bu fayllarda yozgan matningiz saqlanmaydi.

## Litsenziya

MIT. Tijoriy va notijoriy loyihalarda ishlatish, o‘zgartirish va
tarqatish mumkin; litsenziya matnini saqlang.

package uz.shohruhxaydarov.yangilotin

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class TextConverterTest {
    @Test fun cyrillicWordsMatchWindows() {
        val cases = mapOf(
            "Ўзбекистон" to "Özbekiston", "Қўнғироқ" to "Qönğiroq",
            "Ғалла" to "Ğalla", "Шаҳар" to "Şahar", "Чирчиқ" to "Çirçiq",
            "чўл" to "çöl", "тоғ" to "toğ", "ер" to "yer", "Европа" to "Yevropa",
            "поезд" to "poyezd", "келди" to "keldi", "ёш" to "yoş",
            "юрак" to "yurak", "яхши" to "yaxşi"
        )
        cases.forEach { (source, expected) ->
            assertEquals(source, expected, TextConverter.cyrillicToNew(source))
        }
    }

    @Test fun cyrillicLoansAndSignsMatchWindows() {
        val cases = mapOf(
            "цирк" to "sirk", "концерт" to "konsert", "акция" to "aksiya",
            "лицей" to "litsey", "милиция" to "militsiya",
            "конституция" to "konstitutsiya", "пицца" to "pitssa",
            "ацетон" to "aseton", "телецентр" to "telesentr",
            "маъно" to "maʼno", "мўъжиза" to "möjiza",
            "объект" to "obyekt", "инъекция" to "inyeksiya",
            "компьютер" to "kompyuter", "пьеса" to "pyesa"
        )
        cases.forEach { (source, expected) ->
            assertEquals(source, expected, TextConverter.cyrillicToNew(source))
        }
    }

    @Test fun capitalisationAndUnicodeMatchWindows() {
        val cases = mapOf(
            "Ёш" to "Yoş", "ЁШ" to "YOŞ", "ЕЧИМ" to "YEÇIM",
            "ЮЛДУЗ" to "YULDUZ", "МИЛИЦИЯ" to "MILITSIYA",
            "ЁшЛАР" to "YoşLAR", "У\u0306збекистон" to "Özbekiston",
            "Е\u0308ш" to "Yoş"
        )
        cases.forEach { (source, expected) ->
            assertEquals(source, expected, TextConverter.cyrillicToNew(source))
        }
        assertEquals("Salom, dunyo! 2026 😊\r\n\r\nYangi satr.",
            TextConverter.cyrillicToNew("Салом, дунё! 2026 😊\r\n\r\nЯнги сатр."))
    }

    @Test fun oldLatinPairsAndQuotesMatchWindows() {
        val cases = mapOf(
            "shahar" to "şahar", "chiroyli" to "çiroyli",
            "o'zbekiston" to "özbekiston", "g'alaba" to "ğalaba",
            "o'quvchi" to "öquvçi", "g'isht" to "ğişt",
            "SHOVQIN" to "ŞOVQIN", "CHIROYLI" to "ÇIROYLI",
            "O'G'IL" to "ÖĞIL", "Sh Ch sH cH" to "Ş Ç Ş Ç",
            "'go'" to "'go'", "‘o’" to "‘o’",
            "'o''" to "'ö'", "‘oʼ’" to "‘ö’"
        )
        cases.forEach { (source, expected) ->
            assertEquals(source, expected, TextConverter.modernizeOldLatin(source))
        }
        for (mark in "'`´‘’ʻʼ")
            assertEquals("ö ğ Ö Ğ", TextConverter.modernizeOldLatin("o$mark g$mark O$mark G$mark"))
        assertEquals("Şahar va şahar", TextConverter.toNewLatin("Шаҳар va shahar"))
        assertEquals("sh", TextConverter.toNewLatin("сҳ"))
    }

    @Test fun reverseWordsAndLoansMatchWindows() {
        val cases = mapOf(
            "shahar" to "шаҳар", "chiroyli" to "чиройли",
            "o'zbek" to "ўзбек", "g'alaba" to "ғалаба",
            "şahar" to "шаҳар", "çöl" to "чўл",
            "özbekiston" to "ўзбекистон", "qönğiroq" to "қўнғироқ",
            "yoş" to "ёш", "yurak" to "юрак", "yaxşi" to "яхши",
            "Şahar" to "Шаҳар", "CHIROYLI" to "ЧИРОЙЛИ",
            "YOŞLAR" to "ЁШЛАР", "YEÇIM" to "ЕЧИМ",
            "maʼno" to "маъно", "san'at" to "санъат",
            "sirk" to "цирк", "sirka" to "сирка",
            "konsert" to "концерт", "aksiya" to "акция",
            "obyekt" to "объект", "kompyuter" to "компьютер",
            "iyun" to "июнь", "iyunda" to "июнда",
            "sentyabr" to "сентябрь", "sentyabrda" to "сентябрда",
            "poçtalyon" to "почтальон", "möjiza" to "мўъжиза"
        )
        cases.forEach { (source, expected) ->
            assertEquals(source, expected, TextConverter.latinToCyrillic(source))
        }
        assertEquals("Салом, дунё! 2026 😊\r\n\r\nСалом",
            TextConverter.latinToCyrillic("Salom, dunyo! 2026 😊\r\n\r\nСалом"))
    }

    @Test fun sourceGateMatchesEachMode() {
        assertTrue(TextConverter.isSourceCharacter('ш', ConversionMode.CYRILLIC_TO_NEW))
        assertFalse(TextConverter.isSourceCharacter('s', ConversionMode.CYRILLIC_TO_NEW))
        assertTrue(TextConverter.isSourceCharacter('s', ConversionMode.OLD_TO_NEW))
        assertFalse(TextConverter.isSourceCharacter('ш', ConversionMode.OLD_TO_NEW))
        assertTrue(TextConverter.isSourceCharacter('ş', ConversionMode.LATIN_TO_CYRILLIC))
        assertFalse(TextConverter.isSourceCharacter('s', ConversionMode.OFF))
    }
}

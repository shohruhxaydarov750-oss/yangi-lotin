package uz.shohruhxaydarov.yangilotin

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class LiveComposerTest {
    private fun apply(visible: String, edit: EditPlan): String =
        visible.dropLast(edit.backspaces) + edit.insert

    @Test fun eachPrefixMatchesFullConverter() {
        for ((word, mode) in listOf(
            "shahar" to ConversionMode.OLD_TO_NEW,
            "chiroyli" to ConversionMode.OLD_TO_NEW,
            "o'zbek" to ConversionMode.OLD_TO_NEW,
            "Ўзбекистон" to ConversionMode.CYRILLIC_TO_NEW,
            "ЁШ" to ConversionMode.CYRILLIC_TO_NEW,
            "shahar" to ConversionMode.LATIN_TO_CYRILLIC,
            "obyekt" to ConversionMode.LATIN_TO_CYRILLIC
        )) {
            val composer = LiveComposer(renderer = { TextConverter.convert(it, mode) })
            var visible = ""
            for (char in word) {
                visible = apply(visible, composer.feed(char))
                assertEquals(word, TextConverter.convert(composer.sourceToken, mode), visible)
            }
        }
    }

    @Test fun oneBackspaceDeletesOneVisibleLetter() {
        for ((source, mode, letter) in listOf(
            Triple("sh", ConversionMode.OLD_TO_NEW, "ş"),
            Triple("ch", ConversionMode.OLD_TO_NEW, "ç"),
            Triple("o'", ConversionMode.OLD_TO_NEW, "ö"),
            Triple("g'", ConversionMode.OLD_TO_NEW, "ğ"),
            Triple("SH", ConversionMode.OLD_TO_NEW, "Ş"),
            Triple("sh", ConversionMode.LATIN_TO_CYRILLIC, "ш"),
            Triple("yo", ConversionMode.LATIN_TO_CYRILLIC, "ё")
        )) {
            val composer = LiveComposer(renderer = { TextConverter.convert(it, mode) })
            var visible = ""
            source.forEach { visible = apply(visible, composer.feed(it)) }
            assertEquals(source, letter, visible)
            visible = apply(visible, composer.backspace())
            assertEquals(source, "", visible)
            assertFalse(composer.hasToken)
        }
    }

    @Test fun deletionAtEndOfWordDoesNotRevealFirstPairKey() {
        val composer = LiveComposer(renderer = { TextConverter.modernizeOldLatin(it) })
        var visible = ""
        "qo'sh".forEach { visible = apply(visible, composer.feed(it)) }
        assertEquals("qöş", visible)
        visible = apply(visible, composer.backspace())
        assertEquals("qö", visible)
        assertEquals("qo'", composer.sourceToken)
    }
}

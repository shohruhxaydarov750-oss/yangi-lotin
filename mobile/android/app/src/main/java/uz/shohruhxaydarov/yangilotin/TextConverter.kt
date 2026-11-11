package uz.shohruhxaydarov.yangilotin

import java.text.Normalizer
import java.util.Locale

enum class ConversionMode(val title: String) {
    OFF("OFF"),
    CYRILLIC_TO_NEW("Кирилл → Lotin"),
    OLD_TO_NEW("Eski → Yangi"),
    LATIN_TO_CYRILLIC("Lotin → Кирилл")
}

/** Deterministic spelling rules for the Android keyboard. */
object TextConverter {
    const val TUTUQ = '\u02BC'
    private val apostrophes = setOf('\'', '`', '´', '‘', '’', 'ʻ', 'ʼ')
    private val newLetters = setOf('ö', 'Ö', 'ğ', 'Ğ', 'ş', 'Ş', 'ç', 'Ç')
    private val directCyrillic = mapOf(
        'а' to "a", 'б' to "b", 'в' to "v", 'г' to "g", 'д' to "d",
        'ё' to "yo", 'ж' to "j", 'з' to "z", 'и' to "i", 'й' to "y",
        'к' to "k", 'л' to "l", 'м' to "m", 'н' to "n", 'о' to "o",
        'п' to "p", 'р' to "r", 'с' to "s", 'т' to "t", 'у' to "u",
        'ф' to "f", 'х' to "x", 'ч' to "ç", 'ш' to "ş", 'щ' to "ş",
        'ы' to "i", 'э' to "e", 'ю' to "yu", 'я' to "ya", 'ў' to "ö",
        'қ' to "q", 'ғ' to "ğ", 'ҳ' to "h"
    )
    private val cyrillicVowels = "аеёиоуўыэюя".toSet()
    private val plainVowelsAfterSoftSign = "аиоуўыэ".toSet()
    private val droppedHardSignPatterns = listOf(
        "объект", "объём", "объем", "субъект", "подъезд", "разъезд",
        "съезд", "адъют", "конъюнкт", "инъек"
    )
    private val forcedS = listOf("ацетон" to 1, "ацетилен" to 1, "телецентр" to 4)
    private val latinLetters = mapOf(
        'a' to "а", 'b' to "б", 'd' to "д", 'e' to "е", 'f' to "ф",
        'g' to "г", 'h' to "ҳ", 'i' to "и", 'j' to "ж", 'k' to "к",
        'l' to "л", 'm' to "м", 'n' to "н", 'o' to "о", 'p' to "п",
        'q' to "қ", 'r' to "р", 's' to "с", 't' to "т", 'u' to "у",
        'v' to "в", 'x' to "х", 'y' to "й", 'z' to "з",
        'ö' to "ў", 'ğ' to "ғ", 'ş' to "ш", 'ç' to "ч"
    )
    private val yVowels = mapOf('a' to "я", 'e' to "е", 'o' to "ё", 'u' to "ю")
    private val stemOverrides = listOf(
        "sirka" to "сирка", "sirk" to "цирк", "sement" to "цемент",
        "konsert" to "концерт", "aksiya" to "акция", "abzas" to "абзац",
        "aseton" to "ацетон", "asetilen" to "ацетилен",
        "telesentr" to "телецентр", "pitssa" to "пицца",
        "obyekt" to "объект", "subyekt" to "субъект",
        "podyezd" to "подъезд", "inyeksiya" to "инъекция",
        "adyutant" to "адъютант", "konyunktura" to "конъюнктура",
        "albom" to "альбом", "iyun" to "июнь", "iyul" to "июль",
        "rels" to "рельс", "kompyuter" to "компьютер",
        "pyesa" to "пьеса", "poçtalyon" to "почтальон",
        "sentyabr" to "сентябрь", "möjiza" to "мўъжиза",
        "mötadil" to "мўътадил", "mömin" to "мўъмин"
    ).sortedByDescending { it.first.length }

    private fun nfc(text: String) = Normalizer.normalize(text, Normalizer.Form.NFC)
    private fun lower(text: String) = text.lowercase(Locale.ROOT)
    private fun upper(text: String) = text.uppercase(Locale.ROOT)
    private fun isAsciiLatin(char: Char) = char in 'a'..'z' || char in 'A'..'Z'
    private fun isLatinLetter(char: Char) = isAsciiLatin(char) || char in newLetters

    fun isSourceCharacter(char: Char, mode: ConversionMode): Boolean = when (mode) {
        ConversionMode.OFF -> false
        ConversionMode.CYRILLIC_TO_NEW ->
            char.lowercaseChar() in directCyrillic || char.lowercaseChar() in "ецъь"
        ConversionMode.OLD_TO_NEW, ConversionMode.LATIN_TO_CYRILLIC ->
            isLatinLetter(char) || char in apostrophes
    }

    fun convert(text: String, mode: ConversionMode): String = when (mode) {
        ConversionMode.OFF -> text
        ConversionMode.CYRILLIC_TO_NEW -> cyrillicToNew(text)
        ConversionMode.OLD_TO_NEW -> modernizeOldLatin(text)
        ConversionMode.LATIN_TO_CYRILLIC -> latinToCyrillic(text)
    }

    fun toNewLatin(text: String): String = cyrillicToNew(modernizeOldLatin(text))

    private fun isCyrillicLetter(char: Char): Boolean {
        val code = char.code
        return char.isLetter() && (
            code in 0x0400..0x052F || code in 0x1C80..0x1C8F ||
                code in 0x2DE0..0x2DFF || code in 0xA640..0xA69F
            )
    }

    private fun patternCovers(token: String, pattern: String, index: Int): Boolean {
        val offset = pattern.indexOf('ъ')
        var start = token.indexOf(pattern)
        while (start >= 0) {
            if (start + offset == index) return true
            start = token.indexOf(pattern, start + 1)
        }
        return false
    }

    private fun forceS(token: String, index: Int): Boolean = forcedS.any { (pattern, offset) ->
        var start = token.indexOf(pattern)
        while (start >= 0) {
            if (start + offset == index) return@any true
            start = token.indexOf(pattern, start + 1)
        }
        false
    }

    private fun fragmentFor(token: String, index: Int): String {
        val char = token[index]
        directCyrillic[char]?.let { return it }
        return when (char) {
            'е' -> if (index == 0 || token[index - 1] in cyrillicVowels ||
                token[index - 1] in "ъь") "ye" else "e"
            'ц' -> if (forceS(token, index)) "s" else if (
                index > 0 && index < token.lastIndex && token[index - 1] in cyrillicVowels
            ) "ts" else "s"
            'ъ' -> if (index > 0 && token[index - 1] == 'ў' ||
                droppedHardSignPatterns.any { patternCovers(token, it, index) }
            ) "" else TUTUQ.toString()
            'ь' -> if (index < token.lastIndex && token[index + 1] in plainVowelsAfterSoftSign)
                "y" else ""
            else -> char.toString()
        }
    }

    private fun convertCyrillicToken(token: String): String {
        val lowered = lower(token)
        val cased = token.filter { it.isUpperCase() || it.isLowerCase() }
        val allCaps = cased.isNotEmpty() && cased.all { it.isUpperCase() }
        return buildString {
            token.forEachIndexed { index, source ->
                val fragment = fragmentFor(lowered, index)
                append(if (!source.isUpperCase()) fragment else if (allCaps) upper(fragment)
                else fragment.replaceFirstChar { it.uppercase(Locale.ROOT) })
            }
        }
    }

    fun cyrillicToNew(text: String): String {
        val source = nfc(text)
        val result = StringBuilder(source.length)
        var index = 0
        while (index < source.length) {
            if (!isCyrillicLetter(source[index])) {
                result.append(source[index++])
                continue
            }
            var end = index + 1
            while (end < source.length && isCyrillicLetter(source[end])) end++
            result.append(convertCyrillicToken(source.substring(index, end)))
            index = end
        }
        return nfc(result.toString())
    }

    private fun pairedClosingQuote(text: String, letterIndex: Int): Boolean {
        val closingIndex = letterIndex + 1
        val closing = text[closingIndex]
        val openers = when (closing) {
            '\'' -> setOf('\'')
            '’' -> setOf('\'', '‘', '’')
            else -> return false
        }
        if (closingIndex + 1 < text.length && (
                isLatinLetter(text[closingIndex + 1]) || text[closingIndex + 1] in apostrophes
            )) return false
        var start = letterIndex
        while (start > 0 && isLatinLetter(text[start - 1])) start--
        return start > 0 && text[start - 1] in openers
    }

    fun modernizeOldLatin(text: String): String {
        val source = nfc(text)
        val result = StringBuilder(source.length)
        var index = 0
        while (index < source.length) {
            val first = source[index]
            if (index + 1 < source.length) {
                val second = source[index + 1]
                val lowered = first.lowercaseChar()
                if ((lowered == 's' || lowered == 'c') && second.lowercaseChar() == 'h') {
                    val replacement = if (lowered == 's') 'ş' else 'ç'
                    result.append(if (first.isUpperCase() || second.isUpperCase())
                        replacement.uppercaseChar() else replacement)
                    index += 2
                    continue
                }
                if ((lowered == 'o' || lowered == 'g') && second in apostrophes &&
                    !pairedClosingQuote(source, index)
                ) {
                    val replacement = if (lowered == 'o') 'ö' else 'ğ'
                    result.append(if (first.isUpperCase()) replacement.uppercaseChar() else replacement)
                    index += 2
                    continue
                }
            }
            result.append(first)
            index++
        }
        return nfc(result.toString())
    }

    private fun case(fragment: String, source: String): String =
        if (source.any { it.isUpperCase() }) upper(fragment) else fragment

    private fun stemOverride(token: String): Pair<String, Int>? {
        for ((stem, unmodifiedTarget) in stemOverrides) {
            if (!lower(token).startsWith(stem)) continue
            val source = token.substring(0, stem.length)
            var target = unmodifiedTarget
            if (token.length > stem.length && stem in setOf("iyun", "iyul", "sentyabr"))
                target = target.dropLast(1)
            val letters = source.filter { it.isLetter() }
            if (letters.isNotEmpty() && letters.all { it.isUpperCase() })
                return upper(target) to stem.length
            if (letters.isNotEmpty() && letters.all { it.isLowerCase() })
                return target to stem.length
            if (source.first().isUpperCase() && source.drop(1).all { !it.isLetter() || it.isLowerCase() })
                return target.replaceFirstChar { it.uppercase(Locale.ROOT) } to stem.length
        }
        return null
    }

    private fun convertLatinToken(token: String): String {
        val exception = stemOverride(token)
        val result = StringBuilder()
        var index = 0
        if (exception != null) {
            result.append(exception.first)
            index = exception.second
        }
        while (index < token.length) {
            val first = token[index]
            val second = token.getOrNull(index + 1) ?: '\u0000'
            val lowerFirst = first.lowercaseChar()
            if (lowerFirst == 'y' && second.lowercaseChar() in yVowels) {
                result.append(case(yVowels.getValue(second.lowercaseChar()), "$first$second"))
                index += 2
                continue
            }
            if (lowerFirst == 't' && second.lowercaseChar() == 's') {
                result.append(case("ц", "$first$second"))
                index += 2
                continue
            }
            if (first in apostrophes) {
                val internal = index > 0 && index < token.lastIndex &&
                    isLatinLetter(token[index - 1]) && isLatinLetter(token[index + 1])
                result.append(if (internal) 'ъ' else first)
                index++
                continue
            }
            val fragment = latinLetters[lowerFirst]
            result.append(if (fragment == null) first.toString() else case(
                if (lowerFirst == 'e' && index == 0) "э" else fragment,
                first.toString()
            ))
            index++
        }
        return result.toString()
    }

    fun latinToCyrillic(text: String): String {
        val source = modernizeOldLatin(nfc(text))
        val result = StringBuilder(source.length)
        var index = 0
        while (index < source.length) {
            if (!isLatinLetter(source[index])) {
                result.append(source[index++])
                continue
            }
            var end = index + 1
            while (end < source.length && (
                    isLatinLetter(source[end]) || source[end] in apostrophes
                )) end++
            result.append(convertLatinToken(source.substring(index, end)))
            index = end
        }
        return nfc(result.toString())
    }
}

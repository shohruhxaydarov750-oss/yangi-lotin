package uz.shohruhxaydarov.yangilotin

data class EditPlan(val backspaces: Int, val insert: String)

/** Keeps only the unfinished word; no keystrokes are stored after it ends. */
class LiveComposer(
    private val renderer: (String) -> String,
    private val maxTokenLength: Int = 128
) {
    var sourceToken: String = ""
        private set
    var renderedToken: String = ""
        private set

    val hasToken: Boolean get() = sourceToken.isNotEmpty()

    fun reset() {
        sourceToken = ""
        renderedToken = ""
    }

    fun feed(character: Char): EditPlan {
        if (sourceToken.length >= maxTokenLength) reset()
        val previous = renderedToken
        sourceToken += character
        renderedToken = renderer(sourceToken)
        return difference(previous, renderedToken)
    }

    fun backspace(): EditPlan {
        if (!hasToken) return EditPlan(0, "")
        val previous = renderedToken
        val wanted = previous.dropLast(1)
        for (length in sourceToken.lastIndex downTo 0) {
            val candidate = sourceToken.substring(0, length)
            val rendered = renderer(candidate)
            if (rendered == wanted) {
                sourceToken = candidate
                renderedToken = rendered
                return difference(previous, renderedToken)
            }
        }
        sourceToken = sourceToken.dropLast(1)
        renderedToken = renderer(sourceToken)
        return difference(previous, renderedToken)
    }

    private fun difference(previous: String, current: String): EditPlan {
        var prefix = 0
        while (prefix < minOf(previous.length, current.length) && previous[prefix] == current[prefix])
            prefix++
        return EditPlan(previous.length - prefix, current.substring(prefix))
    }
}

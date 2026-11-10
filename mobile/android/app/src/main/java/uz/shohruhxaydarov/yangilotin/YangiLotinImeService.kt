package uz.shohruhxaydarov.yangilotin

import android.content.Context
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.RippleDrawable
import android.inputmethodservice.InputMethodService
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.text.InputType
import android.view.HapticFeedbackConstants
import android.view.KeyEvent
import android.view.MotionEvent
import android.view.View
import android.view.WindowInsets
import android.view.inputmethod.EditorInfo
import android.widget.Button
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.TextView

/** An ordinary Android input method: it edits only the field that owns its InputConnection. */
class YangiLotinImeService : InputMethodService() {
    private val handler = Handler(Looper.getMainLooper())
    private var root: LinearLayout? = null
    private var modeRow: LinearLayout? = null
    private var keyRows: LinearLayout? = null
    private var status: TextView? = null
    private var mode = ConversionMode.OLD_TO_NEW
    private var composer = composerFor(mode)
    private var secureField = false
    private var symbols = false
    private var cyrillicLayout = false
    private var shift = false
    private var capsLock = false
    private var lastShiftTap = 0L
    private val letterButtons = mutableListOf<Pair<Button, Char>>()
    private val consumedHardwareKeys = mutableSetOf<Int>()
    private var repeatDelete: Runnable? = null

    private val dark: Boolean
        get() = resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK ==
            Configuration.UI_MODE_NIGHT_YES
    private val keyboardBackground: Int get() = Color.parseColor(if (dark) "#202633" else "#E8EDF6")
    private val keyBackground: Int get() = Color.parseColor(if (dark) "#364153" else "#FFFFFF")
    private val keyForeground: Int get() = Color.parseColor(if (dark) "#F7FAFF" else "#172033")
    private val mutedBackground: Int get() = Color.parseColor(if (dark) "#2C3545" else "#D7DFEC")
    private val blue = Color.parseColor("#246BFE")

    override fun onCreate() {
        super.onCreate()
        val saved = getSharedPreferences("keyboard", MODE_PRIVATE).getString("mode", null)
        mode = ConversionMode.entries.firstOrNull { it.name == saved } ?: ConversionMode.OLD_TO_NEW
        cyrillicLayout = mode == ConversionMode.CYRILLIC_TO_NEW
        composer = composerFor(mode)
    }

    override fun onCreateInputView(): View {
        val keyboard = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(3), dp(4), dp(3), dp(6))
            setBackgroundColor(keyboardBackground)
            setOnApplyWindowInsetsListener { view, insets ->
                val navigation = if (Build.VERSION.SDK_INT >= 30) {
                    maxOf(
                        insets.getInsets(WindowInsets.Type.navigationBars()).bottom,
                        insets.getInsets(WindowInsets.Type.tappableElement()).bottom
                    )
                } else {
                    @Suppress("DEPRECATION")
                    val legacyBottom = insets.systemWindowInsetBottom
                    legacyBottom
                }
                view.setPadding(dp(3), dp(4), dp(3), dp(6) + navigation)
                insets
            }
        }
        root = keyboard
        status = TextView(this).apply {
            textSize = 12f
            setTextColor(if (dark) Color.parseColor("#C2D2EA") else Color.parseColor("#40516B"))
            setPadding(dp(8), 0, dp(8), dp(3))
        }.also { keyboard.addView(it) }
        modeRow = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }.also {
            keyboard.addView(it)
        }
        keyRows = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }.also {
            keyboard.addView(it)
        }
        renderKeyboard()
        return keyboard
    }

    override fun onStartInput(attribute: EditorInfo?, restarting: Boolean) {
        super.onStartInput(attribute, restarting)
        composer.reset()
        secureField = isProtectedField(attribute?.inputType ?: 0)
        shift = false
        capsLock = false
        symbols = false
        renderKeyboard()
    }

    override fun onFinishInput() {
        composer.reset()
        stopRepeatingDelete()
        super.onFinishInput()
    }

    override fun onDestroy() {
        stopRepeatingDelete()
        super.onDestroy()
    }

    private fun composerFor(direction: ConversionMode) =
        LiveComposer(renderer = { TextConverter.convert(it, direction) })

    private fun setMode(next: ConversionMode) {
        if (mode == next) return
        mode = next
        if (next != ConversionMode.OFF) cyrillicLayout = next == ConversionMode.CYRILLIC_TO_NEW
        composer = composerFor(next)
        getSharedPreferences("keyboard", MODE_PRIVATE).edit().putString("mode", next.name).apply()
        symbols = false
        renderKeyboard()
    }

    private fun isProtectedField(inputType: Int): Boolean {
        val kind = inputType and InputType.TYPE_MASK_CLASS
        val variation = inputType and InputType.TYPE_MASK_VARIATION
        return kind == InputType.TYPE_CLASS_TEXT && variation in setOf(
            InputType.TYPE_TEXT_VARIATION_PASSWORD,
            InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD,
            InputType.TYPE_TEXT_VARIATION_WEB_PASSWORD
        ) || kind == InputType.TYPE_CLASS_NUMBER &&
            variation == InputType.TYPE_NUMBER_VARIATION_PASSWORD
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density + 0.5f).toInt()

    private fun surface(color: Int, radius: Int = 8): RippleDrawable {
        val fill = GradientDrawable().apply {
            shape = GradientDrawable.RECTANGLE
            cornerRadius = dp(radius).toFloat()
            setColor(color)
        }
        return RippleDrawable(ColorStateList.valueOf(0x33446BFE), fill, null)
    }

    private fun key(
        label: String,
        weight: Float = 1f,
        prominent: Boolean = false,
        quiet: Boolean = false,
        height: Int = 48,
        action: () -> Unit
    ): Button = Button(this).apply {
        text = label
        isAllCaps = false
        textSize = if (label.length > 8) 11f else if (label.length > 4) 13f else 19f
        minHeight = 0
        minimumHeight = 0
        minWidth = 0
        minimumWidth = 0
        setPadding(0, 0, 0, 0)
        background = surface(if (prominent) blue else if (quiet) mutedBackground else keyBackground)
        setTextColor(if (prominent) Color.WHITE else keyForeground)
        layoutParams = LinearLayout.LayoutParams(0, dp(height), weight).apply {
            setMargins(dp(2), dp(2), dp(2), dp(2))
        }
        setOnClickListener {
            it.performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP)
            action()
        }
    }

    private fun renderKeyboard() {
        if (root == null) return
        status?.text = when {
            secureField -> "MAXFIY MAYDON · o‘girish to‘xtatilgan"
            mode == ConversionMode.OFF -> "O‘GIRISH OFF · oddiy yozish"
            else -> "${mode.title} · matn telefondan chiqmaydi"
        }
        modeRow?.removeAllViews()
        val labels = listOf("OFF", "КИР→Y", "ESKI→Y", "Y→КИР")
        ConversionMode.entries.forEachIndexed { index, direction ->
            modeRow?.addView(key(labels[index], prominent = mode == direction, height = 38) {
                setMode(direction)
            }.apply { textSize = 11f })
        }
        letterButtons.clear()
        keyRows?.removeAllViews()
        if (symbols) {
            addCharacterRow("1234567890")
            addCharacterRow("@#%&-+()/")
            addCharacterRow("*\"':;!?", lastLetters = true)
        } else if (cyrillicLayout) {
            addCharacterRow("қғҳёъэщ")
            addCharacterRow("йцукенгшўзх")
            addCharacterRow("фывапролдж")
            addCharacterRow("ячсмитьбю", lastLetters = true)
        } else {
            addCharacterRow("qwertyuiop")
            addCharacterRow("asdfghjkl")
            addCharacterRow("zxcvbnm", lastLetters = true)
        }
        addBottomRow()
    }

    private fun addCharacterRow(characters: String, lastLetters: Boolean = false) {
        val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        keyRows?.addView(row)
        if (lastLetters && !symbols)
            row.addView(key("⇧", 1.45f, quiet = true) { toggleShift() })
        for (base in characters) {
            val button = key(letterLabel(base)) { insertCharacter(letterValue(base)) }
            row.addView(button)
            if (!symbols) {
                letterButtons += button to base
                val special = when (base) {
                    'o' -> 'ö'; 'g' -> 'ğ'; 's' -> 'ş'; 'c' -> 'ç'
                    else -> null
                }
                if (special != null) {
                    button.setOnLongClickListener {
                        insertCharacter(letterValue(special))
                        true
                    }
                }
            }
        }
        if (lastLetters) {
            val delete = key("⌫", 1.45f, quiet = true) { backspace() }
            delete.setOnTouchListener { view, event ->
                when (event.actionMasked) {
                    MotionEvent.ACTION_DOWN -> {
                        view.performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP)
                        backspace()
                        repeatDelete = Runnable { repeatBackspace() }
                        handler.postDelayed(repeatDelete!!, 430)
                        true
                    }
                    MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                        stopRepeatingDelete()
                        true
                    }
                    else -> true
                }
            }
            row.addView(delete)
        }
    }

    private fun addBottomRow() {
        val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        keyRows?.addView(row)
        row.addView(key(if (symbols) "ABC" else "?123", 1.25f, quiet = true, height = 52) {
            symbols = !symbols
            renderKeyboard()
        })
        row.addView(key(",", 0.65f, height = 52) { insertLiteral(",") })
        row.addView(key("ʼ", 0.65f, height = 52) { insertCharacter('ʼ') })
        row.addView(key("🌐", 0.9f, quiet = true, height = 52) {
            if (shouldOfferSwitchingToNextInputMethod()) switchToNextInputMethod(false)
            else (getSystemService(Context.INPUT_METHOD_SERVICE) as android.view.inputmethod.InputMethodManager)
                .showInputMethodPicker()
        }.apply { contentDescription = "Boshqa klaviaturaga o‘tish" })
        row.addView(key("bo‘sh joy", 3.0f, height = 52) { insertLiteral(" ") })
        row.addView(key(".", 0.65f, height = 52) { insertLiteral(".") })
        row.addView(key("↵", 1.0f, prominent = true, height = 52) { enter() })
    }

    private fun letterLabel(base: Char): String = letterValue(base).toString()
    private fun letterValue(base: Char): Char =
        if (shift || capsLock) base.uppercaseChar() else base

    private fun toggleShift() {
        val now = android.os.SystemClock.uptimeMillis()
        if (now - lastShiftTap < 350) {
            capsLock = !capsLock
            shift = capsLock
        } else {
            capsLock = false
            shift = !shift
        }
        lastShiftTap = now
        refreshLetterLabels()
    }

    private fun refreshLetterLabels() {
        letterButtons.forEach { (button, base) -> button.text = letterLabel(base) }
    }

    private fun insertLiteral(text: String) {
        composer.reset()
        currentInputConnection?.commitText(text, 1)
        if (shift && !capsLock) {
            shift = false
            refreshLetterLabels()
        }
    }

    private fun insertCharacter(character: Char) {
        val connection = currentInputConnection ?: return
        val active = !secureField && mode != ConversionMode.OFF &&
            TextConverter.isSourceCharacter(character, mode)
        if (!active) {
            insertLiteral(character.toString())
            return
        }
        if (!connection.getSelectedText(0).isNullOrEmpty()) composer.reset()
        if (composer.hasToken && !renderedSuffixMatches()) composer.reset()
        val oldRendered = composer.renderedToken
        val edit = composer.feed(character)
        if (edit.backspaces > 0 && !suffixMatches(oldRendered)) {
            composer.reset()
            composer.feed(character)
            connection.commitText(character.toString(), 1)
        } else {
            applyEdit(edit)
        }
        if (shift && !capsLock) {
            shift = false
            refreshLetterLabels()
        }
    }

    private fun suffixMatches(expected: String): Boolean {
        if (expected.isEmpty()) return true
        val before = currentInputConnection?.getTextBeforeCursor(expected.length, 0)
        return before?.toString() == expected
    }

    private fun renderedSuffixMatches(): Boolean = suffixMatches(composer.renderedToken)

    private fun applyEdit(edit: EditPlan) {
        val connection = currentInputConnection ?: return
        connection.beginBatchEdit()
        try {
            if (edit.backspaces > 0 && !connection.deleteSurroundingText(edit.backspaces, 0)) {
                composer.reset()
                return
            }
            if (edit.insert.isNotEmpty() && !connection.commitText(edit.insert, 1)) composer.reset()
        } finally {
            connection.endBatchEdit()
        }
    }

    private fun backspace() {
        val connection = currentInputConnection ?: return
        if (!connection.getSelectedText(0).isNullOrEmpty()) {
            composer.reset()
            connection.commitText("", 1)
            return
        }
        if (composer.hasToken && !renderedSuffixMatches()) composer.reset()
        if (composer.hasToken) {
            val edit = composer.backspace()
            applyEdit(edit)
        } else if (!connection.deleteSurroundingTextInCodePoints(1, 0)) {
            connection.sendKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_DEL))
            connection.sendKeyEvent(KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_DEL))
        }
    }

    private fun repeatBackspace() {
        backspace()
        repeatDelete?.let { handler.postDelayed(it, 55) }
    }

    private fun stopRepeatingDelete() {
        repeatDelete?.let { handler.removeCallbacks(it) }
        repeatDelete = null
    }

    private fun enter() {
        composer.reset()
        val action = currentInputEditorInfo?.imeOptions?.and(EditorInfo.IME_MASK_ACTION)
            ?: EditorInfo.IME_ACTION_NONE
        if (action != EditorInfo.IME_ACTION_NONE && action != EditorInfo.IME_ACTION_UNSPECIFIED) {
            currentInputConnection?.performEditorAction(action)
        } else {
            currentInputConnection?.commitText("\n", 1)
        }
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent): Boolean {
        if (keyCode == KeyEvent.KEYCODE_SHIFT_LEFT ||
            keyCode == KeyEvent.KEYCODE_SHIFT_RIGHT ||
            keyCode == KeyEvent.KEYCODE_CAPS_LOCK
        ) return super.onKeyDown(keyCode, event)
        if (event.isCtrlPressed || event.isAltPressed || event.isMetaPressed) {
            composer.reset()
            return super.onKeyDown(keyCode, event)
        }
        when (keyCode) {
            KeyEvent.KEYCODE_DEL -> backspace()
            KeyEvent.KEYCODE_ENTER -> enter()
            else -> {
                val value = event.unicodeChar
                if (value <= 0 || value > Char.MAX_VALUE.code) {
                    composer.reset()
                    return super.onKeyDown(keyCode, event)
                }
                insertCharacter(value.toChar())
            }
        }
        consumedHardwareKeys += keyCode
        return true
    }

    override fun onKeyUp(keyCode: Int, event: KeyEvent): Boolean =
        if (consumedHardwareKeys.remove(keyCode)) true else super.onKeyUp(keyCode, event)
}

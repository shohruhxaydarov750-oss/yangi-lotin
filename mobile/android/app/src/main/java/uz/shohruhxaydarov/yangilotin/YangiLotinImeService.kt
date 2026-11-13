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
import android.widget.LinearLayout

/** An ordinary Android input method: it edits only the field that owns its InputConnection. */
class YangiLotinImeService : InputMethodService() {
    private val handler = Handler(Looper.getMainLooper())
    private var root: LinearLayout? = null
    private var modeRow: LinearLayout? = null
    private var keyRows: LinearLayout? = null
    private var mode = ConversionMode.OLD_TO_NEW
    private var composer = composerFor(mode)
    private var secureField = false
    private var symbols = false
    private var emoji = false
    private var cyrillicLayout = false
    private var shift = false
    private var capsLock = false
    private var lastShiftTap = 0L
    private val letterButtons = mutableListOf<Pair<Button, Char>>()
    private var shiftButton: Button? = null
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
        stopRepeatingDelete()
        consumedHardwareKeys.clear()
        composer.reset()
        secureField = isProtectedField(attribute?.inputType ?: 0)
        shift = false
        capsLock = false
        symbols = false
        emoji = false
        renderKeyboard()
    }

    override fun onFinishInput() {
        composer.reset()
        consumedHardwareKeys.clear()
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
        emoji = false
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
        modeRow?.removeAllViews()
        val labels = listOf("OFF", "КИР→Y", "ESKI→Y", "Y→КИР")
        ConversionMode.entries.forEachIndexed { index, direction ->
            modeRow?.addView(key(labels[index], prominent = if (secureField) {
                direction == ConversionMode.OFF
            } else mode == direction, height = 38) {
                setMode(direction)
            }.apply {
                textSize = 11f
                if (secureField && direction != ConversionMode.OFF) isEnabled = false
                contentDescription = if (secureField && direction == ConversionMode.OFF)
                    "Maxfiy maydonda o‘girish to‘xtatilgan" else labels[index]
            })
        }
        letterButtons.clear()
        shiftButton = null
        keyRows?.removeAllViews()
        if (emoji) {
            addEmojiRows()
        } else if (symbols) {
            addCharacterRow("1234567890")
            addCharacterRow("@#%&-+()/")
            addCharacterRow("*\"':;!?,")
            addCharacterRow("[]{}<>_=\\", lastLetters = true)
        } else if (cyrillicLayout) {
            addCharacterRow("қғҳёъэщ", sideInset = 1.5f)
            addCharacterRow("йцукенгшўзх")
            addCharacterRow("фывапролдж")
            addCharacterRow("ячсмитьбю", lastLetters = true)
        } else {
            addNumberRow()
            addCharacterRow("qwertyuiop")
            addCharacterRow("asdfghjkl", sideInset = 0.5f)
            addCharacterRow("zxcvbnm", lastLetters = true)
        }
        addBottomRow()
        refreshLetterLabels()
    }

    private fun addNumberRow() {
        val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        keyRows?.addView(row)
        for (digit in "1234567890") {
            row.addView(key(digit.toString(), height = 38) { insertLiteral(digit.toString()) }
                .apply { textSize = 17f })
        }
    }

    private fun addEmojiRows() {
        val rows = listOf(
            listOf("😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "🙂"),
            listOf("😉", "😍", "🥰", "😘", "😎", "🤔", "😢", "😭", "😡", "🤗"),
            listOf("👍", "👏", "🙌", "👌", "💪", "🙏", "❤️", "💙", "🔥", "🎉"),
            listOf("🌸", "⭐", "☀️", "🎂", "🎁", "🇺🇿", "🚀", "💯", "✅")
        )
        rows.forEachIndexed { index, characters ->
            val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
            keyRows?.addView(row)
            characters.forEach { value ->
                row.addView(key(value) { insertLiteral(value) }.apply {
                    textSize = 22f
                    contentDescription = "Emoji $value"
                })
            }
            if (index == rows.lastIndex) row.addView(deleteKey())
        }
    }

    private fun addCharacterRow(
        characters: String,
        lastLetters: Boolean = false,
        sideInset: Float = 0f
    ) {
        val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        keyRows?.addView(row)
        if (sideInset > 0f)
            row.addView(View(this), LinearLayout.LayoutParams(0, dp(52), sideInset))
        if (lastLetters && !symbols) {
            val shiftKey = key("⇧", 1.45f, quiet = true) { toggleShift() }
            shiftButton = shiftKey
            row.addView(shiftKey)
        }
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
            row.addView(deleteKey())
        }
        if (sideInset > 0f)
            row.addView(View(this), LinearLayout.LayoutParams(0, dp(52), sideInset))
    }

    private fun deleteKey(): Button = key("⌫", 1.45f, quiet = true) { backspace() }.apply {
        contentDescription = "O‘chirish"
        setOnLongClickListener {
            backspace()
            repeatDelete = Runnable { repeatBackspace() }
            handler.postDelayed(repeatDelete!!, 70)
            true
        }
        setOnTouchListener { _, event ->
            if (event.actionMasked == MotionEvent.ACTION_UP ||
                event.actionMasked == MotionEvent.ACTION_CANCEL) stopRepeatingDelete()
            false
        }
    }

    private fun addBottomRow() {
        val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        keyRows?.addView(row)
        row.addView(key(if (symbols) "ABC" else "?123", 1.25f, quiet = true, height = 52) {
            symbols = !symbols
            emoji = false
            renderKeyboard()
        })
        row.addView(key(if (emoji) "ABC" else "☺", 0.65f, quiet = true, height = 52) {
            emoji = !emoji
            symbols = false
            renderKeyboard()
        }.apply { contentDescription = if (emoji) "Harflarga qaytish" else "Emoji" })
        row.addView(key("ʼ", 0.65f, height = 52) { insertCharacter('ʼ') })
        row.addView(key("🌐", 0.9f, quiet = true, height = 52) {
            if (shouldOfferSwitchingToNextInputMethod()) switchToNextInputMethod(false)
            else (getSystemService(Context.INPUT_METHOD_SERVICE) as android.view.inputmethod.InputMethodManager)
                .showInputMethodPicker()
        }.apply { contentDescription = "Boshqa klaviaturaga o‘tish" })
        row.addView(key("bo‘sh joy", 3.0f, height = 52) { insertLiteral(" ") })
        row.addView(key(".", 0.65f, height = 52) { insertLiteral(".") }.apply {
            contentDescription = "Nuqta. Uzoq bosish: vergul"
            setOnLongClickListener { insertLiteral(","); true }
        })
        row.addView(key("↵", 1.0f, prominent = true, height = 52) { enter() }.apply {
            contentDescription = "Yangi qator. Uzoq bosish: yuborish yoki davom etish"
            setOnLongClickListener { performEditorAction(); true }
        })
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
        shiftButton?.apply {
            text = if (capsLock) "⇪" else "⇧"
            background = surface(if (shift || capsLock) blue else mutedBackground)
            setTextColor(if (shift || capsLock) Color.WHITE else keyForeground)
            contentDescription = when {
                capsLock -> "Caps Lock yoqilgan"
                shift -> "Katta harf yoqilgan"
                else -> "Katta harf"
            }
        }
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
            applyEdit(composer.feed(character))
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
        } else {
            val before = connection.getTextBeforeCursor(2, 0)?.toString()
            if (!connection.deleteSurroundingTextInCodePoints(1, 0)) {
                val after = connection.getTextBeforeCursor(2, 0)?.toString()
                if (before == null || before == after) {
                    connection.sendKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_DEL))
                    connection.sendKeyEvent(KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_DEL))
                }
            }
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
        val info = currentInputEditorInfo
        val inputType = info?.inputType ?: 0
        val imeOptions = info?.imeOptions ?: 0
        if (EnterBehavior.shouldInsertNewline(inputType, imeOptions)) {
            currentInputConnection?.commitText("\n", 1)
        } else {
            performEditorAction()
        }
    }

    private fun performEditorAction() {
        composer.reset()
        val action = currentInputEditorInfo?.imeOptions?.and(EditorInfo.IME_MASK_ACTION)
            ?: EditorInfo.IME_ACTION_NONE
        if (action != EditorInfo.IME_ACTION_NONE && action != EditorInfo.IME_ACTION_UNSPECIFIED)
            currentInputConnection?.performEditorAction(action)
        else currentInputConnection?.commitText("\n", 1)
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
            KeyEvent.KEYCODE_ENTER -> if (event.isShiftPressed) insertLiteral("\n") else enter()
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

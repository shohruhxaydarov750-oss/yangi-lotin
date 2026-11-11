package uz.shohruhxaydarov.yangilotin

import android.app.Activity
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.RippleDrawable
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.text.Editable
import android.text.TextWatcher
import android.view.View
import android.view.WindowInsets
import android.view.inputmethod.InputMethodManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast

class MainActivity : Activity() {
    private val blue = Color.parseColor("#246BFE")
    private val ink = Color.parseColor("#172033")
    private val muted = Color.parseColor("#607086")
    private val paper = Color.parseColor("#F3F5F9")
    private var targetNewLatin = true
    private lateinit var setupStatus: TextView
    private lateinit var input: EditText
    private lateinit var output: TextView
    private lateinit var newButton: Button
    private lateinit var cyrillicButton: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = paper
        window.navigationBarColor = paper
        @Suppress("DEPRECATION")
        window.decorView.systemUiVisibility = View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR or
            View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR

        val outer = ScrollView(this).apply {
            isFillViewport = true
            setBackgroundColor(paper)
        }
        val page = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(18), dp(18), dp(18), dp(28))
        }
        outer.addView(page)
        if (Build.VERSION.SDK_INT >= 30) {
            page.setOnApplyWindowInsetsListener { view, insets ->
                val bars = insets.getInsets(WindowInsets.Type.systemBars())
                val keyboard = insets.getInsets(WindowInsets.Type.ime()).bottom
                view.setPadding(dp(18), dp(18) + bars.top, dp(18),
                    dp(28) + maxOf(bars.bottom, keyboard))
                if (::input.isInitialized && input.hasFocus() && keyboard > 0) {
                    view.post {
                        val position = IntArray(2)
                        input.getLocationOnScreen(position)
                        val visibleBottom = resources.displayMetrics.heightPixels - keyboard
                        val overflow = position[1] + input.height - visibleBottom + dp(12)
                        if (overflow > 0) outer.smoothScrollBy(0, overflow)
                    }
                }
                insets
            }
        } else {
            outer.fitsSystemWindows = true
        }
        setContentView(outer)

        page.addView(label("Yangi Lotin", 30f, ink, true))
        page.addView(label("Telefon uchun oflayn o‘zbek klaviaturasi", 15f, muted).apply {
            setPadding(0, dp(3), 0, dp(18))
        })

        val setup = card()
        page.addView(setup, sectionParams())
        setup.addView(label("Klaviaturani ishga tushiring", 19f, ink, true))
        setup.addView(label(
            "Bir marta yoqing va telefon klaviaturalari ro‘yxatidan Yangi Lotin’ni tanlang.",
            14f, muted
        ).apply { setPadding(0, dp(6), 0, dp(10)) })
        setupStatus = label("Holat tekshirilmoqda…", 14f, muted, true)
        setup.addView(setupStatus)
        setup.addView(actionButton("1. Sozlamalarda yoqish") {
            startActivity(Intent(Settings.ACTION_INPUT_METHOD_SETTINGS))
        }, sectionParams(top = 12))
        setup.addView(actionButton("2. Klaviaturani tanlash", primary = true) {
            (getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager)
                .showInputMethodPicker()
        }, sectionParams(top = 8))

        page.addView(label("Shu oynada o‘girish", 20f, ink, true).apply {
            setPadding(0, dp(16), 0, dp(8))
        })
        val converter = card()
        page.addView(converter, sectionParams())
        val targets = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        converter.addView(targets)
        newButton = actionButton("→ Yangi lotin", primary = true) {
            targetNewLatin = true
            refreshTargets()
            convertInput()
        }
        cyrillicButton = actionButton("→ Kirill") {
            targetNewLatin = false
            refreshTargets()
            convertInput()
        }
        targets.addView(newButton, LinearLayout.LayoutParams(0, dp(45), 1f).apply {
            rightMargin = dp(4)
        })
        targets.addView(cyrillicButton, LinearLayout.LayoutParams(0, dp(45), 1f).apply {
            leftMargin = dp(4)
        })

        converter.addView(label("KIRITILGAN MATN", 12f, muted, true).apply {
            setPadding(0, dp(17), 0, dp(5))
        })
        input = EditText(this).apply {
            hint = "Matn yozing yoki qo‘ying…"
            textSize = 17f
            setTextColor(ink)
            setHintTextColor(Color.parseColor("#98A4B5"))
            background = rounded(Color.parseColor("#F6F8FC"), 12)
            setPadding(dp(13), dp(11), dp(13), dp(11))
            minLines = 4
            maxLines = 9
            gravity = android.view.Gravity.TOP
            inputType = android.text.InputType.TYPE_CLASS_TEXT or
                android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE or
                android.text.InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
        }
        converter.addView(input, sectionParams())
        input.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) = Unit
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                convertInput()
            }
            override fun afterTextChanged(s: Editable?) = Unit
        })

        converter.addView(label("NATIJA", 12f, muted, true).apply {
            setPadding(0, dp(15), 0, dp(5))
        })
        output = label("Natija shu yerda chiqadi", 17f, muted).apply {
            background = rounded(Color.parseColor("#EDF3FF"), 12)
            setPadding(dp(13), dp(11), dp(13), dp(11))
            minHeight = dp(95)
        }
        converter.addView(output, sectionParams())

        val actions = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, dp(12), 0, 0)
        }
        converter.addView(actions)
        actions.addView(actionButton("Qo‘yish") {
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val text = clipboard.primaryClip?.getItemAt(0)?.coerceToText(this)?.toString()
            if (!text.isNullOrEmpty()) input.text?.replace(input.selectionStart, input.selectionEnd, text)
        }, LinearLayout.LayoutParams(0, dp(43), 1f).apply { rightMargin = dp(4) })
        actions.addView(actionButton("Nusxalash", primary = true) {
            val result = if (input.text.isNullOrEmpty()) "" else output.text.toString()
            if (result.isNotEmpty()) {
                val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                clipboard.setPrimaryClip(ClipData.newPlainText("Yangi Lotin natijasi", result))
                Toast.makeText(this, "Natija nusxalandi", Toast.LENGTH_SHORT).show()
            }
        }, LinearLayout.LayoutParams(0, dp(43), 1f).apply { rightMargin = dp(4) })
        actions.addView(actionButton("Tozalash") { input.text?.clear() },
            LinearLayout.LayoutParams(0, dp(43), 1f))

        page.addView(label(
            "Klaviatura faqat joriy matn maydonida ishlaydi. Parol maydonida o‘girish o‘chadi. " +
                "Matn internetga yuborilmaydi.",
            12f, muted
        ).apply { setPadding(dp(4), dp(13), dp(4), 0) })
        refreshTargets()
    }

    override fun onResume() {
        super.onResume()
        if (::setupStatus.isInitialized) refreshSetupStatus()
    }

    private fun refreshSetupStatus() {
        val manager = getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
        val enabled = manager.enabledInputMethodList.any {
            it.packageName == packageName && it.serviceName == YangiLotinImeService::class.java.name
        }
        val selected = Settings.Secure.getString(contentResolver, Settings.Secure.DEFAULT_INPUT_METHOD)
            ?.contains(packageName) == true
        setupStatus.text = when {
            selected -> "● TAYYOR — Yangi Lotin klaviaturasi tanlangan"
            enabled -> "● YOQILGAN — 2-qadamda klaviaturani tanlang"
            else -> "● HOZIRCHA O‘CHIQ — 1-qadamdan boshlang"
        }
        setupStatus.setTextColor(if (selected) Color.parseColor("#16805A") else muted)
    }

    private fun convertInput() {
        if (!::input.isInitialized || !::output.isInitialized) return
        val source = input.text?.toString().orEmpty()
        val result = if (targetNewLatin) TextConverter.toNewLatin(source)
            else TextConverter.latinToCyrillic(source)
        output.text = result.ifEmpty { "Natija shu yerda chiqadi" }
        output.setTextColor(if (result.isEmpty()) muted else ink)
    }

    private fun refreshTargets() {
        newButton.background = rounded(if (targetNewLatin) blue else paper, 9)
        cyrillicButton.background = rounded(if (targetNewLatin) paper else blue, 9)
        newButton.setTextColor(if (targetNewLatin) Color.WHITE else ink)
        cyrillicButton.setTextColor(if (targetNewLatin) ink else Color.WHITE)
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density + 0.5f).toInt()

    private fun rounded(color: Int, radius: Int): GradientDrawable = GradientDrawable().apply {
        shape = GradientDrawable.RECTANGLE
        cornerRadius = dp(radius).toFloat()
        setColor(color)
    }

    private fun card(): LinearLayout = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(dp(15), dp(15), dp(15), dp(15))
        background = rounded(Color.WHITE, 16)
    }

    private fun sectionParams(top: Int = 0): LinearLayout.LayoutParams =
        LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT).apply { topMargin = dp(top) }

    private fun label(text: String, size: Float, color: Int, bold: Boolean = false): TextView =
        TextView(this).apply {
            this.text = text
            textSize = size
            setTextColor(color)
            if (bold) typeface = android.graphics.Typeface.DEFAULT_BOLD
        }

    private fun actionButton(text: String, primary: Boolean = false, click: () -> Unit): Button =
        Button(this).apply {
            this.text = text
            isAllCaps = false
            textSize = 14f
            minHeight = 0
            minimumHeight = 0
            setTextColor(if (primary) Color.WHITE else ink)
            val surface = rounded(if (primary) blue else paper, 9)
            background = RippleDrawable(ColorStateList.valueOf(0x33446BFE), surface, null)
            setOnClickListener { click() }
        }
}

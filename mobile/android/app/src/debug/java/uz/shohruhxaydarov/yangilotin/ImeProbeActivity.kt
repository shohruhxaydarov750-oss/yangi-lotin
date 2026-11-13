package uz.shohruhxaydarov.yangilotin

import android.app.Activity
import android.os.Bundle
import android.text.Editable
import android.text.InputType
import android.text.TextWatcher
import android.view.WindowManager
import android.view.inputmethod.EditorInfo
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView

/** Debug-only editor that reproduces a messaging app's SEND action in emulator tests. */
class ImeProbeActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val container = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(24, 24, 24, 24)
        }
        val status = TextView(this).apply { text = "WAITING" }
        val message = EditText(this).apply {
            hint = "Message field"
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE
            imeOptions = EditorInfo.IME_ACTION_SEND
            minLines = 4
            setOnEditorActionListener { _, actionId, _ ->
                if (actionId == EditorInfo.IME_ACTION_SEND) {
                    status.text = "SEND"
                    true
                } else false
            }
        }
        val search = EditText(this).apply {
            hint = "Search field"
            inputType = InputType.TYPE_CLASS_TEXT
            imeOptions = EditorInfo.IME_ACTION_SEARCH
            setOnEditorActionListener { _, actionId, _ ->
                if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                    status.text = "SEARCH"
                    true
                } else false
            }
        }
        val password = EditText(this).apply {
            hint = "Password field"
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
            addTextChangedListener(object : TextWatcher {
                override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int,
                    after: Int) = Unit
                override fun onTextChanged(s: CharSequence?, start: Int, before: Int,
                    count: Int) {
                    status.text = if (s?.toString() == "sh") "PASSWORD_RAW" else "PASSWORD_OTHER"
                }
                override fun afterTextChanged(s: Editable?) = Unit
            })
        }
        container.addView(message)
        container.addView(search)
        container.addView(password)
        container.addView(status)
        setContentView(container)
        message.requestFocus()
        window.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_VISIBLE)
    }
}

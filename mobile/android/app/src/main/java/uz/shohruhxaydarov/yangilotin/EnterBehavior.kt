package uz.shohruhxaydarov.yangilotin

import android.text.InputType
import android.view.inputmethod.EditorInfo

/** A short Enter inserts a line break in messages; a long press uses the editor action. */
internal object EnterBehavior {
    fun shouldInsertNewline(inputType: Int, imeOptions: Int): Boolean {
        val action = imeOptions and EditorInfo.IME_MASK_ACTION
        if (action == EditorInfo.IME_ACTION_NONE || action == EditorInfo.IME_ACTION_UNSPECIFIED)
            return true
        if ((inputType and InputType.TYPE_MASK_CLASS) != InputType.TYPE_CLASS_TEXT) return false
        return (inputType and InputType.TYPE_TEXT_FLAG_MULTI_LINE) != 0 ||
            (imeOptions and EditorInfo.IME_FLAG_NO_ENTER_ACTION) != 0 ||
            action == EditorInfo.IME_ACTION_SEND
    }
}

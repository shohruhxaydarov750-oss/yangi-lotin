package uz.shohruhxaydarov.yangilotin

import android.text.InputType
import android.view.inputmethod.EditorInfo
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class EnterBehaviorTest {
    @Test fun enterInMessageFieldCreatesNewline() {
        val text = InputType.TYPE_CLASS_TEXT
        val multiline = text or InputType.TYPE_TEXT_FLAG_MULTI_LINE
        assertTrue(EnterBehavior.shouldInsertNewline(multiline, EditorInfo.IME_ACTION_SEND))
        assertTrue(EnterBehavior.shouldInsertNewline(text, EditorInfo.IME_ACTION_SEND))
        assertTrue(EnterBehavior.shouldInsertNewline(multiline, EditorInfo.IME_ACTION_DONE))
    }

    @Test fun explicitSearchAndGoActionsStillWork() {
        val text = InputType.TYPE_CLASS_TEXT
        assertFalse(EnterBehavior.shouldInsertNewline(text, EditorInfo.IME_ACTION_SEARCH))
        assertFalse(EnterBehavior.shouldInsertNewline(text, EditorInfo.IME_ACTION_GO))
        assertFalse(EnterBehavior.shouldInsertNewline(
            InputType.TYPE_CLASS_NUMBER, EditorInfo.IME_ACTION_SEND))
    }

    @Test fun editorsMayExplicitlyRequestAnEnterKey() {
        val text = InputType.TYPE_CLASS_TEXT
        assertTrue(EnterBehavior.shouldInsertNewline(text, EditorInfo.IME_ACTION_NONE))
        assertTrue(EnterBehavior.shouldInsertNewline(text,
            EditorInfo.IME_ACTION_SEND or EditorInfo.IME_FLAG_NO_ENTER_ACTION))
    }
}

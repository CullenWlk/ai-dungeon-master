Check /config.py for debug mode bool.

**To Play:** run 'python -m app.gui' after installing requirements

**Rolling:** when the ai asks you to make a roll, simply type "roll" or "rolling" to have it make that roll, or instead ask the chat for a different kind of roll if you do not think it selected the right trait for that particular roll.

**To injest new lore:** 'python -m app.rag.ingest'

structure of lorebook entries:

# Entry Name
Type: category
Tags: keyword1, keyword2, keyword3

Short but clear description paragraph(s).

---

**To edit the setting:** First clear and add in your own lorebook entries for the setting, then update /prompts.py with the introduction you would like to have to that setting. Then play.
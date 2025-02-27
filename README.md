<a href="https://www.buymeacoffee.com/andereoo" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-violet.png" alt="Buy Me A Coffee" style="height: 35px !important;width: 140px !important;" ></a>

# TkSolitaire

TkSolitaire is an accessible and embeddable solitaire game application written in Tkinter.

**Accessability:**
TkSolitaire comes bundled with accessibility options, making it easier for the elderly or those with hand injuries to play solitaire. They include:
* An auto-clicker
* A game finisher
* An option to use larger cards


**Installation:**
Windows users can download the installer from the releases page. Alternatively, the TkSolitaire source code can also be downloaded and run using Python on any OS.
TkSolitaire can be embedded into a Tkinter app:

```python
from TkSolitaire import SolitareGameFrame
import tkinter as tk

root = tk.Tk()
solitaire_frame = SolitareGameFrame(root)
solitaire_frame.pack(expand=True, fill="both")

root.mainloop()
 ```
 
**Screenshots:**

![Alt text](/resources/Screenshots/TkSolitaire-Ubuntu18-Screenshot.png?raw=true "TkSolitaire")

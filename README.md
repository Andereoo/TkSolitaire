# TkSolitaire

TkSolitaire is an accessible and embeddable solitaire game application written in Tkinter.

___
**Accessability:**
TkSolitaire comes bundled with accessibility options, making it easier for the elderly or those with hand injuries to play solitaire. They include:
* An auto-clicker
* A game finisher
* An option to use larger cards


___
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
 
___        
**Screenshots:**

![Alt text](/resources/Screenshots/TkSolitaire-Ubuntu18-Screenshot.png?raw=true "TkSolitaire")

# TkSolitaire
*An embeddable and accessable solitaire game for Tkinter and Python 3*

___
TkSolitaire is a script that allows you to play a simple game of solitaire. It is written for Python 3 on Linux and Windows.

___
**Accessability:**
TkSolitaire comes bundled with accessibility options, making it easier for the elderly or those with hand injuries to play solitaire. They include:
* An auto-clicker
* A game finisher
* An option to use larger cards


___
**Installation:**
Windows users can download the installer from the releases page. Alternatively, Linux and Windows users can also download the source code and run it with python.
TkSolitaire can be embedded into a Tkinter app:

    from TkSolitaire import SolitareGameFrame
    import tkinter as tk

    root = tk.Tk()
    solitaire_frame = SolitareGameFrame(root)
    solitaire_frame.pack(expand=True, fill="both")

    root.mainloop()
    
___        
**Screenshots:**
![Alt text](/resources/Screenshots/TkSolitaire-Ubuntu18-Screenshot.png?raw=true "Optional Title")

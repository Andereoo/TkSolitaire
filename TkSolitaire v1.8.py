# TkSolitaire, an embeddable and accessable solitaire game for Tkinter and Python 3
# This code has had many growing pains and is a bit of a mess, but hey, it works!

# This version is a slightly updated version of the original TkSolitaire game. 
# It has better support for window resizing, a nicer settings page, an information page, and the game finisher is much more responsive. 
# It might have some bugs. It might not.
# Enjoy!

import json
import os
import random
import threading

import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.colorchooser import askcolor

from tkinterweb import HtmlFrame
import webbrowser

from PIL import Image, ImageTk

DEFAULT_SETTINGS = {"movetype": "Drag",
                    "gamemode": "Practice Mode",
                    "canvas_default_item_hover_time": "300",
                    "default_cardsender_freeze_time": "600",
                    "show_footer": "True",
                    "show_header": "True",
                    "continuous_points": "True",
                    "card_back": "python_card_back",
                    "canvas_color": "#103b0a",
                    "larger_cards": "False"
                    }


class OptionBar(tk.Frame):
    def __init__(self, parent, invert=False, manager="pack", height=30, bg="#1c1a1a", fade_colors=None, **kwargs):
        tk.Frame.__init__(self, parent, height=height, bg=bg, **kwargs)
        try:
            self.colors = list(fade_colors)
        except:
            self.colors = ["#4f4f4f", "#484849", "#424142", "#3c3b3c", "#363435",
                           "#323030", "#2d2b2c", "#292727", "#262424", "#222020", "#1f1d1d", "#1c1a1a"]
        self.bg = bg
        self.fade(invert=invert, manager=manager)
        self.buffers = []

    def fade(self, invert, manager):
        if invert:
            if manager == "grid":
                tk.Frame(self, bg=self["bg"], height=3).grid(
                    row=0, column=0, columnspan=100, sticky="new")
                row = 1
                for color in reversed(self.colors):
                    tk.Frame(self, height=1, bg=color).grid(
                        row=row, column=0, columnspan=100, sticky="ew")
                    row += 1
            elif manager == "pack":
                for color in self.colors:
                    tk.Frame(self, height=1, bg=color).pack(
                        side="bottom", fill="both")
            else:
                raise Exception(
                    "OptionBar(invert=True) does not support manager '%s'. Try using grid or pack instead." % manager)
        else:
            if manager == "pack":
                for color in self.colors:
                    tk.Frame(self, height=1, bg=color).pack(
                        side="top", fill="both")
            else:
                raise Exception(
                    "OptionBar(invert=False) does not support manager '%s'. Try using pack instead." % manager)

    def add_buffer(self, width, **kwargs):
        new_label = tk.Label(self, bg=self.bg, width=width)
        new_label.grid(**kwargs)
        self.buffers.append(new_label)

    def clear_buffers(self):
        for i in self.buffers:
            i.grid_forget()
        self.buffers = []


class HoverButton(tk.Button):
    def __init__(self, parent, movetype="Click", alt=None, ttjustify="left", ttbackground="#ffffe0",
                 ttforeground="black", ttrelief="solid", ttborderwidth=0, ttfont=("tahoma", "8", "normal"),
                 ttlocationinvert=False, ttheightinvert=False, disabledcursor="", **kwargs):
        self.command = kwargs.pop("command")
        self.clickedbackground = kwargs.pop("clickedbackground")
        if "state" in kwargs and "cursor" in kwargs:
            self.default_cursor = kwargs["cursor"]
            if kwargs["state"] == "disabled":
                kwargs["cursor"] = disabledcursor
        else:
            self.default_cursor = "hand2"
        tk.Label.__init__(self, parent, **kwargs)
        self.default_highlight = self["highlightbackground"]
        self.default_background = self["background"]
        self.disabledcursor = disabledcursor
        self.text = alt
        self.parent = parent
        self.movetype = movetype
        self.job = None
        self.job2 = None
        self.on_button = False
        self.toggled = False

        self.hover_time = 600
        self.auto_click_time = 1000

        if alt:
            self.tool_tip = ToolTip(self, ttjustify, ttbackground, ttforeground,
                                    ttrelief, ttborderwidth, ttfont, ttlocationinvert, ttheightinvert)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)

        self.reset()

    def cancel_jobs(self):
        if self.text:
            if self.job is not None:
                self.parent.after_cancel(self.job)
                self.job = None
            self.tool_tip.hidetip()
        if self.job2 is not None:
            self.parent.after_cancel(self.job2)
            self.job2 = None

    def on_click(self, event):
        if self["state"] == "normal":
            self.config(bg=self.clickedbackground)
            self.cancel_jobs()

    def on_release(self, event):
         if self["state"] == "normal":
            if self.on_button:
                self.parent.after(0, self.command)
                self.config(bg=self["activebackground"])
            else:
                self.config(bg=self.default_background)
            self.cancel_jobs()
            self.hover_time = 2600
            if self.text:
                self.job = self.parent.after(
                    self.hover_time, self.complete_enter)
            if (self.movetype == "Accessibility Mode") and (self["state"] == "normal"):
                self.job2 = self.parent.after(
                    self.auto_click_time, self.run_command)
            self.hover_time = 600

    def on_enter(self, event):
        self.on_button = True
        self.cancel_jobs()
        if self["state"] == "normal":
            self.config(
                background=self["activebackground"], highlightbackground=self["activebackground"])
        if self.text:
            self.job = self.parent.after(self.hover_time, self.complete_enter)
        if (self.movetype == "Accessibility Mode") and (self["state"] == "normal"):
            self.job2 = self.parent.after(
                self.auto_click_time, self.run_command)

    def run_command(self):
        self.parent.after(0, self.command)
        self.job2 = self.parent.after(self.auto_click_time, self.run_command)

    def complete_enter(self):
        self.after(600, self.begin_motion_binding)
        self.tool_tip.showtip(self.text)

    def begin_motion_binding(self):
        if self.on_button:
            self.bind("<Motion>", self.b1motion)

    def b1motion(self, event):
        self.unbind("<Motion>")
        if self.text:
            if self.job is not None:
                self.parent.after_cancel(self.job)
                self.job = None
            if self.job2 is not None:
                self.parent.after_cancel(self.job2)
                self.job2 = None
            #self.tool_tip.hidetip()
            self.hover_time = 2600
            self.job = self.parent.after(self.hover_time, self.complete_enter)
            if (self.movetype == "Accessibility Mode") and (self["state"] == "normal"):
                self.job2 = self.parent.after(
                    self.auto_click_time, self.run_command)
            self.hover_time = 600

    def on_leave(self, event):
        self.on_button = False
        self.reset()
        self.cancel_jobs()
        self.tool_tip.hidetip()

    def disable(self):
        if self["state"] != "disabled":
            self.reset()
            self.config(cursor=self.disabledcursor)
            self.config(state="disabled")
    
    def enable(self):
        if self["state"] != "normal":
            #self.reset()
            self.config(cursor=self.default_cursor)
            self.config(state="normal")

    def toggle(self):
        self.toggled = True
        self.reset()

    def untoggle(self):
        self.toggled = False
        if not self.on_button:
            self.reset()

    def reset(self):
        if self.toggled:
            self.config(background=self["activebackground"],
                        highlightbackground=self["activebackground"])
        else:
            self.config(background=self.default_background,
                        highlightbackground=self.default_highlight)

    def change_command(self, command):
        self.command = command


class Stopwatch(tk.Label):
    def __init__(self, parent, **kwargs):
        tk.Label.__init__(self, parent, text="Time: 00:00", **kwargs)
        self.value = 0
        self.job_id = None
        self.freeze_label = True

    def tick(self):
        self.value += 1
        if self.freeze_label:
            text = "Time: {:02d}:{:02d}".format(*divmod(self.value, 60))
            self.configure(text=text)
        if self.value > 0:
            self.job_id = self.after(1000, self.tick)

    def start(self, starting_value=0):
        if self.job_id is not None:
            return

        self.value = starting_value
        self.stop_requested = False
        self.after(1000, self.tick)

    def stop(self):
        self.after_cancel(self.job_id)
        self.value = 0
        self.job_id = None

    def freeze(self, value):
        self.freeze_label = value
        if self.freeze_label:
            text = "Time: {:02d}:{:02d}".format(*divmod(self.value, 60))
            self.configure(text=text)


class ToolTip:
    def __init__(self, widget, justify, background, foreground, relief, borderwidth, font, locationinvert, heightinvert):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        
        self.transition = 10

        self.justify = justify
        self.background = background
        self.foreground = foreground
        self.relief = relief
        self.borderwidth = borderwidth
        self.font = font
        self.locationinvert = locationinvert
        self.heightinvert = heightinvert

    def showtip(self, text):
        self.text = text
        if self.tipwindow or not self.text:
            return
        self.tipwindow = tw = tk.Toplevel(self.widget, bg="#2e2b2b")
        tw.attributes("-alpha", 0)
        tw.wm_overrideredirect(1)
        
        label = tk.Label(tw, text="  "+self.text+"  ", justify=self.justify, background=self.background,
                         foreground=self.foreground, relief=self.relief, borderwidth=self.borderwidth, font=self.font)
        label.pack(ipadx=1)

        def get_coords(w):
            if not self.locationinvert:
                xoffset = ((w/2) - (self.widget.winfo_width()/2))
                pos_x = self.widget.winfo_rootx() - xoffset
                if self.widget.winfo_x() - xoffset <= 0:
                    pos_x = self.widget.winfo_rootx()
            else:
                pos_x = self.widget.winfo_rootx() - (w - self.widget.winfo_width())
            if not self.heightinvert:
                pos_y = self.widget.winfo_rooty() + 40
            else:
                pos_y = self.widget.winfo_rooty() - 20
            return pos_x, pos_y
        
        # move the tooltip off the screen while calling update() to avoid flashing
        # a bit dorky but it works
        tw.wm_geometry("+%d+%d" % (2000, 2000)) 
        label.update()
        tw.wm_geometry("+%d+%d" % (get_coords(label.winfo_width())))        
        
        def fade_in(alpha):
            if alpha != 1:
                alpha += .1
                tw.attributes("-alpha", alpha)
                tw.after(self.transition, fade_in, alpha)
        fade_in(0)
    
    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        try:
            def fade_away(alpha):
                if alpha > 0:
                    alpha -= .1
                    tw.attributes("-alpha", alpha)
                    tw.after(self.transition, fade_away, alpha)
                else:
                    tw.destroy()
            if not tw.attributes("-alpha") in [0, 1]:
                tw.destroy()
            else:
                fade_away(1)
        except Exception as e:
            if tw:
                tw.destoy()


class SolitaireGameWindow(tk.Tk):
    def __init__(self, **kwargs):
        tk.Tk.__init__(self, **kwargs)

        self.title("TkSolitaire")
        self.minsize(1300, 700)
        #self.minsize(1500, 700)
        #self.geometry("1536x700")

        solitaire_frame = SolitaireGameFrame(self)
        solitaire_frame.pack(expand=True, fill="both")

        solitaire_frame.bind("<<WindowClose>>", self.close)

        try:
            self.iconbitmap(os.path.dirname(
                os.path.abspath(__file__)) + "/resources/icon.ico")
        except:
            icon = tk.PhotoImage(file=(os.path.dirname(
                os.path.abspath(__file__)) + "/resources/icon.png"))
            self.tk.call("wm", "iconphoto", self._w, icon)
        
    def close(self, *args):
        self.destroy()


class SolitaireGameFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)

        self.bind_all("<Control-n>", self.new_game)
        self.bind_all("<Control-r>", self.restart_game)
        self.bind_all("<Control-d>", lambda event: self.stack_onclick("deal_card_button"))
        self.bind_all("<Control-z>", self.undo_move)
        self.bind_all("<Control-Z>", self.redo_move)
        self.bind_all("<Control-h>", self.generate_hint)
        self.bind_all("<F5>", self.send_cards_up)
        self.bind_all("<F1>", self.open_settings)
        self.bind_all("<F2>", self.open_information)
        self.bind_all("<F11>", self.fullscreen)
        self.bind_all("<Control-q>", self.close_window)
        self.bind_all("<Control-w>", self.close_window)
        self.bind("<Configure>", self.self_configure)

        self.canvas = tk.Canvas(self, bd=0, highlightthickness=0)

        self.card_drawing_count = 0
        self.cards_on_ace = 0
        self.parent = parent
        self.win_fullscreen = not parent.attributes("-fullscreen")
        self.card_moved_to_ace_by_sender = 0
        self.stock_left = 24
        self.redeals_left = 0
        self.larger_cards_pending = None
        self.last_active_card = ""
        self.card_stack_list = ""
        self.cards = []
        self.rect_images = []
        self.button_images = []
        self.dict_of_cards = {}
        self.card_back = None
        self.history = []
        self.redo = []
        self.game_started = False
        self.move_flag = False
        self.job = None
        self.loc_skew = 0
        self.height_skew = 1
        self.max_width = 1536
        self.max_height = 715
        self.width = self.max_width
        self.height = self.max_height
        self.settings = None
        self.information = None    
        self.cardsender_may_continue = True

        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        try:
            self.load_settings()
        except:
            with open("resources/settings.json", "w") as handle:
                handle.write(str(DEFAULT_SETTINGS).replace("'", '"'))
            self.load_settings()

        self.load_images()
        self.shuffle_cards()
        self.draw_card_slots()
        self.generate_card_position()
        self.draw_remaining_cards()
        self.create_widgets()

    def load_settings(self, ignore_scaled_cards_prefix=False):
        settings = json.load(open("resources/settings.json"))
        self.movetype = settings["movetype"]
        self.gamemode = settings["gamemode"]

        self.canvas_default_item_hover_time = int(
            settings["canvas_default_item_hover_time"])
        self.default_cardsender_freeze_time = int(
            settings["default_cardsender_freeze_time"])
        self.show_footer = settings["show_footer"] == "True"
        self.show_header = settings["show_header"] == "True"
        self.continuous_points = settings["continuous_points"] == "True"
        self.larger_cards = settings["larger_cards"] == "True"

        self.canvas.config(bg=settings["canvas_color"])

        self.restart_game_button_enabled = True
        self.undo_last_move_button_enabled = True
        self.redo_last_move_button_enabled = True
        self.hint_button_enabled = True
        self.show_stopwatch = True
        self.starting_points = 0
        self.point_increment = 5

        if not ignore_scaled_cards_prefix:
            if self.larger_cards:
                self.scaled_cards_prefix = "scaled_"
            else:
                self.scaled_cards_prefix = ""

        self.back_of_card_file = os.path.join("resources", self.scaled_cards_prefix+settings["card_back"]+".png")
        self.card_back = settings["card_back"]

        if self.gamemode[0] == "Custom":
            self.restart_game_button_enabled = self.gamemode[1] == "True"
            self.undo_last_move_button_enabled = self.gamemode[2] == "True"
            self.redo_last_move_button_enabled = self.undo_last_move_button_enabled
            self.hint_button_enabled = self.gamemode[3] == "True"
            self.show_stopwatch = self.gamemode[4] == "True"
            self.starting_points = int(self.gamemode[5])
            self.point_increment = int(self.gamemode[6])
            self.total_redeals = self.gamemode[7]
            if self.total_redeals != "unlimited":
                self.total_redeals = int(self.total_redeals)
            self.gamemode = self.gamemode[0]
            self.continuous_points = False
        elif self.gamemode == "TkSolitaire Classic":
            self.total_redeals = 3
            self.continuous_points = False
        elif self.gamemode == "Vegas":
            self.total_redeals = 1
            self.restart_game_button_enabled = False
            self.undo_last_move_button_enabled = False
            self.redo_last_move_button_enabled = False
            self.hint_button_enabled = False
            self.starting_points = -52
        elif self.gamemode == "Practice Mode":
            self.total_redeals = "unlimited"
            self.show_stopwatch = False
            self.point_increment = 1
            self.refresh_points_after_game = True
            self.continuous_points = False

        self.canvas_item_hover_time = self.canvas_default_item_hover_time

    def create_widgets(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self.header = header = OptionBar(self, invert=True, manager="grid")
        button_settings = {"movetype": self.movetype, "ttbackground": "#1c1c1b", "ttforeground": "white",
                           "ttfont": ("Verdana", "10", "normal"), "cursor": "hand2", "relief": "flat",
                           "bg": "#1c1a1a", "activebackground": "#4f4a4a", "highlightbackground": "#1c1a1a",
                           "clickedbackground": "#2e2b2b", "highlightthickness": 3}
        self.new_game_button = new_game_button = HoverButton(
            header, alt="Start a new game (Ctrl+N)", command=self.new_game, image=self.convert_pictures("star.png", main=False), **button_settings)
        self.restart_game_button = restart_game_button = HoverButton(
            header, alt="Restart game (Ctrl+R)", command=self.restart_game, state="disabled", image=self.convert_pictures("restart-game.png", main=False), **button_settings)
        self.deal_next_card_button = deal_next_card_button = HoverButton(header, alt="Deal next card (Ctrl+D)", command=lambda event="deal_card_button": self.stack_onclick(
            event), image=self.convert_pictures("deal.png", main=False), **button_settings)
        self.undo_last_move_button = undo_last_move_button = HoverButton(
            header, alt="Undo last move (Ctrl+Z)", command=self.undo_move, state="disabled", image=self.convert_pictures("undo.png", main=False), **button_settings)
        self.redo_last_move_button = redo_last_move_button = HoverButton(
            header, alt="Redo last move (Ctrl+Shift+Z)", command=self.redo_move, state="disabled", image=self.convert_pictures("redo.png", main=False), **button_settings)
        self.hint_button = hint_button = HoverButton(
            header, alt="Generate hint (Ctrl+H)", command=self.generate_hint, image=self.convert_pictures("hint.png", main=False), **button_settings)
        self.send_cards_up_button = send_cards_up_button = HoverButton(
            header, alt="Send cards to aces (F5)", command=self.send_cards_up, image=self.convert_pictures("ol.png", main=False), **button_settings)
        self.settings_button = settings_button = HoverButton(
            header, alt="Settings (F1)", command=self.open_settings, image=self.convert_pictures("settings.png", main=False), **button_settings)
        self.info_button = info_button = HoverButton(
            header, alt="Information (F2)", command=self.open_information, image=self.convert_pictures("information.png", main=False), **button_settings)
        self.fullscreen_button = fullscreen_button = HoverButton(header, alt="Fullscreen (F11)", command=self.fullscreen, image=self.convert_pictures(
            "fullscreen.png", main=False), ttlocationinvert=True, **button_settings)
        self.quit_button = quit_button = HoverButton(header, alt="Quit (Ctrl+Q)", command=self.close_window, image=self.convert_pictures(
            "quit.png", main=False), ttlocationinvert=True, **button_settings)

        header.columnconfigure(13, weight=1)

        new_game_button.grid(row=1, column=0, padx=6, pady=1)
        if self.restart_game_button_enabled:
            restart_game_button.grid(row=1, column=1, padx=6, pady=1)
        header.add_buffer(width=4, row=1, column=2)
        deal_next_card_button.grid(row=1, column=3, padx=6, pady=1)

        header.add_buffer(width=3, row=1, column=4)

        if self.undo_last_move_button_enabled:
            undo_last_move_button.grid(row=1, column=5, padx=6, pady=1)
        if self.redo_last_move_button_enabled:
            redo_last_move_button.grid(row=1, column=6, padx=6, pady=1)
        header.add_buffer(width=3, row=1, column=7)
        if self.hint_button_enabled:
            hint_button.grid(row=1, column=8, padx=6, pady=1)

        send_cards_up_button.grid(row=1, column=9, padx=6, pady=1)
        header.add_buffer(width=4, row=1, column=10)
        settings_button.grid(row=1, column=11, padx=6, pady=1)
        info_button.grid(row=1, column=12, padx=6, pady=1)
        fullscreen_button.grid(row=1, column=13, padx=6, pady=1, sticky="e")
        quit_button.grid(row=1, column=14, padx=6, pady=1, sticky="e")

        self.headerless_settings_button = headerless_settings_button = HoverButton(self.canvas, movetype=self.movetype,
                                                                                   alt="Settings", ttheightinvert=True, ttbackground="#1c1c1b",
                                                                                   ttforeground="white", ttfont=("Verdana", "10", "normal"),
                                                                                   bg=self.canvas["bg"], activebackground=self.generate_altered_colour(
                                                                                       self.canvas["bg"]),
                                                                                   highlightthickness=3, cursor="hand2",
                                                                                   highlightbackground="#103b0a", clickedbackground=self.generate_altered_colour(self.canvas["bg"]), command=self.open_settings,
                                                                                   relief="flat", image=self.convert_pictures("settings.png", main=False))

        if self.show_header:
            header.grid(row=0, column=0, columnspan=100, sticky="ew")
        else:
            self.canvas.rowconfigure(1, weight=1)
            headerless_settings_button.grid(row=1, sticky="sw", padx=4, pady=4)
        self.canvas.grid(row=1, column=0, sticky="nsew")

        self.footer = footer = OptionBar(self)
        self.sending_cards_label = tk.Label(
            footer, text="Looking for cards.   Please wait.", fg="white", bg="#1c1a1a")
        self.points_label = tk.Label(
            footer, text="Points: %s" % self.starting_points, fg="white", bg="#1c1a1a")
        self.stopwatch = stopwatch = Stopwatch(
            footer, fg="white", bg="#1c1a1a")
        if self.total_redeals != "unlimited":
            self.redeal_label = tk.Label(footer, text="Redeals left: "+str(
                max(0, self.total_redeals + self.redeals_left - 1)), fg="white", bg="#1c1a1a")
        else:
            self.redeal_label = tk.Label(
                footer, text="", fg="white", bg="#1c1a1a")
        self.stock_label = tk.Label(
            footer, text="Stock left: "+str(self.stock_left), fg="white", bg="#1c1a1a")

        if self.show_footer:
            footer.grid(row=2, column=0, columnspan=100, sticky="ew")

        self.points_label.pack(side="right", padx=6, pady=4)
        if self.show_stopwatch:
            stopwatch.pack(side="right", padx=6, pady=4)

    def fade_in(self, widget, count):
        count += 5
        #if widget == self.information: count += 5
        #else: count += 15

        if count < 500:
            widget.place(x=self.canvas.winfo_width()-count)
            self.after(2, lambda widget=widget, count=count: self.fade_in(widget, count))
        else:
            widget.place(x=self.canvas.winfo_width()-500)
    
    def fade_out(self, widget, count):
        count -= 5
        if count > 0:
            widget.place(x=self.canvas.winfo_width()-count)
            self.after(2, lambda widget=widget, count=count: self.fade_out(widget, count))
        else:
            widget.place_forget()
            #destroy()

    def open_information(self, *args):
        if self.move_flag:
            return
        self.initiate_game(close_popups=False)# close_popup()#continue_settings()            
        if not self.information:
            self.information = information = Information(self, width=500, height=self.canvas.winfo_height())
            information.place(x=self.canvas.winfo_width(), y=self.canvas.winfo_y())
            information.update()
            information.bind("<<InformationClose>>", self.close_information)
        else:
            if self.information.winfo_ismapped():
                self.close_information()
                return
            self.information.config(width=500, height=self.canvas.winfo_height())
            self.information.place(x=self.canvas.winfo_width(), y=self.canvas.winfo_y())
        if self.settings and self.settings.winfo_ismapped():
            self.close_settings()
        self.information.lift()
        self.fade_in(self.information, 0)
        self.info_button.toggle()

        self.create_rectangle(0, 0, 2000, 2000, fill="black", alpha=.6, tag="cover")
        self.canvas.config(state="disabled")
        
    def close_information(self, *args, num=500):
        if self.information:
            if self.information.winfo_manager() == "grid":
                self.information.place(x=self.canvas.winfo_width(), y=self.canvas.winfo_y(), width=500, height=self.canvas.winfo_height())
                self.information.update()
            self.fade_out(self.information, num)
            self.canvas.delete("cover")
            self.canvas.config(state="normal")
            self.info_button.untoggle()

    def open_settings(self, *args):
        if self.move_flag:
            return
        self.initiate_game(close_popups=False)#close_popup()#continue_settings()
        if not self.settings:
            self.settings = settings = Settings(self, width=500, height=self.canvas.winfo_height())
            settings.place(x=self.canvas.winfo_width(), y=self.canvas.winfo_y())
            settings.update()
            settings.bind("<<SettingsClose>>", self.close_settings)
            settings.bind("<<SettingsSaved>>", self.continue_settings)
        else:
            if self.settings.winfo_ismapped():
                self.close_settings()
                return
            self.settings.config(width=500, height=self.canvas.winfo_height())
            self.settings.place(x=self.canvas.winfo_width(), y=self.canvas.winfo_y())
        if self.information and self.information.winfo_ismapped():
            self.close_information()
        self.settings.lift()
        self.fade_in(self.settings, 0)
        self.settings_button.toggle()
        self.headerless_settings_button.toggle()

        self.create_rectangle(0, 0, 2000, 2000, fill="black", alpha=.6, tag="cover")
        self.canvas.config(state="disabled")
        
    def close_popup(self):
        if self.information:
            if self.information.winfo_ismapped():
                self.close_information()
        if self.settings:
            if self.settings.winfo_ismapped():
                self.close_settings()
        self.canvas.delete("cover")
        self.canvas.config(state="normal")

    def close_settings(self, event=None, num=500):
        settings = self.settings
        if settings:
            if self.settings.winfo_manager() == "grid":
                self.settings.place(x=self.canvas.winfo_width(), y=self.canvas.winfo_y(), width=500, height=self.canvas.winfo_height())
                self.settings.update()
            settings.save()#delete_window()#destroy()
            settings.grid_propagate(0)
            self.fade_out(settings, num)
            self.canvas.delete("cover")
            self.canvas.config(state="normal")
            self.settings_button.untoggle()
            self.headerless_settings_button.untoggle()

    def close_window(self, event=None):
        if self.history:
            close = messagebox.askquestion(
                "Quit game", "Are you sure you want to quit?", icon="warning")
            if close == "yes":
                self.event_generate("<<WindowClose>>")
        else:
            self.event_generate("<<WindowClose>>")

    def fullscreen(self, event=None):
        self.parent.attributes(
            "-fullscreen", not self.parent.attributes("-fullscreen"))

        if self.win_fullscreen:
            self.fullscreen_button.config(
                image=self.convert_pictures("fullscreen-exit.png", main=False))
            self.win_fullscreen = False
        else:
            self.fullscreen_button.config(
                image=self.convert_pictures("fullscreen.png", main=False))
            self.win_fullscreen = True

    def continue_settings(self, *args):     
        previous_movetype = self.movetype
        previous_larger_cards = self.larger_cards
        self.canvas.tag_unbind("card_below_rect", "<Enter>")
        self.canvas.tag_unbind("rect", "<Enter>")
        self.canvas.tag_unbind("rect", "<Leave>")
        self.canvas.tag_unbind("rect", "<Button-1>")
        self.canvas.delete("rect")
        self.last_active_card = ""
        self.card_stack_list = ""

        self.load_settings(ignore_scaled_cards_prefix=True)

        self.update_idletasks()

        back_of_card = Image.open(self.back_of_card_file)
        self.back_of_card = (ImageTk.PhotoImage(back_of_card))
        self.canvas.itemconfig("face_down", image=self.back_of_card)

        self.restart_game_button.movetype = self.movetype
        self.undo_last_move_button.movetype = self.movetype
        self.redo_last_move_button.movetype = self.movetype
        self.hint_button.movetype = self.movetype
        self.send_cards_up_button.movetype = self.movetype
        self.new_game_button.movetype = self.movetype
        self.deal_next_card_button.movetype = self.movetype
        self.settings_button.movetype = self.movetype
        self.info_button.movetype = self.movetype
        self.fullscreen_button.movetype = self.movetype
        self.headerless_settings_button.movetype = self.movetype

        if self.restart_game_button_enabled:
            if not self.restart_game_button.winfo_ismapped():
                self.restart_game_button.grid(row=1, column=1, padx=6, pady=1)
        else:
            self.restart_game_button.grid_forget()

        if self.undo_last_move_button_enabled:
            if not self.undo_last_move_button.winfo_ismapped():
                self.undo_last_move_button.grid(
                    row=1, column=5, padx=6, pady=1)
        else:
            self.undo_last_move_button.grid_forget()

        if self.redo_last_move_button_enabled:
            if not self.redo_last_move_button.winfo_ismapped():
                self.redo_last_move_button.grid(
                    row=1, column=6, padx=6, pady=1)
        else:
            self.redo_last_move_button.grid_forget()

        if self.hint_button_enabled:
            if not self.hint_button.winfo_ismapped():
                self.hint_button.grid(row=1, column=8, padx=6, pady=1)
        else:
            self.hint_button.grid_forget()

        self.points_label.pack_forget()
        self.stopwatch.pack_forget()
        self.redeal_label.pack_forget()
        self.stock_label.pack_forget()

        if self.show_footer:
            if not self.footer.winfo_ismapped():
                self.update_idletasks()
                self.footer.grid(row=2, column=0, columnspan=100, sticky="ew")
        else:
            self.footer.grid_forget()
        self.points_label["text"] = (
            "Points: "+str((self.cards_on_ace*self.point_increment)+self.starting_points))
        self.points_label.pack(side="right", padx=6, pady=4)
        if self.show_stopwatch:
            self.stopwatch.pack(side="right", padx=6, pady=4)
        if self.total_redeals != "unlimited":
            self.redeal_label.config(
                text="Redeals left: "+str(max(0, self.total_redeals + self.redeals_left - 1)))
            if self.game_started:
                self.redeal_label.pack(side="left", padx=6, pady=4)
        if self.game_started:
            self.stock_label.pack(side="left", padx=6, pady=4)

        self.headerless_settings_button.grid_forget()
        if self.show_header:
            if not self.header.winfo_ismapped():
                self.update_idletasks()
                self.header.grid(row=0, column=0, columnspan=100, sticky="ew")
        else:
            self.header.grid_forget()
            self.canvas.rowconfigure(1, weight=1)
            self.headerless_settings_button.config(bg=self.canvas["bg"])
            self.headerless_settings_button.default_background = self.canvas["bg"]
            self.headerless_settings_button["activebackground"] = self.generate_altered_colour(
                self.canvas["bg"])
            self.canvas.update_idletasks()
            self.headerless_settings_button.grid(row=1, sticky="sw", padx=4, pady=4)

        if self.movetype != previous_movetype:
            for card in self.canvas.find_withtag("face_up"):
                card_tag = self.canvas.gettags(card)[0]
                self.canvas.tag_unbind(card_tag, "<Button-1>")
                self.canvas.tag_unbind(card_tag, "<Button1-Motion>")
                self.canvas.tag_unbind(card_tag, "<ButtonRelease-1>")
                self.canvas.tag_unbind(card_tag, "<Enter>")
                self.canvas.tag_unbind(card_tag, "<Leave>")
                if self.movetype == "Accessibility Mode":
                    self.canvas.tag_bind(card_tag, "<Enter>", self.enter_card)
                    self.canvas.tag_bind(card_tag, "<Leave>", self.leave_hover)
                    self.canvas.tag_bind(
                        card_tag, "<Button-1>", self.card_onclick)
                elif self.movetype == "Click":
                    self.canvas.tag_bind(
                        card_tag, "<Button-1>", self.card_onclick)
                else:
                    self.canvas.tag_bind(
                        card_tag, "<Button-1>", self.end_onclick)
                    self.canvas.tag_bind(
                        card_tag, "<Button1-Motion>", self.move_card)
                    self.canvas.tag_bind(
                        card_tag, "<ButtonRelease-1>", self.drop_card)
                    self.canvas.tag_bind(
                        card_tag, "<Enter>", self.on_draggable_card)
                    self.canvas.tag_bind(
                        card_tag, "<Leave>", self.leave_draggable_card)

            for card in self.canvas.find_overlapping(*self.canvas.bbox("empty_cardstack_slot")):
                card_tag = self.canvas.gettags(card)[0]
                if card_tag == "empty_cardstack_slot":
                    continue
                else:
                    if self.movetype == "Accessibility Mode":
                        self.canvas.tag_bind(
                            card_tag, "<Enter>", self.enter_stack)
                        self.canvas.tag_bind(
                            card_tag, "<Leave>", self.leave_hover)
                    else:
                        self.canvas.tag_unbind(card_tag, "<Enter>")
                        self.canvas.tag_unbind(card_tag, "<Leave>")

            self.canvas.tag_unbind("empty_slot", "<Enter>")
            self.canvas.tag_unbind("empty_ace_slot", "<Enter>")
            self.canvas.tag_unbind("empty_cardstack_slot", "<Enter>")
            self.canvas.tag_unbind("empty_slot", "<Leave>")
            self.canvas.tag_unbind("empty_ace_slot", "<Leave>")
            self.canvas.tag_unbind("empty_cardstack_slot", "<Leave>")
            self.canvas.tag_unbind("empty_slot", "<Button-1>")
            self.canvas.tag_unbind("empty_ace_slot", "<Button-1>")
            self.canvas.tag_unbind("empty_cardstack_slot", "<Button-1>")

            self.canvas.tag_unbind("empty_slot", "<Button-1>")
            self.canvas.tag_unbind("empty_ace_slot", "<Button-1>")
            self.canvas.tag_unbind("empty_cardstack_slot", "<Button-1>")

            self.canvas.tag_unbind("empty_slot", "<Button-1>")
            self.canvas.tag_unbind("empty_ace_slot", "<Button-1>")
            self.canvas.tag_unbind("empty_slot", "<Button1-Motion>")
            self.canvas.tag_unbind("empty_slot", "<ButtonRelease-1>")
            self.canvas.tag_unbind("empty_ace_slot", "<Button1-Motion>")
            self.canvas.tag_unbind("empty_ace_slot", "<ButtonRelease-1>")
            self.canvas.tag_unbind("empty_cardstack_slot", "<Button-1>")

            if self.movetype == "Accessibility Mode":
                self.canvas.tag_bind("empty_slot", "<Enter>", self.enter_card)
                self.canvas.tag_bind(
                    "empty_ace_slot", "<Enter>", self.enter_card)
                self.canvas.tag_bind("empty_cardstack_slot",
                                     "<Enter>", self.enter_refill)
                self.canvas.tag_bind("empty_slot", "<Leave>", self.leave_hover)
                self.canvas.tag_bind(
                    "empty_ace_slot", "<Leave>", self.leave_hover)
                self.canvas.tag_bind("empty_cardstack_slot",
                                     "<Leave>", self.leave_hover)
                self.canvas.tag_bind(
                    "empty_slot", "<Button-1>", self.card_onclick)
                self.canvas.tag_bind(
                    "empty_ace_slot", "<Button-1>", self.card_onclick)
                self.canvas.tag_bind("empty_cardstack_slot",
                                     "<Button-1>", self.refill_card_stack)
            elif self.movetype == "Click":
                self.canvas.tag_bind(
                    "empty_slot", "<Button-1>", self.card_onclick)
                self.canvas.tag_bind(
                    "empty_ace_slot", "<Button-1>", self.card_onclick)
                self.canvas.tag_bind("empty_cardstack_slot",
                                     "<Button-1>", self.refill_card_stack)
            else:
                self.canvas.tag_bind(
                    "empty_slot", "<Button-1>", self.end_onclick)
                self.canvas.tag_bind(
                    "empty_ace_slot", "<Button-1>", self.end_onclick)
                self.canvas.tag_bind(
                    "empty_slot", "<Button1-Motion>", self.move_card)
                self.canvas.tag_bind(
                    "empty_slot", "<ButtonRelease-1>", self.drop_card)
                self.canvas.tag_bind(
                    "empty_ace_slot", "<Button1-Motion>", self.move_card)
                self.canvas.tag_bind(
                    "empty_ace_slot", "<ButtonRelease-1>", self.drop_card)
                self.canvas.tag_bind("empty_cardstack_slot",
                                     "<Button-1>", self.refill_card_stack)
        ret = False
        if self.total_redeals != "unlimited":
            if self.stock_left <= 1 and (self.total_redeals + self.redeals_left - 1) == 0:
                self.deal_next_card_button.disable()
                ret = True
            else:
                self.deal_next_card_button.enable()
        else:
            self.deal_next_card_button.enable()

        if not ret:
            if self.stock_left == 0:
                self.deal_next_card_button.change_command(
                    lambda event=None: self.refill_card_stack(event))
            else:
                self.deal_next_card_button.change_command(
                    lambda event="deal_card_button": self.stack_onclick(event))
        self.compare_cardset(previous_larger_cards)
        
    def compare_cardset(self, previous_larger_cards):
        if not os.path.isdir("resources/scaled_cards"):
                self.create_scaled_images()
        if not previous_larger_cards and self.larger_cards:
            self.larger_cards_pending = self.larger_cards
            self.larger_cards = previous_larger_cards
            restart_game = messagebox.askquestion(
                "Restart game", "In order to use the larger card set, you must restart your game. Do you want to restart now?", icon="warning")
            if restart_game == "yes":
                self.restart_game()
        elif previous_larger_cards and not self.larger_cards:
            self.larger_cards_pending = self.larger_cards
            self.larger_cards = previous_larger_cards
            restart_game = messagebox.askquestion(
                "Restart game", "In order to use the regular card set, you must restart your game. Do you want to restart now?", icon="warning")
            if restart_game == "yes":
                self.restart_game()
                
    def generate_altered_colour(self, color):
        rgb = list(self.hex_to_rgb(color))
        if rgb[0] > 200:
            rgb[0] = round(((rgb[0]))*1/2)
        else:
            rgb[0] = round(min(255, 10+rgb[0]*2))
        if rgb[1] > 130:
            rgb[1] = round((rgb[1])*1/2)
        else:
            rgb[1] = round(min(255, 10+rgb[1]*2))
        if rgb[2] > 130:
            rgb[2] = round((rgb[2])*1/2)
        else:
            rgb[2] = round(min(255, 10+rgb[2]*2))
        return self.rgb_to_hex(*rgb)

    def hex_to_rgb(self, color):
        value = color.lstrip("#")
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

    def rgb_to_hex(self, red, green, blue):
        return "#%02x%02x%02x" % (red, green, blue)

    def create_scaled_images(self):
        path = os.path.join("resources", "scaled_cards")
        try:
            os.mkdir(path)
        except:
            pass
        suits = ["clubs", "diamonds", "spades", "hearts"]
        ranks = ["ace", "2", "3", "4", "5", "6", "7",
                 "8", "9", "10", "jack", "queen", "king"]
        for suit in suits:
            for rank in ranks:
                name_of_old_image = os.path.join(
                    "resources", "cards", "{}_of_{}.png".format(rank, suit))
                name_of_image = os.path.join(
                    "resources", "scaled_cards", "{}_of_{}.png".format(rank, suit))
                im = Image.open(name_of_old_image)
                resized_img = im.resize((100,130), Image.ANTIALIAS)
                resized_img.save(name_of_image, 'PNG', quality=90)

        
        im = Image.open("resources/card_back.png")
        resized_img = im.resize((100,130), Image.ANTIALIAS)
        resized_img.save("resources/scaled_card_back.png", 'PNG', quality=90)
        im = Image.open("resources/python_card_back.png")
        resized_img = im.resize((100,130), Image.ANTIALIAS)
        resized_img.save("resources/scaled_python_card_back.png", 'PNG', quality=90)
        im = Image.open("resources/ace_of_clubs_slot.png")
        resized_img = im.resize((100,130), Image.ANTIALIAS)
        resized_img.save("resources/scaled_ace_of_clubs_slot.png", 'PNG', quality=90)
        im = Image.open("resources/ace_of_spades_slot.png")
        resized_img = im.resize((100,130), Image.ANTIALIAS)
        resized_img.save("resources/scaled_ace_of_spades_slot.png", 'PNG', quality=90)
        im = Image.open("resources/ace_of_hearts_slot.png")
        resized_img = im.resize((100,130), Image.ANTIALIAS)
        resized_img.save("resources/scaled_ace_of_hearts_slot.png", 'PNG', quality=90)
        im = Image.open("resources/ace_of_diamonds_slot.png")
        resized_img = im.resize((100,130), Image.ANTIALIAS)
        resized_img.save("resources/scaled_ace_of_diamonds_slot.png", 'PNG', quality=90)
        im = Image.open("resources/empty_slot.png")
        resized_img = im.resize((100,130), Image.ANTIALIAS)
        resized_img.save("resources/scaled_empty_slot.png", 'PNG', quality=90)

    def load_images(self):
        card_dir = "cards"
        if self.larger_cards:
            card_dir = "scaled_cards"
            if not os.path.isdir("resources/scaled_cards"):
                self.create_scaled_images()
            
        suits = ["clubs", "diamonds", "spades", "hearts"]
        ranks = ["ace", "2", "3", "4", "5", "6", "7",
                 "8", "9", "10", "jack", "queen", "king"]

        for suit in suits:
            for rank in ranks:
                name_of_image = os.path.join(
                    "resources", card_dir, "{}_of_{}.png".format(rank, suit))
                image = Image.open(name_of_image)
                self.cards.append("{}_of_{}".format(rank, suit))
                self.dict_of_cards[("{}_of_{}".format(rank, suit))] = (
                    ImageTk.PhotoImage(image))
        back_of_card = Image.open(self.back_of_card_file)
        self.back_of_card = (ImageTk.PhotoImage(back_of_card))

    def shuffle_cards(self):
        random.shuffle(self.cards)

    def generate_card_position(self):
        rows = 7
        column = 0

        for i in range(rows):
            for e in range(column):
                self.draw_down_cards((i+1), (e+1))
            column += 1
            self.draw_up_cards((i+1), (column))

    def draw_up_cards(self, row, col):
        card_tag = str(self.cards[self.card_drawing_count])
        card_image = self.dict_of_cards[self.cards[self.card_drawing_count]]
        if self.larger_cards:
            self.canvas.create_image(
                255+row*130, col*20, image=card_image, tag=(card_tag, "face_up"), anchor=tk.NW)
        else:
            self.canvas.create_image(
                295+row*110, col*20, image=card_image, tag=(card_tag, "face_up"), anchor=tk.NW)
        if self.movetype == "Accessibility Mode":
            self.canvas.tag_bind(card_tag, "<Enter>", self.enter_card)
            self.canvas.tag_bind(card_tag, "<Leave>", self.leave_hover)
            self.canvas.tag_bind(card_tag, "<Button-1>", self.card_onclick)
        elif self.movetype == "Click":
            self.canvas.tag_bind(card_tag, "<Button-1>", self.card_onclick)
        else:
            self.canvas.tag_bind(card_tag, "<Button-1>", self.end_onclick)
            self.canvas.tag_bind(card_tag, "<Button1-Motion>", self.move_card)
            self.canvas.tag_bind(card_tag, "<ButtonRelease-1>", self.drop_card)
            self.canvas.tag_bind(card_tag, "<Enter>", self.on_draggable_card)
            self.canvas.tag_bind(card_tag, "<Leave>",
                                 self.leave_draggable_card)
        self.card_drawing_count += 1

    def draw_down_cards(self, row, col):
        card_tag = str(self.cards[self.card_drawing_count])
        self.canvas.tag_unbind(card_tag,  "<Button-1>")
        self.canvas.tag_unbind(card_tag, "<Button1-Motion>")
        self.canvas.tag_unbind(card_tag, "<ButtonRelease-1>")
        self.canvas.tag_unbind(card_tag, "<Enter>")
        self.canvas.tag_unbind(card_tag, "<Leave>")
        if self.larger_cards:
            self.canvas.create_image(
                255+row*130, col*20, image=self.back_of_card, tag=(card_tag, "face_down"), anchor=tk.NW)
        else:
            self.canvas.create_image(
                295+row*110, col*20, image=self.back_of_card, tag=(card_tag, "face_down"), anchor=tk.NW)
        self.card_drawing_count += 1

    def draw_remaining_cards(self):
        remaining_cards = 52-self.card_drawing_count
        for i in range(remaining_cards):
            card_tag = str(self.cards[self.card_drawing_count])
            self.canvas.tag_unbind(card_tag, "<Enter>")
            self.canvas.tag_unbind(card_tag, "<Leave>")
            self.canvas.create_image(20, 20, image=self.back_of_card, tag=(
                card_tag, "face_down"), anchor=tk.NW)
            if self.movetype == "Accessibility Mode":
                self.canvas.tag_bind(card_tag, "<Enter>", self.enter_stack)
                self.canvas.tag_bind(card_tag, "<Leave>", self.leave_hover)
                self.canvas.tag_bind(
                    card_tag, "<Button-1>", self.stack_onclick)
            else:
                self.canvas.tag_bind(
                    card_tag, "<Button-1>", self.stack_onclick)
            self.card_drawing_count += 1

    def create_round_rectangle(self, x1, y1, x2, y2, r=17, **kwargs):
        points = (x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2,
                  y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1)
        return self.canvas.create_polygon(points, **kwargs, smooth=True)

    def convert_pictures(self, url, main=True):
        picture = Image.open(os.path.join("resources", url))
        picture = (ImageTk.PhotoImage(picture))
        if main:
            self.canvas.images.append(picture)
        else:
            self.button_images.append(picture)
        return picture

    def self_configure(self, event, after_restart=False):
        if self.information:
            if self.information.winfo_manager() == "place":
                self.information.grid(row=1, column=1, sticky="ns")
        if self.settings:
            if self.settings.winfo_manager() == "place":
                self.settings.grid(row=1, column=1, sticky="ns")
         
        try:
            if after_restart:
                width = self.width
                height = self.height
                wdiff = self.width - self.max_width
                hscale = self.height / self.max_height
                self.height_skew = 1
            else:
                width = event.width
                height = event.height
                wdiff = width - self.width
                hscale = (float(height) / self.height)

            self.width = width
            self.height = height
            change = wdiff / 2
            x = list(self.canvas.bbox("empty_slot"))
            x[3] = 1000
            main_stacks = self.canvas.find_overlapping(*x)#(390, 10, 1280, 1000)
            ace_stacks = self.canvas.find_overlapping(*self.canvas.bbox("empty_ace_slot"))#(1410, 10, 1525, 1000)
            for i in ace_stacks:
                if "cover" not in self.canvas.gettags(i):
                    self.canvas.move(i, wdiff, 0)
            for i in main_stacks:
                if "cover" not in self.canvas.gettags(i):
                    self.canvas.move(i, change, 0)
            self.loc_skew += change
            self.canvas.scale("all", 0, 0, 1, hscale)#self.canvas.canvasy
            self.height_skew *= hscale
        except AttributeError:
            self.self_configure(event)
       
    def draw_card_slots(self):
        self.aces_moved = False
        self.canvas.images = list()
        if not self.larger_cards:
            positions_of_main_rects = [
                (405, 20), (515, 20), (625, 20), (735, 20), (845, 20), (955, 20), (1065, 20)]
        else:
            positions_of_main_rects = [
                (385, 20), (515, 20), (645, 20), (775, 20), (905, 20), (1035, 20), (1165, 20)]

        self.empty_slot = empty_slot = self.convert_pictures(self.scaled_cards_prefix+"empty_slot.png")
        for item in positions_of_main_rects:
            self.canvas.create_image(
                *item, image=empty_slot, tag=("empty_slot"), anchor=tk.NW)

        if not self.larger_cards:
            self.canvas.create_image(1330, 20, image=self.convert_pictures(self.scaled_cards_prefix+
                "ace_of_spades_slot.png"), tag=("spades", "empty_ace_slot"), anchor=tk.NW)
            self.canvas.create_image(1430, 20, image=self.convert_pictures(self.scaled_cards_prefix+
                "ace_of_hearts_slot.png"), tag=("hearts", "empty_ace_slot"), anchor=tk.NW)
            self.canvas.create_image(1330, 140, image=self.convert_pictures(self.scaled_cards_prefix+
                "ace_of_clubs_slot.png"), tag=("clubs", "empty_ace_slot"), anchor=tk.NW)
            self.canvas.create_image(1430, 140, image=self.convert_pictures(self.scaled_cards_prefix+
                "ace_of_diamonds_slot.png"), tag=("diamonds", "empty_ace_slot"), anchor=tk.NW)

            self.canvas.create_image(20, 20, image=self.convert_pictures(self.scaled_cards_prefix+
                "empty_slot.png"), tag="empty_cardstack_slot", anchor=tk.NW)
            self.canvas.create_image(120, 20, image=self.convert_pictures(self.scaled_cards_prefix+
                "empty_slot.png"), tag="empty_cardstack_slotb", anchor=tk.NW)
            #self.create_round_rectangle(
            #    22, 22, 98, 118, width=2, fill="#124f09", outline="#207c12", tag="empty_cardstack_slot")
            #self.create_round_rectangle(
            #    122, 22, 198, 118, width=2, fill="#124f09", outline="#207c12", tag="empty_cardstack_slotb")
        else:
            #self.canvas.create_image(1420, 20, image=self.convert_pictures(self.scaled_cards_prefix+
            #    "ace_of_spades_slot.png"), tag=("spades", "empty_ace_slot"), anchor=tk.NW)
            #self.canvas.create_image(1420, 170, image=self.convert_pictures(self.scaled_cards_prefix+
            #    "ace_of_hearts_slot.png"), tag=("hearts", "empty_ace_slot"), anchor=tk.NW)
            #self.canvas.create_image(1534, 20, image=self.convert_pictures(self.scaled_cards_prefix+
            #    "ace_of_clubs_slot.png"), tag=("clubs", "empty_ace_slot"), anchor=tk.NW)
            #self.canvas.create_image(1534, 170, image=self.convert_pictures(self.scaled_cards_prefix+
            #    "ace_of_diamonds_slot.png"), tag=("diamonds", "empty_ace_slot"), anchor=tk.NW)
            self.canvas.create_image(1420, 20, image=self.convert_pictures(self.scaled_cards_prefix+
                "ace_of_spades_slot.png"), tag=("spades", "empty_ace_slot"), anchor=tk.NW)
            self.canvas.create_image(1420, 165, image=self.convert_pictures(self.scaled_cards_prefix+
                "ace_of_hearts_slot.png"), tag=("hearts", "empty_ace_slot"), anchor=tk.NW)
            self.canvas.create_image(1420, 310, image=self.convert_pictures(self.scaled_cards_prefix+
                "ace_of_clubs_slot.png"), tag=("clubs", "empty_ace_slot"), anchor=tk.NW)
            self.canvas.create_image(1420, 455, image=self.convert_pictures(self.scaled_cards_prefix+
                "ace_of_diamonds_slot.png"), tag=("diamonds", "empty_ace_slot"), anchor=tk.NW)

            self.canvas.create_image(20, 20, image=self.convert_pictures(self.scaled_cards_prefix+
                "empty_slot.png"), tag="empty_cardstack_slot", anchor=tk.NW)
            self.canvas.create_image(134, 20, image=self.convert_pictures(self.scaled_cards_prefix+
                "empty_slot.png"), tag="empty_cardstack_slotb", anchor=tk.NW)

            #self.create_round_rectangle(
            #    22, 22, 118, 148, width=3, fill="#124f09", outline="#207c12", tag="empty_cardstack_slot")
            #self.create_round_rectangle(
            #    136, 22, 233, 148, width=3, fill="#124f09", outline="#207c12", tag="empty_cardstack_slotb")

        if self.movetype == "Accessibility Mode":
            self.canvas.tag_bind("empty_slot", "<Enter>", self.enter_card)
            self.canvas.tag_bind("empty_ace_slot", "<Enter>", self.enter_card)
            self.canvas.tag_bind("empty_cardstack_slot",
                                 "<Enter>", self.enter_refill)
            self.canvas.tag_bind("empty_slot", "<Leave>", self.leave_hover)
            self.canvas.tag_bind("empty_ace_slot", "<Leave>", self.leave_hover)
            self.canvas.tag_bind("empty_cardstack_slot",
                                 "<Leave>", self.leave_hover)
            self.canvas.tag_bind("empty_slot", "<Button-1>", self.card_onclick)
            self.canvas.tag_bind(
                "empty_ace_slot", "<Button-1>", self.card_onclick)
            self.canvas.tag_bind("empty_cardstack_slot",
                                 "<Button-1>", self.refill_card_stack)
        elif self.movetype == "Click":
            self.canvas.tag_bind("empty_slot", "<Button-1>", self.card_onclick)
            self.canvas.tag_bind(
                "empty_ace_slot", "<Button-1>", self.card_onclick)
            self.canvas.tag_bind("empty_cardstack_slot",
                                 "<Button-1>", self.refill_card_stack)
        else:
            self.canvas.tag_bind("empty_slot", "<Button-1>", self.end_onclick)
            self.canvas.tag_bind(
                "empty_ace_slot", "<Button-1>", self.end_onclick)
            self.canvas.tag_bind(
                "empty_slot", "<Button1-Motion>", self.move_card)
            self.canvas.tag_bind(
                "empty_slot", "<ButtonRelease-1>", self.drop_card)
            self.canvas.tag_bind(
                "empty_ace_slot", "<Button1-Motion>", self.move_card)
            self.canvas.tag_bind(
                "empty_ace_slot", "<ButtonRelease-1>", self.drop_card)
            self.canvas.tag_bind("empty_cardstack_slot",
                                 "<Button-1>", self.refill_card_stack)
        self.canvas.bind("<Button-1>", self.on_background)        

    def on_background(self, event):
        self.close_popup()
        self.cardsender_may_continue = False
        if self.sending_cards_label.winfo_ismapped():
            self.send_cards_up_button.untoggle()
            self.sending_cards_label.pack_forget()
            if self.total_redeals != "unlimited":
                self.redeal_label.pack(side="left", padx=6, pady=4)
            self.stock_label.pack(side="left", padx=6, pady=4)
        if event and (self.canvas.find_overlapping(event.x-5, event.y-5, event.x+5, event.y+5)) == ():
            self.canvas.delete("rect")
            self.last_active_card = ""
            self.card_stack_list = ""

    def create_rectangle(self, x1, y1, x2, y2, tag="rect", **kwargs):
        if "alpha" in kwargs:
            alpha = int(kwargs.pop("alpha") * 255)
            fill = kwargs.pop("fill")
            fill = self.winfo_rgb(fill) + (alpha,)
            image = Image.new("RGBA", (x2-x1, y2-y1), fill)
            self.rect_images.append(ImageTk.PhotoImage(image))
            self.canvas.create_image(
                x1, y1, image=self.rect_images[-1], anchor="nw", tag=tag)
        else:
            self.canvas.create_rectangle(x1, y1, x2, y2, tag="rect", **kwargs)

    def initiate_game(self, from_button=True, close_popups=True):
        if from_button:
            self.cardsender_may_continue = False
            if self.sending_cards_label.winfo_ismapped():
                self.send_cards_up_button.untoggle()
                self.sending_cards_label.pack_forget()
                if self.total_redeals != "unlimited":
                    self.redeal_label.pack(side="left", padx=6, pady=4)
                self.stock_label.pack(side="left", padx=6, pady=4)
        if close_popups:
            self.close_popup()
        self.canvas_item_hover_time = self.canvas_default_item_hover_time
        self.restart_game_button.enable()
        self.redo_last_move_button.enable()
        try:
            last_move = self.history[-1]
        except:
            self.undo_last_move_button.disable()
            self.restart_game_button.disable()
        try:
            last_move = self.redo[-1]
        except:
            self.redo_last_move_button.disable()
        if self.game_started == False:
            self.stopwatch.start()
            self.game_started = True
            if self.total_redeals != "unlimited":
                self.redeal_label.pack(side="left", padx=6, pady=4)
            self.stock_label.pack(side="left", padx=6, pady=4)
        else:
            self.game_started = True

    def enter_card(self, event):
        self.job = self.after(
            self.canvas_item_hover_time, lambda: self.card_onclick(event="Accessibility Mode"))

    def enter_stack(self, event):
        self.job = self.after(
            self.canvas_item_hover_time+800, lambda: self.stack_onclick(event="Accessibility Mode"))

    def enter_refill(self, event):
        self.job = self.after(self.canvas_item_hover_time+800,
                              lambda: self.refill_card_stack(event="Accessibility Mode"))

    def leave_hover(self, event):
        if self.job is not None:
            self.after_cancel(self.job)
            self.job = None

    def restart_game(self, *args):
        #self.close_popup()
        if self.move_flag:
            return
        self.reset_vars()
        self.redraw()

    def new_game(self, *args):
        #self.close_popup()
        if self.move_flag:
            return
        self.shuffle_cards()
        self.reset_vars()
        self.redraw()

    def reset_vars(self):
        if self.larger_cards_pending is not None:
            self.larger_cards = self.larger_cards_pending
            self.larger_cards_pending = None
            if self.larger_cards:
                self.scaled_cards_prefix = "scaled_"
            else:
                self.scaled_cards_prefix = ""
            self.back_of_card_file = os.path.dirname(os.path.abspath(
                __file__))+"/resources/"+self.scaled_cards_prefix+self.card_back+".png"
            self.dict_of_cards = {}
            card_dir = "cards"
            if self.larger_cards:
                card_dir = "scaled_cards"
                if not os.path.isdir("resources/scaled_cards"):
                    self.create_scaled_images()

            for card in self.cards:
                    name_of_image = os.path.join(
                        "resources", card_dir, "{}.png".format(card))
                    image = Image.open(os.path.dirname(
                        os.path.abspath(__file__))+"/"+name_of_image)
                    self.dict_of_cards[card] = (
                        ImageTk.PhotoImage(image))
            back_of_card = Image.open(self.back_of_card_file)
            self.back_of_card = (ImageTk.PhotoImage(back_of_card))

        self.card_drawing_count = 0

        if self.continuous_points:
            self.starting_points = (
                self.starting_points + (self.cards_on_ace * self.point_increment)) - 52

        self.cards_on_ace = 0
        self.card_moved_to_ace_by_sender = 0
        self.stock_left = 24
        self.last_active_card = ""
        self.card_stack_list = ""
        self.history = []
        self.redo = []
        self.game_started = False
        self.move_flag = False
        self.job = None

        self.redeals_left = 0

        self.canvas_item_hover_time = self.canvas_default_item_hover_time

        try:
            self.stopwatch.stop()
            self.stopwatch.config(text="Time: 00:00")
        except:
            pass

        self.restart_game_button.disable()
        self.undo_last_move_button.disable()
        self.redo_last_move_button.disable()
        if self.total_redeals != "unlimited":
            self.redeal_label.config(
                text="Redeals left: "+str(max(0, self.total_redeals + self.redeals_left - 1)))
        self.points_label.config(text="Points: "+str(self.starting_points))
        self.stock_label.config(text="Stock left: "+str(self.stock_left))
        self.deal_next_card_button.enable()
        self.deal_next_card_button.change_command(
            lambda event="deal_card_button": self.stack_onclick(event))
        if self.total_redeals != "unlimited":
            self.redeal_label.pack_forget()
        self.stock_label.pack_forget()
        self.canvas.delete("all")

    def redraw(self):
        self.draw_card_slots()
        self.generate_card_position()
        self.draw_remaining_cards()
        
        self_width = self.winfo_width()
        if self_width != 1:
            self.self_configure(event=None, after_restart = True)

    def find_available_cards(self):
        face_up_cards = list(reversed(self.canvas.find_withtag("face_up")))

        flipped_cards = []
        positions_of_ace_rects = []
        found_cards = []

        for card in (self.canvas.find_overlapping(*self.canvas.bbox("empty_cardstack_slotb"))):
            if card in face_up_cards:
                face_up_cards.remove(card)
            if "empty" not in str(self.canvas.gettags(card)):
                flipped_cards.append(card)
        if flipped_cards != []:
            del flipped_cards[:-1]
        ace_slots = self.canvas.find_withtag("empty_ace_slot")
        for slot in ace_slots:
            positions_of_ace_rects.append(self.canvas.bbox(slot))
        for position in positions_of_ace_rects:
            for card in self.canvas.find_overlapping(*position):
                if card in face_up_cards:
                    face_up_cards.remove(card)
                found_cards.append(card)
            if found_cards != []:
                flipped_cards.append(found_cards[-1])
            found_cards = []
        flipped_cards.extend(face_up_cards)
        face_up_cards = flipped_cards

        base_slots = self.canvas.find_withtag("empty_slot")
        for slot in base_slots:
            if len(self.canvas.find_overlapping(*self.canvas.bbox(slot))) == 1:
                face_up_cards.append(slot)

        return face_up_cards

    def generate_hint(self, *args):
        if self.move_flag:
            return
        self.initiate_game()

        self.card_stack_list = ""
        self.last_active_card = ""
        self.canvas.delete("rect")

        face_up_cards = self.find_available_cards()

        returnval = False
        for pair in face_up_cards:
            self.canvas.delete("rect")
            card_stack = list(self.canvas.bbox(pair))
            if self.larger_cards:
                card_stack[1] = (int(card_stack[1]))+129
            else:
                card_stack[1] = (int(card_stack[1]))+99
            card_stack[3] = (int(card_stack[3]))+350
            card_stack = tuple(card_stack)
            card_stack = list(self.canvas.find_overlapping(*card_stack))
            for pairr in self.card_stack_list:
                card_tag = self.canvas.gettags(pairr)
                if ("ace_slot" in str(card_tag)) or ("cardstack" in str(card_tag)):
                    to_be_card_stack_list = card_stack[-1]
                    card_stack = []
                    card_stack.append(to_be_card_stack_list)
                    break
            last_active_card_bbox_list = list(self.canvas.bbox(pair))
            if self.larger_cards:
                last_active_card_bbox_list[1] = int(
                    last_active_card_bbox_list[1])+90
            else:
                last_active_card_bbox_list[1] = int(
                    last_active_card_bbox_list[1])+60
            last_active_card_bbox_list[3] = int(
                last_active_card_bbox_list[3])-25
            last_active_card_bbox_list = tuple(last_active_card_bbox_list)
            card_a_bbox = self.canvas.bbox(pair)

            first_item = list(self.canvas.bbox(
                self.canvas.find_withtag(card_stack[0])))
            last_item = list(self.canvas.bbox(
                self.canvas.find_withtag(card_stack[-1])))
            tl = first_item[0]
            tr = first_item[1]
            bl = last_item[2]
            br = last_item[3]
            positionsb = []
            positionsb.append(tl)
            positionsb.append(tr)
            positionsb.append(bl)
            positionsb.append(br)
            card_a_bbox = tuple(positionsb)

            if ("empty_ace_slot" not in str(self.canvas.gettags(pair)) and "empty_slot" not in str(self.canvas.gettags(pair))):
                last_active_card = str(self.canvas.gettags(pair)).replace(")", "").replace(
                    "('", "").replace("', 'face_down'", "").replace("', 'face_up'", "")
            else:
                continue
            for card in face_up_cards:
                card_tag = str(self.canvas.gettags(card))
                current_image = self.canvas.find_withtag(card)
                current_image_tags = self.canvas.gettags(current_image)
                current_image_bbox = self.canvas.bbox(current_image)

                bbox_list = list(current_image_bbox)
                card_b_bbox = self.canvas.bbox(card)
                current_image_overlapping = self.canvas.find_overlapping(
                    *bbox_list)
                tag_a = str(current_image_tags).replace(", 'current')", "").replace(")", "").replace(
                    "('", "").replace("', 'face_down'", "").replace("', 'face_up'", "")

                overlapping = False
                ace_slot = False
                if ("empty_ace_slot" not in str(current_image_tags)) and ("empty_slot" not in str(current_image_tags)):
                    csl = list(self.canvas.bbox(tag_a))
                    if self.larger_cards:
                        csl[1] = (int(csl[1]))+135
                    else:
                        csl[1] = (int(csl[1]))+110
                    csl[3] = (int(csl[3]))+20
                    csl = tuple(csl)
                    csl = list(self.canvas.find_overlapping(*csl))
                    for card in csl:
                        if card in card_stack:
                            continue
                        elif "empty_cardstack_slot" in str(self.canvas.gettags(card)):
                            overlapping = True
                            break
                        elif "face_up" in self.canvas.gettags(card):
                            overlapping = True
                            break

                if "empty_slot" in str(current_image_tags):
                    if "king" in card_stack:
                        for card in current_image_overlapping:
                            if card in card_stack:
                                continue
                            elif "face" in str(self.canvas.gettags(card)):
                                overlapping = True
                                break

                for item in current_image_overlapping:
                    if "empty_ace_slot" in self.canvas.gettags(self.canvas.find_withtag(item)):
                        ace_slot = True
                for item in self.canvas.find_overlapping(*self.canvas.bbox(pair)):
                    if "empty_ace_slot" in self.canvas.gettags(self.canvas.find_withtag(item)):
                        ace_slot = True

                for item in current_image_overlapping:
                    if last_active_card in self.canvas.gettags(self.canvas.find_withtag(item)):
                        overlapping = True

                if ace_slot:
                    try:
                        for item in card_stack:
                            self.canvas.tag_raise(item)
                        item = self.canvas.find_overlapping(
                            *self.canvas.bbox(self.canvas.find_above(last_active_card)))
                        overlapping = True
                    except:
                        pass
                else:
                    try:
                        below_last = self.canvas.find_overlapping(
                            *self.canvas.bbox(last_active_card))
                    except:
                        continue
                    last_card_index_in_below = below_last.index(
                        list(self.canvas.find_withtag(last_active_card))[0])
                    below_last = str(self.canvas.gettags(
                        below_last[last_card_index_in_below-1]))
                    last_overlapping = self.canvas.find_overlapping(
                        *self.canvas.bbox(last_active_card))
                    if "king" in last_active_card:
                        if ("empty_slot" in below_last):
                            overlapping = True
                    over_cardstack = False
                    for card in current_image_overlapping:
                        if ("empty_cardstack_slot" in str(self.canvas.gettags(card))):
                            over_cardstack = True
                            break
                    if not over_cardstack:
                        over_cardstack = False
                        for card in last_overlapping:
                            if ("empty_cardstack_slot" in str(self.canvas.gettags(card))):
                                over_cardstack = True
                        if not over_cardstack:
                            if ("face_up" in below_last):
                                overlapping = True
                    else:
                        overlapping = True
                if ("ace" not in last_active_card and "empty_ace_slot" in current_image_tags):
                    continue
                elif ("king" not in last_active_card and "empty_slot" in current_image_tags):
                    continue
                elif ("empty_slot" in last_active_card):
                    continue
                elif overlapping:
                    continue
                elif "king" in last_active_card and "empty_slot" in current_image_tags:
                    returnval = True
                    break
                elif self.check_move_validity(tag_a, last_active_card, ace_slot):
                    returnval = True
                    break
                else:
                    continue
            if returnval:
                break

        if returnval:
            self.create_rectangle(*card_b_bbox, fill="purple", alpha=.5)
            self.create_rectangle(*card_a_bbox, fill="purple", alpha=.5)

            if self.movetype == "Accessibility Mode":
                self.canvas.tag_unbind("card_below_rect", "<Enter>")
                self.canvas.tag_bind(
                    "rect", "<Enter>", self.enter_hover_on_hint_rect)
                self.canvas.tag_bind("rect", "<Leave>", self.leave_hover)
                self.canvas.tag_bind("rect", "<Button-1>",
                                     self.click_on_hint_rect)
            elif self.movetype == "Click":
                self.canvas.tag_bind("rect", "<Button-1>",
                                     self.click_on_hint_rect)
            else:
                self.canvas.tag_bind(
                    "rect", "<Enter>", self.enter_on_hint_rect)
        else:
            ret = False
            if self.total_redeals != "unlimited":
                if self.stock_left == 0 and (self.total_redeals + self.redeals_left - 1) <= 0:
                    ret = True
                    messagebox.showinfo(
                        title="Ummmmmm.", message="I can't find any hints for you.\nYou may want to start a new game.")
            if not ret:
                cards = False
                for card in self.canvas.find_overlapping(*self.canvas.bbox("empty_cardstack_slotb")):
                    if "empty_cardstack_slotb" in self.canvas.gettags(card):
                        continue
                    cards = True
                    break
                if not cards:
                    for card in self.canvas.find_overlapping(*self.canvas.bbox("empty_cardstack_slot")):
                        if "empty_cardstack_slot" in self.canvas.gettags(card):
                            continue
                        cards = True
                        break
                if not cards:
                    ret = True
                    messagebox.showinfo(
                        title="Ummmmmm.", message="I can't find any hints for you.\nYou may want to start a new game.")

            if not ret:
                self.create_rectangle(
                    *self.canvas.bbox("empty_cardstack_slot"), fill="purple", alpha=.5)

                if self.movetype == "Accessibility Mode":
                    self.canvas.tag_unbind("card_below_rect", "<Enter>")
                    self.canvas.tag_bind(
                        "rect", "<Enter>", self.enter_hover_on_hint_rect)
                    self.canvas.tag_bind("rect", "<Leave>", self.leave_hover)
                    self.canvas.tag_bind(
                        "rect", "<Button-1>", self.click_on_hint_rect)
                elif self.movetype == "Click":
                    self.canvas.tag_bind(
                        "rect", "<Button-1>", self.click_on_hint_rect)
                else:
                    self.canvas.tag_bind(
                        "rect", "<Button-1>", self.click_on_hint_rect)

    def send_cards_up(self, *args):
        if self.move_flag:
            return
        if self.send_cards_up_button.toggled:
            self.on_background(None)
            return
        self.send_cards_up_button.toggle()
        self.initiate_game(False)
        #self.stopwatch.freeze(False)
        thread = threading.Thread(daemon=True, target=self.continue_sending_cards)
        thread.start()
    
    def continue_sending_cards(self):
        if not self.sending_cards_label.winfo_ismapped():
            self.sending_cards_label["text"] = "Looking for cards.   Please wait."
            self.sending_cards_label.pack(side="left", padx=6, pady=4)
            self.redeal_label.pack_forget()
            self.stock_label.pack_forget()
            self.sending_cards_label.update()
            self.cardsender_may_continue = True
        if not self.cardsender_may_continue:
            return
        self.card_stack_list = ""
        self.last_active_card = ""
        self.canvas.delete("rect")
        face_up_cards = list(reversed(self.canvas.find_withtag("face_up")))
        for card in face_up_cards:
            below_last = self.canvas.find_overlapping(*self.canvas.bbox(card))
            last_card_index_in_below = below_last.index(
                list(self.canvas.find_withtag(card))[0])
            below_last = str(self.canvas.gettags(
                below_last[last_card_index_in_below-1]))
            if "face_up" in self.canvas.gettags(below_last):
                face_up_cards.remove(card)
        flipped_cards = []
        for card in (self.canvas.find_overlapping(*self.canvas.bbox("empty_cardstack_slotb"))):
            if card in face_up_cards:
                face_up_cards.remove(card)
            if "empty" not in str(self.canvas.gettags(card)):
                flipped_cards.append(card)
        if flipped_cards != []:
            del flipped_cards[:-1]
        flipped_cards.extend(face_up_cards)
        face_up_cards = flipped_cards
        cards_moved = self.card_moved_to_ace_by_sender
        over_ace = []
        temp_over_ace = []
        for item in self.canvas.find_withtag("empty_ace_slot"):
            temp_over_ace = []
            for card in self.canvas.find_overlapping(*self.canvas.bbox(item)):
                temp_over_ace.append(card)
                if card in face_up_cards:
                    face_up_cards.remove(card)
            over_ace.append(temp_over_ace[-1])
        for pair in over_ace:
            for card in face_up_cards:
                if pair == card:
                    continue
                self.after(0, self.continue_sending_cards2, card, pair)

        if self.cardsender_may_continue:
            if cards_moved != self.card_moved_to_ace_by_sender:
                self.continue_sending_cards()
            else:
                self.card_moved_to_ace_by_sender = 0
                self.send_cards_up_button.untoggle()
                self.sending_cards_label.pack_forget()
                if self.total_redeals != "unlimited":
                    self.redeal_label.pack(side="left", padx=6, pady=4)
                self.stock_label.pack(side="left", padx=6, pady=4)

    def continue_sending_cards2(self, card, pair):
        if not self.cardsender_may_continue:
            return
        self.change_current(card)
        self.end_onclick(event="send_cards_to_ace")
        self.canvas.dtag("current")
        self.change_current(pair)
        self.card_onclick(event="send_cards_to_ace")
        self.canvas.dtag("current")
        self.card_stack_list = ""
        self.last_active_card = ""
        self.canvas.delete("cardsender_highlight")
        self.update_idletasks()
        if self.card_moved_to_ace_by_sender == 1:
            message = "Moved 1 card.   Please wait."
        elif self.card_moved_to_ace_by_sender > 0:
            message = "Moved %s cards.   Please wait." % (
                self.card_moved_to_ace_by_sender)
        else:
            message = None
        if self.sending_cards_label["text"] != message:
            self.sending_cards_label["text"] = message

    def redo_move(self, *args):
        if self.move_flag:
            return
        try:
            last_move = self.redo[-1]
        except:
            return
        self.last_active_card = ""
        self.card_stack_list = ""
        self.canvas.delete("rect")
        del self.redo[-1]
        self.initiate_game()

        if "refill_card_stack" in last_move:
            self.refill_card_stack(event="redo")
        elif "stack_click_move" in last_move:
            self.stack_onclick(event="redo")
        else:
            if "move_card" in last_move:
                last_active_card = list(last_move[2])[0]
            else:
                last_active_card = last_move[3]
            self.change_current(last_active_card)
            self.end_onclick(event="redo")
            self.canvas.dtag("current")
            if "empty" in str(last_move[-1]):
                last_move[-1] = list(str(last_move[-1]).split("'"))[0]
            self.change_current(last_move[-1])
            self.card_onclick(event="redo")
            self.canvas.dtag("current")
        self.initiate_game()
        try:
            last_move = self.redo[-1]
            self.redo_last_move_button.enable()
            if self.redo_last_move_button.on_button:
                self.redo_last_move_button.config(
                    background=self.redo_last_move_button["activebackground"])
        except:
            self.redo_last_move_button.disable()
        self.update_deal_button()

    def change_current(self, tag):
        self.canvas.dtag("current")
        self.canvas.focus("")
        self.canvas.addtag_withtag("current", tag)

    def undo_move(self, *args):
        
        if self.move_flag:
            return
        self.last_active_card = ""
        self.card_stack_list = ""
        self.canvas.delete("rect")
        self.initiate_game()
        try:
            last_move = self.history[-1]
        except:
            return
        self.redo.append(last_move)
        del self.history[-1]
        if "refill_card_stack" in last_move:
            self.redeals_left += 1
            if self.total_redeals != "unlimited":
                self.redeal_label.config(
                    text="Redeals left: "+str(max(0, self.total_redeals + self.redeals_left - 1)))
            for card in reversed(list(self.canvas.find_overlapping(*self.canvas.bbox("empty_cardstack_slot")))):
                current_item_tags = self.canvas.gettags(card)
                tag_a = current_item_tags[0]
                if "empty_cardstack_slot" in (self.canvas.gettags(card)):
                    continue
                self.canvas.tag_unbind(tag_a, "<Enter>")
                self.canvas.tag_unbind(tag_a, "<Leave>")
                self.canvas.tag_unbind(tag_a, "<Button-1>")
                if self.movetype == "Accessibility Mode":
                    self.canvas.tag_bind(tag_a, "<Enter>", self.enter_card)
                    self.canvas.tag_bind(tag_a, "<Leave>", self.leave_hover)
                    self.canvas.tag_bind(
                        tag_a, "<Button-1>", self.card_onclick)
                elif self.movetype == "Click":
                    self.canvas.tag_bind(
                        tag_a, "<Button-1>", self.card_onclick)
                else:
                    self.canvas.tag_bind(tag_a, "<Button-1>", self.end_onclick)
                    self.canvas.tag_bind(
                        tag_a, "<Button1-Motion>", self.move_card)
                    self.canvas.tag_bind(
                        tag_a, "<ButtonRelease-1>", self.drop_card)
                    self.canvas.tag_bind(
                        tag_a, "<Enter>", self.on_draggable_card)
                    self.canvas.tag_bind(
                        tag_a, "<Leave>", self.leave_draggable_card)
                self.canvas.tag_raise(card)
                if not self.larger_cards:
                    self.canvas.move(card, 100, 0)
                else:
                    self.canvas.move(card, 115, 0)
                self.canvas.itemconfig(
                    card, image=self.dict_of_cards[tag_a], tag=(tag_a, "face_up"))
                self.stock_left -= 1
            self.stock_label.config(text="Stock left: "+str(self.stock_left))
            self.undo_last_move_button.enable()
            self.restart_game_button.enable()
            self.redo_last_move_button.disable()

        elif "stack_click_move" in last_move:
            self.canvas.delete("rect")
            self.stock_left += 1
            self.stock_label.config(text="Stock left: "+str(self.stock_left))
            tag_a = last_move[0]
            if not self.larger_cards:
                self.canvas.move(tag_a, -100, 0)
            else:
                self.canvas.move(tag_a, -115, 0)
            self.canvas.itemconfig(
                tag_a, image=self.back_of_card, tag=(tag_a, "face_down"))
            self.canvas.tag_unbind(tag_a, "<Enter>")
            self.canvas.tag_unbind(tag_a, "<Leave>")
            self.canvas.tag_unbind(tag_a, "<Button-1>")
            if self.movetype == "Accessibility Mode":
                self.canvas.tag_bind(tag_a, "<Enter>", self.enter_stack)
                self.canvas.tag_bind(tag_a, "<Leave>", self.leave_hover)
                self.canvas.tag_bind(tag_a, "<Button-1>", self.stack_onclick)
            else:
                self.canvas.tag_bind(tag_a, "<Button-1>", self.stack_onclick)
            self.canvas.tag_raise(self.canvas.find_withtag(tag_a))
            self.deal_next_card_button.enable()
            self.deal_next_card_button.change_command(
                lambda event="deal_card_button": self.stack_onclick(event))

        elif "move_card" in last_move:
            card_tags = last_move[-2]
            self.canvas.itemconfig(
                card_tags, image=self.back_of_card, tag=(card_tags, "face_down"))
            self.canvas.tag_unbind(card_tags, "<Enter>")
            self.canvas.tag_unbind(card_tags, "<Leave>")
            self.canvas.tag_unbind(card_tags, "<Button-1>")
            for i in last_move[2]:
                card_location = self.canvas.coords(i)
                current_location = last_move[2][i]
                xpos = int(current_location[0] - (card_location[0] - self.loc_skew))
                ypos = (current_location[1] * self.height_skew) - (card_location[1])
                self.canvas.move(i, xpos, ypos)
                if True in last_move:
                    self.canvas.tag_raise(i)
            if last_move[1] == 1:
                self.cards_on_ace -= 1
                for i in last_move[2]:
                    self.canvas.tag_raise(i)
                self.points_label["text"] = (
                    "Points: "+str((self.cards_on_ace*self.point_increment)+self.starting_points))
            elif last_move[1] == 2:
                self.cards_on_ace += 1
                self.points_label["text"] = (
                    "Points: "+str((self.cards_on_ace*self.point_increment)+self.starting_points))

        elif "move_card_srv" in last_move:
            card_location = self.canvas.coords(last_move[3])
            current_image_location = last_move[-2]
            
            if last_move[1]:
                current_image_location = self.canvas.coords(last_move[1])
                    
            xpos = int(current_image_location[0]) - int(card_location[0])# + self.loc_skew
            ypos = int(current_image_location[1] * self.height_skew) - int(card_location[1])
            self.canvas.move(last_move[3], xpos, ypos)
            self.canvas.tag_raise(last_move[3])

            if last_move[2] == 1:
                self.cards_on_ace -= 1
                self.points_label["text"] = (
                    "Points: "+str((self.cards_on_ace*self.point_increment)+self.starting_points))
            elif last_move[2] == 2:
                self.cards_on_ace += 1
                self.points_label["text"] = (
                    "Points: "+str((self.cards_on_ace*self.point_increment)+self.starting_points))
        self.canvas.tag_raise("face_up")
        self.restart_game_button.enable()
        self.redo_last_move_button.enable()
        try:
            last_move = self.history[-1]
        except:
            self.undo_last_move_button.disable()
            self.restart_game_button.disable()
        self.deal_next_card_button.enable()
        if self.total_redeals != "unlimited":
            if self.stock_left < 1 and (self.total_redeals + self.redeals_left - 1) == 0:
                self.deal_next_card_button.disable()
        if self.stock_left == 0:
            self.deal_next_card_button.change_command(
                lambda event=None: self.refill_card_stack(event))
        else:
            self.deal_next_card_button.change_command(
                lambda event="deal_card_button": self.stack_onclick(event))
        self.update_deal_button()

    def check_move_validity(self, current_card, last_card, ace_slot):
        #return True#######################################
        if ace_slot:
            if "clubs" in current_card and "clubs" not in last_card:
                return False
            if "spades" in current_card and "spades" not in last_card:
                return False
            if "diamonds" in current_card and "diamonds" not in last_card:
                return False
            if "hearts" in current_card and "hearts" not in last_card:
                return False
        else:
            if (("clubs" in current_card) or ("spades" in current_card)) and (("clubs" in last_card) or ("spades" in last_card)):
                return False
            elif (("diamonds" in current_card) or ("hearts" in current_card)) and (("diamonds" in last_card) or ("hearts" in last_card)):
                return False
        if "empty_ace_slot" in current_card:
            return True
        else:
            if last_card[1] == "0":
                last_card = "10"
            else:
                last_card = last_card[0]

            if current_card[1] == "0":
                current_card = "10"
            else:
                current_card = current_card[0]

            if last_card == "j":
                last_card = "11"
            elif last_card == "q":
                last_card = "12"
            elif last_card == "k":
                last_card = "13"
            elif last_card == "a":
                last_card = "1"

            if current_card == "j":
                current_card = "11"
            elif current_card == "q":
                current_card = "12"
            elif current_card == "k":
                current_card = "13"
            elif current_card == "a":
                current_card = "1"

            last_card = int(last_card)
            current_card = int(current_card)

            if ace_slot:
                if last_card-1 == current_card:
                    return True
                else:
                    return False
            else:
                if last_card+1 == current_card:
                    return True
                else:
                    return False

    def stack_onclick(self, event):
        if self.move_flag:
            return
        self.initiate_game()
        current_item = list(self.canvas.find_overlapping(
            *self.canvas.bbox("empty_cardstack_slot")))[-1]
        current_item_tags = self.canvas.gettags(current_item)
        if event == "deal_card_button":
            if "rect" in str(current_item_tags):
                self.canvas.delete('rect')
                self.stack_onclick(event="deal_card_button")
                return
        tag_a = current_item_tags[0]
        if (event != "redo") and (event != "deal_card_button"):
            self.redo = []
            if "empty_cardstack_slot" in tag_a:
                return
            elif event != "hint":
                if current_item not in self.canvas.find_withtag("current"):
                    return
            elif "rect" in tag_a:
                return
        else:
            if "empty_cardstack_slot" in tag_a:
                return

        self.canvas.delete("rect")
        self.stock_left -= 1
        self.stock_label.config(text="Stock left: "+str(self.stock_left))
        self.last_active_card = ""
        self.card_stack_list = ""

        history_to_add = [tag_a, "stack_click_move"]
        self.history.append(history_to_add)

        if not self.larger_cards:
            self.canvas.move(current_item, 100, 0)
        else:
            self.canvas.move(current_item, 115, 0)
        self.canvas.itemconfig(
            current_item, image=self.dict_of_cards[tag_a], tag=(tag_a, "face_up"))

        self.canvas.tag_unbind(tag_a, "<Button-1>")

        if self.movetype == "Accessibility Mode":
            self.canvas.tag_unbind(tag_a, "<Enter>")
            self.canvas.tag_unbind(tag_a, "<Leave>")
            self.canvas.tag_bind(tag_a, "<Enter>", self.enter_card)
            self.canvas.tag_bind(tag_a, "<Leave>", self.leave_hover)
            self.canvas.tag_bind(tag_a, "<Button-1>", self.card_onclick)
        elif self.movetype == "Click":
            self.canvas.tag_bind(tag_a, "<Button-1>", self.card_onclick)
        else:
            self.canvas.tag_bind(tag_a, "<Button-1>", self.end_onclick)
            self.canvas.tag_bind(tag_a, "<Button1-Motion>", self.move_card)
            self.canvas.tag_bind(tag_a, "<ButtonRelease-1>", self.drop_card)
            self.canvas.tag_bind(tag_a, "<Enter>", self.on_draggable_card)
            self.canvas.tag_bind(tag_a, "<Leave>", self.leave_draggable_card)

        self.canvas.tag_raise(self.canvas.find_withtag(tag_a))

        self.undo_last_move_button.enable()
        self.restart_game_button.enable()
        self.redo_last_move_button.disable()

        self.update_deal_button()

    def refill_card_stack(self, event):
        if self.move_flag:
            return
        if event != "redo":
            self.redo = []
        self.initiate_game()
        self.canvas.delete("rect")
        ret = False
        if self.total_redeals != "unlimited":
            if (self.total_redeals + self.redeals_left - 1) <= 0:
                messagebox.showinfo(title="No Redeals Left",
                                    message="Sorry. You have no redeals left.")
                ret = True
        if not ret:
            history_to_add = ["refill_card_stack"]
            self.history.append(history_to_add)
            self.redeals_left -= 1
            if self.total_redeals != "unlimited":
                self.redeal_label.config(
                    text="Redeals left: "+str(max(0, self.total_redeals + self.redeals_left - 1)))

            for card in reversed(list(self.canvas.find_overlapping(*self.canvas.bbox("empty_cardstack_slotb")))):
                if "empty_cardstack_slotb" in self.canvas.gettags(card):
                    continue
                card = self.canvas.gettags(card)[0]

                self.canvas.tag_unbind(card, "<Button-1>")
                if self.movetype == "Accessibility Mode":
                    self.canvas.tag_unbind(card, "<Enter>")
                    self.canvas.tag_unbind(card, "<Leave>")
                    self.canvas.tag_bind(card, "<Enter>", self.enter_stack)
                    self.canvas.tag_bind(card, "<Leave>", self.leave_hover)
                    self.canvas.tag_bind(
                        card, "<Button-1>", self.stack_onclick)
                else:
                    self.canvas.tag_unbind(card, "<Enter>")
                    self.canvas.tag_unbind(card, "<Leave>")
                    self.canvas.tag_bind(
                        card, "<Button-1>", self.stack_onclick)
                self.canvas.tag_raise(card)
                if not self.larger_cards:
                    self.canvas.move(card, -100, 0)
                else:
                    self.canvas.move(card, -115, 0)
                self.canvas.itemconfig(
                    card, image=self.back_of_card, tag=(card, "face_down"))
            self.stock_left -= 1
            for i in (self.canvas.find_overlapping(*self.canvas.bbox("empty_cardstack_slot"))):
                self.stock_left += 1
            self.stock_label.config(text="Stock left: "+str(self.stock_left))
            self.undo_last_move_button.enable()
            self.restart_game_button.enable()
            self.redo_last_move_button.config(state="disabled")
            self.update_deal_button()

    def update_deal_button(self):
        if self.total_redeals != "unlimited":
            if self.stock_left < 1 and (self.total_redeals + self.redeals_left - 1) == 0:
                self.deal_next_card_button.disable()
            else:
                self.deal_next_card_button.enable()
        else:
            self.deal_next_card_button.enable()
        if self.stock_left == 0:
            self.unbind_all("<Control-d>")
            self.bind_all("<Control-d>", lambda event=None: self.refill_card_stack(event))
            self.deal_next_card_button.change_command(
                lambda event=None: self.refill_card_stack(event))
        else:
            self.unbind_all("<Control-d>")
            self.bind_all("<Control-d>", lambda event: self.stack_onclick("deal_card_button"))
            self.deal_next_card_button.change_command(
                lambda event="deal_card_button": self.stack_onclick(event))

    def on_draggable_card(self, event):
        if self.canvas["cursor"] != "fleur":
            self.canvas.config(cursor="hand2")

    def leave_draggable_card(self, event):
        if self.canvas["cursor"] != "fleur":
            self.canvas.config(cursor="")

    def move_card(self, event):
        self.canvas.delete("available_card_rect")
        self.canvas.delete("rect")
        if self.move_flag:
            new_xpos, new_ypos = event.x, event.y
            self.canvas.move("moveable", new_xpos -
                             self.mouse_xpos, new_ypos-self.mouse_ypos)

            self.mouse_xpos = new_xpos
            self.mouse_ypos = new_ypos

            self.highlight_available_cards()
        else:
            for item in self.card_stack_list:
                card_tag = list(self.canvas.gettags(item))[0]
                if "empty" in str(self.canvas.gettags(item)):
                    continue
                elif "face_down" in str(self.canvas.gettags(item)):
                    continue
                else:
                    self.canvas.addtag_withtag("moveable", card_tag)
            self.move_flag = True
            self.canvas.tag_raise("moveable")
            self.mouse_xpos = event.x
            self.mouse_ypos = event.y

    def highlight_available_cards(self):
        try:
            returnval = True
            bbox = list(self.canvas.bbox(self.canvas.find_withtag("current")))
            bbox[0] = int(bbox[0]) - 15
            bbox[1] = int(bbox[1]) - 15
            bbox[2] = int(bbox[2]) + 15
            bbox[3] = int(bbox[3]) + 15
            card_overlapping = self.canvas.find_overlapping(*tuple(bbox))
        except:
            return
        for card in card_overlapping:
            if (self.canvas.find_withtag("current")) == card:
                continue
            card_tag = str(self.canvas.gettags(card))
            if "face_down" in card_tag:
                continue
            elif "current" in card_tag:
                continue
            elif "empty_cardstack_slot" in card_tag:
                break
            else:
                current_image = self.canvas.find_withtag(card)
                current_image_bbox = self.canvas.bbox(current_image)
                returnval = self.generate_returnval(current_image)
                if returnval:
                    self.create_rectangle(
                        *current_image_bbox, fill="blue", alpha=.3, tag="available_card_rect")
                    for card in self.card_stack_list:
                        if "empty_slot" not in self.canvas.gettags(card):
                            self.canvas.tag_raise(card)
                    continue

    def drop_card(self, event):
        if self.canvas["cursor"] == "fleur":
            self.canvas.config(cursor="hand2")
        self.canvas.delete("available_card_rect")
        self.move_flag = False
        self.canvas.dtag("face_up", "moveable")
        try:
            last_image_location = self.current_image_location
            returnval = True
            bbox = list(self.canvas.bbox(self.canvas.find_withtag("current")))
            bbox[0] = int(bbox[0]) - 15
            bbox[1] = int(bbox[1]) - 15
            bbox[2] = int(bbox[2]) + 15
            bbox[3] = int(bbox[3]) + 15
            card_overlapping = self.canvas.find_overlapping(*tuple(bbox))
        except:
            moving_count = 0
            for item in self.card_stack_list:
                if "empty" in str(self.canvas.gettags(item)):
                    continue
                elif "face_down" in str(self.canvas.gettags(item)):
                    continue
                else:
                    xpos = int(last_image_location[0]) - \
                        int(self.canvas.coords(item)[0])
                    ypos = moving_count + \
                        (int(last_image_location[1]) -
                         int(self.canvas.coords(item)[1]))
                    self.canvas.move(item, xpos, ypos)
                    moving_count += 20
            return
        for card in card_overlapping:
            card_tag = str(self.canvas.gettags(card))
            if "face_down" in card_tag:
                continue
            elif "current" in card_tag:
                continue
            elif "empty_cardstack_slot" in card_tag:
                break
            else:
                self.current_image = current_image = self.canvas.find_withtag(
                    card)
                self.current_image_tags = current_image_tags = self.canvas.gettags(
                    current_image)
                self.current_image_location = self.canvas.coords(current_image)
                self.current_image_bbox = current_image_bbox = self.canvas.bbox(
                    current_image)
                bbox_list = list(current_image_bbox)
                current_image_overlapping = self.canvas.find_overlapping(
                    *bbox_list)
                self.tag_a = tag_a = str(current_image_tags).replace(", 'current')", "").replace(
                    ")", "").replace("('", "").replace("', 'face_down'", "").replace("', 'face_up'", "")
                overlapping = False
                ace_slot = False
                over_ace_slot = False
                for card in self.canvas.find_overlapping(*self.canvas.bbox(current_image)):
                    if "empty_ace_slot" in self.canvas.gettags(card):
                        over_ace_slot = True
                        break
                if (not over_ace_slot) and ("empty_slot" not in str(current_image_tags)):
                    csl = list(self.canvas.bbox(tag_a))
                    if self.larger_cards:
                        csl[1] = (int(csl[1]))+135
                    else:
                        csl[1] = (int(csl[1]))+110
                    csl[3] = (int(csl[3]))+20
                    csl = tuple(csl)
                    csl = list(self.canvas.find_overlapping(*csl))
                    for card in csl:
                        if card in self.card_stack_list:
                            continue
                        elif "empty_cardstack_slot" in str(self.canvas.gettags(card)):
                            overlapping = True
                            break
                        elif "face_up" in self.canvas.gettags(card):
                            overlapping = True
                            break

                if "empty_slot" in str(self.current_image_tags):
                    if "king" in self.last_active_card:
                        for card in current_image_overlapping:
                            if card in self.card_stack_list:
                                continue
                            elif "face" in str(self.canvas.gettags(card)):
                                overlapping = True
                                break

                for item in current_image_overlapping:
                    if "empty_ace_slot" in self.canvas.gettags(self.canvas.find_withtag(item)):
                        ace_slot = True

                if ace_slot:
                    try:
                        for item in self.card_stack_list:
                            self.canvas.tag_raise(item)
                        item = self.canvas.find_overlapping(
                            *self.canvas.bbox(self.canvas.find_above(self.last_active_card)))
                        overlapping = True
                    except:
                        pass

                try:
                    if str(list(current_image)[0]) == str(self.last_active_card_over[self.last_active_card_over.index(list(self.canvas.find_withtag(self.last_active_card))[0])-1]):
                        overlapping = True
                except (ValueError, IndexError):
                    pass
                
                if ("ace" not in self.last_active_card and "empty_ace_slot" in self.current_image_tags):
                    continue
                elif ("king" not in self.last_active_card and "empty_slot" in self.current_image_tags):
                    continue
                elif ("empty_slot" in self.last_active_card):
                    continue
                elif overlapping:
                    continue
                elif "king" in self.last_active_card and "empty_slot" in self.current_image_tags:
                    self.continue_onclick(ace_slot=ace_slot, event=event)
                    returnval = False
                    break
                elif self.check_move_validity(tag_a, self.last_active_card, ace_slot):
                    self.continue_onclick(ace_slot=ace_slot, event=event)
                    returnval = False
                    break
                else:
                    continue

        if returnval:
            moving_count = 0
            for item in self.card_stack_list:
                if "empty" in str(self.canvas.gettags(item)):
                    continue
                elif "face_down" in str(self.canvas.gettags(item)):
                    continue
                else:
                    xpos = int(last_image_location[0]) - \
                        int(self.canvas.coords(item)[0])
                    ypos = moving_count + \
                        (int(last_image_location[1]) -
                         int(self.canvas.coords(item)[1]))

                    self.canvas.move(item, xpos, ypos)
                    moving_count += 20
        self.card_stack_list = ""
        self.canvas.delete("rect")
        self.last_active_card = ""

    def generate_returnval(self, current_image, use_last_active_card=None):
        if use_last_active_card:
            last_active_card = use_last_active_card
        else:
            last_active_card = self.last_active_card
        current_image_tags = self.canvas.gettags(current_image)

        current_image_bbox = self.canvas.bbox(current_image)
        bbox_list = list(current_image_bbox)
        current_image_overlapping = self.canvas.find_overlapping(*bbox_list)

        tag_a = str(current_image_tags).replace(", 'current')", "").replace(")", "").replace(
            "('", "").replace("', 'face_down'", "").replace("', 'face_up'", "")
        overlapping = False
        ace_slot = False
        returnval = False
                
        over_ace_slot = False
        for card in self.canvas.find_overlapping(*self.canvas.bbox(current_image)):
            if "empty_ace_slot" in self.canvas.gettags(card):
                over_ace_slot = True
                break
        if (not over_ace_slot) and ("empty_slot" not in str(current_image_tags)):
            csl = list(self.canvas.bbox(current_image))
            if self.larger_cards:
                csl[1] = (int(csl[1]))+135
            else:
                csl[1] = (int(csl[1]))+110
            csl[3] = (int(csl[3]))+20
            csl = tuple(csl)
            csl = list(self.canvas.find_overlapping(*csl))
            for card in csl:
                if card in self.card_stack_list:
                    continue
                elif "face_up" in self.canvas.gettags(card):

                    overlapping = True
                    break

        if "empty_slot" in str(current_image_tags):
            if "king" in last_active_card:
                for card in current_image_overlapping:
                    if card in self.card_stack_list:
                        continue
                    elif "face" in str(self.canvas.gettags(card)):
                        overlapping = True
                        break

        for item in current_image_overlapping:
            if "empty_ace_slot" in self.canvas.gettags(self.canvas.find_withtag(item)):
                ace_slot = True

        if ace_slot:
            try:
                for item in self.card_stack_list:
                    self.canvas.tag_raise(item)
                item = self.canvas.find_overlapping(
                    *self.canvas.bbox(self.canvas.find_above(last_active_card)))
                overlapping = True
            except:
                pass

        if ("ace" not in last_active_card and "empty_ace_slot" in current_image_tags):
            return returnval
        elif ("king" not in last_active_card and "empty_slot" in current_image_tags):
            return returnval
        elif ("empty_slot" in last_active_card):
            return returnval
        elif overlapping:
            return returnval
        elif "king" in last_active_card and "empty_slot" in current_image_tags:
            return True
        elif self.check_move_validity(tag_a, last_active_card, ace_slot):
            return True
        else:
            return returnval

    def card_onclick(self, event):
        self.initiate_game(False)
        self.current_image = current_image = self.canvas.find_withtag(
            "current")
        self.current_image_tags = current_image_tags = self.canvas.gettags(
            current_image)
        if self.movetype == "Accessibility Mode":
            if "rect" in self.current_image_tags:
                return
            elif "()" in str(self.current_image_tags):
                return
        if len(current_image) > 1:
            current_image = current_image[0]
        self.current_image_location = self.canvas.coords(current_image)

        self.current_image_bbox = current_image_bbox = self.canvas.bbox(
            current_image)
        bbox_list = list(current_image_bbox)
        current_image_overlapping = self.canvas.find_overlapping(*bbox_list)

        self.tag_a = tag_a = str(current_image_tags).replace(", 'current')", "").replace(
            "('", "").replace("', 'face_down'", "").replace("', 'face_up'", "")
        overlapping = False
        ace_slot = False
        if self.last_active_card != "":
            if ("empty_ace_slot" not in str(current_image_tags)) and ("empty_slot" not in str(current_image_tags)):
                csl = list(self.canvas.bbox(tag_a))
                if self.larger_cards:
                    csl[1] = (int(csl[1]))+135
                else:
                    csl[1] = (int(csl[1]))+110
                csl[3] = (int(csl[3]))+20
                csl = tuple(csl)
                csl = list(self.canvas.find_overlapping(*csl))
                for i in csl:
                    if "face_up" in self.canvas.gettags(self.canvas.find_withtag(i)):
                        overlapping = True

            for item in current_image_overlapping:
                if "empty_ace_slot" in self.canvas.gettags(self.canvas.find_withtag(item)):
                    ace_slot = True

            if ace_slot:
                try:
                    for item in self.card_stack_list:
                        self.canvas.tag_raise(item)
                    item = self.canvas.find_overlapping(
                        *self.canvas.bbox(self.canvas.find_above(self.last_active_card)))
                    overlapping = True
                except:
                    pass
                self.canvas.tag_raise("rect")

            try:
                for card in self.canvas.find_overlapping(*self.canvas.bbox(self.tag_a)):
                    if "empty_cardstack" in str(self.canvas.gettags(card)):
                        overlapping = True
            except:
                pass
            if ("ace" not in self.last_active_card and "empty_ace_slot" in current_image_tags):
                if event != "send_cards_to_ace":
                    self.end_onclick(event=event)
            elif ("king" not in self.last_active_card and "empty_slot" in current_image_tags):
                if event != "send_cards_to_ace":
                    self.end_onclick(event=event)
            elif ("empty_slot" in self.last_active_card):
                if event != "send_cards_to_ace":
                    self.end_onclick(event=event)
            elif overlapping is True:
                if event != "send_cards_to_ace":
                    self.end_onclick(event=event)
            elif "king" in self.last_active_card and "empty_slot" in current_image_tags:
                self.continue_onclick(ace_slot=ace_slot, event=event)
            elif self.check_move_validity(tag_a, self.last_active_card, ace_slot) is True:
                if event == "send_cards_to_ace":
                    self.create_rectangle(
                        *self.canvas.bbox(self.last_active_card), fill="blue", tag="cardsender_highlight", alpha=.5)
                    self.canvas.tag_raise("cardsender_highlight")
                    self.update_idletasks()
                    self.canvas.after(self.default_cardsender_freeze_time)
                    self.update_idletasks()
                self.continue_onclick(ace_slot=ace_slot, event=event)
            else:
                if event != "send_cards_to_ace":
                    self.end_onclick(event=event)
        else:
            if event != "send_cards_to_ace":
                self.end_onclick(event=event)

    def end_onclick(self, event, current_tag_name="current", pass_variable_updates=False):
        self.initiate_game(False)
        self.canvas.tag_unbind("face_up", "<Enter>")
        self.canvas.tag_unbind("card_below_rect", "<Enter>")
        self.canvas.dtag("card_below_rect")

        self.current_image = current_image = self.canvas.find_withtag(
            current_tag_name)[0]
        self.current_image_tags = current_image_tags = self.canvas.gettags(
            current_image)
        self.current_image_location = self.canvas.coords(current_image)
        self.current_image_bbox = self.canvas.bbox(
            current_image)

        self.tag_a = current_image_tags[0]

        if ("empty_ace_slot" not in self.current_image_tags and "empty_slot" not in self.current_image_tags) or pass_variable_updates:
            self.card_stack_list = ""
            self.canvas.delete("rect")
            self.last_active_card = ""
            self.last_active_card = self.tag_a

            self.card_stack_list = list(
                self.canvas.bbox(self.last_active_card))
            if self.larger_cards:
                self.card_stack_list[1] = (int(self.card_stack_list[1]))+129
            else:
                self.card_stack_list[1] = (int(self.card_stack_list[1]))+99
            self.card_stack_list[3] = (int(self.card_stack_list[3]))+350
            self.card_stack_list = tuple(self.card_stack_list)
            self.card_stack_list = list(
                self.canvas.find_overlapping(*self.card_stack_list))

            if (self.movetype == "Drag"):
                if event != "send_cards_to_ace":
                    self.canvas.config(cursor="fleur")
                for card in self.card_stack_list:
                    card_tag = self.canvas.gettags(card)
                    if ("cardstack" in str(card_tag)):
                        to_be_card_stack_list = self.card_stack_list[-1]
                        self.card_stack_list = []
                        self.card_stack_list.append(to_be_card_stack_list)
                        break
                    elif ("ace_slot" in str(card_tag)):
                        self.card_stack_list = []
                        for card in self.canvas.find_withtag(self.last_active_card):
                            self.card_stack_list.append(card)
                        break
            last_active_card_bbox_list = list(
                self.canvas.bbox(self.last_active_card))
            if self.larger_cards:
                last_active_card_bbox_list[1] = int(
                    last_active_card_bbox_list[1]+80+20/self.height_skew)
            else:
                last_active_card_bbox_list[1] = int(
                    last_active_card_bbox_list[1]+70/self.height_skew)
            last_active_card_bbox_list[3] = int(
                last_active_card_bbox_list[3])#-(20*self.height_skew))
            last_active_card_bbox_list = tuple(last_active_card_bbox_list)
            self.last_active_card_overlapping = self.canvas.find_overlapping(
                *last_active_card_bbox_list)


            self.last_active_card_over = self.canvas.find_overlapping(
                *self.canvas.bbox(self.last_active_card))
            self.last_active_card_coordinates = []
            for card in self.card_stack_list:
                self.last_active_card_coordinates.append(
                    self.canvas.coords(card))

            if (self.movetype != "Drag") and (event != "send_cards_to_ace"):
                first_item = list(self.canvas.bbox(self.last_active_card))
                last_item = list(self.canvas.bbox(
                    self.canvas.find_withtag(self.card_stack_list[-1])))

                tl = first_item[0]
                tr = first_item[1]
                bl = last_item[2]
                br = last_item[3]

                positionsb = []
                positionsb.append(tl)
                positionsb.append(tr)
                positionsb.append(bl)
                positionsb.append(br)
                positionsb = tuple(positionsb)

                positions = self.canvas.bbox(self.last_active_card)

                returnval = False
                for item in self.card_stack_list:
                    if "empty_ace_slot" in self.canvas.gettags(self.canvas.find_withtag(item)):
                        returnval = True
                        break
                if returnval is True:
                    self.create_rectangle(*positions, fill="blue", alpha=.3)
                else:
                    self.create_rectangle(*positionsb, fill="blue", alpha=.3)
                if self.movetype == "Accessibility Mode":
                    self.canvas.tag_unbind("face_up", "<Enter>")
                    self.canvas.tag_bind(
                        "rect", "<Enter>", self.enter_hover_on_rect)
                    self.canvas.tag_bind("rect", "<Leave>", self.leave_hover)
                    self.canvas.tag_bind(
                        "rect", "<Button-1>", self.click_on_rect)
                elif self.movetype == "Click":
                    self.canvas.tag_bind(
                        "rect", "<Button-1>", self.click_on_rect)

    def enter_hover_on_rect(self, event):
        self.job = self.after(
            self.canvas_item_hover_time+1000, lambda: self.click_on_rect(event=event))

    def enter_hover_on_hint_rect(self, event):
        self.job = self.after(
            self.canvas_item_hover_time, lambda: self.click_on_hint_rect(event=event))

    def click_on_hint_rect(self, event):
        try:
            below_last = self.canvas.find_overlapping(*self.canvas.bbox("current"))
        except:
            return
        last_card_index_in_below = below_last.index(
            list(self.canvas.find_withtag("current"))[0])
        below_last = (below_last[last_card_index_in_below-1])
        if "empty_cardstack_slot" in self.canvas.gettags(below_last):
            self.refill_card_stack(event="hint")
        else:
            returnval = False
            for card in self.canvas.find_overlapping(*self.canvas.bbox(below_last)):
                if "empty_cardstack_slot" in self.canvas.gettags(card):
                    self.canvas.delete("rect")
                    self.stack_onclick(event="hint")
                    returnval = True
                    break
            if not returnval:
                self.canvas.tag_bind("face_up", "<Enter>", self.end_onclick)
        self.canvas.tag_unbind("rect", "<Enter>")
        self.canvas.tag_unbind("rect", "<Leave>")
        self.canvas.tag_unbind("rect", "<Button-1>")
        self.canvas.delete("rect")

    def click_on_rect(self, event):
        self.canvas.tag_bind("face_up", "<Enter>", self.end_onclick)
        self.canvas.delete("rect")

    def enter_on_hint_rect(self, event):
        self.canvas.tag_unbind("rect", "<Enter>")
        self.canvas.delete("rect")

    def continue_onclick(self, ace_slot, event):
        self.update_idletasks()
        self.cardsender_may_continue = True
        if event != "redo":
            self.redo = []
        self.canvas.delete("rect")
        tag_list = []
        new_card_on_ace = 0
        self.card_drawing_count = 20

        for i in self.last_active_card_overlapping:
            tag_list.append(self.canvas.gettags(i))
            
        if "empty_ace_slot" in str(tag_list):
            self.cards_on_ace -= 1
            self.points_label["text"] = (
                "Points: "+str((self.cards_on_ace*self.point_increment)+self.starting_points))
            new_card_on_ace = 2
            check = self.generate_drawing_count(ace_slot=ace_slot)
            if self.movetype == "Drag":
                self.card_drawing_count = 20
                for i in self.canvas.find_overlapping(*self.canvas.bbox(self.current_image)):
                    tag_list.append(self.canvas.gettags(i))
                if "empty_ace_slot" in str(tag_list):
                    check = self.generate_drawing_count(ace_slot=ace_slot)
                    if check != None:
                        new_card_on_ace = check
        else:
            check = self.generate_drawing_count(ace_slot=ace_slot)
            if check != None:
                new_card_on_ace = check

        last_active_card_bbox_list = list(
            self.canvas.bbox(self.last_active_card))
        last_active_card_bbox_list[1] = int(
            last_active_card_bbox_list[1])+60
        last_active_card_bbox_list[3] = int(
            last_active_card_bbox_list[3])-25
        last_active_card_bbox_list = tuple(last_active_card_bbox_list)

        secondreturnval = False
        empty_ace_slot_found = False
        for i in list(self.last_active_card_overlapping):
            if "empty_ace_slot" in self.canvas.gettags(self.canvas.find_withtag(i)):
                secondreturnval = True
                empty_ace_slot_found = i
                break
            elif "empty_cardstack_slotb" in self.canvas.gettags(self.canvas.find_withtag(i)):
                secondreturnval = True
                break
            
        if secondreturnval:
            last_active_card = self.canvas.find_withtag(
                self.last_active_card)
            last_active_card_coordinates = self.canvas.coords(
                last_active_card)
            xpos = int(
                self.current_image_location[0]) - int(last_active_card_coordinates[0])
            ypos = self.card_drawing_count * self.height_skew + \
                (int(self.current_image_location[1]) -
                 int(last_active_card_coordinates[1]))
            self.canvas.move(last_active_card, xpos, ypos)
            self.canvas.tag_raise(last_active_card)

            if event == "send_cards_to_ace":
                self.canvas.tag_raise("cardsender_highlight")
                self.card_moved_to_ace_by_sender += 1
            if self.movetype != "Drag":
                last_active_card_coordinates[1] = last_active_card_coordinates[1] / self.height_skew
                history_to_add = ["move_card_srv", empty_ace_slot_found, new_card_on_ace,
                                  self.last_active_card, last_active_card_coordinates, self.tag_a]
            else:
                coords = list(self.last_active_card_coordinates[0])
                coords[1] = coords[1] / self.height_skew
                history_to_add = ["move_card_srv", empty_ace_slot_found, new_card_on_ace, self.last_active_card,
                                  coords, self.current_image]
        else:
            flipped_cards = []
            moved_cards = {}
            for card in list(self.last_active_card_overlapping):
                card_values = self.canvas.find_withtag(card)
                if "face_down" in self.canvas.gettags(card_values):
                    card_tags = str(self.canvas.gettags(card_values))
                    tag_a = card_tags.replace("('", "").replace(
                        "', 'face_down')", "").replace("', 'face_up')", "")
                    self.canvas.itemconfig(
                        card_values, image=self.dict_of_cards[tag_a], tag=(tag_a, "face_up"))
                    if self.movetype == "Accessibility Mode":
                        self.canvas.tag_bind(
                            tag_a, "<Enter>", self.enter_card)
                        self.canvas.tag_bind(
                            tag_a, "<Leave>", self.leave_hover)
                        self.canvas.tag_bind(
                            tag_a, "<Button-1>", self.card_onclick)
                    elif self.movetype == "Click":
                        self.canvas.tag_bind(
                            tag_a, "<Button-1>", self.card_onclick)
                    else:
                        self.canvas.tag_bind(
                            tag_a, "<Button-1>", self.end_onclick)
                        self.canvas.tag_bind(
                            tag_a, "<Button1-Motion>", self.move_card)
                        self.canvas.tag_bind(
                            tag_a, "<ButtonRelease-1>", self.drop_card)
                        self.canvas.tag_bind(
                            tag_a, "<Enter>", self.on_draggable_card)
                        self.canvas.tag_bind(
                            tag_a, "<Leave>", self.leave_draggable_card)
                    flipped_cards.append(tag_a)
            for card in list(self.card_stack_list):
                if "face_up" in self.canvas.gettags(self.canvas.find_withtag(card)):
                    card_location = self.canvas.coords(card)
                    xpos = int(
                        self.current_image_location[0]) - int(card_location[0])
                    yincrease = self.card_drawing_count*self.height_skew
                    ypos = (yincrease + \
                        (int(self.current_image_location[1]) - int(card_location[1])))
                    self.canvas.move(card, xpos, ypos)
                    self.canvas.tag_raise(card)
                    if event == "send_cards_to_ace":
                        self.canvas.tag_raise("cardsender_highlight")
                        self.card_moved_to_ace_by_sender += 1
                    self.card_drawing_count += 20
                    coords = self.last_active_card_coordinates[self.card_stack_list.index(card)]
                    coords[0] = coords[0] - self.loc_skew
                    coords[1] = coords[1] / self.height_skew
                    moved_cards[str(self.canvas.gettags(self.canvas.find_withtag(card))).replace("('", "").replace("', 'face_down')", "").replace(
                        "', 'face_up')", "").replace("', 'face_up', 'current')", "")] = coords
            history_to_add = ["move_card", new_card_on_ace, moved_cards,
                              self.card_drawing_count, flipped_cards, self.current_image]
        self.card_stack_list = ""
        self.last_active_card = ""

        if self.cards_on_ace == 52:
            if self.sending_cards_label.winfo_ismapped():
                self.canvas.delete("cardsender_highlight")
                self.card_moved_to_ace_by_sender = 0
                self.stopwatch.freeze(True)
            self.history = []
            self.cardsender_may_continue = False
            after_game = messagebox.askquestion(
                "You've won!", "Congratulations! You've won the game! Do you want to play again?", icon="warning")
            if after_game == "yes":
                self.new_game()
            else:
                self.destroy()
                exit()

        self.history.append(history_to_add)
        self.undo_last_move_button.enable()
        self.restart_game_button.enable()
        self.redo_last_move_button.disable()
        self.update_idletasks()

    def generate_drawing_count(self, ace_slot):
        ace_slots = self.canvas.find_withtag("empty_ace_slot")
        positions_of_ace_rects = []
        for slot in ace_slots:
            positions_of_ace_rects.append(self.canvas.bbox(slot))
        returnval = False
        for i in positions_of_ace_rects:
            if str(self.current_image_bbox) == str(i):
                returnval = True
        if returnval is False:
            self.card_drawing_count = 20
        else:
            self.card_drawing_count = 0
        if "king" in self.last_active_card and "empty_slot" in self.current_image_tags:
            self.card_drawing_count = 0
        if ace_slot:
            self.cards_on_ace += 1
            self.points_label["text"] = (
                "Points: "+str((self.cards_on_ace*self.point_increment)+self.starting_points))
            self.card_drawing_count = 0
            new_card_on_ace = 1
            self.canvas_item_hover_time += 300
            return new_card_on_ace


class CustomGameMaker(tk.Toplevel):
    def __init__(self, parent, **kwargs):
        tk.Toplevel.__init__(self, parent, background="#4f4f4f", **kwargs)
        self.title("Create Custom Game")
        self.resizable(False, False)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=3)

        try:
            self.settings = json.load(open(os.path.dirname(
                os.path.abspath(__file__))+"/resources/settings.json"))
        except:
            with open((os.path.dirname(os.path.abspath(__file__))+"/resources/settings.json"), "w") as handle:
                handle.write(str(DEFAULT_SETTINGS).replace("'", '"'))
            self.settings = DEFAULT_SETTINGS
        self.custom_game = None

        try:
            self.load_settings()
        except Exception:
            self.load_settings(bypass=True)

        self.create_widgets()
        self.config_widgets()
        self.grid_all()

        try:
            self.iconbitmap(os.path.dirname(
                os.path.abspath(__file__)) + "/resources/icon.ico")
        except:
            icon = tk.PhotoImage(file=(os.path.dirname(
                os.path.abspath(__file__)) + "/resources/icon.png"))
            self.tk.call('wm', 'iconphoto', self._w, icon)

    def create_widgets(self):
        self.restart_game_button = tk.Checkbutton(
            self, text="Enable restart game button", variable=self.restart_game_button_enabled, anchor="w", bg="#4f4f4f", selectcolor="#4f4f4f",fg="#e3e3e3", activeforeground="#e3e3e3", activebackground="#706c6c", highlightthickness=0)
        self.undo_button = tk.Checkbutton(self, text="Enable undo/redo button",
                                          variable=self.undo_last_move_button_enabled, anchor="w", bg="#4f4f4f", selectcolor="#4f4f4f",fg="#e3e3e3", activeforeground="#e3e3e3", activebackground="#706c6c", highlightthickness=0)
        self.hint_button = tk.Checkbutton(
            self, text="Enable hint button", variable=self.hint_button_enabled, anchor="w", bg="#4f4f4f", selectcolor="#4f4f4f",fg="#e3e3e3", activeforeground="#e3e3e3", activebackground="#706c6c", highlightthickness=0)
        self.stopwatch_button = tk.Checkbutton(
            self, text="Show stopwatch", variable=self.show_stopwatch, anchor="w", bg="#4f4f4f", selectcolor="#4f4f4f",fg="#e3e3e3", activeforeground="#e3e3e3", activebackground="#706c6c", highlightthickness=0)
        self.starting_points_entry = tk.Spinbox(self, from_=-1000000, to=1000000, increment=5, width=30, textvariable=self.starting_points, relief="flat", highlightbackground="#e3e3e3",
                                          highlightthickness=1, bg="#cccaca", buttonbackground="#cccacc", disabledbackground="#cccaca", disabledforeground="grey")
        self.point_increment_entry = tk.Spinbox(self, from_=-1000000, to=1000000, increment=1, width=30, textvariable=self.point_increment, relief="flat", highlightbackground="#e3e3e3",
                                          highlightthickness=1, bg="#cccaca", buttonbackground="#cccacc", disabledbackground="#cccaca", disabledforeground="grey")
        self.infinite_redeals = tk.Checkbutton(
            self, text="Infinite redeals", variable=self.unlimited_redeals, anchor="w", bg="#4f4f4f", selectcolor="#4f4f4f",fg="#e3e3e3", activeforeground="#e3e3e3", activebackground="#706c6c", highlightthickness=0)
        self.redeals_label = tk.Label(
            self, text="Total Redeals:", anchor="w", bg="#4f4f4f", fg="#e3e3e3")
        self.redeals_entry = tk.Spinbox(self, from_=1, to=1000000, increment=1, width=30, textvariable=self.total_redeals, relief="flat", highlightbackground="#e3e3e3",
                                          highlightthickness=1, bg="#cccaca", buttonbackground="#cccacc", disabledbackground="#cccaca", disabledforeground="grey")
        self.bottom_frame = tk.Frame(self, background="#4f4f4f")
        self.save_button = tk.Button(self.bottom_frame, text="Save", cursor="hand2", relief="solid", borderwidth=1, padx=10, pady=1, fg="#e3e3e3", activeforeground="#e3e3e3",
                                     command=self.save, bg="#4f4f4f", activebackground="#706c6c")
        self.reset_button = tk.Button(self.bottom_frame, text="Reset", cursor="hand2", relief="solid", borderwidth=1, padx=10, pady=1, fg="#e3e3e3", activeforeground="#e3e3e3",
                                      command=self.reset_all, bg="#4f4f4f", activebackground="#706c6c")
        self.cancel_button = tk.Button(self.bottom_frame, text="Cancel", cursor="hand2", relief="solid", borderwidth=1, padx=10, pady=1, fg="#e3e3e3", activeforeground="#e3e3e3",
                                       command=lambda: self.destroy(), bg="#4f4f4f", activebackground="#706c6c")

    def config_widgets(self):
        self.starting_points_entry.config(validate="all", validatecommand=(
            (self.register(self.validate_entry)), "%P"))
        self.point_increment_entry.config(validate="all", validatecommand=(
            (self.register(self.validate_redeal_entry)), "%P"))
        self.redeals_entry.config(validate="all", validatecommand=(
            (self.register(self.validate_redeal_entry)), "%P"))

        self.restart_game_button.bind("<Enter>", self.enter_button)
        self.undo_button.bind("<Enter>", self.enter_button)
        self.infinite_redeals.bind("<Enter>", self.enter_button)
        self.hint_button.bind("<Enter>", self.enter_button)
        self.stopwatch_button.bind("<Enter>", self.enter_button)
        self.save_button.bind("<Enter>", self.enter_button)
        self.reset_button.bind("<Enter>", self.enter_button)
        self.cancel_button.bind("<Enter>", self.enter_button)

        self.restart_game_button.bind("<Leave>", self.leave_button)
        self.undo_button.bind("<Leave>", self.leave_button)
        self.infinite_redeals.bind("<Leave>", self.leave_button)
        self.hint_button.bind("<Leave>", self.leave_button)
        self.stopwatch_button.bind("<Leave>", self.leave_button)
        self.save_button.bind("<Leave>", self.leave_button)
        self.reset_button.bind("<Leave>", self.leave_button)
        self.cancel_button.bind("<Leave>", self.leave_button)

        self.unlimited_redeals_trace()

        self.wm_protocol("WM_DELETE_WINDOW", self.window_close)

    def grid_all(self):
        #tk.Label(self, text="Custom Game Creator", font=("Calibri", 10, "normal"), bg="#4f4f4f", fg="#e3e3e3",
        #         fg="grey").grid(row=0, column=0, columnspan=3, padx=8, pady=2, sticky="ew")
        self.restart_game_button.grid(
            row=1, column=0, columnspan=3, padx=8, pady=7, sticky="ew")
        self.undo_button.grid(row=2, column=0, padx=8,
                              columnspan=3, pady=7, sticky="ew")
        self.hint_button.grid(row=3, column=0, padx=8,
                              columnspan=3, pady=7, sticky="ew")
        self.stopwatch_button.grid(
            row=4, column=0, padx=8, pady=7, columnspan=3, sticky="ew")
        #ttk.Separator(self).grid(row=5, column=0, columnspan=3,
        #                         padx=8, pady=5, sticky="ew")
        tk.Label(self, text="Starting points:", anchor="w", bg="#4f4f4f", fg="#e3e3e3").grid(
            row=6, column=0, padx=8, pady=7, sticky="ew")
        self.starting_points_entry.grid(
            row=6, column=1, columnspan=2, padx=8, pady=7, sticky="ew")
        tk.Label(self, text="Point increment:", anchor="w", bg="#4f4f4f", fg="#e3e3e3").grid(
            row=7, column=0, padx=8, pady=7, sticky="ew")
        self.point_increment_entry.grid(
            row=7, column=1, columnspan=2, padx=8, pady=7, sticky="ew")
        #ttk.Separator(self).grid(row=8, column=0, columnspan=3,
        #                         padx=8, pady=5, sticky="ew")
        self.infinite_redeals.grid(
            row=9, column=0, padx=8, columnspan=3, pady=7, sticky="ew")
        self.redeals_label.grid(row=10, column=0, padx=8, pady=7, sticky="ew")
        self.redeals_entry.grid(
            row=10, column=1, columnspan=2, padx=8, pady=7, sticky="ew")
        #ttk.Separator(self).grid(row=11, column=0,
        #                         columnspan=3, padx=8, pady=5, sticky="ew")
        #ttk.Separator(self, orient="vertical").grid(
        #    row=12, column=0, padx=8, pady=5, sticky="nse")
        self.bottom_frame.grid(row=12, column=0, columnspan=3, sticky="e")
        self.cancel_button.grid(row=0, column=0, padx=8, pady=7, sticky="e")
        self.save_button.grid(row=0, column=1, padx=8, pady=7, sticky="e")
        self.reset_button.grid(row=0, column=2, padx=8, pady=7, sticky="e")

    def enter_button(self, event):
        event.widget.config(bg="#706c6c")

    def leave_button(self, event):
        event.widget.config(bg="#4f4f4f")

    def validate_entry(self, var):
        if var == "":
            return True
        if var == "-":
            return True
        else:
            try:
                int(var)
                return True
            except:
                return False

    def validate_redeal_entry(self, var):
        if var == "":
            return True
        else:
            try:
                int(var)
                if int(var) < 1:
                    return False
                else:
                    return True
            except:
                return False

    def red_bg(self, widget):
        widget.config(bg="red")
        widget.bind("<Key>", lambda event,
                    widget=widget: self.normal_bg(event, widget))
        widget.bind("<Button-1>", lambda event,
                    widget=widget: self.normal_bg(event, widget))

    def normal_bg(self, event, widget):
        widget.config(bg="#cccaca")
        widget.unbind("<Key>")
        widget.unbind("<Button-1>")

    def load_settings(self, bypass=None):
        self.gamemode = self.settings["gamemode"]

        if (self.gamemode[0] == "Custom") and not bypass:
            self.restart_game_button_enabled = tk.BooleanVar(
                value=self.gamemode[1] == "True")
            self.undo_last_move_button_enabled = tk.BooleanVar(
                value=self.gamemode[2] == "True")
            self.hint_button_enabled = tk.BooleanVar(
                value=self.gamemode[3] == "True")
            self.show_stopwatch = tk.BooleanVar(
                value=self.gamemode[4] == "True")
            self.starting_points = tk.IntVar(value=int(self.gamemode[5]))
            self.point_increment = tk.IntVar(value=int(self.gamemode[6]))
            total_redeals = self.gamemode[7]
        else:
            self.restart_game_button_enabled = tk.BooleanVar(value=True)
            self.undo_last_move_button_enabled = tk.BooleanVar(value=True)
            self.hint_button_enabled = tk.BooleanVar(value=True)
            self.show_stopwatch = tk.BooleanVar(value=True)
            self.starting_points = tk.IntVar(value=0)
            self.point_increment = tk.IntVar(value=5)
            total_redeals = "unlimited"

        if total_redeals == "unlimited":
            self.unlimited_redeals = tk.BooleanVar(value=True)
            self.total_redeals = tk.IntVar(value=1)
        else:
            self.unlimited_redeals = tk.BooleanVar(value=False)
            self.total_redeals = tk.IntVar(value=int(total_redeals))

        self.unlimited_redeals.trace("w", self.unlimited_redeals_trace)

    def unlimited_redeals_trace(self, *args):
        if self.unlimited_redeals.get() == True:
            self.redeals_label.config(state="disabled")
            self.redeals_entry.config(
                state="disabled", highlightbackground="grey")
        else:
            self.redeals_label.config(state="normal")
            self.redeals_entry.config(
                state="normal", highlightbackground="black")

    def save(self):
        custom_game = []
        custom_game.append("Custom")
        custom_game.append(str(self.restart_game_button_enabled.get()))
        custom_game.append(str(self.undo_last_move_button_enabled.get()))
        custom_game.append(str(self.hint_button_enabled.get()))
        custom_game.append(str(self.show_stopwatch.get()))

        empty_entries = 0
        try:
            custom_game.append(str(self.starting_points.get()))
        except:
            self.red_bg(self.starting_points_entry)
            empty_entries += 1
        try:
            custom_game.append(str(self.point_increment.get()))
        except:
            self.red_bg(self.point_increment_entry)
            empty_entries += 1
        if self.unlimited_redeals.get():
            custom_game.append("unlimited")
        else:
            try:
                custom_game.append(str(self.total_redeals.get()))
            except:
                self.red_bg(self.redeals_entry)
                empty_entries += 1

        if empty_entries > 0:
            return
        self.custom_game = custom_game

        self.settings["gamemode"] = custom_game
        with open((os.path.dirname(os.path.abspath(__file__))+"/resources/settings.json"), "w") as handle:
            handle.write(str(self.settings).replace("'", '"'))

        self.destroy()

    def window_close(self, *args):
        new_custom_game = []
        new_custom_game.append("Custom")
        new_custom_game.append(str(self.restart_game_button_enabled.get()))
        new_custom_game.append(str(self.undo_last_move_button_enabled.get()))
        new_custom_game.append(str(self.hint_button_enabled.get()))
        new_custom_game.append(str(self.show_stopwatch.get()))
        try:
            new_custom_game.append(str(self.starting_points.get()))
        except:
            new_custom_game.append(0)
        try:
            new_custom_game.append(str(self.point_increment.get()))
        except:
            new_custom_game.append(0)
        if self.unlimited_redeals.get():
            new_custom_game.append("unlimited")
        else:
            try:
                new_custom_game.append(str(self.total_redeals.get()))
            except:
                new_custom_game.append(0)
        if str(new_custom_game) not in str(self.settings):
            warning = messagebox.askyesnocancel(
                "Save Game.", "You haven't saved this game. Do you want to save it?", parent=self, default="yes", icon='warning')
            if warning:
                self.save()
            elif warning is None:
                return
            else:
                self.destroy()
        else:
            self.destroy()

    def reset_all(self):
        if self.gamemode[0] == "Custom":
            self.restart_game_button_enabled.set(self.gamemode[1] == "True")
            self.undo_last_move_button_enabled.set(self.gamemode[2] == "True")
            self.hint_button_enabled.set(self.gamemode[3] == "True")
            self.show_stopwatch.set(self.gamemode[4] == "True")
            self.starting_points.set(int(self.gamemode[5]))
            self.point_increment.set(int(self.gamemode[6]))
            total_redeals = self.gamemode[7]
        else:
            self.restart_game_button_enabled.set(True)
            self.undo_last_move_button_enabled.set(True)
            self.hint_button_enabled.set(True)
            self.show_stopwatch.set(True)
            self.starting_points.set(0)
            self.point_increment.set(5)
            self.total_redeals.set(True)
            total_redeals = "unlimited"

        if total_redeals == "unlimited":
            self.unlimited_redeals.set(True)
        else:
            self.unlimited_redeals.set(False)


class Combobox(tk.Frame):
    def __init__(self, parent, values=[], frame_args={}, entry_args={}, label_args={}, listbox_args={}, replace_entry_with_label=True):
        tk.Frame.__init__(self, parent, **frame_args)
        
        self.parent = parent
        self.values = values
        self.listbox_args = listbox_args
        self.box_opened_count = False
        self.mouse_on_self = False
        self.box_opened = 0
        self.pack_propagate(0)
        self.label_image = tk.PhotoImage(
            file=(os.path.dirname(os.path.abspath(__file__))+"/resources/arrow.png"))
        self.other_label_image = tk.PhotoImage(
            file=(os.path.dirname(os.path.abspath(__file__))+"/resources/arrow_up.png"))
        try:
            self.textvariable = entry_args["textvariable"]
        except:
            self.textvariable = tk.StringVar()
            entry_args["textvariable"] = self.textvariable
        try:
            self.highlightthickness = entry_args["highlightthickness"]
        except:
            self.highlightthickness = 0
        if "image" in label_args:
            label_args.pop("image")
        if replace_entry_with_label:
            self.entry = entry = tk.Label(self, **entry_args)
        else:
            self.entry = entry = tk.Entry(self, **entry_args)
        entry.pack(side="left", expand=True, fill="both")

        self.entry.config(highlightthickness=self.highlightthickness)

        self.label = label = tk.Label(
            self, image=self.label_image, cursor="hand2", **label_args)
        label.pack(side="right", fill="both")

        try:
            activecolor = label_args.pop("activebackground")
            try:
                color = label_args["background"]
            except:
                try:
                    color = label_args["bg"]
                except:
                    color = "white"
            label.bind("<Enter>", lambda event,
                       color=activecolor: self.label_hover(event, color))
            label.bind("<Leave>", lambda event,
                       color=color: self.label_hover(event, color))
        except:
            pass

        divider = tk.Frame(self, width=1, bg="black")
        divider.pack(side="right", pady=4, fill="both")
        self.bind("<Button-1>", self.focusin, "+")
        self.label.bind("<Button-1>", self.focusin, "+")
        self.entry.bind("<Button-1>", self.focusin, "+")
        divider.bind("<Button-1>", self.focusin, "+")

        self.bind("<Enter>", self.on_self, "+")
        self.label.bind("<Enter>", self.on_self, "+")
        self.entry.bind("<Enter>", self.on_self, "+")
        divider.bind("<Enter>", self.on_self, "+")
        self.bind("<Leave>", self.off_self, "+")
        self.label.bind("<Leave>", self.off_self, "+")
        self.entry.bind("<Leave>", self.off_self, "+")
        divider.bind("<Leave>", self.off_self, "+")

        if os.name != "nt":
           self.parent.bind("<Button-1>", self.focusout, "+")

    def on_self(self, event):
        self.mouse_on_self = True

    def off_self(self, event):
        self.mouse_on_self = False

    def open_listbox(self, event):
        self.entry.config(highlightthickness=self.highlightthickness)

        if self.box_opened_count:
            if self.box_opened == 1:
                self.box_opened = 0
            else:
                self.delete_box()
                self.box_opened += 1
                return

        self.entry.update()
        self.label.update()
        loc_x = self.winfo_rootx()
        loc_y = self.entry.winfo_rooty() + self.winfo_height() - 2
        width = self.entry.winfo_width() + self.label.winfo_width() + 3
        self.box = box = tk.Toplevel(self.parent)
        box.wm_overrideredirect(1)
        self.listbox = listbox = tk.Listbox(box, **self.listbox_args)
        height_increment = 23
        height = 0
        for item in self.values:
            listbox.insert("end", item)
            height += height_increment
        listbox.pack(fill="both")
        listbox.config(width=0, height=0)
        box.wm_geometry("%dx%d+%d+%d" % (width, height, loc_x, loc_y))
        listbox.update()
        box.wm_geometry("%dx%d" % (width, listbox.winfo_height()))
        listbox.bind("<<ListboxSelect>>", self.listbox_select)
        listbox.bind("<Motion>", self.on_listbox_enter)
        self.label.config(image=self.other_label_image)
        self.box.focus_set()
        self.box.bind("<FocusOut>", self.window_move, "+")

    def focusin(self, event):
        self.open_listbox(event=event)
        self.box_opened_count = True

    def focusout(self, event):
        for item in self.winfo_children():
            if str(item) in str(event.widget):
                return
        try:
            self.delete_box()
        except:
            pass

    def window_move(self, event):
        if self.mouse_on_self:
            return
        try:
            self.delete_box()
        except:
            pass

    def label_hover(self, event, color):
        event.widget.config(background=color)

    def delete_box(self, event=None):
        self.box.unbind("<FocusOut>")
        self.label.config(image=self.label_image)
        self.box.destroy()
        self.box_opened_count = False

    def listbox_select(self, event):
        widget = event.widget
        try:
            index = widget.curselection()[0]
        except:
            return
        selected = widget.get(index)
        self.delete_box()
        self.textvariable.set(selected)
        self.event_generate("<<ComboboxSelect>>")

    def on_listbox_enter(self, event):
        index = event.widget.index("@%s,%s" % (event.x, event.y))
        event.widget.selection_clear(0, "end")
        event.widget.select_set(index)

class Information(tk.Frame):
    def __init__(self, parent, **kwargs):
        tk.Frame.__init__(self, parent, background="#4f4f4f", **kwargs)
        style = ttk.Style()
        style.configure("TScrollbar",
                        troughcolor="#4f4f4f",
                        background="#4f4f4f",
                        bordercolor="#4f4f4f")
        style.map("TScrollbar",
                background=[("active", "darkgray")])
        self.rowconfigure(0, weight=1)
        self.text = HtmlFrame(self, messages_enabled=False, on_link_click=lambda url: webbrowser.open(url), **kwargs)
        self.grid_propagate(0)
        self.text.grid_propagate(0)
        self.text.load_html("""<style>body {background-color: #4f4f4f; color: #e3e3e3} a {color: #19beff} h4 {margin-bottom: -5px} hr {border-bottom-width: 0; border-top-width: 1px; border-color: grey} div {text-align: center} div p {margin-bottom: 10px}</style><body>
                       <div><p style="font-size: 12px; margin-top: 0px; color:grey; margin-bottom:0">TkSolitaire V.1.8.0</p>
                            <a style="font-size: 12px" href="https://github.com/Andereoo/TkSolitaire/">https://github.com/Andereoo/TkSolitaire/</a>
                            <p>An embeddable and accessable solitaire game written in Tkinter and Python 3</p>
                            </div>
<h4>About Solitaire</h4><hr>
<p>Solitaire is one of the most pleasurable pastimes for one person. Often called, "Patience," more than 150 Solitaire games have been devised.</p>
<h4>The Pack</h4><hr>
<p>Virtually all Solitaire games are played with one or more standard 52-card packs. Standard Solitaire uses one 52-card pack.</p>
<h4>Object of the Game</h4><hr>
<p>The first objective is to release and play into position certain cards to build up each foundation, in sequence and in suit, from the ace through the king. The ultimate objective is to build the whole pack onto the foundations, and if that can be done, the Solitaire game is won.</p>
<h4>Rank of Cards</h4><hr>
<p>The rank of cards in Solitaire games is: K (high), Q, J, 10, 9, 8, 7, 6, 5, 4, 3, 2, A (low).</p>
<h4>The Deal</h4><hr>
<p>There are four different types of piles in Solitaire:   </p>                     
<ul>
    <li>The Tableau: Seven piles that make up the main table.</li>
    <li>The Foundations: Four piles on which a whole suit or sequence must be built up. In most Solitaire games, the four aces are the bottom card or base of the foundations. The foundation piles are hearts, diamonds, spades, and clubs.</li>
    <li>The Stock (or “Hand”) Pile: If the entire pack is not laid out in a tableau at the beginning of a game, the remaining cards form the stock pile from which additional cards are brought into play according to the rules.</li>
    <li>The Talon (or “Waste”) Pile: Cards from the stock pile that have no place in the tableau or on foundations are laid face up in the waste pile.</li>
</ul>                   
<p>To form the tableau, seven piles need to be created. Starting from left to right, place the first card face up to make the first pile, deal one card face down for the next six piles. Starting again from left to right, place one card face up on the second pile and deal one card face down on piles three through seven. Starting again from left to right, place one card face up on the third pile and deal one card face down on piles four through seven. Continue this pattern until pile seven has one card facing up on top of a pile of six cards facing down.</p>
<p>The remaining cards form the stock (or “hand”) pile and are placed above the tableau.</p>
<p>When starting out, the foundations and waste pile do not have any cards.</p>
<h4>The Play</h4><hr>
<p>The initial array may be changed by "building" - transferring cards among the face-up cards in the tableau. Certain cards of the tableau can be played at once, while others may not be played until certain blocking cards are removed. For example, of the seven cards facing up in the tableau, if one is a nine and another is a ten, you may transfer the nine to on top of the ten to begin building that pile in sequence. Since you have moved the nine from one of the seven piles, you have now unblocked a face down card; this card can be turned over and now is in play.</p>
<p>As you transfer cards in the tableau and begin building sequences, if you uncover an ace, the ace should be placed in one of the foundation piles. The foundations get built by suit and in sequence from ace to king.</p>
<p>Continue to transfer cards on top of each other in the tableau in sequence. If you can’t move any more face up cards, you can utilize the stock pile by flipping over the first card. This card can be played in the foundations or tableau. If you cannot play the card in the tableau or the foundations piles, move the card to the waste pile and turn over another card in the stock pile.</p>
<p>If a vacancy in the tableau is created by the removal of cards elsewhere it is called a “space”, and it is of major importance in manipulating the tableau. If a space is created, it can only be filled in with a king. Filling a space with a king could potentially unblock one of the face down cards in another pile in the tableau.</p>
<p style="margin-bottom: 0px">Continue to transfer cards in the tableau and bring cards into play from the stock pile until all the cards are built in suit sequences in the foundation piles to win!</p>
<p style="float: right; font-size: 12px; margin-top: 0">From <a href="https://bicyclecards.com/how-to-play/solitaire">bicyclecards.com</a></p>
</body>
""")
        self.text.grid(row=0, column=0, sticky="nsew")
        closebtn = tk.Button(self, text="Close", relief="solid", borderwidth=1, padx=10, pady=1, cursor="hand2", command=self.close, fg="#e3e3e3", activeforeground="#e3e3e3", bg="#4f4f4f", activebackground="#706c6c")
        closebtn.grid(row=1, column=0, padx=8, pady=7, sticky="e")
        closebtn.bind("<Enter>", self.enter_button)
        closebtn.bind("<Leave>", self.leave_button)
        
    def enter_button(self, event):
        event.widget.config(bg="#706c6c")

    def leave_button(self, event):
        event.widget.config(bg="#4f4f4f")

    def close(self):
        self.event_generate("<<InformationClose>>")

class Settings(tk.Frame):
    def __init__(self, parent, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        self.config(background="#4f4f4f")

        self.columnconfigure(0, weight=1)

        self.custom_game_settings = None
        self.updated_settings = False

        try:
            self.settings = settings = json.load(open(os.path.dirname(
                os.path.abspath(__file__))+"/resources/settings.json"))
            movetype = settings["movetype"]
            gamemode = settings["gamemode"]
            if gamemode[0] == "Custom":
                self.custom_game_settings = gamemode
                gamemode = gamemode[0]
            canvas_default_item_hover_time = int(
                settings["canvas_default_item_hover_time"])
            default_cardsender_freeze_time = int(
                settings["default_cardsender_freeze_time"])
            show_footer = settings["show_footer"] == "True"
            show_header = settings["show_header"] == "True"
            continuous_points = settings["continuous_points"] == "True"
            card_back = settings["card_back"]
            canvas_color = settings["canvas_color"]
            larger_cards = settings["larger_cards"]
        except:
            with open((os.path.dirname(os.path.abspath(__file__))+"/resources/settings.json"), "w") as handle:
                handle.write(str(DEFAULT_SETTINGS).replace("'", '"'))
            self.settings = settings = json.load(open(os.path.dirname(
                os.path.abspath(__file__))+"/resources/settings.json"))
            settings = json.load(open(os.path.dirname(
                os.path.abspath(__file__))+"/resources/settings.json"))
            movetype = settings["movetype"]
            gamemode = settings["gamemode"]
            canvas_default_item_hover_time = int(
                settings["canvas_default_item_hover_time"])
            default_cardsender_freeze_time = int(
                settings["default_cardsender_freeze_time"])
            show_footer = settings["show_footer"] == "True"
            show_header = settings["show_header"] == "True"
            continuous_points = settings["continuous_points"] == "True"
            card_back = settings["card_back"]
            canvas_color = settings["canvas_color"]
            larger_cards = settings["larger_cards"]

        self.movetype_chooser_var = tk.StringVar(value=movetype)
        self.gametype_chooser_var = tk.StringVar(value=gamemode)
        self.hovertime_scale_var = tk.IntVar(
            value=canvas_default_item_hover_time)
        self.cardsender_scale_var = tk.IntVar(
            value=default_cardsender_freeze_time)
        self.card_back_var = tk.StringVar(value=card_back)
        self.canvas_color_var = tk.StringVar(value=canvas_color)
        self.header_button_var = tk.BooleanVar(value=show_header)
        self.footer_button_var = tk.BooleanVar(value=show_footer)
        self.larger_cards_button_var = tk.BooleanVar(
            value=larger_cards)
        self.continuous_points_button_var = tk.BooleanVar(
            value=continuous_points)
        self.movetype_chooser_options = ["Drag", "Click", "Accessibility Mode"]
        self.gametype_chooser_options = [
            "TkSolitaire Classic", "Vegas", "Practice Mode", "Custom"]

        self.create_widgets()
        self.config_widgets()
        self.grid_propagate(0)

        self.grid_all()

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TScale", background="#4f4f4f")
        self.text = HtmlFrame(self, messages_enabled=False, on_link_click=lambda url: webbrowser.open(url), selection_enabled=False)
        #self.intro_label = tk.Label(self, text="TkSolitaire Settings", font=(
        #    "Calibri", 10, "normal"), bg="#4f4f4f", fg="#e3e3e3", fg="grey") #4f4f4f; color: #e3e3e3; 19beff
        self.movetype_chooser = Combobox(self, self.movetype_chooser_options, {"height": 21, "width": 200, "bg": "#cccaca", "highlightbackground": "#e3e3e3", "highlightthickness": 1},
                                         {"textvariable": self.movetype_chooser_var, "anchor": "w",
                                             "padx": 2, "background": "#cccaca", "cursor": "arrow"},
                                         {"width": 10, "relief": "flat",
                                          "activebackground": "#b0b2bf", "bg": "#cccaca"},
                                         {"relief": "flat", "highlightbackground": "#e3e3e3", "highlightthickness": 1, "bg": "#d4d2d2"})
        self.gametype_chooser = Combobox(self, self.gametype_chooser_options, {"height": 21, "width": 200, "bg": "#cccaca", "highlightbackground": "#e3e3e3", "highlightthickness": 1},
                                         {"textvariable": self.gametype_chooser_var, "anchor": "w",
                                             "padx": 2, "background": "#cccaca", "cursor": "arrow"},
                                         {"width": 10, "relief": "flat",
                                          "activebackground": "#b0b2bf", "bg": "#cccaca"},
                                         {"relief": "flat", "highlightbackground": "#e3e3e3", "highlightthickness": 1, "bg": "#d4d2d2"})
        #self.movetype_label = tk.Label(self,
        #                               text="Move Type:", bg="#4f4f4f", fg="#e3e3e3", fg="#e3e3e3")
        #self.gametype_label = tk.Label(self,
        #                               text="Game Type:", bg="#4f4f4f", fg="#e3e3e3", fg="#e3e3e3")

        self.hovertime_scale = ttk.Scale(self, from_=0, to=2000, variable=self.hovertime_scale_var,
                                         value=self.hovertime_scale_var.get(), command=self.hovertime_scale_change)
        self.cardsender_scale = ttk.Scale(self, from_=0, to=2000, variable=self.cardsender_scale_var,
                                          value=self.cardsender_scale_var.get(), command=self.cardsender_scale_change)
        self.hovertime_entry = tk.Spinbox(self, from_=0, to=2000, increment=100, textvariable=self.hovertime_scale_var, relief="flat", highlightbackground="#e3e3e3",
                                          highlightthickness=1, bg="#cccaca", buttonbackground="#cccacc", disabledbackground="#cccaca", disabledforeground="grey")
        self.cardsender_entry = tk.Spinbox(self, from_=0, to=2000, increment=100, textvariable=self.cardsender_scale_var,
                                           relief="flat",  highlightbackground="#e3e3e3", highlightthickness=1, bg="#cccaca", buttonbackground="#cccacc")
        #self.hover_after_label = tk.Label(self, fg="#e3e3e3",
        #                                  text="Auto click after:                 \n(Accessibility Mode only)", anchor="w", bg="#4f4f4f", fg="#e3e3e3")
        #self.card_stack_hover_after_label = tk.Label(self, fg="#e3e3e3",
        #                                             text="Game solver wait time:", bg="#4f4f4f", fg="#e3e3e3")

        self.python_card_button = tk.Radiobutton(self, text="Python card", variable=self.card_back_var, highlightthickness=0, fg="#e3e3e3", activeforeground="#e3e3e3", selectcolor="#4f4f4f",
                                               value="python_card_back", anchor="w", bg="#4f4f4f", activebackground="#706c6c")
        self.traditional_card_button = tk.Radiobutton(self, text="Classic card", variable=self.card_back_var, highlightthickness=0, fg="#e3e3e3", activeforeground="#e3e3e3", selectcolor="#4f4f4f",
                                                      value="card_back", anchor="w", bg="#4f4f4f", activebackground="#706c6c")
        self.larger_cards_button = tk.Checkbutton(self, highlightthickness=0, fg="#e3e3e3", activeforeground="#e3e3e3", selectcolor="#4f4f4f",
                                                       text="Use larger cards   (will require game restart)", variable=self.larger_cards_button_var, anchor="w", bg="#4f4f4f", activebackground="#706c6c")

        #self.color_entry_label = tk.Label(self, fg="#e3e3e3",
        #                                  text="Canvas background color:", bg="#4f4f4f", fg="#e3e3e3")
        self.color_entry = tk.Entry(self, textvariable=self.canvas_color_var, state='disabled', relief="flat", highlightbackground="#000000", highlightthickness=1,
                                    bg=self.canvas_color_var.get(), disabledbackground=self.canvas_color_var.get(), disabledforeground=self.generate_altered_colour(self.canvas_color_var.get()), cursor="hand2")

        self.continuous_points_button = tk.Checkbutton(self, highlightthickness=0, selectcolor="#4f4f4f",
                                                       text="Continuous points (Vegas mode only)", variable=self.continuous_points_button_var, anchor="w", bg="#4f4f4f", fg="#e3e3e3", activebackground="#706c6c")

        self.header_button = tk.Checkbutton(self, fg="#e3e3e3", activeforeground="#e3e3e3", selectcolor="#4f4f4f",
                                            text="Show header", variable=self.header_button_var, highlightthickness=0, anchor="w", bg="#4f4f4f", activebackground="#706c6c")
        self.footer_button = tk.Checkbutton(self, fg="#e3e3e3", activeforeground="#e3e3e3", selectcolor="#4f4f4f",
                                            text="Show footer", variable=self.footer_button_var, highlightthickness=0, anchor="w", bg="#4f4f4f", activebackground="#706c6c")
        self.save_button = tk.Button(self, text="Save", cursor="hand2", relief="solid", borderwidth=1, padx=10, pady=1, fg="#e3e3e3", activeforeground="#e3e3e3",
                                     command=self.close, bg="#4f4f4f", activebackground="#706c6c")
        self.reset_button = tk.Button(self, text="Reset", cursor="hand2", relief="solid", borderwidth=1, padx=10, pady=1, fg="#e3e3e3", activeforeground="#e3e3e3",
                                      command=self.reset_all, bg="#4f4f4f", activebackground="#706c6c")

    def config_widgets(self):
        self.movetype_chooser.bind(
            "<<ComboboxSelect>>", self.movetype_chooser_select)
        self.gametype_chooser.bind(
            "<<ComboboxSelect>>", self.gametype_chooser_select)

        self.hovertime_entry.config(validate="all", validatecommand=((self.register(
            lambda var, scale=self.hovertime_scale: self.validate_entry(var, scale))), "%P"))
        self.cardsender_entry.config(validate="all", validatecommand=((self.register(
            lambda var, scale=self.cardsender_scale: self.validate_entry(var, scale))), "%P"))

        if self.gametype_chooser_var.get() != "Vegas":
            self.continuous_points_button.config(state="disabled")
        else:
            self.continuous_points_button.bind("<Enter>", self.enter_button)
            self.continuous_points_button.bind("<Leave>", self.leave_button)
        if self.movetype_chooser_var.get() != "Accessibility Mode":
            self.hovertime_scale.state(["disabled"])
            self.hovertime_entry.config(
                state="disabled", highlightbackground="grey")
            #self.hover_after_label.config(state="disabled")

        self.python_card_button.bind("<Enter>", self.enter_button)
        self.traditional_card_button.bind("<Enter>", self.enter_button)
        self.larger_cards_button.bind("<Enter>", self.enter_button)
        self.header_button.bind("<Enter>", self.enter_button)
        self.footer_button.bind("<Enter>", self.enter_button)
        self.python_card_button.bind("<Leave>", self.leave_button)
        self.traditional_card_button.bind("<Leave>", self.leave_button)
        self.larger_cards_button.bind("<Leave>", self.leave_button)
        self.header_button.bind("<Leave>", self.leave_button)
        self.footer_button.bind("<Leave>", self.leave_button)
        self.save_button.bind("<Enter>", self.enter_button)
        self.reset_button.bind("<Enter>", self.enter_button)
        self.save_button.bind("<Leave>", self.leave_button)
        self.reset_button.bind("<Leave>", self.leave_button)

        self.color_entry.bind("<Button-1>", self.open_colorpicker)
        self.color_entry.bind("<Enter>", lambda event: self.color_entry.config(
            highlightbackground=self.color_entry["bg"]))
        self.color_entry.bind("<Leave>", self.leave_combo)

        self.hovertime_entry.bind("<Enter>", self.enter_entry)
        self.hovertime_entry.bind("<Leave>", self.leave_entry)
        self.cardsender_entry.bind("<Enter>", self.enter_entry)
        self.cardsender_entry.bind("<Leave>", self.leave_entry)

        self.movetype_chooser.bind("<Enter>", self.enter_combo)
        self.movetype_chooser.bind("<Leave>", self.leave_combo)
        self.gametype_chooser.bind("<Enter>", self.enter_combo)
        self.gametype_chooser.bind("<Leave>", self.leave_combo)

        self.last_gamemode = self.gametype_chooser_var.get()

    def enter_entry(self, event):
        if event.widget["state"] == "normal":
            event.widget.config(highlightbackground="grey")

    def leave_entry(self, event):
        if event.widget["state"] == "normal":
            event.widget.config(highlightbackground="#e3e3e3")

    def enter_combo(self, event):
        event.widget.config(highlightbackground="grey")

    def leave_combo(self, event):
        event.widget.config(highlightbackground="#e3e3e3")

    def grid_all(self):
        self.grid_rowconfigure(0, weight=1)
        self.text.load_html("""<style>span, object {margin-top: 5px; margin-bottom: 5px} body {background-color: #4f4f4f; color: #e3e3e3; cursor: default} a {color: #19beff} h4 {margin-bottom: -5px} hr {margin-bottom: 10px; border-bottom-width: 0; border-top-width: 1px; border-color: grey} div p {margin-bottom: 10px}</style><body>
                       <div style="text-align: center"><p style="font-size: 12px; margin-top: 0px; color:grey; margin-bottom:0">TkSolitaire V.1.8.0</p>
                            </div>
<h4>Game:</h4><hr>
<table style="width: 100%"><tr><td><span style="vertical-align: middle;">Move type:</span></td><td style="width: 60%"><object allowscrolling style="vertical-align: middle; width:100%" data="""+str(self.movetype_chooser)+"""></object></td></tr>
<tr><td><span style="vertical-align: middle;">Game type:</span></td><td style="width: 60%"><object allowscrolling style="vertical-align: middle; width:100%" data="""+str(self.gametype_chooser)+"""></object></td></tr></table>
<h4 style="">Timing:</h4><hr>
<table style="width: 100%"><tr><td><span style="vertical-align: middle;">Auto click after:<br>(accessibility mode only)</span></td><td style="width: 60%"><object allowscrolling style="vertical-align: middle; width:30%" data="""+str(self.hovertime_scale)+"""></object><object allowscrolling style="vertical-align: middle; width:68%; padding-left:2%;" data="""+str(self.hovertime_entry)+"""></object></td></tr>
<tr><td><span style="vertical-align: middle;">Game solver wait time:</span></td><td style="width: 60%"><object allowscrolling style="vertical-align: middle; width:30%" data="""+str(self.cardsender_scale)+"""></object><object allowscrolling style="vertical-align: middle; width:68%; padding-left:2%;" data="""+str(self.cardsender_entry)+"""></object></td></tr></table>
<h4 style="">Cards:</h4><hr>
<div style=""><object allowscrolling style="vertical-align: middle; width: 100%" data="""+str(self.larger_cards_button)+"""></object></div>
<table style="width: 100%"><tr><td><object allowscrolling style="vertical-align: middle; width:100%" data="""+str(self.python_card_button)+"""></object></td><td><object allowscrolling style="vertical-align: middle; width:100%" data="""+str(self.traditional_card_button)+"""></object></td></tr></table></div>
<hr style="">
<table style="width: 100%"><tr><td><span style="vertical-align: middle;">Canvas background color:</span></td><td style="width: 60%"><object allowscrolling style="vertical-align: middle; width:100%" data="""+str(self.color_entry)+"""></object></td></tr></table>
<hr style="margin-top: 10px">
<div style=""><object allowscrolling style="vertical-align: middle; width: 100%" data="""+str(self.continuous_points_button)+"""></object></div>
<table style="width: 100%"><tr><td><object allowscrolling style="vertical-align: middle; width:100%" data="""+str(self.header_button)+"""></object></td><td><object allowscrolling style="vertical-align: middle; width:100%" data="""+str(self.footer_button)+"""></object></td></tr></table></div>
</body>
""")
        self.text.grid(row=0, column=0, sticky="nsew", columnspan=3)
        self.save_button.grid(row=1, column=1, padx=8, pady=7, sticky="ew")
        self.reset_button.grid(row=1, column=2, padx=8, pady=7, sticky="ew")

    def open_colorpicker(self, event):
        color = askcolor(parent=self, color=self.canvas_color_var.get(
        ), title="Choose canvas background color")[1]
        if color:
            self.canvas_color_var.set(color)
            self.color_entry.config(bg=color, disabledbackground=color,
                                    disabledforeground=self.generate_altered_colour(color))

    def generate_altered_colour(self, color):
        rgb = list(self.hex_to_rgb(color))
        rgb[0] = max(1, min(255, 240-rgb[0]))
        rgb[1] = max(1, min(255, 240-rgb[1]))
        rgb[2] = max(1, min(255, 240-rgb[2]))
        return self.rgb_to_hex(*rgb)

    def hex_to_rgb(self, color):
        value = color.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

    def rgb_to_hex(self, red, green, blue):
        return '#%02x%02x%02x' % (red, green, blue)

    def reset_all(self):
        self.focus()
        self.movetype_chooser_var.set("Drag")
        self.gametype_chooser_var.set("TkSolitaire Classic")
        self.continuous_points_button.unbind("<Enter>")
        self.continuous_points_button.unbind("<Leave>")
        self.hovertime_scale.config(value=300)
        self.hovertime_scale.state(["disabled"])
        self.cardsender_scale.config(value=600)
        self.hovertime_scale_var.set(300)
        self.cardsender_scale_var.set(600)
        self.hovertime_entry.config(
            state="disabled", highlightbackground="grey")
        #self.hover_after_label.config(state="disabled")
        self.continuous_points_button.config(state="disabled")
        self.continuous_points_button_var.set(True)
        self.canvas_color_var.set("#103b0a")
        self.color_entry.config(bg="#103b0a", disabledbackground="#103b0a")
        self.header_button_var.set(True)
        self.footer_button_var.set(True)
        self.larger_cards_button_var.set(False)
        self.card_back_var.set("python_card_back")
        self.last_gamemode = self.gametype_chooser_var.get()

    def red_bg(self, widget):
        widget.config(bg="red")
        widget.bind("<Key>", lambda event,
                    widget=widget: self.normal_bg(event, widget))
        widget.bind("<Button-1>", lambda event,
                    widget=widget: self.normal_bg(event, widget))

    def normal_bg(self, event, widget):
        widget.config(bg="#cccaca")
        widget.unbind("<Key>")
        widget.unbind("<Button-1>")

    def close(self):
        self.event_generate("<<SettingsClose>>")

    def save(self):
        settings = {}
        settings["movetype"] = self.movetype_chooser_var.get()
        if self.gametype_chooser_var.get() == "Custom":
            settings["gamemode"] = self.custom_game_settings
        else:
            settings["gamemode"] = self.gametype_chooser_var.get()
        empty_entries = 0
        try:
            settings["canvas_default_item_hover_time"] = str(
                self.hovertime_scale_var.get())
        except:
            if self.hovertime_entry["state"] == 'normal':
                self.red_bg(self.hovertime_entry)
                empty_entries += 1
            else:
                self.hovertime_scale_var.set(0)
                settings["canvas_default_item_hover_time"] = str(
                    self.hovertime_scale_var.get())
        try:
            settings["default_cardsender_freeze_time"] = str(
                self.cardsender_scale_var.get())
        except:
            self.red_bg(self.cardsender_entry)
            empty_entries += 1
        if empty_entries > 0:
            return
        settings["show_footer"] = str(self.footer_button_var.get())
        settings["show_header"] = str(self.header_button_var.get())
        settings["continuous_points"] = str(
            self.continuous_points_button_var.get())
        settings["card_back"] = str(self.card_back_var.get())
        settings["canvas_color"] = str(self.canvas_color_var.get())
        settings["larger_cards"] = str(
            self.larger_cards_button_var.get())
        self.updated_settings = True
        with open((os.path.dirname(os.path.abspath(__file__))+"/resources/settings.json"), "w") as handle:
            handle.write(str(settings).replace("'", '"'))
        self.event_generate("<<SettingsSaved>>")

    def enter_button(self, event):
        event.widget.config(bg="#706c6c")

    def leave_button(self, event):
        event.widget.config(bg="#4f4f4f")

    def validate_entry(self, var, scale):
        if var == "":
            return True
        elif " " in var:
            return False
        else:
            try:
                int(var)
                return True
            except:
                return False

    def hovertime_scale_change(self, val):
        self.focus()
        self.hovertime_scale_var.set(round(self.hovertime_scale_var.get()))

    def cardsender_scale_change(self, val):
        self.focus()
        self.cardsender_scale_var.set(round(self.cardsender_scale_var.get()))

    def gametype_chooser_select(self, event):
        self.focus()
        if self.gametype_chooser_var.get() != "Vegas":
            self.continuous_points_button.config(state="disabled")
            self.continuous_points_button.unbind("<Enter>")
            self.continuous_points_button.unbind("<Leave>")
            if self.gametype_chooser_var.get() == "Custom":
                settings = CustomGameMaker(self)
                settings.grab_set()
                settings.bind("<Destroy>", lambda event: self.update_custom(
                    event, item=settings.custom_game), "+")
            else:
                self.last_gamemode = self.gametype_chooser_var.get()
        else:
            self.continuous_points_button.config(state="normal")
            self.continuous_points_button.bind("<Enter>", self.enter_button)
            self.continuous_points_button.bind("<Leave>", self.leave_button)

    def update_custom(self, event, item):
        if item:
            self.custom_game_settings = item
            self.last_gamemode = self.gametype_chooser_var.get()
        else:
            self.gametype_chooser_var.set(self.last_gamemode)

    def movetype_chooser_select(self, event):
        self.focus()
        if self.movetype_chooser_var.get() == "Accessibility Mode":
            self.hovertime_scale.state(["!disabled"])
            self.hovertime_entry.config(
                state="normal", highlightbackground="#e3e3e3")
            #self.hover_after_label.config(state="normal")
        else:
            self.hovertime_scale.state(["disabled"])
            self.hovertime_entry.config(
                state="disabled", highlightbackground="grey")
            #self.hover_after_label.config(state="disabled")

    def delete_window(self, *args):
        if not self.updated_settings:
            settings = {}
            settings["movetype"] = self.movetype_chooser_var.get()
            if self.gametype_chooser_var.get() == "Custom":
                settings["gamemode"] = self.custom_game_settings
            else:
                settings["gamemode"] = self.gametype_chooser_var.get()
            empty_entries = 0
            try:
                settings["canvas_default_item_hover_time"] = str(
                    self.hovertime_scale_var.get())
            except:
                if self.hovertime_entry["state"] == "normal":
                    self.red_bg(self.hovertime_entry)
                    empty_entries += 1
                else:
                    self.hovertime_scale_var.set(0)
                    settings["canvas_default_item_hover_time"] = str(
                        self.hovertime_scale_var.get())
            try:
                settings["default_cardsender_freeze_time"] = str(
                    self.cardsender_scale_var.get())
            except:
                self.red_bg(self.cardsender_entry)
                empty_entries += 1
            if empty_entries > 0:
                return
            
            settings["show_footer"] = str(self.footer_button_var.get())
            settings["show_header"] = str(self.header_button_var.get())
            settings["continuous_points"] = str(
                self.continuous_points_button_var.get())
            settings["canvas_color"] = str(self.canvas_color_var.get())
            settings["card_back"] = str(self.card_back_var.get())
            settings["larger_cards"] = str(
                self.larger_cards_button_var.get())
            if self.settings != settings:
                save = messagebox.askyesnocancel(
                    "Save Settings.", "You haven't saved your settings. Do you want to save them?", parent=self, default="yes", icon="warning")
                if save:
                    with open((os.path.dirname(os.path.abspath(__file__))+"/resources/settings.json"), "w") as handle:
                        handle.write(str(settings).replace("'", '"'))
                elif save is None:
                    return
        self.event_generate("<<SettingsClose>>")

def main():
    window = SolitaireGameWindow()
    window.mainloop()


if __name__ == "__main__":
    if os.name == "nt":
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    main()

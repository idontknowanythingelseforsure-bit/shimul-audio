import os
import json
import time

# Timestamp taken before Kivy/KivyMD are imported, used by the temporary
# startup report. Safe to remove once startup work is done.
_T_IMPORT_START = time.time()

import random
import threading

from kivy.config import Config
# Cheaper first frame on low-end phone GPUs (no MSAA).
Config.set("graphics", "multisamples", "0")

from kivy.factory import Factory
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import platform, get_color_from_hex
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivymd.app import MDApp
from kivymd.uix.list import (
    OneLineListItem,
    TwoLineAvatarIconListItem,
    IconLeftWidget,
    IconRightWidget,
)
from kivymd.toast import toast

_T_IMPORT_END = time.time()

# ---------- Cross-Platform Audio Engine Setup ----------
USE_PYGAME = False
USE_ANDROID_PLAYER = False

if platform == "android":
    try:
        from jnius import autoclass
        MediaPlayer = autoclass("android.media.MediaPlayer")
        USE_ANDROID_PLAYER = True
    except Exception:
        from kivy.core.audio import SoundLoader
else:
    try:
        import pygame
        pygame.mixer.init()
        USE_PYGAME = True
    except Exception:
        from kivy.core.audio import SoundLoader

KV = '''
#:import hex kivy.utils.get_color_from_hex

<DrawerItem@OneLineAvatarIconListItem>:
    icon: "music"
    count: "0"
    theme_text_color: "Custom"
    text_color: hex("#e5e7eb")
    bg_color: hex("#1c1c1c")
    IconLeftWidget:
        icon: root.icon
        theme_text_color: "Custom"
        text_color: hex("#64dd17")
    MDLabel:
        text: root.count
        halign: "right"
        theme_text_color: "Custom"
        text_color: hex("#9ca3af")
        font_style: "Caption"
        padding_x: "16dp"

MDScreen:
    md_bg_color: hex("#181818")

    MDNavigationLayout:
        ScreenManager:
            id: screen_manager

            # ==================== SCREEN 1: PLAYLISTS & BROWSER ====================
            MDScreen:
                name: "playlists"
                
                MDBoxLayout:
                    orientation: "vertical"

                    MDTopAppBar:
                        id: main_top_bar
                        title: app.view_title
                        md_bg_color: hex("#202020")
                        specific_text_color: hex("#ffffff")
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")], ["playlist-play", lambda x: app.toggle_playlists_view()]]
                        right_action_items: [["plus-box-multiple", lambda x: app.show_create_playlist_dialog()], ["magnify", lambda x: app.scan_music_folder()], ["dots-vertical", lambda x: app.open_menu(x)]]
                        elevation: 2

                    RecycleView:
                        id: playlist_rv
                        viewclass: "TrackRow"
                        key_viewclass: "viewclass"
                        RecycleBoxLayout:
                            default_size: None, dp(64)
                            default_size_hint: 1, None
                            size_hint_y: None
                            height: self.minimum_height
                            orientation: "vertical"

                    MDLabel:
                        id: startup_info
                        text: app.startup_info
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: hex("#ffb300")
                        size_hint_y: None
                        height: "16dp" if app.startup_info else "0dp"
                        halign: "center"

                    # Bottom Mini-Player Bar
                    MDCard:
                        size_hint_y: None
                        height: "62dp"
                        md_bg_color: hex("#262626")
                        radius: [0]
                        on_release: screen_manager.current = "now_playing"
                        padding: "8dp"
                        spacing: "12dp"

                        MDIconButton:
                            icon: "album"
                            theme_text_color: "Custom"
                            text_color: hex("#9ca3af")
                            pos_hint: {"center_y": .5}
                            on_release: screen_manager.current = "now_playing"

                        MDBoxLayout:
                            orientation: "vertical"
                            pos_hint: {"center_y": .5}
                            MDLabel:
                                text: app.current_title
                                theme_text_color: "Custom"
                                text_color: hex("#ffffff")
                                bold: True
                                shorten: True
                            MDLabel:
                                text: app.current_artist
                                theme_text_color: "Custom"
                                text_color: hex("#9ca3af")
                                font_style: "Caption"

                        MDIconButton:
                            icon: "pause" if app.is_playing else "play"
                            theme_text_color: "Custom"
                            text_color: hex("#64dd17")
                            icon_size: "36sp"
                            pos_hint: {"center_y": .5}
                            on_release: app.play_pause()

                MDFloatingActionButton:
                    icon: "plus"
                    md_bg_color: hex("#64dd17")
                    text_color: hex("#ffffff")
                    pos_hint: {"right": 0.94, "y": 0.13}
                    on_release: app.on_fab_pressed()

            # ==================== SCREEN 2: NOW PLAYING ====================
            MDScreen:
                name: "now_playing"
                md_bg_color: hex("#242424")

                MDBoxLayout:
                    orientation: "vertical"

                    MDTopAppBar:
                        title: "Now playing"
                        md_bg_color: hex("#1c1c1c")
                        specific_text_color: hex("#ffffff")
                        left_action_items: [["arrow-left", lambda x: app.switch_screen("playlists")], ["playlist-play", lambda x: app.open_playlists_from_player()]]
                        right_action_items: [["playlist-plus", lambda x: app.add_current_track_to_playlist_menu(x)], ["dots-vertical", lambda x: app.open_menu(x)]]
                        elevation: 2

                    # Giant Metallic CD Artwork Area
                    AnchorLayout:
                        size_hint_y: 0.52
                        MDIcon:
                            icon: "disc"
                            font_size: "240sp"
                            halign: "center"
                            theme_text_color: "Custom"
                            text_color: hex("#7c7c7c")

                    # Track Info Row
                    MDBoxLayout:
                        size_hint_y: None
                        height: "68dp"
                        md_bg_color: hex("#202020")
                        padding: ["12dp", "6dp"]

                        MDIconButton:
                            icon: "playlist-music"
                            theme_text_color: "Custom"
                            text_color: hex("#d1d5db")
                            pos_hint: {"center_y": .5}
                            on_release: app.switch_screen("playlists")

                        MDBoxLayout:
                            orientation: "vertical"
                            pos_hint: {"center_y": .5}
                            MDLabel:
                                text: f"[{app.track_counter}]  {app.current_title}"
                                halign: "center"
                                theme_text_color: "Custom"
                                text_color: hex("#ffffff")
                                font_style: "H6"
                                shorten: True
                            MDLabel:
                                text: app.current_artist
                                halign: "center"
                                theme_text_color: "Custom"
                                text_color: hex("#9ca3af")
                                font_style: "Subtitle2"

                        MDIconButton:
                            icon: "dots-vertical-circle-outline"
                            theme_text_color: "Custom"
                            text_color: hex("#d1d5db")
                            pos_hint: {"center_y": .5}
                            on_release: app.add_current_track_to_playlist_menu(self)

                    # Playback Controls Row (With -10s / +10s seek buttons + Prev/Next)
                    # Every button shares the row width proportionally so all
                    # seven controls stay on screen on narrow phones.
                    MDBoxLayout:
                        size_hint_y: None
                        height: "92dp"
                        padding: ["4dp", "6dp"]
                        spacing: "2dp"

                        MDIconButton:
                            icon: "shuffle-variant"
                            icon_size: "24sp"
                            size_hint_x: 1
                            theme_text_color: "Custom"
                            text_color: hex("#64dd17") if app.shuffle else hex("#6b7280")
                            pos_hint: {"center_y": .5}
                            on_release: app.toggle_shuffle()

                        MDIconButton:
                            icon: "skip-previous"
                            icon_size: "30sp"
                            size_hint_x: 1
                            theme_text_color: "Custom"
                            text_color: hex("#e5e7eb")
                            pos_hint: {"center_y": .5}
                            on_release: app.prev_track()

                        MDIconButton:
                            icon: "rewind-10"
                            icon_size: "26sp"
                            size_hint_x: 1
                            theme_text_color: "Custom"
                            text_color: hex("#9ca3af")
                            pos_hint: {"center_y": .5}
                            on_release: app.skip_seconds(-10)

                        MDIconButton:
                            icon: "pause-circle" if app.is_playing else "play-circle"
                            icon_size: "52sp"
                            size_hint_x: 1.5
                            theme_text_color: "Custom"
                            text_color: hex("#64dd17")
                            pos_hint: {"center_y": .5}
                            on_release: app.play_pause()

                        MDIconButton:
                            icon: "fast-forward-10"
                            icon_size: "26sp"
                            size_hint_x: 1
                            theme_text_color: "Custom"
                            text_color: hex("#9ca3af")
                            pos_hint: {"center_y": .5}
                            on_release: app.skip_seconds(10)

                        MDIconButton:
                            icon: "skip-next"
                            icon_size: "30sp"
                            size_hint_x: 1
                            theme_text_color: "Custom"
                            text_color: hex("#e5e7eb")
                            pos_hint: {"center_y": .5}
                            on_release: app.next_track()

                        MDIconButton:
                            icon: "repeat"
                            icon_size: "24sp"
                            size_hint_x: 1
                            theme_text_color: "Custom"
                            text_color: hex("#64dd17") if app.repeat else hex("#6b7280")
                            pos_hint: {"center_y": .5}
                            on_release: app.toggle_repeat()

                    # Interactive Seek Slider Row
                    MDBoxLayout:
                        size_hint_y: None
                        height: "44dp"
                        padding: ["16dp", "0dp"]
                        spacing: "8dp"

                        MDLabel:
                            text: app.cur_time_str
                            size_hint_x: None
                            width: "46dp"
                            theme_text_color: "Custom"
                            text_color: hex("#64dd17")
                            font_style: "Caption"

                        MDSlider:
                            id: seek_slider
                            min: 0
                            max: max(app.track_length, 1)
                            value: 0
                            hint: False
                            color: hex("#64dd17")
                            thumb_color_active: hex("#64dd17")
                            thumb_color_inactive: hex("#64dd17")
                            on_touch_down: app.on_slider_touch_down(self, args[1])
                            on_value: app.on_slider_value(self, self.value)
                            on_touch_up: app.on_slider_touch_up(self, args[1])

                        MDLabel:
                            text: app.total_time_str
                            size_hint_x: None
                            width: "46dp"
                            halign: "right"
                            theme_text_color: "Custom"
                            text_color: hex("#9ca3af")
                            font_style: "Caption"

                    # Technical Footer
                    MDLabel:
                        text: "mpeg 44.1kHz 320kBps stereo  •  SHIMUL Edition"
                        halign: "center"
                        size_hint_y: None
                        height: "32dp"
                        theme_text_color: "Custom"
                        text_color: hex("#6b7280")
                        font_style: "Caption"

        # ==================== SIDEBAR NAVIGATION DRAWER ====================
        MDNavigationDrawer:
            id: nav_drawer
            md_bg_color: hex("#1c1c1c")

            MDBoxLayout:
                orientation: "vertical"
                padding: "8dp"
                spacing: "4dp"

                MDLabel:
                    text: "PlayerPro"
                    font_style: "H5"
                    bold: True
                    size_hint_y: None
                    height: "48dp"
                    padding_x: "12dp"
                    theme_text_color: "Custom"
                    text_color: hex("#64dd17")

                ScrollView:
                    MDList:
                        MDLabel:
                            text: "FAVORITES"
                            font_style: "Caption"
                            theme_text_color: "Custom"
                            text_color: hex("#64dd17")
                            padding: ["16dp", "12dp"]
                            size_hint_y: None
                            height: "32dp"

                        DrawerItem:
                            text: "Recently added"
                            icon: "album"
                            count: str(len(app.playlist))
                            on_release:
                                nav_drawer.set_state("close")
                                app.open_playlist_by_name("Recently added")
                        DrawerItem:
                            text: "Top rated"
                            icon: "star-circle"
                            count: "0"
                            on_release:
                                nav_drawer.set_state("close")
                                app.open_playlist_by_name("Top rated")
                        DrawerItem:
                            text: "Most played"
                            icon: "fire"
                            count: "0"
                            on_release:
                                nav_drawer.set_state("close")
                                app.open_playlist_by_name("Most played")

                        MDLabel:
                            text: "BROWSERS"
                            font_style: "Caption"
                            theme_text_color: "Custom"
                            text_color: hex("#64dd17")
                            padding: ["16dp", "12dp"]
                            size_hint_y: None
                            height: "32dp"

                        DrawerItem:
                            text: "Playlists"
                            icon: "playlist-play"
                            count: str(app.playlists_count)
                            on_release:
                                nav_drawer.set_state("close")
                                app.show_playlists_overview()
                        DrawerItem:
                            text: "Songs (All Tracks)"
                            icon: "music-note"
                            count: str(len(app.playlist))
                            on_release:
                                nav_drawer.set_state("close")
                                app.open_playlist_by_name("Recently added")
                        DrawerItem:
                            text: "Folders (Add Music)"
                            icon: "folder-music"
                            count: "+"
                            on_release:
                                nav_drawer.set_state("close")
                                app.open_file_manager()
'''


class OptionSheet(ModalView):
    """Bottom-sheet menu.

    Used instead of MDDropdownMenu: in KivyMD 1.2 the dropdown measures its
    growth before it knows its own width/height, so menus opened near the
    right edge (or with several items) end up partly off-screen. A sheet
    anchored to the bottom always fits.
    """

    def __init__(self, items, **kwargs):
        super().__init__(**kwargs)
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.card import MDCard

        self.size_hint = (1, 1)
        self.anchor_y = "bottom"
        self.background_color = (0, 0, 0, 0.5)
        self.auto_dismiss = True
        self._dismissed = False

        item_h = dp(52)
        sheet_h = min(item_h * len(items) + dp(16), Window.height * 0.7)

        card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=sheet_h,
            radius=[dp(18), dp(18), 0, 0],
            md_bg_color=get_color_from_hex("#2a2a2a"),
            padding=[0, dp(8), 0, dp(8)],
            elevation=12,
        )

        box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=item_h * len(items),
        )
        for data in items:
            item = OneLineListItem(
                text=str(data.get("text", "")),
                size_hint_y=None,
                height=item_h,
            )
            item.bind(on_release=self._make_handler(data.get("on_release")))
            box.add_widget(item)

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        scroll.add_widget(box)
        card.add_widget(scroll)
        self.add_widget(card)

    def _make_handler(self, callback):
        def handler(*args):
            self.dismiss()
            if callback:
                Clock.schedule_once(lambda dt: callback(), 0)
        return handler

    def dismiss(self, *args, **kwargs):
        if self._dismissed:
            return
        self._dismissed = True
        super().dismiss(*args, **kwargs)


class TrackRow(TwoLineAvatarIconListItem):
    """One song row, used inside the virtualized RecycleView list.

    Only the rows that are visible on screen exist, so a playlist with
    hundreds (or thousands) of songs opens instantly.
    """

    track_path = StringProperty("")
    track_index = NumericProperty(-1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(IconLeftWidget(icon="music-note"))
        self.add_widget(IconRightWidget(icon="dots-vertical", on_release=self._open_menu))
        self.bind(on_release=self._play)

    def _play(self, *args):
        app = MDApp.get_running_app()
        if app:
            app.on_track_selected(self.track_index)

    def _open_menu(self, *args):
        app = MDApp.get_running_app()
        if app:
            widget = args[0] if args else self
            app.open_track_item_menu(widget, self.track_path, self.track_index)


class PlaylistRow(TwoLineAvatarIconListItem):
    """One playlist folder row in the overview."""

    playlist_name = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(IconLeftWidget(icon="playlist-play"))
        self.add_widget(IconRightWidget(icon="dots-vertical", on_release=self._open_menu))
        self.bind(on_release=self._open)

    def _open(self, *args):
        app = MDApp.get_running_app()
        if app:
            app.open_playlist_by_name(self.playlist_name)

    def _open_menu(self, *args):
        app = MDApp.get_running_app()
        if app:
            widget = args[0] if args else self
            app.open_playlist_folder_menu(widget, self.playlist_name)


class CreatePlaylistRow(TwoLineAvatarIconListItem):
    """The '+ Create New Playlist' row at the top of the overview."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(IconLeftWidget(icon="playlist-plus"))
        self.bind(on_release=lambda *a: MDApp.get_running_app().show_create_playlist_dialog())


Factory.register("TrackRow", cls=TrackRow)
Factory.register("PlaylistRow", cls=PlaylistRow)
Factory.register("CreatePlaylistRow", cls=CreatePlaylistRow)


class ShimulAudioApp(MDApp):
    view_title = StringProperty("Playlists")
    current_title = StringProperty("No track loaded")
    current_artist = StringProperty("Tap + to load audio files")
    cur_time_str = StringProperty("0:00")
    total_time_str = StringProperty("0:00")
    track_counter = StringProperty("0/0")
    track_length = NumericProperty(1.0)
    playlists_count = NumericProperty(4)
    is_playing = BooleanProperty(False)
    shuffle = BooleanProperty(False)
    repeat = BooleanProperty(False)
    startup_info = StringProperty("")

    def build(self):
        _t0 = time.time()
        self.title = "Shimul Audio"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "LightGreen"

        # Persistent Playlists Dictionary: { "Playlist Name": [list_of_file_paths] }
        self.playlists_db = {
            "Recently added": [],
            "Top rated": [],
            "Most played": [],
            "sura": []
        }
        self.active_playlist_name = "Recently added"
        self.playlist = []          # Currently active track list for playback
        self.showing_overview = False  # True = showing list of playlists, False = showing tracks

        self.current_index = -1
        self.sound = None
        self.android_player = None
        self.paused = False
        self.dialog = None
        self.track_menu = None

        # Seeking & Clock tracking
        self.is_seeking = False
        self.start_time = 0.0
        self.start_offset = 0.0

        # The file manager builds a fairly large widget tree; create it only
        # when the user actually opens it so startup stays quick.
        self.file_manager = None

        self.root_widget = Builder.load_string(KV)
        self._build_seconds = time.time() - _t0
        self.load_saved_playlists()
        Clock.schedule_interval(self.update_progress, 0.2)
        return self.root_widget

    def on_start(self):
        # Draw the saved playlist right away; never rebuild the library on
        # startup. The Music folder is only scanned once, on a fresh install
        # (or when the user taps the search button).
        self.refresh_main_list()
        self._ui_seconds = time.time() - _T_IMPORT_START
        Clock.schedule_once(self._report_startup, 0.1)

        first_run = not getattr(self, "_db_existed", False)
        if platform == "android":
            # Accept audio files sent by other apps ("Open with").
            self.set_up_open_with_intents()
            try:
                from android.permissions import request_permissions, Permission
                request_permissions(
                    [Permission.READ_EXTERNAL_STORAGE, Permission.READ_MEDIA_AUDIO],
                    (lambda perms, grants: self.scan_music_folder()) if first_run else None,
                )
            except Exception:
                if first_run:
                    Clock.schedule_once(lambda dt: self.scan_music_folder(), 1.0)
        elif first_run:
            Clock.schedule_once(lambda dt: self.scan_music_folder(), 0.5)

    def _report_startup(self, dt):
        """Show how long startup took (temporary diagnostic line)."""
        total = time.time() - _T_IMPORT_START
        self.startup_info = (
            f"import {_T_IMPORT_END - _T_IMPORT_START:.1f}s | "
            f"build {getattr(self, '_build_seconds', 0):.1f}s | "
            f"ui {getattr(self, '_ui_seconds', 0):.1f}s | "
            f"list {getattr(self, '_first_list_seconds', 0):.1f}s | "
            f"total {total:.1f}s"
        )
        Clock.schedule_once(lambda dt: setattr(self, "startup_info", ""), 25)

    # ---------- Persistent JSON Storage for Playlists ----------
    def get_db_path(self):
        folder = self.user_data_dir if platform == "android" else os.path.abspath(".")
        return os.path.join(folder, "playlists_data.json")

    def load_saved_playlists(self):
        path = self.get_db_path()
        # A missing database means a fresh install: scan the Music folder
        # once. Afterwards the saved paths are the single source of truth,
        # so the folder is never rescanned automatically.
        self._db_existed = os.path.exists(path)
        if self._db_existed:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Keep the stored paths as-is: checking every file
                        # with os.path.isfile() on startup is slow on
                        # Android's FUSE storage and delayed the UI.
                        for k, v in data.items():
                            if isinstance(v, list):
                                self.playlists_db[k] = list(v)
            except Exception:
                pass
        self.playlist = list(self.playlists_db.get(self.active_playlist_name, []))
        self.playlists_count = len(self.playlists_db)

    def save_playlists(self):
        self.playlists_count = len(self.playlists_db)
        try:
            with open(self.get_db_path(), "w", encoding="utf-8") as f:
                json.dump(self.playlists_db, f, indent=2)
        except Exception:
            pass

    # ---------- Playlist Overview vs Track List Switching ----------
    def toggle_playlists_view(self):
        """Triggered by clicking the top-left Playlist icon next to the menu icon."""
        if self.showing_overview:
            self.open_playlist_by_name(self.active_playlist_name)
        else:
            self.show_playlists_overview()

    def open_playlists_from_player(self):
        self.switch_screen("playlists")
        self.show_playlists_overview()

    def show_playlists_overview(self):
        """Displays all Playlist folders (like Image 2/4 in your screenshots)."""
        self.showing_overview = True
        self.view_title = "Playlists"

        data = [{
            "viewclass": "CreatePlaylistRow",
            "text": "+ Create New Playlist",
            "secondary_text": "Tap to create a custom playlist",
        }]
        for pl_name, tracks in self.playlists_db.items():
            data.append({
                "viewclass": "PlaylistRow",
                "text": pl_name,
                "secondary_text": f"{len(tracks)} songs",
                "playlist_name": pl_name,
            })
        self.root_widget.ids.playlist_rv.data = data

    def open_playlist_by_name(self, name):
        """Opens a specific playlist and shows its tracks."""
        if name not in self.playlists_db:
            self.playlists_db[name] = []
        self.active_playlist_name = name
        self.showing_overview = False
        self.view_title = f"Playlist: {name}"
        self.playlist = list(self.playlists_db[name])
        self.refresh_main_list()

    def refresh_main_list(self):
        if self.showing_overview:
            self.show_playlists_overview()
            return

        self.view_title = f"{self.active_playlist_name} ({len(self.playlist)})"
        playlist_name = self.active_playlist_name

        # Hand the rows to the RecycleView instead of creating one widget per
        # song: it only builds the few rows that are actually visible, so a
        # playlist with 400+ tracks opens immediately.
        self.root_widget.ids.playlist_rv.data = [
            {
                "viewclass": "TrackRow",
                "text": os.path.basename(p),
                "secondary_text": f"Playlist: {playlist_name}  •  Tap 3-dots to add/manage",
                "track_path": p,
                "track_index": idx,
            }
            for idx, p in enumerate(self.playlist)
        ]
        self._first_list_seconds = time.time() - _T_IMPORT_START

    # ---------- Create / Manage Playlists Dialogs & Menus ----------
    def show_create_playlist_dialog(self, track_to_add=None):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton, MDRaisedButton
        from kivymd.uix.textfield import MDTextField

        self.new_pl_input = MDTextField(
            hint_text="Enter playlist name (e.g., Favorites, Workout)",
            mode="rectangle"
        )
        self.dialog = MDDialog(
            title="Create New Playlist",
            type="custom",
            content_cls=self.new_pl_input,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="CREATE",
                    on_release=lambda x: self.confirm_create_playlist(track_to_add)
                ),
            ],
        )
        self.dialog.open()

    def confirm_create_playlist(self, track_to_add=None):
        name = self.new_pl_input.text.strip()
        if self.dialog:
            self.dialog.dismiss()
        if not name:
            toast("Playlist name cannot be empty")
            return
        if name not in self.playlists_db:
            self.playlists_db[name] = []
        if track_to_add and track_to_add not in self.playlists_db[name]:
            self.playlists_db[name].append(track_to_add)
            toast(f"Created '{name}' & added song!")
        else:
            toast(f"Playlist '{name}' created!")
        self.save_playlists()
        self.refresh_main_list()

    # ---------- Dropdown helper ----------
    def open_dropdown(self, caller, items, width_mult=4):
        """Show options in a bottom sheet that always stays on screen."""
        menu = OptionSheet(items)
        menu.open()
        return menu

    def open_playlist_folder_menu(self, caller, pl_name):
        options = [
            ("Play this playlist", lambda: self.play_entire_playlist(pl_name)),
            ("Add files to this playlist", lambda: self.add_files_to_specific_playlist(pl_name)),
            ("Clear all songs", lambda: self.clear_specific_playlist(pl_name)),
        ]
        if pl_name not in ("Recently added", "Top rated", "Most played"):
            options.append(("Delete playlist", lambda: self.delete_playlist(pl_name)))

        menu_items = [
            {
                "text": label,
                "viewclass": "OneLineListItem",
                "on_release": lambda act=action: (self.track_menu.dismiss(), act()),
            } for label, action in options
        ]
        self.track_menu = self.open_dropdown(caller, menu_items)

    def play_entire_playlist(self, pl_name):
        self.open_playlist_by_name(pl_name)
        if self.playlist:
            self.load_track(0, autoplay=True)
            self.switch_screen("now_playing")
        else:
            toast(f"'{pl_name}' is empty. Tap + to add songs!")

    def add_files_to_specific_playlist(self, pl_name):
        self.active_playlist_name = pl_name
        self.showing_overview = False
        self.open_file_manager()

    def clear_specific_playlist(self, pl_name):
        self.playlists_db[pl_name] = []
        if self.active_playlist_name == pl_name:
            self.playlist = []
        self.save_playlists()
        self.refresh_main_list()
        toast(f"Cleared '{pl_name}'")

    def delete_playlist(self, pl_name):
        if pl_name in self.playlists_db:
            del self.playlists_db[pl_name]
        if self.active_playlist_name == pl_name:
            self.active_playlist_name = "Recently added"
            self.playlist = list(self.playlists_db["Recently added"])
        self.save_playlists()
        self.refresh_main_list()
        toast(f"Deleted playlist '{pl_name}'")

    # ---------- Per-Track 3-Dot Menu (Add Song to Playlist / Remove) ----------
    def open_track_item_menu(self, caller, track_path, index):
        menu_items = [
            {
                "text": "+ New Playlist with this song",
                "viewclass": "OneLineListItem",
                "on_release": lambda: (self.track_menu.dismiss(), self.show_create_playlist_dialog(track_path)),
            }
        ]
        for pl_name in self.playlists_db.keys():
            if pl_name != self.active_playlist_name:
                menu_items.append({
                    "text": f"Add to '{pl_name}'",
                    "viewclass": "OneLineListItem",
                    "on_release": lambda name=pl_name: (self.track_menu.dismiss(), self.add_song_to_playlist(track_path, name)),
                })

        menu_items.append({
            "text": f"Remove from '{self.active_playlist_name}'",
            "viewclass": "OneLineListItem",
            "on_release": lambda: (self.track_menu.dismiss(), self.remove_song_from_active(index)),
        })

        self.track_menu = self.open_dropdown(caller, menu_items)

    def add_current_track_to_playlist_menu(self, caller):
        if not (0 <= self.current_index < len(self.playlist)):
            toast("No track currently loaded")
            return
        track_path = self.playlist[self.current_index]
        self.open_track_item_menu(caller, track_path, self.current_index)

    def add_song_to_playlist(self, track_path, pl_name):
        if pl_name not in self.playlists_db:
            self.playlists_db[pl_name] = []
        if track_path not in self.playlists_db[pl_name]:
            self.playlists_db[pl_name].append(track_path)
            self.save_playlists()
            toast(f"Added to '{pl_name}'")
        else:
            toast(f"Already in '{pl_name}'")

    def remove_song_from_active(self, index):
        if 0 <= index < len(self.playlist):
            removed = self.playlist.pop(index)
            if removed in self.playlists_db.get(self.active_playlist_name, []):
                self.playlists_db[self.active_playlist_name].remove(removed)
            self.save_playlists()
            self.refresh_main_list()
            toast("Removed from playlist")

    def on_fab_pressed(self):
        """If viewing playlist folders, '+' creates a playlist; if viewing songs, '+' opens file manager."""
        if self.showing_overview:
            self.show_create_playlist_dialog()
        else:
            self.open_file_manager()

    # ---------- Formatting & Screen Navigation ----------
    def fmt_time(self, sec):
        if sec is None or sec < 0 or sec != sec:
            sec = 0
        sec = int(sec)
        return f"{sec // 60}:{sec % 60:02d}"

    def switch_screen(self, screen_name):
        self.root_widget.ids.screen_manager.current = screen_name

    # ---------- Top-Right 3-Dot Overflow Menu ----------
    def open_menu(self, caller):
        options = [
            "All Playlists Overview",
            "Create New Playlist",
            "Save now playing as playlist",
            "Clear current playlist",
            "Turn party shuffle on",
            "Quit"
        ]
        menu_items = [
            {
                "text": item,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=item: self.handle_menu_click(x),
            } for item in options
        ]
        self.menu = self.open_dropdown(caller, menu_items)

    def handle_menu_click(self, option):
        self.menu.dismiss()
        if option == "All Playlists Overview":
            self.switch_screen("playlists")
            self.show_playlists_overview()
        elif option == "Create New Playlist":
            self.show_create_playlist_dialog()
        elif option == "Save now playing as playlist":
            self.show_create_playlist_dialog()
        elif option == "Clear current playlist":
            self.stop_audio()
            self.clear_specific_playlist(self.active_playlist_name)
            self.current_title = "No track loaded"
            self.track_counter = "0/0"
        elif option == "Turn party shuffle on":
            self.toggle_shuffle()
        elif option == "Quit":
            self.stop()
        else:
            toast(option)

    # ---------- File & Folder Loading ----------
    def open_file_manager(self):
        if self.file_manager is None:
            from kivymd.uix.filemanager import MDFileManager

            self.file_manager = MDFileManager(
                exit_manager=self.close_file_manager,
                select_path=self.select_path,
                ext=[".mp3", ".wav", ".ogg", ".flac"]
            )
        start_dir = "/storage/emulated/0" if platform == "android" else os.path.expanduser("~")
        self.file_manager.show(start_dir)

    def close_file_manager(self, *args):
        if self.file_manager:
            self.file_manager.close()

    def select_path(self, path):
        self.close_file_manager()
        if os.path.isdir(path):
            files = [
                os.path.join(path, f) for f in sorted(os.listdir(path))
                if f.lower().endswith((".mp3", ".wav", ".ogg", ".flac"))
            ]
            self.add_to_playlist(files)
        elif os.path.isfile(path):
            self.add_to_playlist([path])

    # ---------- "Open with" support: play a file sent by another app ----------
    def _android_activity(self):
        from jnius import autoclass
        return autoclass("org.kivy.android.PythonActivity").mActivity

    def set_up_open_with_intents(self):
        """Listen for audio files other apps ask us to open."""
        try:
            from android import activity
            activity.bind(on_new_intent=self._on_new_intent)
        except Exception:
            pass
        # The intent that started the app (cold start) is read after the
        # first screen exists.
        Clock.schedule_once(self._check_launch_intent, 0.8)

    def _on_new_intent(self, intent):
        # This runs on Java's UI thread, so hand the work to the Kivy loop.
        Clock.schedule_once(lambda dt: self._handle_open_intent(intent), 0)

    def _check_launch_intent(self, dt):
        try:
            intent = self._android_activity().getIntent()
        except Exception:
            return
        self._handle_open_intent(intent)

    def _handle_open_intent(self, intent):
        """Play an audio file another app handed to us (ACTION_VIEW / SEND)."""
        if intent is None:
            return
        try:
            action = intent.getAction()
            uri = intent.getData()
            if uri is None and action == "android.intent.action.SEND":
                from jnius import cast
                uri = cast("android.net.Uri",
                           intent.getParcelableExtra("android.intent.extra.STREAM"))
        except Exception:
            return
        if uri is None:
            return
        try:
            path = self._uri_to_path(uri)
        except Exception:
            path = None
        if not path or not os.path.isfile(path):
            toast("Sorry, this file could not be opened")
            return
        self.play_external_file(path)

    def _uri_to_path(self, uri):
        """Turn a file:// or content:// URI into a path we can play."""
        try:
            scheme = uri.getScheme()
        except Exception:
            return None

        if scheme in (None, "file"):
            path = uri.getPath()
            if path and os.path.isfile(path):
                return path
            return None

        if scheme != "content":
            return None

        # Video/audio providers from the media store still expose the real
        # path through the "_data" column.
        try:
            resolver = self._android_activity().getContentResolver()
            cursor = resolver.query(uri, None, None, None, None)
            if cursor is not None:
                try:
                    if cursor.moveToFirst():
                        idx = cursor.getColumnIndex("_data")
                        if idx >= 0:
                            real = cursor.getString(idx)
                            if real and os.path.isfile(real):
                                return real
                finally:
                    cursor.close()
        except Exception:
            pass

        # Otherwise copy the file into our own storage once.
        return self._copy_uri_to_storage(uri)

    def _copy_uri_to_storage(self, uri):
        src_fd = -1
        try:
            resolver = self._android_activity().getContentResolver()
            pfd = resolver.openFileDescriptor(uri, "r")
            if pfd is None:
                return None
            src_fd = pfd.detachFd()
            name = self._uri_display_name(uri) or "opened_track"
            safe = "".join(c for c in name if c.isalnum() or c in "._- ").strip()
            dest = os.path.join(self.user_data_dir, "opened_" + (safe or "track.mp3"))
            with open(dest, "wb") as out:
                while True:
                    chunk = os.read(src_fd, 262144)
                    if not chunk:
                        break
                    out.write(chunk)
            return dest
        except Exception:
            return None
        finally:
            if src_fd >= 0:
                try:
                    os.close(src_fd)
                except Exception:
                    pass

    def _uri_display_name(self, uri):
        try:
            resolver = self._android_activity().getContentResolver()
            cursor = resolver.query(uri, None, None, None, None)
            if cursor is not None:
                try:
                    if cursor.moveToFirst():
                        idx = cursor.getColumnIndex("_display_name")
                        if idx >= 0:
                            return cursor.getString(idx) or ""
                finally:
                    cursor.close()
        except Exception:
            pass
        try:
            return os.path.basename(uri.getLastPathSegment() or "")
        except Exception:
            return ""

    def play_external_file(self, path):
        """Play a file that was opened from another app and remember it."""
        pl_name = "Recently added"
        pl = self.playlists_db.setdefault(pl_name, [])
        if path not in pl:
            pl.insert(0, path)
            self.save_playlists()

        self.active_playlist_name = pl_name
        self.showing_overview = False
        self.playlist = list(pl)
        self.refresh_main_list()

        try:
            index = self.playlist.index(path)
        except ValueError:
            index = 0
        self.switch_screen("now_playing")
        self.load_track(index, autoplay=True)

    def scan_music_folder(self):
        """Look for audio files in the Music folder on a worker thread.

        Walking the folder over Android's FUSE layer can take a long time,
        so the UI list is built from the saved data first and the scan result
        is applied when it finishes.
        """
        target_pl = self.active_playlist_name

        def worker():
            music_dir = "/storage/emulated/0/Music" if platform == "android" else os.path.expanduser("~/Music")
            found = []
            if os.path.exists(music_dir):
                for root_dir, dirs, files in os.walk(music_dir):
                    # Skip hidden/system folders.
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                    for f in sorted(files):
                        if f.lower().endswith((".mp3", ".wav", ".ogg", ".flac")):
                            found.append(os.path.join(root_dir, f))
            Clock.schedule_once(lambda dt: self._apply_scan(found, target_pl), 0)

        threading.Thread(target=worker, daemon=True).start()

    def _apply_scan(self, found, target_pl):
        """Merge a finished scan into the playlists (runs on the UI thread)."""
        if not found:
            return

        if target_pl not in self.playlists_db:
            self.playlists_db[target_pl] = []
        recent = self.playlists_db.setdefault("Recently added", [])

        added = 0
        for p in found:
            if p not in self.playlists_db[target_pl]:
                self.playlists_db[target_pl].append(p)
                added += 1
            if p not in recent:
                recent.append(p)

        if added == 0:
            return

        self.save_playlists()
        if target_pl == self.active_playlist_name and not self.showing_overview:
            self.playlist = list(self.playlists_db[target_pl])
            self.refresh_main_list()
        toast(f"Added {added} song(s) from Music")

    def add_to_playlist(self, paths):
        was_empty = len(self.playlist) == 0
        target_pl = self.active_playlist_name

        if target_pl not in self.playlists_db:
            self.playlists_db[target_pl] = []

        added_count = 0
        for p in paths:
            if os.path.isfile(p):
                if p not in self.playlists_db[target_pl]:
                    self.playlists_db[target_pl].append(p)
                    added_count += 1
                # Also keep "Recently added" synced with all imported songs
                if p not in self.playlists_db["Recently added"]:
                    self.playlists_db["Recently added"].append(p)

        self.playlist = list(self.playlists_db[target_pl])
        self.save_playlists()
        self.showing_overview = False
        self.refresh_main_list()

        if added_count > 0:
            toast(f"Added {added_count} song(s) to '{target_pl}'")

        if was_empty and self.playlist:
            self.load_track(0, autoplay=False)

    def on_track_selected(self, index):
        self.load_track(index, autoplay=True)
        self.switch_screen("now_playing")

    # ---------- Crash-Free Cross-Platform Audio Logic ----------
    def get_pygame_duration(self, path):
        try:
            return float(pygame.mixer.Sound(path).get_length())
        except Exception:
            return 240.0

    def load_track(self, index, autoplay=True, direction=1):
        if not self.playlist:
            return
        total = len(self.playlist)
        index = index % total

        # The playlist only stores file paths, so the file may have been
        # deleted or moved since it was added. Tell the user once and move on
        # to the next (or previous) song instead of failing silently.
        skipped = 0
        while not os.path.isfile(self.playlist[index]):
            skipped += 1
            if skipped >= total:
                toast("No playable files in this playlist")
                self.is_playing = False
                self.paused = True
                self.current_title = "No track loaded"
                self.current_artist = "All files are missing"
                return
            if skipped == 1:
                toast(f"File not found, skipping: {os.path.basename(self.playlist[index])}")
            index = (index + direction) % total

        self.current_index = index
        path = self.playlist[index]

        self.is_playing = False
        self.paused = False
        self.start_offset = 0.0
        self.start_time = time.time()

        if USE_ANDROID_PLAYER:
            try:
                if self.android_player:
                    self.android_player.reset()
                else:
                    self.android_player = MediaPlayer()
                self.android_player.setDataSource(path)
                self.android_player.prepare()
                dur_ms = self.android_player.getDuration()
                self.track_length = max(dur_ms / 1000.0, 1.0)
                if autoplay:
                    self.android_player.start()
                    self.is_playing = True
            except Exception as e:
                toast(f"Audio error: {e}")
                return

        elif USE_PYGAME:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(path)
                self.track_length = max(self.get_pygame_duration(path), 1.0)
                if autoplay:
                    pygame.mixer.music.play(start=0.0)
                    self.start_time = time.time()
                    self.is_playing = True
            except Exception as e:
                toast(f"Cannot load file: {e}")
                return

        else:
            if self.sound:
                self.sound.stop()
            self.sound = SoundLoader.load(path)
            if not self.sound:
                toast("Unable to load audio")
                return
            self.track_length = max(self.sound.length or 180.0, 1.0)
            if autoplay:
                self.sound.play()
                self.start_time = time.time()
                self.is_playing = True

        # Automatically log played songs into "Most played"
        if autoplay and path not in self.playlists_db.get("Most played", []):
            self.playlists_db.setdefault("Most played", []).append(path)
            self.save_playlists()

        self.current_title = os.path.basename(path)
        self.current_artist = f"Playlist: {self.active_playlist_name}"
        self.track_counter = f"{index + 1}/{len(self.playlist)}"
        self.total_time_str = self.fmt_time(self.track_length)
        self.cur_time_str = "0:00"
        self.root_widget.ids.seek_slider.max = self.track_length
        self.root_widget.ids.seek_slider.value = 0.0

    def get_current_pos(self):
        if USE_ANDROID_PLAYER and self.android_player:
            try:
                return self.android_player.getCurrentPosition() / 1000.0
            except Exception:
                return 0.0
        if self.is_playing and not self.paused:
            return min(self.start_offset + (time.time() - self.start_time), self.track_length)
        return self.start_offset

    def play_pause(self):
        if self.current_index < 0:
            if self.playlist:
                self.load_track(0, autoplay=True)
            else:
                toast("Tap + to add audio files first")
            return

        if USE_ANDROID_PLAYER and self.android_player:
            if self.is_playing:
                self.android_player.pause()
                self.is_playing = False
                self.paused = True
            else:
                self.android_player.start()
                self.is_playing = True
                self.paused = False

        elif USE_PYGAME:
            if self.is_playing and not self.paused:
                self.start_offset = self.get_current_pos()
                pygame.mixer.music.pause()
                self.paused = True
                self.is_playing = False
            elif self.paused:
                pygame.mixer.music.unpause()
                self.start_time = time.time()
                self.paused = False
                self.is_playing = True
            else:
                pygame.mixer.music.play(start=self.start_offset)
                self.start_time = time.time()
                self.paused = False
                self.is_playing = True

        elif self.sound:
            if self.is_playing:
                self.start_offset = self.get_current_pos()
                self.sound.stop()
                self.is_playing = False
            else:
                self.sound.play()
                self.start_time = time.time()
                self.is_playing = True

    def stop_audio(self):
        if USE_ANDROID_PLAYER and self.android_player:
            try:
                self.android_player.stop()
            except Exception:
                pass
        elif USE_PYGAME:
            pygame.mixer.music.stop()
        elif self.sound:
            self.sound.stop()

        self.is_playing = False
        self.paused = False
        self.start_offset = 0.0
        self.cur_time_str = "0:00"
        self.root_widget.ids.seek_slider.value = 0.0

    def prev_track(self):
        if not self.playlist:
            return
        new_idx = (self.current_index - 1) % len(self.playlist)
        self.load_track(new_idx, autoplay=True, direction=-1)

    def next_track(self):
        if not self.playlist:
            return
        if self.shuffle:
            new_idx = random.randint(0, len(self.playlist) - 1)
        else:
            new_idx = (self.current_index + 1) % len(self.playlist)
        self.load_track(new_idx, autoplay=True)

    # ---------- Slider Drag & +/-10s Seek ----------
    def on_slider_touch_down(self, slider, touch):
        if slider.collide_point(*touch.pos):
            self.is_seeking = True

    def on_slider_value(self, slider, value):
        # Driven by the slider's own value updates, so the time label stays
        # in sync while dragging instead of lagging one touch-move behind.
        if self.is_seeking:
            self.cur_time_str = self.fmt_time(value)

    def on_slider_touch_up(self, slider, touch):
        if self.is_seeking:
            self.is_seeking = False
            self.seek_audio(slider.value)

    def skip_seconds(self, delta):
        if self.current_index < 0:
            return
        target = max(0.0, min(self.get_current_pos() + delta, self.track_length))
        self.seek_audio(target)

    def seek_audio(self, value):
        if self.current_index < 0:
            return
        value = max(0.0, min(float(value), self.track_length))
        self.start_offset = value
        self.start_time = time.time()
        self.cur_time_str = self.fmt_time(value)
        self.root_widget.ids.seek_slider.value = value

        if USE_ANDROID_PLAYER and self.android_player:
            try:
                self.android_player.seekTo(int(value * 1000))
            except Exception:
                pass
        elif USE_PYGAME:
            was_playing = self.is_playing and not self.paused
            pygame.mixer.music.stop()
            try:
                pygame.mixer.music.play(start=value)
            except Exception:
                pygame.mixer.music.play()
            if not was_playing:
                pygame.mixer.music.pause()
                self.is_playing = False
                self.paused = True
            else:
                self.is_playing = True
                self.paused = False
        elif self.sound:
            self.sound.seek(value)

    def update_progress(self, dt):
        if self.is_playing and not self.is_seeking:
            pos = self.get_current_pos()
            self.root_widget.ids.seek_slider.value = pos
            self.cur_time_str = self.fmt_time(pos)

            if self.track_length > 1.0 and pos >= self.track_length - 0.25:
                if self.repeat:
                    self.load_track(self.current_index, autoplay=True)
                else:
                    self.next_track()

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        toast(f"Shuffle {'ON' if self.shuffle else 'OFF'}")

    def toggle_repeat(self):
        self.repeat = not self.repeat
        toast(f"Repeat {'ON' if self.repeat else 'OFF'}")

    def msg(self, text):
        toast(text)


if __name__ == "__main__":
    ShimulAudioApp().run()

#!/usr/bin/env python

import gi
gi.require_version('Gtk', '3.0')

import os
import json
import threading
import notify2
import webbrowser

from datetime import datetime

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GObject
from gi.repository import Pango

from gi.repository.GdkPixbuf import Pixbuf

from twisted.internet import gtk3reactor
gtk3reactor.install()

from twisted.words.protocols import irc
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.internet import ssl

from ui import *
from irc import *

class Parser():

    def __init__(self):
        pass

    def parse(self, data, buf, tags):
        words = data.split()
        for word in words:
            if word.startswith("http://") or word.startswith("https://"):
                tag = buf.create_tag(None, 
                                    foreground="#4a85cb", 
                                    underline=Pango.Underline.SINGLE)
                tag.connect("event", self.open, word)
                buf.insert_with_tags(buf.get_end_iter(),
                                    word,
                                    tag)
            else:
                buf.insert(buf.get_end_iter(), word)
            buf.insert(buf.get_end_iter(), " ")

    def open(self, tag, obj, event, it, url):
        # parser opens the url, not sure if this
        # is the right to place this.
        if event.type != Gdk.EventType.BUTTON_PRESS:
            return
        webbrowser.open(url)



class Interface(Gtk.Window):

    channel = None
    channel_buffers = {}
    channel_tabs = {}
    last_user = {}
    tags = {}

    def __init__(self, title):
        
        # Setup the window
        Gtk.Window.__init__(self, title="Chatt")
        icontheme = Gtk.IconTheme.get_default()
        self.set_icon(icontheme.load_icon("applications-internet", 128, 0))

        self.set_default_size(800, 600)
        self.init_window(title)
        self.parser = Parser()

    def init_window(self, title):

        # Create basic layout
        layout = Gtk.Paned()
        layout.set_position(220)

        # Create chat window and sidebar
        self.chat = ChatWindow("", "")
        self.sidebar = Sidebar()
        self.sidebar.content.connect("row-selected", self.update_channel)

        # Split chatwindow and leave room for entrybox
        chatwindow = Gtk.VBox()
        self.entry = Gtk.Entry()
        chatwindow.pack_start(self.chat.view, True, True, 0)
        chatwindow.pack_start(self.entry, False, False, 0)

        # Finish layout
        layout.add1(self.sidebar.view)
        layout.add2(chatwindow)

        notify2.init(title)

        # Connect to window
        #self.set_titlebar(self.titlebar)
        self.add(layout)

    def _on_link_tag_event(self, tag, buf, event, itr):
        if event.type != Gdk.EventType.BUTTON_RELEASE: return
        text_buffer = self.get_buffer()
        if text_buffer.get_selection_bounds(): return
        nfoview.util.show_uri(tag.get_data("url"))

    def on_key_press_entry(self, widget, ev, client):
        if ev.keyval == Gdk.KEY_Escape:
            widget.set_text("")

    def on_key_press_window(self, widget, ev, data=None):
        if ev.keyval == Gdk.KEY_Tab:
            print "TAB"
            return True

    def update_channel(self, _, row):

        # Update current channel
        self.channel = row.channel
        self.chat.set_buffer(self.channel_buffers.get(self.channel))
        self.set_symbol(self.channel_tabs.get(self.channel), self.channel, "_greyed")

    def add_channel(self, channel):

        # Create buffer and text tags
        buf = Gtk.TextBuffer()
        self.channel_buffers[channel] = buf
        self.tags[channel] = {}
        tags = {}
        tags["bold"] = buf.create_tag(None, weight=Pango.Weight.BOLD)
        self.tags[channel] = tags

        # Update content
        c = Channel()
        c.set_content(channel, channel, channel)
        self.channel_tabs[channel] = c
        self.sidebar.add(c)

        # If no channel is current, set this to be.
        if self.channel == None:
            self.channel = channel
            self.sidebar.content.select_row(c)

        self.set_symbol(c, channel, "_greyed")

    def leave_channel(self, channel):
        
        # Clean up UI
        if self.channel == channel:
            if len(self.channel_tabs) > 0:
                new = self.channel_tabs.keys()[0]
                self.sidebar.content.select_row(self.channel_tabs.get(new))
            else:
                self.channel = None

        # Clear sidebar and buffer entries
        current_tab = self.channel_tabs.get(channel)
        self.sidebar.content.remove(current_tab)
        del self.channel_buffers[channel]

    def set_symbol(self, row, channel, suffix):
        if channel.startswith("#"):
            row.set_symbol("irc{}".format(suffix))
        else:
            row.set_symbol("user{}".format(suffix))

    def get_channel(self):
        return self.channel

    def set_highlights(self, highlights):
        self.highlights = highlights

    def notify(self, user, text, channel=None):
        if channel:
            n = notify2.Notification("{} i {}".format(user, channel),
                                     text, "applications-internet")
        else:
            n = notify2.Notification(user,
                                     text, "applications-internet")
        n.show()

    def update_chat(self, user, channel, text):

        # Check if channel is there
        if channel not in self.channel_buffers:
            self.add_channel(channel)

        tags = self.tags.get(channel)

        # Get users
        buf = self.channel_buffers.get(channel)
        if self.last_user.get(channel) != user:
            buf.insert_with_tags(buf.get_end_iter(), 
                                 "{}\n".format(user), 
                                 tags.get("bold"))
        self.parser.parse(text, buf, tags)
        buf.insert(buf.get_end_iter(), "\n")

        self.last_user[channel] = user
        self.channel_tabs.get(channel).set_content(channel, channel, text[:20])

        if self.channel == channel:
            self.set_symbol(self.channel_tabs.get(channel), channel, "_greyed")
        else:
            self.set_symbol(self.channel_tabs.get(channel), channel, "")
            for highlight in self.highlights:
                if highlight in text:
                    self.notify(user, text, channel=channel)
            if not channel.startswith("#"):
                self.notify(user, text)

if __name__ == "__main__":

    with open("settings.json", "r") as f:
        settings = json.loads(f.read())
    
    hostname, port = settings.get("server").split(":")
    description = settings.get("description")
    credentials = settings.get("credentials")
    nickname = str(credentials.get("nickname").strip())
    try:
        password = str(credentials.get("password").strip())
    except:
        pass
    
    def a():
        Gtk.main()

    def sendmessage(entry, channel):
        msg = entry.get_text()
        if msg.startswith("/p"):
            f.client.leave(channel())
            pass
            # leave channel
        elif msg.startswith("/j "):
            f.client.join(msg.split()[1])
            # join channel
        else:
            f.client.msg(channel(), msg)
            win.update_chat(f.client.nickname, channel(), str(msg))
        entry.set_text("")

    def stop(*args):
        Gtk.main_quit()
        reactor.stop()
        os._exit(0)

    # Init window
    win = Interface(description)
    GObject.threads_init()
    win.show_all()
    Gdk.threads_init()

    # Connect textentry to sendmessage function
    win.entry.connect("activate", sendmessage, win.get_channel)
    win.entry.connect("key-press-event", win.on_key_press_entry, f)  

    # Add client with callback
    f = ClientFactory([], nickname, password, win)
    reactor.connectSSL(hostname, int(port), f, ssl.ClientContextFactory())

    # Add highlights
    win.set_highlights([nickname])

    #win.connect("delete-event", stop)
    win.connect("destroy", stop)

    threading.Thread(target=Gtk.main)
    Gdk.threads_leave()

    reactor.run()
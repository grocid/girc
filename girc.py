#!/usr/bin/env python

import gi
gi.require_version('Gtk', '3.0')

import os
import json
import threading
import notify2

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio, GObject, Pango
from gi.repository.GdkPixbuf import Pixbuf

from twisted.internet import gtk3reactor
gtk3reactor.install()

from twisted.words.protocols import irc
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.internet import ssl

from ui import *
from irc import *


class Interface(Gtk.Window):

    channel = ""
    channel_buffers = {}
    channel_tabs = {}
    last_user = {}
    user_tag = {}

    def __init__(self, title):
        Gtk.Window.__init__(self, title="Chatt")
        icontheme = Gtk.IconTheme.get_default()
        self.set_icon(icontheme.load_icon("applications-internet", 64, 0))
        self.set_default_size(800, 600)
        self.init_window(title)

    def __html_encode(self, s):
        escapeChars = (
            ('>', '&gt;'),
            ('<', '&lt;'),
            ("'", '&#39;'),
            ('"', '&quot;'),
            ('&', '&amp;')
        )
        for char in escapeChars:
            s = s.replace(char[0], char[1])
        return s

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

        # Connect to window
        #self.set_titlebar(self.titlebar)
        self.add(layout)

    def update_channel(self, _, row):
        self.channel = row.channel
        self.chat.set_caption(row.channel, row.topic)
        self.chat.set_buffer(self.channel_buffers[self.channel])

    def add_channel(self, channel):

        if self.channel == None:
            self.channel = channel

        # Create buffer and a text tag
        buf = Gtk.TextBuffer()
        self.channel_buffers[channel] = buf
        self.user_tag[channel] = buf.create_tag("bold", weight=Pango.Weight.BOLD)

        # Update content
        c = Channel()
        c.set_content(channel, channel, channel)
        if not channel.startswith("#"):
            c.set_symbol("user.png")

        self.channel_tabs[channel] = c
        self.sidebar.add(c)

    def leave_channel(self, channel):
        print "LEFT", channel

    def get_channel(self):
        return self.channel

    def update_chat(self, user, channel, text):
        # Check if channel is there
        if channel not in self.channel_buffers:
            self.add_channel(channel)

        # Get users
        
        buf = self.channel_buffers[channel]
        if self.last_user.get(channel) != user:
            buf.insert_with_tags(buf.get_end_iter(), "{}\n".format(user), self.user_tag[channel])
        buf.insert(buf.get_end_iter(), "{}\n".format(text))

        self.last_user[channel] = user
        self.channel_tabs[channel].set_content(channel, channel, text[:20])


if __name__ == "__main__":

    with open("settings.json", "r") as f:
        settings = json.loads(f.read())
    
    hostname, port = settings.get("server").split(":")
    description = settings.get("description")
    credentials = settings.get("credentials")
    nickname = str(credentials.get("nickname").strip())
    password = str(credentials.get("password").strip())
    
    def a():
        Gtk.main()

    def sendmessage(entry, channel):
        print channel(), entry.get_text() 
        f.client.msg(channel(), entry.get_text())
        win.update_chat(f.client.nickname, channel(), "" + entry.get_text())
        entry.set_text("")

    def stop(*args):
        Gtk.main_quit()
        reactor.stop()
        os._exit(0)

    notify2.init('Chat')

    # Init window
    win = Interface(description)
    GObject.threads_init()
    win.show_all()
    Gdk.threads_init()

    # Connect textentry to sendmessage function
    win.entry.connect("activate", sendmessage, win.get_channel)

    # Add client with callback
    f = ClientFactory([], nickname, password, win)
    reactor.connectSSL(hostname, int(port), f, ssl.ClientContextFactory())

    #win.connect("delete-event", stop)
    win.connect("destroy", stop)

    threading.Thread(target=Gtk.main)
    Gdk.threads_leave()

    reactor.run()
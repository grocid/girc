import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

class Channel(Gtk.ListBoxRow):
    
    __gtype_name__ = 'ChannelWidget'

    def __init__(self, *args, **kwds):
        super(Channel, self).__init__(*args, **kwds)
        # Create elements
        self.symbol = Gtk.Image()
        self.symbol.set_from_file("irc.png")
        self.caption = Gtk.Label()
        self.caption.set_justify(Gtk.Justification.LEFT)

        # Fix layout
        inner = Gtk.HBox()
        inner.pack_start(self.symbol, False, False, 15)
        inner.pack_start(self.caption, False, False, 0)
        outer = Gtk.VBox()
        outer.pack_start(inner, True, True, 6)

        # Add to layout
        self.add(outer)

    def set_symbol(self, symbol):
        self.symbol.set_from_file(symbol)

    def set_content(self, channel, topic, lastmessage):
        self.channel = channel
        self.topic = topic
        self.lastmessage = lastmessage
        self.caption.set_markup("<b>{}</b>\n{}\n<small>{}</small>".format(self.channel, 
                                                                          self.topic, 
                                                                          self.lastmessage))

class Sidebar():
    def __init__(self):
        self.view = Gtk.ScrolledWindow()
        self.content = Gtk.ListBox()
        self.view.get_vscrollbar().set_visible(False)
        self.view.get_hscrollbar().set_visible(False)
        self.view.add(self.content)

    def add(self, element):
        self.content.add(element)
        self.content.show_all()

def changed(vadjust):
    vadjust.set_value(vadjust.get_upper() - vadjust.get_page_size())   

class ChatWindow():
    def __init__(self, channel, topic):
        
        header = Gtk.VBox()

        # Content view
        self.content = Gtk.TextView()
        self.content.set_property('editable', False)
        self.content.set_wrap_mode(True)
        self.content.set_cursor_visible(False)
        self.textbuffer = self.content.get_buffer()
        
        # Header
        #self.label = Gtk.Label()
        #self.set_caption(channel, topic)
        #self.label.set_justify(Gtk.Justification.CENTER)
        
        # Wrap in scrolled window
        self.view = Gtk.ScrolledWindow()
        self.view.get_vscrollbar().set_visible(False)
        self.view.add(self.content)
        
        # Put in context
        #header.pack_start(self.label, False, False, 5)
        header.pack_start(self.content, True, True, 0)
        self.view.get_vadjustment().connect("changed", changed)
       

    def set_caption(self, channel, topic):
        self.channel = channel
        self.topic = topic
        #self.label.set_markup("<b>{}</b>\n{}".format(channel, topic))

    def set_text(self, text):
        self.textbuffer.set_text(text)

    def set_buffer(self, text):
        self.content.set_buffer(text)

    def add_text(self, text):
        self.textbuffer.set_text(self.textbuffer.get_text() + text)

    def changed (vadjust):
        vadjust.set_value(vadjust.get_upper()-vadjust.get_page_size())           
        self.output_container.get_vadjustment().connect("changed", changed)        
    
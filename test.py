import gtk
from gui import chatwindow
applicationSession={'windows': {'ContactTab': {}}}
chat = chatwindow.ChatWindow(applicationSession)
from contact import Contact
c=Contact('123', 'Yaseen', '', '','','','')
chat.createChatTab(c)
gtk.main()

import asyncore
from smtpd import SMTPServer
import email.parser
import bminterface

class outgoingServer(SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data):
        parser = email.parser.FeedParser()
        parser.feed(data)
        msg = parser.close()

        toAddress = msg['To']
        fromAddress = msg['From']
        subject = msg['Subject']
        body = self._bmformat(msg)
        
        if bminterface.send(toAddress, fromAddress, subject, body):
          print "Message queued for sending..."
        else:
          print "There was an error trying to send the message..."
        
        return 0
    
    def _bmformat(self, msg):
      disclaimer = """
      <!-- Email sent from bmwrapper -->
      <!-- https://github.com/Arceliar/bmwrapper -->
      """
      imageNotice = """<!-- Note: An image is attached below -->
      """
      if not msg.is_multipart():
        #This is a single part message, so there's nothing to do.
        #Will still parse, just to get rid of awkward quote '>' everywhere.
        myText, oldText = self._parseQuoteText(msg.get_payload())
        return myText + oldText
      else:
        #This is a multipart message.
        #Unfortunately, now we have to actually do work.
        myText, oldText, image = self._recurseParse(msg)
        return disclaimer + imageNotice + myText + oldText + image
      
    def _recurseParse(self, msg):
      text = ''
      image = ''
      for item in msg.get_payload():
        if 'text/plain' in item['Content-Type']:
          text += item.get_payload()
        elif 'image' in item['Content-Type']:
          [filetype, name] = item['Content-Type'].rstrip().split('\n')
          name = name.replace('name', 'alt')
          imageraw = item.get_payload().rstrip().split('\n')
          imagedata = ''
          for line in imageraw:
            if not line[0] == '-':
              imagedata += line
          image += '<img '+name+' src="data:'+filetype+'base64,'+imagedata+'" />'
        elif 'multipart' in item['Content-Type']:
          text_new, image_new = self._recurseParse(item)
          text += text_new
          image += image_new
        else:
          #Note that there's a chance we may die horribly if nothing returns.
          pass
      firstText, text = self._parseQuoteText(text)
      return firstText, text, image

    def _parseQuoteText(self, text):
      rawText = text.split('\n')
      tempText = []
      text = ''
      firstText = ''
      n = 0
      while len(rawText):
        for line in range(len(rawText)):
          if rawText[line]:
            if rawText[line][0] == '>':
              tempText.append(rawText[line][1:])
            else:
              if n == 0:
                firstText += rawText[line]+'\n'
              else:
                text += rawText[line]+'\n'
          else:
            if n == 0:
              firstText += '\n'
            else:
              text += '\n'
        if len(tempText):
          text += '\n-------------------------------------------------------------------------------\n\n'
        rawText = tempText
        tempText = []
        n += 1
      return firstText, text
        
def run():
    foo = outgoingServer(('localhost', 12345), None)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
	run()
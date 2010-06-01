
import ctypes

WC_BLUE = 0x01
WC_GREEN = 0x02
WC_RED = 0x04

class OutputHandler:
    """A handler that hooks up with the error bundler to colorize the
    output of the application for *nix-based terminals."""
    
    def __init__(self, pipe=None):
        """Pipe is the output stream that the printed data will be
        written to. For instance, this could be a file, a StringIO
        object, or stdout."""
        
        self.pipe = pipe
        self.handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        
        # Initialize a store for the colors and populate with the
        # necessary color values.
        self.colors = {"BLUE": WC_BLUE,
                       "RED": WC_RED,
                       "GREEN": WC_GREEN,
                       "YELLOW": WC_GREEN | WC_RED,
                       "WHITE": WC_BLUE | WC_GREEN | WC_RED,
                       "BLACK": 0,
                       "NORMAL": WC_BLUE | WC_GREEN | WC_RED}
        
    
    def colorize_text(self, color):
        "Changes the color of the console depending on the color code"
        
        color_code = self.colors[color]
        
        ctypes.windll.kernel32.SetConsoleTextAttribute(self.handle,
                                                       color_code)
        
        
    def _output(self, text):
        "Outputs data to the console or a file or whatever."
        
        if self.pipe:
            self.pipe.write(text)
        else:
            sys.stdout(text)
        
    
    def write(self, text, no_color=False):
        "Uses ctypes to print in the fanciest way possible."
        
        # If there is no color, then we don't need any processing.
        if no_color:
            
            # Strip color codes out.
            pattern = re.compile("\<\<[A-Z]*?\>\>")
            text = pattern.sub("", text)
            
            self._output(text)
            return
        
        color_code = "NORMAL"
        
        # Iterate the string until there aren't any more color codes.
        while True:
            next_index = text.find("<<")
            if next_index < 0:
                break
            
            self._output(text[0:next_index])
            
            end_index = text.find(">>")
            
            # Grab out the color code and the remaining text
            color_code = text[next_index + 2:end_index]
            text = text[end_index + 2:]
            
            
            self.colorize_text(color_code)
        
        # Print anything left over.
        self._output(text)
        self._output("\n")
        
        # If the client didn't close out with a normal color code,
        # force it at the end of the message.
        if color_code != "NORMAL":
            self.colorize_text("NORMAL")
        
        return self
        

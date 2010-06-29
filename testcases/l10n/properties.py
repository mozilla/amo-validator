
class PropertiesParser(object):
    """
    Parses and serializes .properties files. Even though you can pretty
    much do this in your sleep, it's still useful for L10n tests.
    """
    
    def __init__(self, dtd):
        """
        Properties parsers can initialized based on a file path
        (provided as a string to the path), or directly (in memory as a
        StringIO object).
        """
        
        self.entities = {}
        
        if isinstance(dtd, str):
            dtd_instance = open(dtd)
            data = dtd_instance.read()
            dtd_instance.close()
        else:
            data = dtd.getvalue()
        
        split_data = data.split("\n")
        line_buffer = None
        for line in split_data:
            clean_line = line.strip()
            if not clean_line:
                continue
            if clean_line.startswith("#"):
                continue
            
            if clean_line.count("=") == 0:
                if line_buffer:
                    line_buffer[-1] += clean_line
                else:
                    continue
            else:
                if line_buffer:
                    self.entities[line_buffer[0].strip()] = \
                        line_buffer[1].strip()
                line_buffer = clean_line.split("=", 1)
        
        if line_buffer:
            self.entities[line_buffer[0].strip()] = \
                line_buffer[1].strip()
    
    def __len__(self):
        return len(self.entities)
    

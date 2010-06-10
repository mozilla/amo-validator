
import cssutils

CSS_CURRENT_ERR = None

def _fetcher(url):
    
    
    return (None, '/* no thanks :) */')
    

def test_css_file(err, filename, data):
    "Parse and test a whole CSS file."
    
    global CSS_CURRENT_ERR
    CSS_CURRENT_ERR = err
    
    parser = CSSParser()
    parser.setFetcher(_fetcher)
    
    sheet = parser.parseString(data)
    _run_css_tests(sheet)
    
def _run_css_tests(sheet):
    
    

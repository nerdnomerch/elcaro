# __builtins__.__dict__['__import__'] = __elcaro__imports__
# __builtins__.open = __elcaro__builtins__open
# __builtins__.getattr = __elcaro__builtins__getattr
# __builtins__.globals = __elcaro__builtins__globals
# __builtins__.exec = __elcaro__builtins__exec
# __builtins__.eval = __elcaro__builtins__eval
# __builtins__.exit = __elcaro__builtins__exit
# __builtins__.compile = __elcaro__builtins__compile

import json
import sys

with open(sys.argv[0] + ".result", 'w') as outfile:
    json.dump({"result": __elcora_result}, outfile)

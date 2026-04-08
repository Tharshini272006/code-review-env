import sys
import os

# Add the current directory to the path explicitly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    # This forces uvicorn to look at the app correctly
    uvicorn.run("server.app:app", host="127.0.0.1", port=7860, reload=True)
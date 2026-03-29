## Quick Start

```bash
# Create virtual environment
python3.12 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

python main.py
```

Use a stable Python 3.12 interpreter for this service. The current dependency stack can fail on Python 3.13 with `pydantic_core` import errors.

## Mac faced issue: LZMA support
If you run into an error regarding LZMA, do the following:
```
brew install xz
pyenv uninstall 3.12.0
pyenv install 3.12.0
```

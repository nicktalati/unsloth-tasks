python -m venv venv
source venv/bin/activate
pip install python-language-server pylsp-mypy mypy
pip install -e ".[core-depless]"
pip install ".[core]"

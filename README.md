# Time Recorder
Simple time recorder app.

**Main Display**

![main_display](./main_screen.png)

## Run

```
# install

python -m pip install https://github.com/sgooding/time_recorder/releases/download/v0.1.0/time_recorder-0.1.0-py3-none-any.whl

# run
time_recorder

```

## Build

**Development Build**
```
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .

# run
time_recorder
```


## Setup

* `pyside6-designer` - edit the .ui file.
* `pyside6-uic` - window.ui -o ui_window.py


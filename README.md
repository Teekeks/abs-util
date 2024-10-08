# Audiobookshelf Utility

Utility program for various things related to your own Audiobookshelf instance.

> [!NOTE]
> This tool is mostly for personal use, you can request new features or bug fixes via issues but I do not guarantee any support

## Install

Python 3.12 is required to run this.

### Using pipx

```bash
pipx install git+https://github.com/Teekeks/abs-util.git --python python3.12
```

### Using pip

```bash
pip install -r ./requirements.txt
```

## Usage

```bash
abs_util <action>
```

Available actions

- `setup`: Used to set up your default Audiobookshelf credentials
- `clear-authors`: Remove authors with no books from either all or selected libraries
- `goodreads-folder-import`: Create ABS compatible folders from Goodreads Series Link
- `kobo-sync`: Sync a library with a USB connected Kobo Reader


### Example usees

- Syncing the "books" library to your kobo device which is mounted on G:\

```bash
abs_util kobo-sync -l books -kdir G:\
```

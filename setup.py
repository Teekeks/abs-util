from setuptools import setup, find_packages

version = ''

with open('abs_util/__init__.py') as f:
    for line in f.readlines():
        if line.startswith('__version__'):
            version = line.split('= \'')[-1][:-2].strip()

if version.endswith(('a', 'b', 'rc')):
    try:
        import subprocess
        p = subprocess.Popen(['git', 'rev-list', '--count', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += out.decode('utf-8').strip()
        p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += '+g' + out.decode('utf-8').strip()
    except:
        pass

setup(
    packages=find_packages(),
    version=version,
    python_requires='>=3.12',
    keywords=['audiobookshelf'],
    entry_points={
        'console_scripts': ['abs_util=abs_util.main:run'],
    },
    install_requires=[
        'pick',
        'audiobookshelf@git+https://github.com/Teekeks/audiobookshelfAPI.git',
        'colorama~=0.4.6',
        'prompt_toolkit',
        'aiosqlite',
        'beautifulsoup4',
        'aiohttp'
    ],
    package_data={'abs_util': ['py.typed']}
)

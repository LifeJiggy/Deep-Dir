"""
DeepDir - Advanced Directory Enumeration Tool
"""

__version__ = "1.0.0"
__author__ = "ArkhAngelLifeJiggy"
__email__ = "Bloomtonjovish@gmail.com"
__url__ = "https://github.com/LifeJiggy/Deep-Dir.git"

def main():
    """Main entry point for the deepdir command"""
    from .deepdir import main as _main
    _main()

__all__ = ["main"]
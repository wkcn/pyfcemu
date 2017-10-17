import sys
import ui

def getPaths():
    if len(sys.argv) >= 2:
        name = sys.argv[1]
        if name.split('.')[-1].lower() == "nes":
            return [name]
    return []

def main():
    paths = getPaths()
    if len(paths) == 0:
        print ("no rom files specified or found")
        return
    ui.Run(paths)

if __name__ == "__main__":
    main()

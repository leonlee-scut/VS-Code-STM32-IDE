'''
Common utilities for 'update*.py' scripts.

This script can be called standalone to verify if folder structure is correct and to print out all workspace
paths.
'''

import os
import shutil
import subprocess
import sys
import traceback
import platform

import templateStrings as tmpStr

__version__ = '1.4'  # this is inherited by all 'update*.py' scripts

########################################################################################################################
# Global utilities and paths
########################################################################################################################

workspacePath = None  # absolute path to workspace folder
workspaceFilePath = None  # absolute file path to '*.code-workspace' file
cubeMxProjectFilePath = None  # absolute path to *.ioc STM32CubeMX workspace file
ideScriptsPath = None  # absolute path to 'ideScripts' folder

makefilePath = None
makefileBackupPath = None
cPropertiesPath = None
cPropertiesBackupPath = None
buildDataPath = None
toolsPaths = None  # absolute path to toolsPaths.json with common user settings
tasksPath = None
tasksBackupPath = None
launchPath = None
launchBackupPath = None


def printAndQuit(msg):
    '''
    Unrecoverable error, print and quit with system
    '''
    msg = "\n**** ERROR (unrecoverable) ****\n" + str(msg)
    print(msg)

    if sys.exc_info()[2]:  # was exception raised?
        print("\nTraceback:")
        traceback.print_exc()
    sys.exit(1)


def pathExists(path):
    if path is not None:
        if os.path.exists(path):
            return True
        elif shutil.which(path): # This adds support for commands on PATH
            return True
        else:
            return False
    else:
        return False


def detectOS():
    '''
    This function detects the operating system that python is running in. We use this for OS specific operations
    '''
    if os.name == "nt":
        osIs = "windows"
    elif os.name == "java":
        osIs = "java"
    elif os.name == "posix":
        release = platform.release() #get system release
        release = release.lower()
        if release.endswith("microsoft"): # Detect windows subsystem for linux (wsl)
            osIs = "wsl"
        else:
            osIs = "unix"
    return osIs


def copyAndRename(filePath, newName):
    if not pathExists(filePath):
        errorMsg = "Can't copy and rename file " + str(filePath) + ", does not exist or other error."
        printAndQuit(errorMsg)

    fileFolderPath = os.path.dirname(filePath)
    copyFilePath = os.path.join(fileFolderPath, newName)
    shutil.copyfile(filePath, copyFilePath)

    msg = "Copy of file (new name: " + newName + "):\n\t" + str(filePath)
    print(msg)


def verifyFolderStructure():
    '''
    Verify if folder structure is correct.
    'ideScript' folder must be placed in the root of the project, where:
        - exactly one '*.code-workspace' file must exist (this is also Workspace name)
        - '.vscode' folder is present (it is created if it doesn't exist jet)

    If this requirements are met, all paths are built - but not checked (they are checked in their respective .py files).
        - build, launch, tasks, cpp properties files
        - Makefile
        - STM32CubeMX '.ioc'
        - backup file paths
    '''
    global workspacePath
    global workspaceFilePath
    global cubeMxProjectFilePath
    global ideScriptsPath

    global makefilePath
    global makefileBackupPath
    global cPropertiesPath
    global cPropertiesBackupPath
    global buildDataPath
    global toolsPaths
    global tasksPath
    global tasksBackupPath
    global launchPath
    global launchBackupPath

    thisFolderPath = os.path.dirname(sys.argv[0])
    workspacePath = pathWithForwardSlashes(os.path.dirname(thisFolderPath))
    ideScriptsPath = pathWithForwardSlashes(os.path.join(workspacePath, 'ideScripts'))

    codeWorkspaces = getCodeWorkspaces()
    if len(codeWorkspaces) == 1:
        # '*.code-workspace' file found
        workspaceFilePath = codeWorkspaces[0]  # file existance is previously checked in getCodeWorkspaces()
    else:
        errorMsg = "Invalid folder/file structure:\n"
        errorMsg += "Exactly one VS Code workspace ('*.code-workspace') file must exist "
        errorMsg += "in the root folder where 'ideScripts' folder is placed.\n"
        errorMsg += "Expecting one '*.code-workspace' file in: " + workspacePath
        printAndQuit(errorMsg)

    vscodeFolder = pathWithForwardSlashes(os.path.join(workspacePath, ".vscode"))
    if not pathExists(vscodeFolder):
        try:
            os.mkdir(vscodeFolder)
            print("'.vscode' folder created.")
        except Exception as err:
            errorMsg = "Exception error creating '.vscode' subfolder:\n" + str(err)
            printAndQuit(errorMsg)
    else:
        print("Existing '.vscode' folder used.")

    # 'ideScripts' folder found in the same folder as '*.code-workspace' file. Structure seems OK.
    cPropertiesPath = os.path.join(workspacePath, '.vscode', 'c_cpp_properties.json')
    cPropertiesPath = pathWithForwardSlashes(cPropertiesPath)
    cPropertiesBackupPath = cPropertiesPath + ".backup"

    makefilePath = os.path.join(workspacePath, 'Makefile')
    makefilePath = pathWithForwardSlashes(makefilePath)
    makefileBackupPath = makefilePath + ".backup"

    buildDataPath = os.path.join(workspacePath, '.vscode', 'buildData.json')
    buildDataPath = pathWithForwardSlashes(buildDataPath)
    # does not have backup file, always regenerated

    # TODO make this not hard-coded
    osIs = detectOS()
    if osIs == "windows":
        vsCodeSettingsFolderPath = os.path.expandvars("%APPDATA%\\Code\\User\\")
    elif osIs == "unix":
        vsCodeSettingsFolderPath = os.path.expandvars("$HOME/.config/Code/User/")
    toolsPaths = os.path.join(vsCodeSettingsFolderPath, 'toolsPaths.json')
    toolsPaths = pathWithForwardSlashes(toolsPaths)

    tasksPath = os.path.join(workspacePath, '.vscode', 'tasks.json')
    tasksPath = pathWithForwardSlashes(tasksPath)
    tasksBackupPath = tasksPath + ".backup"

    launchPath = os.path.join(workspacePath, '.vscode', 'launch.json')
    launchPath = pathWithForwardSlashes(launchPath)
    launchBackupPath = launchPath + ".backup"

    cubeMxFiles = getCubeMXProjectFiles()
    if len(cubeMxFiles) == 1:
        cubeMxProjectFilePath = cubeMxFiles[0]
        print("One STM32CubeMX file found: " + cubeMxProjectFilePath)
    else:  # more iocFiles:
        cubeMxProjectFilePath = None
        print("WARNING: None or more than one STM32CubeMX files found. None or one expected.")


def printWorkspacePaths():
    print("\nWorkspace root folder:", workspacePath)
    print("VS Code workspace file:", workspaceFilePath)
    print("CubeMX project file:", cubeMxProjectFilePath)
    print("'ideScripts' folder:", ideScriptsPath)

    print("\n'Makefile':", makefilePath)
    print("'Makefile.backup':", makefileBackupPath)

    print("\n'c_cpp_properties.json':", cPropertiesPath)
    print("'c_cpp_properties.json.backup':", cPropertiesBackupPath)

    print("\n'buildData.json':", buildDataPath)
    print("'toolsPaths.json':", toolsPaths)

    print("\n'tasks.json':", tasksPath)
    print("'tasks.json.backup':", tasksBackupPath)

    print("\n'launch.json':", launchPath)
    print("'launch.json.backup':", launchBackupPath)
    print()


def getCubeMXProjectFiles():
    '''
    Returns list of all STM32CubeMX '.ioc' files in root directory.
    '''
    iocFiles = []
    for theFile in os.listdir(workspacePath):
        if theFile.endswith('.ioc'):
            filePath = pathWithForwardSlashes(os.path.join(workspacePath, theFile))
            iocFiles.append(filePath)

    return iocFiles


def createBuildFolder(folderName='build'):
    '''
    Create (if not already created) build folder with specified name where objects are stored when 'make' is executed.
    '''
    buildFolderPath = os.path.join(workspacePath, folderName)
    if not pathExists(buildFolderPath):
        os.mkdir(buildFolderPath)
        print("Build folder created: " + buildFolderPath)
    else:
        print("Build folder already exist: '" + buildFolderPath + "'")


def getCubeWorkspaces():
    '''
    Search workspacePath for files that ends with '.ioc' (STM32CubeMX projects).
    Returns list of all available STM32CubeMX workspace paths.

    Only root directory is searched.
    '''
    iocFiles = []

    for theFile in os.listdir(workspacePath):
        if theFile.endswith(".ioc"):
            theFilePath = os.path.join(workspacePath, theFile)
            iocFiles.append(pathWithForwardSlashes(theFile))

    return iocFiles


def getCodeWorkspaces():
    '''
    Search workspacePath for files that ends with '.code-workspace' (VS Code workspaces).
    Returns list of all available VS Code workspace paths.

    Only root directory is searched.
    '''
    codeFiles = []

    for theFile in os.listdir(workspacePath):
        if theFile.endswith(".code-workspace"):
            theFilePath = os.path.join(workspacePath, theFile)
            codeFiles.append(pathWithForwardSlashes(theFilePath))

    return codeFiles


def getWorkspaceName():
    '''
    Return name (without extension) for this project '.code-workspace' file.

    Return first available file name without extension.
    '''
    _, fileNameExt = os.path.split(workspaceFilePath)
    fileName, _ = os.path.splitext(fileNameExt)
    return fileName


def stripStartOfString(dataList, stringToStrip):
    newData = []

    for data in dataList:
        if data.find(stringToStrip) != -1:
            item = data[len(stringToStrip):]
            newData.append(item)
        else:
            newData.append(data)

    return newData


def preappendString(data, stringToAppend):
    if type(data) is list:
        for itemIndex, item in enumerate(data):
            data[itemIndex] = stringToAppend + item
    else:
        data = stringToAppend + data

    return data


def stringToList(string, separator):
    '''
    Get list of unparsed string items into list. Strip any redundant spaces.
    '''
    allItems = []
    items = string.split(separator)
    for item in items:
        item = item.strip()
        allItems.append(item)

    return allItems


def getYesNoAnswer(msg):
    '''
    Asks the user a generic yes/no question.
    Returns True for yes, False for no
    '''
    while(True):
        resp = input(msg).lower()
        if resp == 'y':
            return True
        elif resp == 'n':
            return False
        else:
            continue


def getUserPath(pathName):
    '''
    Get absolute path from user (by entering path in terminal window).
    Repeated as long as user does not enter a valid path to file/folder.
    '''
    while True:
        msg = "\n\tEnter path to '" + pathName + "':\n\tPaste here and press Enter: "
        path = input(msg)
        path = path.replace('\"', '')  # remove " "
        path = path.replace('\'', '')  # remove ' '
        path = pathWithForwardSlashes(path)

        if pathExists(path):
            break
        else:
            print("\tPath not valid: ", path)

    return path


def pathWithForwardSlashes(path):
    path = os.path.normpath(path)
    path = path.replace("\\", "/")
    return path


def getGccIncludePath(gccExePath):
    '''
    Get path to '...\include' folder from 'gccExePath', where standard libs and headers. Needed for VS Code Intellisense.

    If ARM GCC folder structure remains the same as official, the executable is located in \bin folder.
    Other headers can be found in '\lib\gcc\arm-none-eabi\***\include' folder, which is found by searching for
    <stdint.h>.
    '''
    gccExeFolderPath = os.path.dirname(gccExePath)
    gccFolderPath = os.path.dirname(gccExeFolderPath)
    searchPath = os.path.join(gccFolderPath, "lib", "gcc", "arm-none-eabi")

    searchForFile = "stdint.h"
    for root, dirs, files in os.walk(searchPath, topdown=False):
        if searchForFile in files:
            folderPath = pathWithForwardSlashes(root)
            return folderPath

    errorMsg = "Unable to find 'include' subfolder with " + searchForFile + " file on path:\n\t"
    errorMsg += searchPath
    printAndQuit(errorMsg)

def getPython3Path():
    '''
    Uses detectOs() to determine the correct python command to use for python related tasks
    '''
    osIs = detectOS()

    if osIs == "unix" or osIs == "wsl": # detected unix based system
        pythonPath = "python3"
    else: # windows or other system
        pythonPath = "python"

    if not pathExists(pythonPath):
        msg = "\n\tPython version 3 or later installation not detected, please install or enter custom path below."
        print(msg)
        pythonPath = getUserPath(pythonPath)

    return pythonPath


def getOpenOcdConfig(openOcdPath):
    '''
    Get openOCD configuration from user, eg. '-f interface/stlink.cfg -f target/stm32f0x.cfg'
    Returns the absolute path to these config files.

    Default (official) folder structure:
    /bin/
        -/openocd (executable)
    /share/
        -/openocd/
            - /scripts/
                - /target/ (stm32f0x.cfg)
                - /interface/ (stlink.cfg)
                - etc
    '''
    openOcdExePath = os.path.dirname(openOcdPath) # ../bin
    openOcdRootPath = os.path.dirname(openOcdExePath) # ../
    openOcdScriptsPath = os.path.join(openOcdRootPath, "share", "openocd", "scripts") # ../share/openocd/scripts

    while(True):
        msg = "\n\tEnter OpenOCD configuration files (eg: '-f interface/stlink.cfg -f target/stm32f0x.cfg):\n\tconfig files: "
        config = input(msg)
        config = pathWithForwardSlashes(config)

        # split config into list, seperating the arguments
        config = config.split()
        configPaths = list()
        for arg in config:
            if pathExists(openOcdScriptsPath + "/" + arg):
                msg = "\tConfiguration file '" + arg + "' detected successfully"
                print(msg)
                configPaths.append(openOcdScriptsPath + "/" + arg)
            elif arg.startswith("-"):
                continue
            else:
                msg = "\tConfiguration invalid: '" + arg + "' not found in " + openOcdScriptsPath
                print(msg)
                break
        else:
            break # break loop if config detected successfully
        continue # continue if unsuccessful

    return configPaths


def getStm32SvdFile(stm32SvdPath):
    '''
    Get stm32SvdFile from user, eg. 'STM32F042x.svd'
    Validates that file exists
    '''
    while True:
        msg = "\n\tEnter SVD File name (eg: 'STM32F042x.svd'), or 'ls' to list available SVD files.\n\tSVD file name: "
        fileName = input(msg)
        if fileName == "ls":
            print(os.listdir(stm32SvdPath))
            continue
        if pathExists(stm32SvdPath + "/" + fileName):
            break
        else:
            print("\tSVD File '" + fileName + "' not found")
            continue

    return fileName


def getBuildElfFilePath(buildDirPath, projectName):
    '''
    Returns .elf file path.
    '''
    elfFile = projectName + ".elf"
    buildFileName = os.path.join(workspacePath, buildDirPath, elfFile)
    buildFileName = pathWithForwardSlashes(buildFileName)

    return buildFileName


def getAllFilesInFolderTree(pathToFolder):
    '''
    Get the list of all files in directory tree at given path
    '''
    allFiles = []
    if os.path.exists(pathToFolder):
        for (dirPath, dirNames, fileNames) in os.walk(pathToFolder):
            for theFile in fileNames:
                filePath = os.path.join(dirPath, theFile)
                filePath = pathWithForwardSlashes(filePath)
                allFiles.append(filePath)

    return allFiles


def findExecutablePath(extension, raiseException=False):
    '''
    Find default associated path of a given file extension, for example 'pdf'.
    '''
    arguments = "for /f \"delims== tokens=2\" %a in (\'assoc "
    arguments += "." + extension
    arguments += "\') do @ftype %a"

    errorMsg = "Unable to get associated program for ." + extension + "."
    try:
        proc = subprocess.run(arguments, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        if proc.returncode == 0:
            returnString = str(proc.stdout)
            path = returnString.split('=')[1]
            path = path.split('\"')[0]
            path = path.strip()
            path = os.path.normpath(path)
            if os.path.exists(path):
                return path
        else:
            print(errorMsg)

    except Exception as err:
        errorMsg += "Exception:\n" + str(err)

    if raiseException:
        raise Exception(errorMsg)
    else:
        return None


########################################################################################################################
if __name__ == "__main__":
    print("Workspace generation script version: " + __version__)
    verifyFolderStructure()
    print("This workspace name:", getWorkspaceName())
    printWorkspacePaths()
